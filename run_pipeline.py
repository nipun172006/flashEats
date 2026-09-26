from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import time

import pandas as pd
import requests

from pipeline.config import PipelineConfig
from pipeline.logging_utils import build_logger
from pipeline.extract import extract_local_sources, extract_dispatch_api
from pipeline.validate import ValidationError, run_raw_validations
from pipeline.clean import clean_orders, clean_event_source
from pipeline.transform import build_order_journey
from pipeline.metrics import build_metrics
from pipeline.save import save_outputs


def wait_for_health(api_url: str, timeout_seconds: int = 8) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            if requests.get(f"{api_url}/health", timeout=1).status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.2)
    return False


def maybe_start_mock_api(config, logger):
    if not config.start_mock_api:
        logger.info("Mock API autostart disabled")
        return None
    if wait_for_health(config.dispatch_api_url, timeout_seconds=1):
        logger.info("Dispatch API already running")
        return None

    script = config.project_root / "api" / "mock_dispatch_api.py"
    logger.info("Starting local HTTP dispatch API")
    process = subprocess.Popen([sys.executable, str(script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not wait_for_health(config.dispatch_api_url):
        process.terminate()
        raise RuntimeError("Mock dispatch API did not become healthy")
    logger.info("Mock dispatch API is healthy")
    return process


def apply_chaos_scenario(sources, scenario, logger):
    if scenario == "none":
        return sources
    sources = dict(sources)
    orders = sources["orders"].copy()
    if scenario == "missing_column":
        logger.warning("CHAOS: dropping promised_eta to simulate schema break")
        orders = orders.drop(columns=["promised_eta"])
    elif scenario == "duplicate_order":
        logger.warning("CHAOS: injecting an extra duplicate order")
        orders = pd.concat([orders, orders.iloc[[0]].copy()], ignore_index=True)
    elif scenario == "stale_data":
        logger.warning("CHAOS: shifting created_at backward by 365 days")
        parsed = pd.to_datetime(orders["created_at"], format="mixed", errors="coerce")
        orders["created_at"] = (parsed - pd.Timedelta(days=365)).astype(str)
    else:
        raise ValueError(f"Unknown chaos scenario: {scenario}")
    sources["orders"] = orders
    return sources


def _write_evidence_table(project_root: Path, run_date: str, metrics: dict, validation_results):
    rows = [
        {"metric": "Late Delivery Rate", "value": metrics["late_delivery_rate_pct"], "unit": "%", "definition": "late KPI-eligible delivered orders / KPI-eligible delivered orders"},
        {"metric": "Median Order-to-Pickup Time", "value": metrics["median_order_to_pickup_min"], "unit": "min", "definition": "median(pickup_at - created_at) among KPI-eligible delivered orders"},
        {"metric": "Median Pickup-to-Delivery Transit", "value": metrics["median_transit_min"], "unit": "min", "definition": "median(actual_delivery_at - pickup_at) among KPI-eligible delivered orders"},
        {"metric": "Intervention Rate", "value": metrics["intervention_rate_pct"], "unit": "%", "definition": "orders with >=1 recorded intervention / all unique orders"},
        {"metric": "Customer Interaction Rate", "value": metrics["customer_interaction_rate_pct"], "unit": "%", "definition": "orders with >=1 retained customer interaction / all unique orders"},
    ]
    from csv import DictWriter
    path = project_root / "data" / "processed" / f"run_date={run_date}" / "evidence_table.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = DictWriter(f, fieldnames=["metric", "value", "unit", "definition"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def _write_source_manifest(project_root: Path, run_date: str, sources, dispatch, validation_results):
    manifest = {
        "run_date": run_date,
        "inputs": {name: int(len(df)) for name, df in sources.items()},
        "dispatch_rows": int(len(dispatch)),
        "validation_summary": {
            "PASS": sum(r.status == "PASS" for r in validation_results),
            "WARN": sum(r.status == "WARN" for r in validation_results),
            "FAIL": sum(r.status == "FAIL" for r in validation_results),
        },
    }
    path = project_root / "data" / "processed" / f"run_date={run_date}" / "run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2))
    return path


def run(run_date: date, chaos: str):
    project_root = Path(__file__).resolve().parent
    config = PipelineConfig.from_env(project_root)
    logger = build_logger(project_root / "logs" / f"pipeline_{run_date.isoformat()}.log", config.log_level)
    raw_root = project_root / "data" / "raw" / f"run_date={run_date.isoformat()}"
    raw_dispatch_dir = raw_root / "dispatch"
    api_process = None

    try:
        logger.info("Pipeline started | run_date=%s chaos=%s", run_date, chaos)
        api_process = maybe_start_mock_api(config, logger)

        # 1. EXTRACT
        sources = extract_local_sources(project_root, raw_root, logger)
        sources = apply_chaos_scenario(sources, chaos, logger)
        dispatch = extract_dispatch_api(
            api_url=config.dispatch_api_url,
            page_size=config.page_size,
            max_retries=config.max_retries,
            retry_base_seconds=config.retry_base_seconds,
            raw_output_dir=raw_dispatch_dir,
            logger=logger,
        )

        # 2. VALIDATE RAW INPUTS — no published processed output before this gate.
        validation_results = run_raw_validations(
            orders=sources["orders"],
            dispatch=dispatch,
            interactions=sources["interactions"],
            interventions=sources["interventions"],
            run_date=run_date,
            max_age_days=config.max_data_age_days,
        )
        for result in validation_results:
            logger.info("Validation | check=%s status=%s detail=%s", result.check, result.status, result.detail)

        # 3. CLEAN
        orders = clean_orders(sources["orders"], logger)
        interactions = clean_event_source(sources["interactions"], "interaction_id", "interaction_at", logger)
        interventions = clean_event_source(sources["interventions"], "intervention_id", "intervention_at", logger)

        # 4. TRANSFORM TO ONE ROW PER ORDER + METRICS
        journey = build_order_journey(
            orders=orders,
            interactions=interactions,
            interventions=interventions,
            dispatch=dispatch,
            logger=logger,
        )
        metrics = build_metrics(journey)

        # 5. SAVE
        outputs = save_outputs(journey, metrics, validation_results, project_root, run_date.isoformat(), logger)
        _write_source_manifest(project_root, run_date.isoformat(), sources, dispatch, validation_results)
        evidence_path = _write_evidence_table(project_root, run_date.isoformat(), metrics, validation_results)

        logger.info("Pipeline completed successfully | rows=%s output=%s evidence=%s", len(journey), outputs["journey"], evidence_path)
        print("\nPIPELINE SUCCESS")
        print(json.dumps(metrics, indent=2))
        print("\nOutputs:")
        for key, path in outputs.items():
            print(f"  {key}: {path}")
        return 0

    except ValidationError as exc:
        logger.error("Pipeline stopped at validation gate | error=%s | no processed output published", exc)
        print(f"\nPIPELINE FAILED: {exc}")
        return 2
    except Exception as exc:
        logger.exception("Pipeline failed unexpectedly | error=%s", exc)
        print(f"\nPIPELINE FAILED: {exc}")
        return 1
    finally:
        if api_process is not None:
            api_process.terminate()
            try:
                api_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                api_process.kill()


def parse_args():
    parser = argparse.ArgumentParser(description="Run the FlashEats Assessment 2 dependable data pipeline")
    parser.add_argument("--run-date", default=date.today().isoformat(), help="Logical run date in YYYY-MM-DD")
    parser.add_argument("--chaos", default="none", choices=["none", "missing_column", "duplicate_order", "stale_data"], help="Failure scenario for dependability demos")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        logical_run_date = date.fromisoformat(args.run_date)
    except ValueError as exc:
        raise SystemExit("--run-date must use YYYY-MM-DD") from exc
    raise SystemExit(run(logical_run_date, args.chaos))

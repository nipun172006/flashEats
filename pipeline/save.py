from pathlib import Path
import json
import os
import tempfile


def atomic_write_text(text: str, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, dir=destination.parent) as tmp:
        temp_path = Path(tmp.name)
        tmp.write(text)
    try:
        os.replace(temp_path, destination)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def atomic_write_csv(df, destination: Path):
    import pandas as pd  # local import keeps save.py focused on output behavior
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".csv", delete=False, dir=destination.parent) as tmp:
        temp_path = Path(tmp.name)
    try:
        df.to_csv(temp_path, index=False)
        os.replace(temp_path, destination)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def save_outputs(journey, metrics, validation_results, project_root: Path, run_date: str, logger):
    partition = project_root / "data" / "processed" / f"run_date={run_date}"
    partition.mkdir(parents=True, exist_ok=True)
    journey_path = partition / "order_journey.csv"
    metrics_path = partition / "metrics.json"
    validation_path = partition / "validation_report.json"

    atomic_write_csv(journey, journey_path)
    atomic_write_text(json.dumps(metrics, indent=2), metrics_path)
    payload = [{"check": r.check, "status": r.status, "detail": r.detail} for r in validation_results]
    atomic_write_text(json.dumps(payload, indent=2), validation_path)

    logger.info("Saved outputs | partition=%s", partition)
    return {"journey": journey_path, "metrics": metrics_path, "validation": validation_path}

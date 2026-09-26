from pathlib import Path
import json
import sqlite3
import time

import pandas as pd
import requests


class RetryableAPIError(RuntimeError):
    pass


class NonRetryableAPIError(RuntimeError):
    pass


LOCAL_TABLES = ["orders", "customers", "drivers", "restaurants"]


def extract_local_sources(project_root: Path, raw_output_dir: Path, logger):
    db_path = project_root / "database" / "flasheats.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with sqlite3.connect(db_path) as con:
        extracted = {table: pd.read_sql(f"SELECT * FROM {table}", con) for table in LOCAL_TABLES}

    data_dir = project_root / "data"
    extracted["interactions"] = pd.read_csv(data_dir / "customer_interactions.csv")
    extracted["interventions"] = pd.read_csv(data_dir / "order_interventions.csv")

    # Preserve local raw snapshots so the same run can be audited/replayed.
    local_raw_dir = raw_output_dir / "local"
    local_raw_dir.mkdir(parents=True, exist_ok=True)
    for table, df in extracted.items():
        df.to_csv(local_raw_dir / f"{table}.csv", index=False)

    logger.info(
        "Extracted local sources | orders=%s customers=%s drivers=%s restaurants=%s interactions=%s interventions=%s",
        len(extracted["orders"]), len(extracted["customers"]), len(extracted["drivers"]),
        len(extracted["restaurants"]), len(extracted["interactions"]), len(extracted["interventions"]),
    )
    return extracted


def _request_page(session, url, page, page_size, max_retries, base_seconds, logger):
    for attempt in range(1, max_retries + 1):
        try:
            response = session.get(
                f"{url}/dispatch/orders",
                params={"page": page, "page_size": page_size},
                timeout=5,
            )
            if response.status_code == 200:
                return response.json()

            if response.status_code in {429, 500, 502, 503, 504}:
                retry_after = response.headers.get("Retry-After")
                if response.status_code == 429:
                    try:
                        retry_after = response.json().get("retry_after_seconds", retry_after)
                    except Exception:
                        pass
                wait_seconds = float(retry_after) if retry_after is not None else base_seconds * (2 ** (attempt - 1))
                logger.warning(
                    "Retryable dispatch API failure | page=%s status=%s attempt=%s/%s wait=%.2fs",
                    page, response.status_code, attempt, max_retries, wait_seconds,
                )
                if attempt < max_retries:
                    time.sleep(wait_seconds)
                    continue
                raise RetryableAPIError(
                    f"Dispatch API page {page} failed after {max_retries} attempts; status={response.status_code}"
                )

            raise NonRetryableAPIError(
                f"Dispatch API returned non-retryable status {response.status_code} on page {page}"
            )
        except requests.RequestException as exc:
            wait_seconds = base_seconds * (2 ** (attempt - 1))
            logger.warning(
                "Dispatch API request exception | page=%s attempt=%s/%s error=%s",
                page, attempt, max_retries, exc,
            )
            if attempt < max_retries:
                time.sleep(wait_seconds)
                continue
            raise RetryableAPIError(
                f"Dispatch API page {page} failed after {max_retries} attempts: {exc}"
            ) from exc


def extract_dispatch_api(api_url, page_size, max_retries, retry_base_seconds, raw_output_dir: Path, logger):
    raw_output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    page = 1
    rows = []
    expected_total = None

    while True:
        payload = _request_page(session, api_url, page, page_size, max_retries, retry_base_seconds, logger)
        (raw_output_dir / f"dispatch_page_{page:03d}.json").write_text(json.dumps(payload, indent=2))

        if expected_total is None:
            expected_total = int(payload.get("total_records", 0))
        page_rows = payload.get("data", [])
        rows.extend(page_rows)
        logger.info("Fetched dispatch API page | page=%s rows=%s cumulative=%s", page, len(page_rows), len(rows))
        if not payload.get("has_more", False):
            break
        page += 1

    received_unique = len({r.get("order_id") for r in rows})
    if expected_total and len(rows) != expected_total:
        raise ValueError(f"Dispatch retrieval incomplete: expected={expected_total}, received={len(rows)}")
    if expected_total and received_unique != expected_total:
        raise ValueError(f"Dispatch retrieval not unique: expected_unique={expected_total}, received_unique={received_unique}")

    logger.info("Dispatch extraction complete | records=%s expected=%s unique_order_ids=%s", len(rows), expected_total, received_unique)
    return pd.DataFrame(rows)

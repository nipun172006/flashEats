from dataclasses import dataclass
from datetime import date
import pandas as pd


class ValidationError(ValueError):
    pass


@dataclass
class CheckResult:
    check: str
    status: str
    detail: str


ORDER_REQUIRED_COLUMNS = {
    "order_id", "customer_id", "restaurant_id", "created_at", "promised_eta",
    "pickup_at", "actual_delivery_at", "final_status",
}


def validate_required_columns(df, required_columns, dataset_name):
    missing = sorted(set(required_columns) - set(df.columns))
    if missing:
        raise ValidationError(f"{dataset_name}: missing required columns: {missing}")
    return CheckResult(f"{dataset_name}.required_columns", "PASS", f"{len(required_columns)} required columns present")


def validate_order_uniqueness(orders):
    duplicate_rows = int(orders.duplicated("order_id", keep=False).sum())
    status = "WARN" if duplicate_rows else "PASS"
    return CheckResult("orders.order_id_uniqueness", status, f"duplicate rows involved={duplicate_rows}; unique_order_ids={orders.order_id.nunique()}")


def validate_auxiliary_id_uniqueness(df, id_col, dataset_name):
    dup_rows = int(df.duplicated(id_col, keep=False).sum())
    status = "WARN" if dup_rows else "PASS"
    return CheckResult(f"{dataset_name}.{id_col}_uniqueness", status, f"duplicate rows involved={dup_rows}")


def validate_critical_nulls(orders):
    status_norm = orders["final_status"].astype(str).str.strip().str.lower()
    delivered = status_norm.eq("delivered")
    missing_actual = int((delivered & orders["actual_delivery_at"].isna()).sum())
    status = "WARN" if missing_actual else "PASS"
    return CheckResult("orders.delivered_completion_timestamp", status, f"delivered rows missing actual_delivery_at={missing_actual}")


def validate_timestamp_chronology(orders):
    parsed = orders.copy()
    for c in ["created_at", "promised_eta", "pickup_at", "actual_delivery_at"]:
        parsed[c] = pd.to_datetime(parsed[c], format="mixed", errors="coerce")
    bad_promised = int((parsed["promised_eta"] < parsed["created_at"]).fillna(False).sum())
    bad_pickup = int((parsed["pickup_at"] < parsed["created_at"]).fillna(False).sum())
    bad_delivery = int((parsed["actual_delivery_at"] < parsed["pickup_at"]).fillna(False).sum())
    total = bad_promised + bad_pickup + bad_delivery
    status = "WARN" if total else "PASS"
    return CheckResult(
        "orders.timestamp_chronology", status,
        f"promised_before_created={bad_promised}; pickup_before_created={bad_pickup}; delivery_before_pickup={bad_delivery}",
    )


def validate_freshness(orders, run_date: date, max_age_days: int):
    parsed = pd.to_datetime(orders["created_at"], format="mixed", errors="coerce")
    latest = parsed.max()
    if pd.isna(latest):
        raise ValidationError("orders freshness check failed: no parseable created_at values")
    age_days = (pd.Timestamp(run_date) - latest.normalize()).days
    if age_days > max_age_days:
        raise ValidationError(f"orders data is stale: latest_created_at={latest}, age_days={age_days}, allowed={max_age_days}")
    return CheckResult("orders.freshness", "PASS", f"latest_created_at={latest}; age_days={age_days}; allowed={max_age_days}")


def validate_dispatch(dispatch):
    return validate_required_columns(dispatch, {"order_id", "current_delivery_eta"}, "dispatch")


def validate_cross_source_keys(orders, dispatch, interactions, interventions):
    order_ids = set(orders["order_id"])
    checks = []
    for name, df in [("dispatch", dispatch), ("customer_interactions", interactions), ("order_interventions", interventions)]:
        missing = int((~df["order_id"].isin(order_ids)).sum())
        status = "FAIL" if missing else "PASS"
        detail = f"rows_with_unknown_order_id={missing}"
        result = CheckResult(f"{name}.order_id_referential_integrity", status, detail)
        if status == "FAIL":
            raise ValidationError(f"{name} references unknown orders: {missing} rows")
        checks.append(result)
    return checks


def validate_kpi_eligibility(orders):
    # Validate KPI counts at the agreed business grain so raw duplicate rows do not
    # inflate the denominator. Cleaning later applies the same one-row-per-order rule.
    unique_orders = orders.drop_duplicates("order_id", keep="first").copy()
    status_norm = unique_orders["final_status"].astype(str).str.strip().str.lower()
    cancelled = int(status_norm.eq("cancelled").sum())
    eligible = int((status_norm.eq("delivered") & unique_orders["actual_delivery_at"].notna() & unique_orders["promised_eta"].notna()).sum())
    missing_delivery = int((status_norm.eq("delivered") & unique_orders["actual_delivery_at"].isna()).sum())
    detail = f"eligible={eligible}; cancelled_excluded={cancelled}; delivered_missing_actual={missing_delivery}; grain=unique_order_id"
    return CheckResult("kpi.eligibility", "PASS", detail)


def run_raw_validations(orders, dispatch, interactions, interventions, run_date, max_age_days):
    results = [
        validate_required_columns(orders, ORDER_REQUIRED_COLUMNS, "orders"),
        validate_order_uniqueness(orders),
        validate_auxiliary_id_uniqueness(interactions, "interaction_id", "customer_interactions"),
        validate_auxiliary_id_uniqueness(interventions, "intervention_id", "order_interventions"),
        validate_critical_nulls(orders),
        validate_timestamp_chronology(orders),
        validate_freshness(orders, run_date=run_date, max_age_days=max_age_days),
        validate_dispatch(dispatch),
        *validate_cross_source_keys(orders, dispatch, interactions, interventions),
        validate_kpi_eligibility(orders),
    ]
    return results

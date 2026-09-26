from dataclasses import dataclass
from datetime import date
import pandas as pd


class ValidationError(ValueError):
    def __init__(self, message, check="validation", results=None):
        super().__init__(message)
        self.check = check
        self.results = list(results or [])


@dataclass
class CheckResult:
    check: str
    status: str
    detail: str


ORDER_REQUIRED_COLUMNS = {
    "order_id", "customer_id", "restaurant_id", "created_at", "promised_eta",
    "pickup_at", "actual_delivery_at", "final_status", "traffic_bucket", "weather_bucket",
}

DISPATCH_REQUIRED_COLUMNS = {
    "order_id", "driver_id", "original_driver_id", "assigned_at", "reassigned_at",
    "estimated_pickup_at", "current_delivery_eta", "dispatch_status", "eta_model_version",
}


def validate_ids(df, columns, dataset_name):
    missing = {c: int((df[c].isna() | df[c].astype(str).str.strip().eq("")).sum()) for c in columns}
    if any(missing.values()):
        raise ValidationError(f"{dataset_name}: missing IDs: {missing}")
    return CheckResult(f"{dataset_name}.ids", "PASS", "No missing join/event IDs")


def validate_timestamp_parsing(df, columns, dataset_name):
    invalid = {}
    for c in columns:
        parsed = pd.to_datetime(df[c], format="mixed", errors="coerce")
        invalid[c] = int((df[c].notna() & parsed.isna()).sum())
    if any(invalid.values()):
        raise ValidationError(f"{dataset_name}: unparseable timestamps: {invalid}")
    return CheckResult(f"{dataset_name}.timestamp_parsing", "PASS", "All supplied timestamps parse; nulls checked separately")


def validate_dispatch_coverage(orders, dispatch):
    if dispatch["order_id"].duplicated().any():
        raise ValidationError("Dispatch has duplicate order IDs; an order-level join would multiply rows")
    missing = set(orders["order_id"]) - set(dispatch["order_id"])
    if missing:
        raise ValidationError(f"Dispatch missing {len(missing)} orders from the order source")
    return CheckResult("dispatch.order_coverage", "PASS", "Exactly one dispatch row for each unique order")


def validate_journey(journey, expected_orders):
    if len(journey) != expected_orders or journey["order_id"].duplicated().any():
        raise ValidationError("Order journey does not have exactly one row per order", "journey.grain")
    return CheckResult("journey.grain", "PASS", f"rows={len(journey)}; unique_order_ids={journey.order_id.nunique()}")


def validate_required_columns(df, required_columns, dataset_name):
    missing = sorted(set(required_columns) - set(df.columns))
    if missing:
        raise ValidationError(f"{dataset_name}: missing required columns: {missing}")
    return CheckResult(f"{dataset_name}.required_columns", "PASS", f"{len(required_columns)} required columns present")


def validate_order_uniqueness(orders):
    duplicate_rows = int(orders.duplicated("order_id", keep=False).sum())
    status = "WARN" if duplicate_rows else "PASS"
    detail = duplicate_detail(orders, "order_id")
    return CheckResult("orders.order_id_uniqueness", status, detail)


def validate_auxiliary_id_uniqueness(df, id_col, dataset_name):
    dup_rows = int(df.duplicated(id_col, keep=False).sum())
    status = "WARN" if dup_rows else "PASS"
    return CheckResult(f"{dataset_name}.{id_col}_uniqueness", status, duplicate_detail(df, id_col))


def duplicate_detail(df, id_col):
    repeated = df[df.duplicated(id_col, keep=False)]
    distinct = df.drop_duplicates()
    conflicts = distinct.loc[distinct.duplicated(id_col, keep=False), id_col].nunique()
    return (f"duplicate rows involved={len(repeated)}; unique_ids={df[id_col].nunique()}; "
            f"exact_excess_rows={len(df) - len(distinct)}; conflicting_ids={conflicts}; "
            "policy=first source row provisionally retained; repeated rows saved for review")


def validate_critical_nulls(orders):
    status_norm = orders["final_status"].astype(str).str.strip().str.lower()
    delivered = status_norm.eq("delivered")
    missing_actual = int((delivered & orders["actual_delivery_at"].isna()).sum())
    missing_promised = int((delivered & orders["promised_eta"].isna()).sum())
    missing_stage = int((delivered & (orders["created_at"].isna() | orders["pickup_at"].isna())).sum())
    if not status_norm.isin(["delivered", "cancelled"]).all():
        raise ValidationError("Unrecognised final_status; confirm its meaning before calculating the KPI")
    status = "WARN" if missing_actual or missing_promised or missing_stage else "PASS"
    return CheckResult("orders.delivered_completion_timestamp", status,
                       f"delivered rows missing actual_delivery_at={missing_actual}; missing_promised_eta={missing_promised}; "
                       f"missing_created_or_pickup={missing_stage}")


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
    return validate_required_columns(dispatch, DISPATCH_REQUIRED_COLUMNS, "dispatch")


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
    results = []

    def check(name, function, *args, **kwargs):
        try:
            result = function(*args, **kwargs)
        except ValidationError as exc:
            raise ValidationError(str(exc), name, results + [CheckResult(name, "FAIL", str(exc))]) from exc
        results.extend(result if isinstance(result, list) else [result])

    # Schemas first, so later checks cannot fail just because a column is absent.
    check("orders.required_columns", validate_required_columns, orders, ORDER_REQUIRED_COLUMNS, "orders")
    check("dispatch.required_columns", validate_dispatch, dispatch)
    for df, name, id_col, ts_col, type_col in [
        (interactions, "customer_interactions", "interaction_id", "interaction_at", "interaction_type"),
        (interventions, "order_interventions", "intervention_id", "intervention_at", "intervention_type"),
    ]:
        check(f"{name}.required_columns", validate_required_columns, df, {id_col, "order_id", ts_col, type_col}, name)
        check(f"{name}.ids", validate_ids, df, [id_col, "order_id"], name)
        check(f"{name}.timestamp_parsing", validate_timestamp_parsing, df, [ts_col], name)
        check(f"{name}.{id_col}_uniqueness", validate_auxiliary_id_uniqueness, df, id_col, name)
    check("orders.ids", validate_ids, orders, ["order_id"], "orders")
    check("dispatch.ids", validate_ids, dispatch, ["order_id"], "dispatch")
    check("orders.timestamp_parsing", validate_timestamp_parsing, orders,
          ["created_at", "promised_eta", "pickup_at", "actual_delivery_at"], "orders")
    check("dispatch.timestamp_parsing", validate_timestamp_parsing, dispatch,
          ["assigned_at", "reassigned_at", "estimated_pickup_at", "current_delivery_eta"], "dispatch")
    check("orders.order_id_uniqueness", validate_order_uniqueness, orders)
    check("orders.delivered_completion_timestamp", validate_critical_nulls, orders)
    check("orders.timestamp_chronology", validate_timestamp_chronology, orders)
    check("orders.freshness", validate_freshness, orders, run_date, max_age_days)
    check("cross_source.order_ids", validate_cross_source_keys, orders, dispatch, interactions, interventions)
    check("dispatch.order_coverage", validate_dispatch_coverage, orders, dispatch)
    check("kpi.eligibility", validate_kpi_eligibility, orders)
    return results

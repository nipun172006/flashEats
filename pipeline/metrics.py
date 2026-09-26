import pandas as pd


def _pct(numerator: int, denominator: int):
    return round((numerator / denominator) * 100, 2) if denominator else None


def build_metrics(journey: pd.DataFrame):
    eligible = journey[journey["kpi_eligible"]].copy()
    late = eligible[eligible["is_late"]].copy()

    metrics = {
        "orders_in_journey": int(len(journey)),
        "delivered_orders": int(journey["final_status"].eq("delivered").sum()),
        "cancelled_orders": int(journey["final_status"].eq("cancelled").sum()),
        "delivered_missing_actual_delivery_at": int(
            (journey["final_status"].eq("delivered") & journey["actual_delivery_at"].isna()).sum()
        ),
        "kpi_eligible_orders": int(len(eligible)),
        "late_orders": int(len(late)),
        "late_delivery_rate_pct": _pct(len(late), len(eligible)),
        "median_late_delay_min": round(float(late["delay_min"].median()), 2) if len(late) else None,
        "median_order_to_pickup_min": round(float(eligible["order_to_pickup_min"].median()), 2) if len(eligible) else None,
        "median_transit_min": round(float(eligible["transit_min"].median()), 2) if len(eligible) else None,
        "orders_with_intervention": int(journey["has_intervention"].sum()),
        "intervention_rate_pct": _pct(int(journey["has_intervention"].sum()), len(journey)),
        "orders_with_customer_interaction": int(journey["has_customer_interaction"].sum()),
        "customer_interaction_rate_pct": _pct(int(journey["has_customer_interaction"].sum()), len(journey)),
        "reassigned_orders": int(journey["was_reassigned"].sum()),
        "reassignment_rate_pct": _pct(int(journey["was_reassigned"].sum()), len(journey)),
    }

    metrics["late_rate_by_traffic"] = _group_rate(eligible, "traffic_bucket")
    metrics["late_rate_by_weather"] = _group_rate(eligible, "weather_bucket")
    metrics["late_rate_by_intervention"] = _group_rate(eligible, "has_intervention")
    metrics["late_rate_by_reassignment"] = _group_rate(eligible, "was_reassigned")
    return metrics


def _group_rate(df: pd.DataFrame, group_col: str):
    grouped = (
        df.groupby(group_col, dropna=False)
        .agg(
            orders=("order_id", "size"),
            late_orders=("is_late", "sum"),
            late_rate_pct=("is_late", "mean"),
            median_delay_min=("delay_min", "median"),
        )
        .reset_index()
    )
    grouped["late_rate_pct"] = (grouped["late_rate_pct"] * 100).round(2)
    grouped["median_delay_min"] = grouped["median_delay_min"].round(2)
    return grouped.to_dict(orient="records")

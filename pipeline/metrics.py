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


def build_definition_comparison(journey):
    eligible = journey[journey["kpi_eligible"]]
    historical = journey[
        journey["final_status"].eq("delivered") & journey["actual_delivery_at"].notna()
    ]
    rows = []
    for name, population, threshold in [
        ("Operations: any delay > 0 min (assessment baseline)", eligible, 0),
        ("Support: delay > 10 min (same eligible population)", eligible, 10),
        ("Historical population + assumed > 0 min rule", historical, 0),
    ]:
        unknown = int(population["promised_eta"].isna().sum())
        late = int((population["delay_min"] > threshold).sum())
        rows.append({"definition": name, "population_orders": len(population),
                     "unclassifiable_orders": unknown, "late_orders": late,
                     "late_rate_pct": _pct(late, len(population)) if not unknown else None})
    return pd.DataFrame(rows)


def build_duplicate_sensitivity(journey, raw_interactions):
    all_orders = set(journey["order_id"])
    represented_orders = len(set(raw_interactions["order_id"]) & all_orders)
    retained_orders = int(journey["has_customer_interaction"].sum())
    return {
        "policy": "First source row per ID is provisionally retained; conflicts require source-owner review.",
        "denominator_orders": len(journey),
        "retained_interaction_orders": retained_orders,
        "retained_interaction_rate_pct": _pct(retained_orders, len(journey)),
        "all_recorded_interaction_orders": represented_orders,
        "all_recorded_interaction_rate_pct": _pct(represented_orders, len(journey)),
        "interpretation": "Alternative preservation scenario, not a corrected or owner-approved metric.",
    }

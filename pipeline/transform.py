import pandas as pd


def _join_list(series):
    values = sorted({str(x).strip() for x in series.dropna() if str(x).strip()})
    return ",".join(values)


def build_order_journey(orders, interactions, interventions, dispatch, logger):
    journey = orders.copy()
    journey["delay_min"] = (journey["actual_delivery_at"] - journey["promised_eta"]).dt.total_seconds() / 60
    journey["order_to_pickup_min"] = (journey["pickup_at"] - journey["created_at"]).dt.total_seconds() / 60
    journey["transit_min"] = (journey["actual_delivery_at"] - journey["pickup_at"]).dt.total_seconds() / 60

    # Assessment analytical definition: late iff actual delivery exceeds promised ETA.
    journey["is_late"] = journey["delay_min"] > 0
    journey["kpi_eligible"] = (
        journey["final_status"].eq("delivered")
        & journey["actual_delivery_at"].notna()
        & journey["promised_eta"].notna()
    )

    interaction_summary = (
        interactions.groupby("order_id")
        .agg(
            customer_interaction_count=("interaction_id", "count"),
            customer_interaction_types=("interaction_type", _join_list),
            first_customer_interaction_at=("interaction_at", "min"),
        )
        .reset_index()
    )

    intervention_summary = (
        interventions.groupby("order_id")
        .agg(
            intervention_count=("intervention_id", "count"),
            intervention_types=("intervention_type", _join_list),
            first_intervention_at=("intervention_at", "min"),
        )
        .reset_index()
    )

    dispatch_small = dispatch.copy()
    dispatch_small["assigned_at"] = pd.to_datetime(dispatch_small["assigned_at"], format="mixed", errors="coerce")
    dispatch_small["reassigned_at"] = pd.to_datetime(dispatch_small["reassigned_at"], format="mixed", errors="coerce")
    dispatch_small["current_delivery_eta"] = pd.to_datetime(dispatch_small["current_delivery_eta"], format="mixed", errors="coerce")
    dispatch_small["estimated_pickup_at"] = pd.to_datetime(dispatch_small["estimated_pickup_at"], format="mixed", errors="coerce")
    dispatch_small["was_reassigned"] = dispatch_small["reassigned_at"].notna()
    dispatch_small = dispatch_small[[
        "order_id", "driver_id", "original_driver_id", "assigned_at", "reassigned_at",
        "estimated_pickup_at", "current_delivery_eta", "dispatch_status", "eta_model_version",
        "was_reassigned",
    ]]

    journey = journey.merge(interaction_summary, on="order_id", how="left", validate="one_to_one")
    journey = journey.merge(intervention_summary, on="order_id", how="left", validate="one_to_one")
    journey = journey.merge(dispatch_small, on="order_id", how="left", suffixes=("", "_dispatch"), validate="one_to_one")

    for col in ["customer_interaction_count", "intervention_count"]:
        journey[col] = journey[col].fillna(0).astype(int)
    for col in ["customer_interaction_types", "intervention_types"]:
        journey[col] = journey[col].fillna("")
    journey["has_customer_interaction"] = journey["customer_interaction_count"] > 0
    journey["has_intervention"] = journey["intervention_count"] > 0
    journey["support_ticket_count"] = journey["customer_interaction_types"].str.contains("SUPPORT_TICKET", regex=False).astype(int)

    logger.info("Built order journey | rows=%s columns=%s", len(journey), len(journey.columns))
    return journey

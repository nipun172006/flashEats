import pandas as pd


def duplicate_rows_for_review(df, id_col):
    """Keep every repeated-ID row, including the row provisionally selected."""
    review = df.loc[df.duplicated(id_col, keep=False)].copy()
    review.insert(0, "source_row", df.index[df.duplicated(id_col, keep=False)] + 1)
    review["retained_in_baseline"] = ~df.duplicated(id_col, keep="first").loc[review.index]
    distinct = df.drop_duplicates()
    conflicting_ids = set(distinct.loc[distinct.duplicated(id_col, keep=False), id_col])
    review["duplicate_kind"] = review[id_col].map(
        lambda value: "conflicting_id" if value in conflicting_ids else "exact_duplicate"
    )
    return review


def clean_orders(orders, logger):
    cleaned = orders.copy()
    before = len(cleaned)
    # Provisional classroom policy, not an assertion that the first record is true.
    # run_pipeline saves both selected and discarded records before this step.
    cleaned = cleaned.drop_duplicates(subset=["order_id"], keep="first").copy()
    cleaned["final_status"] = cleaned["final_status"].astype(str).str.strip().str.lower()

    for col in ["traffic_bucket", "weather_bucket"]:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].astype(str).str.strip().str.lower()

    for col in ["created_at", "promised_eta", "pickup_at", "actual_delivery_at"]:
        cleaned[col] = pd.to_datetime(cleaned[col], format="mixed", errors="coerce")

    if "distance_km_estimate" in cleaned.columns:
        cleaned["distance_km_estimate"] = pd.to_numeric(cleaned["distance_km_estimate"], errors="coerce")

    logger.info("Cleaned orders | input_rows=%s output_rows=%s deduplicated=%s", before, len(cleaned), before - len(cleaned))
    return cleaned


def clean_event_source(df, id_col, timestamp_col, logger):
    out = df.copy()
    before = len(out)
    out = out.drop_duplicates(subset=[id_col], keep="first").copy()
    out[timestamp_col] = pd.to_datetime(out[timestamp_col], format="mixed", errors="coerce")
    logger.info("Cleaned event source | source=%s input_rows=%s output_rows=%s", id_col, before, len(out))
    return out

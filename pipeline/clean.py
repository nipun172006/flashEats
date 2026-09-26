import pandas as pd


def clean_orders(orders, logger):
    cleaned = orders.copy()
    before = len(cleaned)
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

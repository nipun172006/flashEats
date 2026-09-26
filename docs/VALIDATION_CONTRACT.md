# Validation Contract — Assessment 2

The validation gate runs before cleaning, modelling, or publishing processed outputs.

| Check | Treatment |
|---|---|
| Required columns | FAIL / stop pipeline |
| Order grain / duplicate order IDs | WARN; clean to one row per `order_id` |
| Event-ID duplicates | WARN; deduplicate explicitly |
| Delivered rows missing actual delivery | WARN; exclude from KPI denominator and report |
| Timestamp chronology | WARN for anomalous rows; preserve and report |
| Freshness | FAIL if older than configured threshold |
| Dispatch completeness | FAIL if retrieved rows do not match API `total_records` |
| Cross-source order IDs | FAIL if unknown order references exist |
| KPI eligibility | PASS with eligible/cancelled/missing counts |

A FAIL stops publication of processed outputs. WARN does not silently disappear; it is stored in `validation_report.json`.

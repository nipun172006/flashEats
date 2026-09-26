# Validation Contract — Assessment 2

The validation gate runs before cleaning, modelling, or publishing processed outputs.

| Check | Treatment |
|---|---|
| Required columns in orders, dispatch and both event sources | FAIL before downstream checks if a consumed column is absent |
| Missing order/event join IDs | FAIL |
| Supplied timestamps that cannot be parsed | FAIL; do not silently turn them into nulls |
| Order grain / duplicate order IDs | WARN; save repeated rows and provisionally retain the first |
| Event-ID duplicates | WARN; save repeated rows, identify conflicts and report sensitivity |
| Delivered rows missing actual delivery | WARN; exclude from KPI denominator and report |
| Timestamp chronology | WARN for anomalous rows; preserve and report |
| Freshness | FAIL if older than configured threshold |
| Dispatch completeness | FAIL if retrieved rows do not match API `total_records` |
| Dispatch order coverage | FAIL if there is not exactly one dispatch row per source order |
| Cross-source order IDs | FAIL if unknown order references exist |
| KPI eligibility | PASS with eligible/cancelled/missing counts |
| Final journey grain | FAIL unless row count and uniqueness match the cleaned orders; joins also enforce one-to-one cardinality |

A FAIL stops publication of processed outputs. WARN does not silently disappear; it is stored in `validation_report.json`.

The current successful run has **20 PASS / 4 WARN / 0 FAIL**, including the final journey-grain check. The warnings still represent order conflicts, interaction conflicts, missing completion timestamps and chronology.

Null promised/actual timestamps exclude a delivered order from the KPI; missing creation/pickup timestamps affect duration metrics and are reported. Unrecognised final statuses fail pending a semantic decision.

The 60-day freshness threshold is a disclosed classroom assumption for historical analysis. On logical date 2026-09-26, the newest order is 29 days old. It would not be an appropriate live-dispatch SLA. This check measures the newest creation time, not per-record update freshness.

Each attempt writes a JSON status under `logs/attempts/`, plus `logs/latest_status_YYYY-MM-DD.json`. On validation failure, completed checks and the failing check are retained. Consumers should require latest status SUCCESS before using that partition. A failed rerun leaves older files in place; a save-stage failure may leave mixed files. Each file is replaced atomically, but the directory is not a transaction.

Raw snapshots are replaced on a rerun of the same logical date. They preserve the current extract, not an immutable history of every attempt. The attempt record names the chaos scenario, which is applied in memory after the original input snapshot.

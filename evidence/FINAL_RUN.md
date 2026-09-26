# Final Verified Run — 2026-09-26

This folder contains a checked-in snapshot of the final run used for the assessment.

- Dispatch API: **1,600 / 1,600** records across **16 pages**.
- Validation: **8 PASS / 4 WARN / 0 FAIL**.
- Raw orders: **1,603** rows → **1,600** unique order IDs.
- KPI eligible: **1,495** delivered orders.
- Late orders: **843**.
- Late Delivery Rate: **56.39%**.
- Idempotent rerun: identical `order_journey.csv` checksum.
- Failure tests: missing-column and stale-data scenarios stopped at validation; duplicate-order scenario surfaced a warning and then applied explicit deduplication.

The full run outputs are regenerated under `data/processed/run_date=YYYY-MM-DD/` when the pipeline is executed.

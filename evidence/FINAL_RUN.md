# Final Verified Run — 2026-09-26

This folder contains a checked-in snapshot of the final run used for the assessment.

- Dispatch API: **1,600 / 1,600** records across **16 pages**.
- Validation: **20 PASS / 4 WARN / 0 FAIL** (including final order grain).
- Raw orders: **1,603** rows → **1,600** unique order IDs.
- KPI eligible: **1,495** delivered orders.
- Late orders: **843**.
- Late Delivery Rate: **56.39%**.
- Idempotent rerun: identical `order_journey.csv` checksum.
- Failure tests: missing-column and stale-data scenarios stopped at validation; duplicate-order scenario surfaced a warning and then applied explicit deduplication.

The verification details and both rerun checksums are in `verification.json`. Failed-attempt reports are included, and the checks confirm that validation failures leave all existing processed files unchanged. `final_attempt_status.json` is the last normal successful run.

Additional evidence: `kpi_definition_comparison.csv` (56.39% vs 23.34%), `duplicate_sensitivity.json` (28.75% vs 28.94%), and the repeated-ID CSVs showing selected and discarded rows. The five headline metrics have not changed.

To refresh this snapshot, run `python scripts/verify_run.py` after installing the project requirements. It runs the focused unit checks, normal/rerun checks and chaos cases, then finishes with a normal run. It replaces the evidence files in this folder.

The full run outputs are regenerated under `data/processed/run_date=YYYY-MM-DD/` when the pipeline is executed.

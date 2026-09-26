# Gate 2 — Data Readiness Evidence

| Area | Status | Evidence |
|---|---|---|
| One-command run | PASS | `python run_pipeline.py --run-date ...` |
| Repeatable run | PASS | Same logical partition is atomically replaced |
| Raw API preserved | PASS | `data/raw/run_date=.../dispatch/dispatch_page_*.json` |
| Validation gate | PASS | `run_pipeline.py` validates before publishing processed output |
| Bounded retries | PASS | configurable max retries + exponential backoff / Retry-After |
| Logging | PASS | console + `logs/pipeline_YYYY-MM-DD.log` |
| Cross-source integrity | PASS | order IDs checked across dispatch/interactions/interventions |
| Failure handling | PASS | validation failures return non-zero and suppress processed publication |
| Configuration outside core logic | PASS | environment variables in `pipeline/config.py` |
| Known limitations | DOCUMENTED | `docs/FINDINGS.md` |

**Gate decision: READY for assessment submission.**

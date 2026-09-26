# FlashEats — Assessment 2: Dependable Operational Data Pipeline

## Business situation

FlashEats has order, dispatch, intervention and customer-interaction data coming from different systems. The problem is not just getting the data; it is figuring out what can actually be trusted before using it for an operations decision.

### Business question

**Where do delays accumulate in the order lifecycle, what operational/customer signals are present, and can we reproduce a trustworthy Late Delivery Rate from multiple source systems?**

### Core KPI

**Late Delivery Rate** using the assessment analytical definition in [`docs/KPI_CONTRACT.md`](docs/KPI_CONTRACT.md).

> Important: the classroom material does not identify a formally documented canonical KPI owner. The definition used here is therefore an explicit assessment assumption, not an enterprise-approved KPI.

## Who this is for

| Stakeholder | Role in this work | What they need |
|---|---|---|
| Operations | Decision user | A clear late-delivery baseline and where time is accumulating |
| Data / Engineering | System owner | Reliable extraction, validation and reruns |
| Support | Customer context | Customer interactions connected back to the order journey |

## FDE approach

I worked backwards from the business question rather than joining every source first:

```text
Problem → Questions → Information → Fields → Sources
                              ↓
                 Retrieve evidence from sources
                              ↓
                       Validate first
                              ↓
                 One row per order / order journey
                              ↓
                       Calculate metrics
                              ↓
                    Evidence for operations
```

## Source and retrieval overview

The project deliberately uses multiple retrieval modes:

- **SQL:** SQLite `orders` table is the primary source for lifecycle timestamps and order status.
- **CSV:** `customer_interactions.csv` and `order_interventions.csv` provide event-level customer and intervention context.
- **HTTP + JSON API:** the local Dispatch API provides assignment/reassignment and current ETA data through paginated responses.

See [`docs/SOURCE_MAP.md`](docs/SOURCE_MAP.md) for the business-question → information → source mapping, grain, ownership gaps and retrieval method.

## Pipeline

```text
SQL + CSV + HTTP API
        ↓
      EXTRACT
        ↓
  RAW SNAPSHOT
        ↓
 VALIDATION GATE ────── FAIL → stop publication
        ↓ PASS
      CLEAN
        ↓
  ORDER JOURNEY
  (1 row/order)
        ↓
     METRICS
        ↓
 CSV + JSON + LOG
```

The pipeline is implemented in `pipeline/` and orchestrated by `run_pipeline.py`.

## Repository structure

```text
api/                  mock HTTP API + dispatch JSON
pipeline/             extraction, validation, cleaning, transformation, metrics, save
 database/             SQLite source data
data/                 CSV source data
 docs/                 source map, KPI contract, validation, model, findings
evidence/             checked-in final run evidence for the assessment
config/               example environment configuration
run_pipeline.py       one-command orchestration
requirements.txt      Python dependencies
```

## Prerequisites

Python 3.10+ is recommended. The included data is classroom/simulated FlashEats data; no production credentials are required.

## Setup and run

I recommend using a virtual environment so the project does not install packages into the macOS/Homebrew Python environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_pipeline.py --run-date 2026-09-26
```

The run starts the local mock Dispatch API automatically. The API demonstrates pagination plus transient `500` and `429` responses. The pipeline retries those failures, preserves the raw API pages, validates completeness, and only then publishes processed outputs.

## Expected final evidence

The verified assessment run produced:

| Metric | Result |
|---|---:|
| Late Delivery Rate | **56.39%** |
| KPI-eligible delivered orders | **1,495** |
| Late orders | **843** |
| Median Order → Pickup | **26.07 min** |
| Median Pickup → Delivery | **47.23 min** |
| Intervention Rate | **16.25%** |
| Customer Interaction Rate | **28.75%** |

The checked-in copies of the final evidence are in `evidence/` and the full run outputs are generated under `data/raw/` and `data/processed/` when the pipeline runs.

## Dependability checks

```bash
python run_pipeline.py --run-date 2026-09-26 --chaos missing_column
python run_pipeline.py --run-date 2026-09-26 --chaos duplicate_order
python run_pipeline.py --run-date 2026-09-26 --chaos stale_data
```

Expected behaviour:

- `missing_column` → validation FAIL; processed publication stops.
- `stale_data` → validation FAIL; processed publication stops.
- `duplicate_order` → validation WARN; explicit one-row-per-order cleaning handles the duplicate.

A normal run also proves API completeness (`1,600 / 1,600` across 16 pages), preserves raw inputs and supports idempotent reruns.

## Final outputs from a run

```text
data/raw/run_date=YYYY-MM-DD/
  local/*.csv
  dispatch/dispatch_page_*.json

data/processed/run_date=YYYY-MM-DD/
  order_journey.csv
  metrics.json
  validation_report.json
  run_manifest.json
  evidence_table.csv

logs/pipeline_YYYY-MM-DD.log
```

## Known / Unknown / Assumption / Limitation

See [`docs/FINDINGS.md`](docs/FINDINGS.md), [`docs/KPI_CONTRACT.md`](docs/KPI_CONTRACT.md), and [`docs/VALIDATION_CONTRACT.md`](docs/VALIDATION_CONTRACT.md).

## What decision this supports

Operations can review a reproducible late-delivery baseline, see which part of the journey is taking time, and use interventions, reassignments, traffic/weather and customer interactions as follow-up signals.

The analysis does **not** claim that any single factor caused the delay.

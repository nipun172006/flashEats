# Assessment 2 Story

## Problem → Questions → Information → Fields → Sources

**Problem:** late deliveries reduce operational reliability and may trigger customer friction and interventions.

**Questions:**
- How large is the late-delivery problem?
- Where does time accumulate: order-to-pickup or pickup-to-delivery?
- What interventions/reassignments occurred?
- How did customers interact with orders?
- Can the KPI be reproduced reliably tomorrow?

**Information/fields:** lifecycle timestamps, final status, traffic/weather/distance, dispatch assignment/ETA, interventions, customer interactions.

**Sources:** SQLite (`orders` and reference tables), CSV event logs, paginated HTTP dispatch API.

## Decision supported
The output supports an operations review of the late-delivery baseline, where time accumulates in the lifecycle, and which order cohorts show operational/customer signals for follow-up. Intervention/reassignment comparisons are observational associations, not causal estimates.

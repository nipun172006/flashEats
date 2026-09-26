# KPI Contract — Assessment 2

**KPI:** Late Delivery Rate

**Assessment analytical definition:** an eligible delivered order is late when `actual_delivery_at > promised_eta`.

**Denominator:** delivered orders with non-null `actual_delivery_at` and `promised_eta`.

**Excluded:** cancelled orders and delivered orders missing `actual_delivery_at`.

**Important:** the classroom source says there is no formally documented canonical KPI owner, so this is an assessment definition/assumption rather than an enterprise-approved KPI.

**Derived field:** `delay_min = actual_delivery_at - promised_eta`.

## Now, what happens if the definition changes?

The classroom `client_metric_definitions.json` records a real disagreement. Operations counts any delay after ETA. Support counts only a delay of more than 10 minutes. The Data Team describes the historical denominator, but does not separately specify a lateness threshold.

| Interpretation | Late orders | Denominator | Late rate |
|---|---:|---:|---:|
| Operations: delay > 0 minutes | 843 | 1,495 | 56.39% |
| Support: delay > 10 minutes, using the same eligible orders | 349 | 1,495 | 23.34% |
| Historical delivered/non-null-actual population, with > 0 minutes assumed | 843 | 1,495 | 56.39% |

The historical and assessment populations happen to match here because all 1,495 completed deliveries also have a promised ETA. This would not be safe to assume for another extract. The comparison returns an unknown rate if a historical-population order has no promised ETA.

My Analysis: I used the Operations definition because this baseline asks whether the original delivery promise was met. The Support definition answers a different question: how many deliveries were meaningfully late under its 10-minute rule. Neither number should be published without its definition.

Finance also asks to exclude cancelled/refunded orders. The 68 cancelled orders are excluded. Refund status is not available in the selected lifecycle source, so I cannot fully implement Finance's requested population. A refund offer is not proof of a completed refund.

There is no documented canonical owner. Before enterprise publication, I would ask the client to name an accountable KPI owner and have Operations, Support, Finance and Data agree on the threshold, exclusions and source fields. This remains a provisional assessment baseline.

The pipeline generates `kpi_definition_comparison.csv`; a checked-in copy is in `evidence/`. The supplied definition file is preserved in `docs/classroom_metric_definitions.json`.

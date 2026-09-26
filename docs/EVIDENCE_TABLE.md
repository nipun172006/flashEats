# Final Evidence Table — Assessment 2

| Metric | Result | Business meaning |
|---|---:|---|
| Late Delivery Rate | **56.39%** | Primary KPI baseline under the assessment definition |
| Median Order → Pickup | **26.07 min** | Typical time spent before pickup |
| Median Pickup → Delivery | **47.23 min** | Typical transit time after pickup |
| Intervention Rate | **16.25%** | Share of unique orders with ≥1 recorded intervention |
| Customer Interaction Rate | **28.75%** | Share of unique orders with ≥1 retained customer interaction |

## Data-quality evidence

| Check | Result |
|---|---|
| Raw order rows | 1,603 |
| Unique order IDs | 1,600 |
| Duplicate order rows | 6 rows involved; 3 excess rows removed in cleaning |
| KPI-eligible delivered orders | 1,495 |
| Late orders | 843 |
| Delivered rows missing actual delivery | 37 (reported, excluded from denominator) |
| Dispatch API records | 1,600 / 1,600 across 16 pages |
| Unknown order references across linked sources | 0 |
| Chronology anomalies | 4 promised-before-created; 5 delivery-before-pickup (WARN, retained) |

## Interpretation boundary

Traffic/weather, interventions, reassignment, and customer interactions are used as descriptive operational context. Differences across cohorts are not treated as causal effects.

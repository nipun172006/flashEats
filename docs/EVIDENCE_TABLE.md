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
| Duplicate order rows | 6 rows involved; 3 conflicting IDs; first records provisionally retained |
| Duplicate interaction IDs | 3 conflicting IDs; all 6 rows saved for review |
| KPI-eligible delivered orders | 1,495 |
| Late orders | 843 |
| Delivered rows missing actual delivery | 37 (reported, excluded from denominator) |
| Dispatch API records | 1,600 / 1,600 across 16 pages |
| Unknown order references across linked sources | 0 |
| Chronology anomalies | 4 promised-before-created; 5 delivery-before-pickup (WARN, retained) |

The two duration medians use KPI-eligible deliveries. Intervention and customer-interaction rates use all 1,600 unique orders. Customer coverage refers to retained interactions under the documented first-record policy.

## Additional checks on the interpretation

- Any delay: 843 / 1,495 = 56.39%. More than 10 minutes: 349 / 1,495 = 23.34%.
- Eligible orders with intervention: 142 / 245 late (57.96%); without: 701 / 1,250 (56.08%). This is not a causal comparison.
- All recorded interaction rows cover 463 orders (28.94%); first-record retention covers 460 (28.75%). Source-owner review is still needed.

## Interpretation boundary

Traffic/weather, interventions, reassignment, and customer interactions are used as descriptive operational context. Differences across cohorts are not treated as causal effects.

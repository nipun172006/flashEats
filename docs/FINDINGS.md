# Findings — Assessment 2 run

These are descriptive results from the supplied FlashEats classroom data using the assessment KPI definition.

1. **Late-delivery baseline:** 843 of 1,495 KPI-eligible deliveries are late, giving **56.39% Late Delivery Rate**.
2. **Time concentration:** median order-to-pickup time is **26.07 min** and median pickup-to-delivery transit time is **47.23 min** among KPI-eligible deliveries.
3. **Operational intervention exposure:** **260 / 1,600 orders (16.25%)** have at least one recorded intervention; **95 / 1,600 (5.94%)** were reassigned.
4. **Customer reaction:** **460 / 1,600 orders (28.75%)** have at least one retained customer interaction under the provisional first-record policy.
5. **Context association:** late rate is higher in rainy weather and severe/high traffic buckets in this dataset. These are descriptive associations, not causal estimates.
6. **Known data-quality limitation:** 37 delivered rows are missing `actual_delivery_at`, so they cannot be placed in the KPI denominator. Five rows also show delivery-before-pickup chronology anomalies and are retained for investigation rather than silently removed.
7. **Known workflow unknown:** the broader classroom driver event model was inspected separately and does not provide a reliable observed `arrived_at_restaurant` event, limiting precise restaurant-vs-driver attribution. That source is not part of the runnable Assessment 2 ingestion path.

## Did interventions help?

| KPI-eligible orders | Late / eligible | Late rate |
|---|---:|---:|
| With a recorded intervention | 142 / 245 | 57.96% |
| Without a recorded intervention | 701 / 1,250 | 56.08% |

There are 260 intervened orders overall; 245 belong to the KPI-eligible population used above. The observed difference is 1.88 percentage points. Difficult orders may be more likely to receive an intervention, so this does not show that interventions caused delays or failed to help. It tells me which journeys to inspect next. I would need the reason, timing and a defensible comparison design before estimating an effect.

## What do I still need to be careful about?

The first-record rule affects customer coverage: retaining all recorded interaction rows would cover 463 orders (28.94%), compared with the baseline's 460 (28.75%). Three interaction IDs are reused for different orders. This is a sensitivity comparison, not a claim that one version is the approved truth. See `DUPLICATE_POLICY.md`.

The longer 47.23-minute transit median is elapsed time, not proof that drivers caused avoidable delay. The five negative transit intervals remain in the baseline and are reported. The medians exclude missing stage durations if encountered; this run has none among eligible deliveries.

## Decision supported

Operations can use this baseline to choose the next investigation: review high-traffic/rain cohorts and intervened late orders. Data/Engineering should resolve the 37 missing completions, repeated IDs and chronology exceptions. I would ask for a reliable restaurant-arrival event before separating restaurant delay from driver delay. The 60-day freshness threshold supports this historical classroom run, not a live dispatch decision.

# Findings — Assessment 2 run

These are descriptive results from the supplied FlashEats classroom data using the assessment KPI definition.

1. **Late-delivery baseline:** 843 of 1,495 KPI-eligible deliveries are late, giving **56.39% Late Delivery Rate**.
2. **Time concentration:** median order-to-pickup time is **26.07 min** and median pickup-to-delivery transit time is **47.23 min** among KPI-eligible deliveries.
3. **Operational intervention exposure:** **260 / 1,600 orders (16.25%)** have at least one recorded intervention; **95 / 1,600 (5.94%)** were reassigned.
4. **Customer reaction:** **460 / 1,600 orders (28.75%)** have at least one recorded customer interaction.
5. **Context association:** late rate is higher in rainy weather and severe/high traffic buckets in this dataset. These are descriptive associations, not causal estimates.
6. **Known data-quality limitation:** 37 delivered rows are missing `actual_delivery_at`, so they cannot be placed in the KPI denominator. Five rows also show delivery-before-pickup chronology anomalies and are retained for investigation rather than silently removed.
7. **Known workflow unknown:** the broader classroom driver event model was inspected separately and does not provide a reliable observed `arrived_at_restaurant` event, limiting precise restaurant-vs-driver attribution. That source is not part of the runnable Assessment 2 ingestion path.

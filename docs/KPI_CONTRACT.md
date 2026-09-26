# KPI Contract — Assessment 2

**KPI:** Late Delivery Rate

**Assessment analytical definition:** an eligible delivered order is late when `actual_delivery_at > promised_eta`.

**Denominator:** delivered orders with non-null `actual_delivery_at` and `promised_eta`.

**Excluded:** cancelled orders and delivered orders missing `actual_delivery_at`.

**Important:** the classroom source says there is no formally documented canonical KPI owner, so this is an assessment definition/assumption rather than an enterprise-approved KPI.

**Derived field:** `delay_min = actual_delivery_at - promised_eta`.

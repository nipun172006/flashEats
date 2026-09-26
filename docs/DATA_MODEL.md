# Workflow / Data Model

```text
CUSTOMER ──places──> ORDER <──prepared by── RESTAURANT
                       │
                       ├── assigned / reassigned ──> DRIVER
                       │
                       ├── STATES: preparing → dispatched → delivered / cancelled
                       │
                       ├── EVENTS: created → pickup → delivery
                       │
                       ├── INTERVENTION: ETA_MESSAGE / DRIVER_REASSIGNMENT / ...
                       │
                       └── CUSTOMER INTERACTION: ETA_VIEW / SUPPORT_TICKET / ...

                       ↓
                 ORDER OUTCOME
            on-time / late / cancelled

Analytics grain: one row per ORDER.

Event-level sources are aggregated to order grain before joining to the lifecycle table.
```

## Main entities

- **Order:** primary analytical entity.
- **Customer:** customer identity/context.
- **Restaurant:** restaurant identity/context.
- **Driver:** assigned driver context.

## Events / states

- Lifecycle events: order created, pickup, delivery.
- States: preparing, dispatched, delivered, cancelled.
- Dispatch events: assignment and reassignment.
- Interventions: operational actions such as ETA message, restaurant contact, priority dispatch or refund offer.
- Customer interactions: actions such as ETA views and support-related interactions.

## Outcomes

The KPI outcome is whether an eligible delivered order is **late** or **not late** under the assessment definition. Cancelled orders are excluded from the KPI denominator.

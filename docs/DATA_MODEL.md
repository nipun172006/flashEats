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

## Keys used in the implemented model

| Input / model | Key and grain | Link |
|---|---|---|
| Clean orders / order_journey | `order_id`, one row per order | Customer, restaurant and driver IDs retained as context |
| Customer interactions | `interaction_id`, one retained event | `order_id` to orders; repeated-ID conflicts saved separately |
| Interventions | `intervention_id`, one retained event | `order_id` to orders |
| Dispatch | `order_id`, one row per order | One-to-one left join to orders |

The customer, restaurant and driver reference tables are extracted for context but are not joined into the KPI calculation. Intermediate preparing/dispatched states in the diagram describe the business workflow; this model does not claim to reconstruct a complete state-transition log.

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

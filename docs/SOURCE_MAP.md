# Source Map — Assessment 2

The source map was built backwards from the business question. The goal is to identify what information is required, which system contains it, what grain it arrives at, and where the source has known gaps.

| Business question | Information needed | Source | Retrieval | Grain | Ownership / source role | Important gap |
|---|---|---|---|---|---|---|
| Was the order late? | promised ETA, actual delivery, final status | `database/flasheats.db` → `orders` | SQL | 1/order row | Order system; specific owner not documented in classroom pack | KPI ownership is not formally documented |
| Where does time accumulate? | created, pickup, delivery timestamps | `database/flasheats.db` → `orders` | SQL | 1/order row | Order system; specific owner not documented | 5 delivery-before-pickup chronology warnings retained |
| Traffic/weather/distance context | distance, traffic, weather | `database/flasheats.db` → `orders` | SQL | 1/order row | Order system context; owner not documented | Descriptive context only; not causal evidence |
| Did dispatch change the assignment/ETA? | original/current driver, reassignment, current ETA | `api/dispatch_data.json` via local HTTP API | HTTP + JSON | 1/order | Dispatch system simulation; owner not documented | Mock API is classroom/simulated evidence |
| What interventions occurred? | type, time, reason, initiator | `data/order_interventions.csv` | CSV | event/order | Operational event source; owner not documented | Event-level source must be aggregated to order grain |
| How did customers react? | interaction type, time, channel | `data/customer_interactions.csv` | CSV | event/order | Customer interaction source; owner not documented | Describes interaction, not canonical operational state |
| Customer / driver / restaurant reference context | IDs and static attributes | `database/flasheats.db` → reference tables | SQL | entity | Reference data; owner not documented | Used for source completeness/context, not required for the core KPI |

## Retrieval completeness

The Dispatch API is paginated. The pipeline continues until `has_more=false`, preserves every raw response page, and checks that received row count and unique `order_id` count match the API's `total_records` value.

The verified run retrieved **1,600 / 1,600 dispatch records across 16 pages**.

## Source-of-truth reasoning

For the core late-delivery KPI, `orders` is treated as the primary source because it contains the lifecycle timestamps and final status at the required one-order grain. Dispatch, interventions and customer interactions are supporting/context sources rather than substitutes for the canonical order lifecycle.

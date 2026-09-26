# What I did with repeated IDs

The baseline needs one row per order, but that does not make every repeated ID an exact duplicate.

| Source | What I found | Effect |
|---|---|---|
| Orders | Three repeated IDs; their traffic buckets disagree | Traffic cohorts depend on which record is retained; lifecycle timestamps agree |
| Customer interactions | Three repeated IDs used for different orders and event types | Keeping the first removes the only interaction for three other orders |
| Interventions | No repeated IDs | No deduplication needed in this run |

For this assessment, I kept the starter's first-record rule as a provisional baseline. SQLite extraction now explicitly orders by `rowid`; CSVs retain file order. This is reproducible for the same source files, but physical source order is not an authority or recency rule.

All repeated-ID rows are saved under `data/raw/run_date=.../exceptions/`. Each row shows its source position, whether it was retained, and whether its ID has conflicting content. The checked-in evidence includes both sides of the conflicts. Nothing in the source files is edited.

## Does this change the result?

- The three conflicting order IDs have identical status and lifecycle timestamps, so the 56.39% headline rate is unchanged by choosing their other versions. Their traffic attribution can change.
- Baseline retained customer interactions: 460 / 1,600 = 28.75%.
- Alternative, keeping all recorded interaction rows: 463 / 1,600 = 28.94%.

My Analysis: reporting only that I removed three rows would hide the important part. I cannot tell which version is authoritative from these fields. The next step is source-owner review, ideally with a stable event key or version timestamp. I have kept this uncertainty visible rather than calling the discarded rows wrong.

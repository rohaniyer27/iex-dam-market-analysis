# Reproducible SQLite market analysis

From the repository root, run:

```bash
python SQL/load_market_data.py
```

Requires Python 3.9+ with SQLite 3.25+. No third-party Python packages are needed. Paths are resolved relative to the script, so it also works from other directories. Optional arguments: `--csv`, `--database`, `--output-dir`.

The loader reads `Exports/cleaned_dam_data.csv`, validates full 96-interval market days and creates `SQL/market_data.sqlite`. It then executes `market_analysis.sql` to create seven views and writes seven `Exports/sql_*.csv` files. Existing generated tables/views and output files are replaced on rerun; the source CSV is unchanged. Keep the generated SQLite database local.

## Queries

| View | Purpose |
| --- | --- |
| `data_quality` | Completeness, missing numeric fields, duplicates, negative quantities and irregular time steps |
| `daily_summary` | Mean/min/max MCP, range, cleared MWh and volume-weighted MCP |
| `hourly_profile` | Clock-hour price and power averages, energy totals and aggregate purchase-bid fulfilment |
| `interval_metrics` | Recomputed bid-volume gap, energy, fulfilment, LAG price changes and trailing four-interval price statistics |
| `price_movement_ranking` | Absolute price-change ranking with ties preserved |
| `fulfilment_ranking` | Lowest purchase-bid fulfilment ranking, with undefined ratios excluded |
| `maximum_price_runs` | Consecutive runs at the observed daily maximum using gaps-and-islands |

For example, after loading, use Python's sqlite3 API or a SQLite client to run:

```sql
SELECT * FROM price_movement_ranking WHERE movement_rank <= 10
ORDER BY market_date, movement_rank, timestamp;
SELECT * FROM hourly_profile ORDER BY market_date, clock_hour;
```

## Definitions and boundaries

- The committed input has 96 quarter-hour intervals for **24 May 2026**. This is a single-day descriptive analysis, not seasonal evidence or a causal explanation of prices.
- Source timestamps remain market wall-clock times. Clock hours are labelled 00-23 rather than the source hour field's 1-24 convention.
- Input MW quantities are treated as interval-average power. Cleared energy in MWh = MCV in MW times 0.25 hours. Sum energy across intervals; average power across equal intervals.
- MCP is Rs/MWh. Volume-weighted MCP = sum(MCP times cleared MWh) / sum(cleared MWh).
- Bid-volume gap = purchase bids minus sell bids. It is not measured physical grid imbalance. Purchase-bid fulfilment = MCV / purchase bids, with zero denominators yielding NULL.
- Price differences are recomputed after timestamp ordering, partitioned by market day; each day's first difference is NULL. The exported source's precomputed differences are not used.
- Rolling windows include the current and up to three preceding observations within a day. `rolling_interval_count` identifies the first three partial windows. Only count=4 means a full hour.
- Maximum-price runs refer to the observed daily maximum, not a verified market price cap. Run end timestamps are exclusive.
- Missing/non-finite values, negative quantities, duplicate/missing intervals and date/timestamp mismatches are rejected before the database is replaced. Negative prices themselves are not rejected.

## Checked results for the committed snapshot

- 96 intervals, 24 hourly groups, no duplicate timestamps or irregular time steps.
- Mean MCP: **Rs 5,895.31/MWh**; volume-weighted MCP: **Rs 4,052.78/MWh**.
- Cleared energy: **142,283.7525 MWh**.
- Largest absolute price change: **+Rs 3,987.73/MWh**, at 19:15.
- Observed maximum Rs 10,000/MWh: runs 00:00-05:15 and 19:15-00:00 next day, totalling 600 minutes.

Validation on 29 October 2026 independently checked SQL daily totals, weighted price, every interval change, rolling mean and fulfilment ratio against standard-library Python calculations. Hourly energy reconciled to the daily total, and maximum-price run counts matched the raw intervals. Missing-interval, duplicate-row and negative-quantity fixtures were rejected. These checks validate this snapshot; they do not establish source authenticity or broader market representativeness.

-- SQLite 3.25+. Input is the typed dam_intervals table created by the loader.
-- MW is interval-average power; each record covers 0.25 h. Timestamps are
-- source market wall-clock times, not converted to UTC. No causal claims.
DROP VIEW IF EXISTS interval_metrics;
CREATE VIEW interval_metrics AS
SELECT *,
       mcv_mw * 0.25 AS cleared_mwh,
       purchase_bid_mw - sell_bid_mw AS bid_volume_gap_mw,
       mcv_mw / NULLIF(purchase_bid_mw, 0) AS purchase_bid_fulfilment,
       LAG(mcp_rs_mwh) OVER (PARTITION BY market_date ORDER BY timestamp) AS previous_mcp_rs_mwh,
       mcp_rs_mwh - LAG(mcp_rs_mwh) OVER (PARTITION BY market_date ORDER BY timestamp) AS price_change_rs_mwh,
       COUNT(*) OVER w AS rolling_interval_count,
       AVG(mcp_rs_mwh) OVER w AS rolling_mcp_mean_rs_mwh,
       MIN(mcp_rs_mwh) OVER w AS rolling_mcp_min_rs_mwh,
       MAX(mcp_rs_mwh) OVER w AS rolling_mcp_max_rs_mwh
FROM dam_intervals
WINDOW w AS (PARTITION BY market_date ORDER BY timestamp ROWS BETWEEN 3 PRECEDING AND CURRENT ROW);

-- 1. Validation. Expected 96 intervals per complete source market day.
DROP VIEW IF EXISTS data_quality;
CREATE VIEW data_quality AS
WITH ordered AS (
 SELECT *, LAG(timestamp) OVER (PARTITION BY market_date ORDER BY timestamp) AS previous_timestamp
 FROM dam_intervals
)
SELECT market_date, COUNT(*) AS interval_count,
       COUNT(*) - COUNT(DISTINCT timestamp) AS duplicate_timestamps,
       SUM(CASE WHEN mcp_rs_mwh IS NULL OR purchase_bid_mw IS NULL OR sell_bid_mw IS NULL
                     OR mcv_mw IS NULL OR final_scheduled_volume_mw IS NULL THEN 1 ELSE 0 END) AS missing_numeric_rows,
       SUM(CASE WHEN purchase_bid_mw < 0 OR sell_bid_mw < 0 OR mcv_mw < 0
                     OR final_scheduled_volume_mw < 0 THEN 1 ELSE 0 END) AS negative_quantity_rows,
       SUM(CASE WHEN previous_timestamp IS NOT NULL AND
         CAST(strftime('%s', timestamp) AS INTEGER) - CAST(strftime('%s', previous_timestamp) AS INTEGER) <> 900
         THEN 1 ELSE 0 END) AS irregular_steps,
       MIN(timestamp) AS first_timestamp, MAX(timestamp) AS last_timestamp
FROM ordered GROUP BY market_date;

-- 2. Daily price and cleared-energy summary. Weight price by cleared energy.
DROP VIEW IF EXISTS daily_summary;
CREATE VIEW daily_summary AS
SELECT market_date, COUNT(*) AS interval_count,
       AVG(mcp_rs_mwh) AS mean_mcp_rs_mwh,
       MIN(mcp_rs_mwh) AS min_mcp_rs_mwh, MAX(mcp_rs_mwh) AS max_mcp_rs_mwh,
       MAX(mcp_rs_mwh) - MIN(mcp_rs_mwh) AS price_range_rs_mwh,
       SUM(cleared_mwh) AS cleared_mwh,
       SUM(mcp_rs_mwh * cleared_mwh) / NULLIF(SUM(cleared_mwh), 0) AS volume_weighted_mcp_rs_mwh
FROM interval_metrics GROUP BY market_date;

-- 3. Hourly averages of power, sums of energy; clock hour is 00-23.
DROP VIEW IF EXISTS hourly_profile;
CREATE VIEW hourly_profile AS
SELECT market_date, strftime('%H', timestamp) AS clock_hour, COUNT(*) AS interval_count,
       AVG(mcp_rs_mwh) AS mean_mcp_rs_mwh,
       AVG(purchase_bid_mw) AS mean_purchase_bid_mw,
       AVG(sell_bid_mw) AS mean_sell_bid_mw,
       AVG(bid_volume_gap_mw) AS mean_bid_volume_gap_mw,
       SUM(cleared_mwh) AS cleared_mwh,
       SUM(mcv_mw) / NULLIF(SUM(purchase_bid_mw), 0) AS purchase_bid_fulfilment
FROM interval_metrics GROUP BY market_date, strftime('%H', timestamp);

-- 4. Rank absolute changes, preserving ties. Filter rank <= 10 to inspect.
DROP VIEW IF EXISTS price_movement_ranking;
CREATE VIEW price_movement_ranking AS
SELECT market_date, timestamp, previous_mcp_rs_mwh, mcp_rs_mwh, price_change_rs_mwh,
       DENSE_RANK() OVER (PARTITION BY market_date ORDER BY ABS(price_change_rs_mwh) DESC) AS movement_rank
FROM interval_metrics WHERE previous_mcp_rs_mwh IS NOT NULL;

-- 5. Rolling prices are in interval_metrics. First three rows have partial
-- windows: rolling_interval_count makes this explicit. Full windows = 4.

-- 6. Rank lowest purchase-bid fulfilment, excluding undefined zero denominators.
DROP VIEW IF EXISTS fulfilment_ranking;
CREATE VIEW fulfilment_ranking AS
SELECT market_date, timestamp, purchase_bid_mw, mcv_mw, purchase_bid_fulfilment,
       DENSE_RANK() OVER (PARTITION BY market_date ORDER BY purchase_bid_fulfilment) AS lowest_fulfilment_rank
FROM interval_metrics WHERE purchase_bid_fulfilment IS NOT NULL;

-- 7. Consecutive runs at each day's OBSERVED maximum, not a regulatory cap.
DROP VIEW IF EXISTS maximum_price_runs;
CREATE VIEW maximum_price_runs AS
WITH labelled AS (
 SELECT *, MAX(mcp_rs_mwh) OVER (PARTITION BY market_date) AS daily_max
 FROM dam_intervals
), peaks AS (
 SELECT *, LAG(timestamp) OVER (PARTITION BY market_date ORDER BY timestamp) AS previous_peak
 FROM labelled WHERE mcp_rs_mwh = daily_max
), starts AS (
 SELECT *, CASE WHEN previous_peak IS NULL OR
    CAST(strftime('%s', timestamp) AS INTEGER) - CAST(strftime('%s', previous_peak) AS INTEGER) <> 900
    THEN 1 ELSE 0 END AS starts_run
 FROM peaks
), islands AS (
 SELECT *, SUM(starts_run) OVER (PARTITION BY market_date ORDER BY timestamp ROWS UNBOUNDED PRECEDING) AS run_id
 FROM starts
)
SELECT market_date, run_id, MIN(timestamp) AS start_inclusive,
       datetime(MAX(timestamp), '+15 minutes') AS end_exclusive,
       COUNT(*) AS interval_count, COUNT(*) * 15 AS duration_minutes,
       MAX(mcp_rs_mwh) AS maximum_mcp_rs_mwh
FROM islands GROUP BY market_date, run_id;

# IEX DAM Market Monitoring Dashboard

Open `iex_dam_dashboard.twb` in Tableau. This is the original workbook, containing the IEX DAM Market Monitoring Dashboard and five worksheets: AVG MCP, Max MCP, MAX IMBALANCE, MCP Trend, and Demand vs Supply.

## Reconnect the data

The `.twb` contains workbook definitions, not embedded data. Its original connection points to a local Mac folder.

1. Download or clone the repository, including `Exports/cleaned_dam_data.csv`.
2. Open `Tableau/iex_dam_dashboard.twb` in Tableau.
3. If Tableau reports a missing data source, edit the connection and browse to `Exports/cleaned_dam_data.csv` in your local copy.
4. Save the workbook after reconnecting. Optionally save a packaged workbook (`.twbx`) to bundle the data.

The supplied CSV is a single-day snapshot for 24 May 2026 with 15-minute intervals. The workbook's imbalance field is purchase bids minus sell bids, not measured physical grid imbalance. MW fields represent interval power quantities; multiply by 0.25 hours to obtain MWh.

The dashboard screenshot is available in the repository's main README. The uploaded workbook XML was inspected for worksheet names and data connections; it has not been reopened or rendered in Tableau as part of this upload.

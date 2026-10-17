# IEX Day-Ahead Market (DAM) Analysis

## What is this project?
Analysis of Indian Energy Exchange (IEX) Day-Ahead Market electricity pricing data 
to explore price volatility, demand-supply dynamics, and operational trends.

## Data Sources
- IEX DAM historical market data (price, volume, demand, supply)
- Weather data (coming soon — correlating temperature with demand patterns)

## Key Questions Explored
- What drives MCP (Market Clearing Price) volatility?
- How do demand and supply imbalances affect pricing?
- Are there identifiable peak demand patterns?

## Tools Used
- Python (pandas) — data cleaning, time-series analysis
- SQL — market data querying and aggregation
- Tableau — interactive dashboard visualisation
- Jupyter Notebook — exploratory analysis

## Current Status

- Data cleaning and preprocessing completed
- Exploratory analysis completed using Python
- SQL analysis included
- Tableau dashboard created
- Baseline Linear Regression model added for MCP forecasting
- Rolling-horizon battery optimisation prototype added
- Weather API integration planned
- ARIMA / advanced forecasting planned

## Dashboard Preview
<img width="1606" height="1216" alt="image" src="https://github.com/user-attachments/assets/08424593-322f-46cb-ad92-889338b3ccba" />


## Battery Optimisation Extension

A deterministic rolling-horizon battery arbitrage prototype is available in
[`battery-rolling-optimisation/`](battery-rolling-optimisation/).

It uses the IEX DAM 15-minute price data already stored in this repository and
compares 1-hour, 4-hour, 8-hour and full-day look-ahead horizons under explicit
state-of-charge, power and efficiency constraints.

The 8-hour rolling horizon achieved gross arbitrage revenue of approximately
**Rs 73,656.55**, compared with **Rs 73,686.35** for the full-day
perfect-foresight benchmark in this single-day experiment. The prototype is
intentionally deterministic and is intended as a baseline before stochastic
optimisation and learning-based extensions.

## Hydropower scheduling and decision analysis

[HydroOpt](hydropower-scheduling/) studies single-reservoir scheduling with deterministic and two-stage stochastic LPs, CVaR risk preferences, head-dependent production experiments, and out-of-sample first-stage decision-regret evaluation. Its synthetic benchmarks and modelling assumptions are documented within the project folder.

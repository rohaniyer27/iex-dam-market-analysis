# Rolling-Horizon Battery Optimisation

This extension moves the IEX Day-Ahead Market project from descriptive/predictive analysis into a small, explicit sequential decision problem.

## Question

How does battery dispatch change when current charging and discharging decisions account for future electricity prices over a rolling look-ahead horizon?

## Data

The prototype reuses the IEX DAM workbook already stored in this repository at `DATA/DAM_Market Snapshot.xlsx`. The model uses the first 96 consecutive 15-minute trading intervals and Market Clearing Price (MCP) as the price signal.

## Battery assumptions

- 10 MWh energy capacity
- 2.5 MW maximum charge/discharge power
- 5 MWh initial state of charge
- 95% charging efficiency
- 95% discharging efficiency
- price-taker assumption
- 15-minute settlement intervals

## Model

At every 15-minute interval, a linear programme selects charge/discharge decisions over a look-ahead horizon subject to state-of-charge, power and efficiency constraints. Only the first action is implemented, then the optimiser rolls forward and solves again.

When the look-ahead window reaches the end of the observed day, the model restores as much of the initial 5 MWh inventory as is physically reachable so that free depletion of the starting battery inventory is not counted as arbitrage value.

## Results

| Horizon | Gross arbitrage revenue (Rs) | Ending SOC (MWh) |
|---|---:|---:|
| 1 hour | 17,998.74 | 4.35 |
| 4 hours | 69,858.51 | 5.00 |
| 8 hours | 73,656.55 | 5.00 |
| Full day / perfect foresight | 73,686.35 | 5.00 |

The 8-hour rolling horizon captures almost all of the value of the full-day perfect-foresight benchmark in this single-day example, while the 1-hour horizon misses much of the intertemporal opportunity.

## Limitations

This is intentionally a deterministic learning prototype, not a production bidding model:

- realised prices are used inside each look-ahead window;
- there are no probabilistic forecasts or uncertainty scenarios;
- wind generation, mFRR participation, imbalance settlement and degradation costs are excluded;
- it is not reinforcement learning;
- results are based on one observed trading day.

The purpose is to establish the mechanics of state-of-charge constraints, intertemporal value and rolling re-optimisation before extending to stochastic optimisation and learning-based methods.

## Run

From this folder:

```bash
pip install -r requirements.txt
python battery_rolling_optimiser.py --data "../DATA/DAM_Market Snapshot.xlsx" --horizon-hours 8
```

## Natural next steps

1. Replace realised future prices with forecast/scenario distributions.
2. Add wind generation and imbalance settlement.
3. Add CVaR/downside-risk terms.
4. Compare stochastic optimisation with a learned continuation value.
5. Compare the structured optimiser with a direct RL policy.

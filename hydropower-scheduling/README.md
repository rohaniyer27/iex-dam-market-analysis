# Hydropower scheduling mini-lab

A **synthetic educational optimisation project**, developed as technical preparation for research on long-term hydropower scheduling. Kept separate from the Indian Electricity Exchange analysis in the parent repository.

## What it demonstrates

- A seven-day **deterministic** single-reservoir linear programme with storage balance, discharge/spill, physical limits, and fixed terminal water value (`reservoir_lab.py`).
- A small **two-stage stochastic** linear programme with dry/normal/wet inflow scenarios and probabilities 0.25/0.50/0.25 (`stochastic_reservoir.py`). Day-1 actions are non-anticipative; the remaining days can respond to the revealed scenario.
- Assertions for water balance and common first-day decisions.

## Run

```bash
python -m pip install -r requirements.txt
python hydropower-scheduling/reservoir_lab.py
python hydropower-scheduling/stochastic_reservoir.py
```

From the repository root. Or enter the `hydropower-scheduling` directory and omit its prefix.

## Modelling assumptions and limits

All inputs are **illustrative**, with arbitrary water and monetary units. Release-to-generation conversion is 1 MWh per water unit, independent of hydraulic head. The horizon is seven days, and water can be spilled without penalty. The terminal value is a **fixed linear coefficient**, not a learned water-value function. The stochastic model assumes day-1 inflow is known and the whole future inflow regime is revealed after day 1. The individual deterministic scenarios are **perfect-information solves**, not stochastic optimisation.

This is **not** a calibrated Norwegian hydropower system; it does **not** implement nonlinear head-dependent production, multireservoir routing, SDDP, reinforcement learning, or machine-learned continuation values. Do not interpret its synthetic scenario differences as evidence of economic improvements over a real baseline.

## Mathematical formulation

For each day, end-of-day storage satisfies:

`S[t] = S[t-1] + inflow[t] - discharge[t] - spill[t]`

with storage and discharge bounds. Maximise generation revenue plus `terminal_value * final_storage`; the stochastic model maximises the probability-weighted objective and shares first-day decisions across scenarios.

## Validation

Both scripts check equality constraints numerically after solving. The stochastic script also verifies the non-anticipativity equalities. More realistic extensions would compare expected-policy performance out of sample, include nonlinear generation, and test alternative water-value approximations.

## Attribution

Independent educational example implemented with NumPy and SciPy's open-source HiGHS LP backend.

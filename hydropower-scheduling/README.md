# HydroOpt: Hydropower Scheduling and Decision Analysis

HydroOpt is a Python project for studying reservoir scheduling decisions under inflow uncertainty. It compares deterministic, stochastic and risk-aware optimisation approaches, explores how reservoir head changes generation, and evaluates the effect of water-value approximations on scheduling decisions.

The models use a seven-day, single-reservoir test system with generated data. The focus is on transparent formulations, reproducible experiments and decisions under imperfect forecasts.

## Project scope

| Module | Description |
| --- | --- |
| `reservoir_lab.py` | Deterministic linear programme for turbine release, spillage, reservoir storage and terminal water value |
| `stochastic_reservoir.py` | Two-stage stochastic linear programme with shared first-day decisions across dry, normal and wet inflow scenarios |
| `risk_cvar.py` | Two-stage risk-aware variant using Conditional Value at Risk (CVaR) of operating loss |
| `advanced_lab.py` | Rolling-horizon re-optimisation, nonlinear head-dependent generation example and concave piecewise-linear continuation-value approximation |
| `benchmark.py` | Seeded out-of-sample comparison using first-stage decision regret |
| `BENCHMARK.md` | Experimental design, summary metrics and sensitivity checks |
| `ADVANCED.md` | Detailed assumptions for the advanced experiments |

## Formulation

Reservoir storage follows the daily water balance:

```text
storage[t] = storage[t-1] + inflow[t] - discharge[t] - spillage[t]
```

Storage and turbine-release limits constrain the feasible schedule. The linear models maximise electricity revenue plus a terminal value for water remaining at the end of the horizon. The two-stage formulations enforce non-anticipativity: first-day decisions are the same across all scenarios, while later decisions can respond after the scenario is revealed.

The nonlinear example makes release-to-generation conversion depend on beginning-of-day reservoir storage. The continuation-value experiment fits a concave piecewise-linear curve to value samples from small deterministic optimisation problems.

## Setup and execution

Requires Python 3.10+.

From the **repository root**:

```bash
python -m pip install -r hydropower-scheduling/requirements.txt

python hydropower-scheduling/reservoir_lab.py
python hydropower-scheduling/stochastic_reservoir.py
python hydropower-scheduling/risk_cvar.py
python hydropower-scheduling/advanced_lab.py
python hydropower-scheduling/benchmark.py
```

The benchmark writes `hydropower-scheduling/benchmark_results.csv` when executed.

## Benchmark design and findings

The out-of-sample benchmark tests three first-stage policies across 35 seeded synthetic operating contexts and five unseen inflow outcomes per context (175 outcomes per policy). Each policy's first release/spillage decision is fixed, after which the realised scenario is evaluated with optimal remaining-horizon recourse. Decision regret is computed relative to a perfect-information oracle.

| First-stage policy | Mean regret | 90th-percentile regret | Maximum regret |
| --- | ---: | ---: | ---: |
| Expected-inflow LP | 43.543 | 169.752 | 643.047 |
| Scenario LP | 35.020 | 154.990 | 412.959 |
| CVaR LP | 36.192 | 117.647 | 630.094 |

Values are in the model's arbitrary objective units; lower regret is better. The scenario LP reduced mean regret by 19.6% **in this seeded test**, while CVaR produced the lowest 90th-percentile regret. Additional random-seed checks show that rankings vary across samples. Full methodology and sensitivity results are documented in [BENCHMARK.md](BENCHMARK.md).

## Model assumptions

- Single reservoir, seven-day horizon and generated price/inflow data; no claim of calibration to a particular hydropower plant.
- The LP models use constant water-to-energy conversion and a fixed linear terminal water value.
- The two-stage scenario model assumes the future inflow regime is revealed after the first day; this is simpler than realistic sequential forecasting.
- The head-dependent example uses a synthetic production function and a local nonlinear solver, without a global-optimality certificate.
- The fitted concave continuation-value curve is an approximation, not a neural model or a certified SDDP cut.
- The regret benchmark evaluates the **first-stage decision**, not a full sequential policy rollout.

These boundaries help distinguish the formulations and keep comparisons interpretable.

## Next experiments

Extend evaluation to sequential policy rollouts and multi-seed confidence intervals; compare learned terminal-value policies at matched computing budgets; add multi-reservoir routing and calibrated head-dependent production data.

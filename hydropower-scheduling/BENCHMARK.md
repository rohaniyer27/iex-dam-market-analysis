# Synthetic out-of-sample decision-regret benchmark

Reproduce with `python hydropower-scheduling/benchmark.py` after installing `requirements.txt`.

## Experimental design

- 35 random **synthetic** price/inflow contexts, 5 unseen inflow outcomes each (175 matched outcomes per policy), fixed seed 20261017.
- Same initial storage, known day-1 inflow, day-1 price and assumed future inflow information across policies.
- Deterministic **expected-inflow** LP versus a **three-scenario two-stage** LP versus its **CVaR-regularised** variant.
- Each chooses day-1 release and spillage before future inflows are revealed. To score, that first decision is fixed and an optimal deterministic recourse plan is solved for days 2–7 using the realised future inflows.
- The oracle sees all inflows before day 1. **First-stage decision regret** equals oracle objective minus policy objective. It is not sequential closed-loop regret or ML generalisation.
- Scenario factors used in planning: 0.55/1/1.55; realised factors: 0.45/0.70/1/1.30/1.75. Explicitly shifted between planning and evaluation.

## Reproducible results

| Policy | Evaluations | Mean regret | p90 regret | Maximum regret | Zero-regret fraction |
| --- | ---: | ---: | ---: | ---: | ---: |
| Expected-inflow LP | 175 | 43.543 | 169.752 | 643.047 | 81.1% |
| Scenario LP | 175 | 35.020 | 154.990 | 412.959 | 77.1% |
| CVaR LP (weight 0.6) | 175 | 36.192 | 117.647 | 630.094 | 78.9% |

Scenario LP shows a **19.6% lower mean regret in this particular synthetic benchmark** relative to the expected-inflow LP. However, it has a *lower* zero-regret fraction. CVaR improves the 90th-percentile regret but does not beat scenario LP on mean or maximum regret in this experiment. This is not a general statistical performance claim and does not prove efficacy for real hydropower systems.

## Caveats and checks

The optimisation LP constraints are checked numerically and oracle dominance is checked for every scored policy/outcome. The risk objective operates on negative total operating value. Scenarios are synthetic, single-reservoir and linearly convert water to electricity. The model assumes the **entire** remaining hydrological regime becomes known immediately after day 1; that is a simplifying two-stage information structure, not a realistic daily-updated forecast process. CVaR uses the planning distribution, not the shifted evaluation distribution.

No learning model was trained for this benchmark; the concave value approximation remains a *separate*, preliminary experiment in `advanced_lab.py`. More rigorous work should add multiple independent seeds, confidence intervals clustered by context, full policy rollouts, physically calibrated heads, and matched-compute model comparisons. 


## Additional seed sensitivity check (15 contexts × 5 outcomes per seed)

| Seed | Expected-inflow mean regret | Scenario LP | CVaR LP |
| --- | ---: | ---: | ---: |
| 31 | 35.183 | 36.456 | 37.550 |
| 42 | 20.748 | 20.748 | 20.748 |
| 99 | 45.466 | 50.401 | 59.604 |

**Interpretation:** Relative performance changes across synthetic draws. The main-seed 19.6% improvement is **not stable evidence of a general gain**. These are quick robustness spot checks, not confidence intervals or formal significance analysis. They reinforce the research motivation: decision-level evaluation matters, and favorable single-seed numbers should not be overgeneralized.

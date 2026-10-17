## Advanced experiments

Run from the project directory: `python advanced_lab.py`.

This adds: (1) rolling-horizon re-optimisation under biased forecasts; (2) a **synthetic** nonlinear head-dependent generation proxy solved locally using SLSQP; and (3) a concave piecewise-linear approximation to continuation values sampled from deterministic LPs, evaluated on a held-out **synthetic context**. Two-stage stochastic optimisation and non-anticipativity remain in `stochastic_reservoir.py`.

**Limitations:** This is an educational experiment. It is not SDDP, neural SDDP, calibrated head-dependent generation, a trained neural network, multi-reservoir optimisation, or a production decision-support engine. The concavity projection does not create certified SDDP cuts. Held-out error is not decision regret. The nonlinear solver provides local solutions only; results across the different formulations are not directly comparable. Do not claim benchmark gains without measured experiments.

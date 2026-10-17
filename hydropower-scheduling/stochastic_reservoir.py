"""Synthetic two-stage reservoir scheduling using SciPy / HiGHS.
Day-1 actions are common to all scenarios; future releases adapt after uncertainty is observed.
Not SDDP, head-dependent production, or learned water-value optimisation.
"""
import numpy as np
from scipy.optimize import linprog

PRICES = np.array([42, 38, 60, 85, 52, 95, 70.], dtype=float)
INFLOW = np.array([9, 8, 11, 7, 6, 10, 8.], dtype=float)
SCENARIOS = {"dry": (0.65, 0.25), "normal": (1.0, 0.50), "wet": (1.40, 0.25)}
INITIAL, CAPACITY, MAX_RELEASE, TERMINAL_VALUE = 55.0, 100.0, 22.0, 50.0

def solve_stochastic():
    names, T = list(SCENARIOS), len(PRICES)
    n = len(names) * 3 * T
    costs, rows, rhs, bounds = np.zeros(n), [], [], []
    for k, name in enumerate(names):
        multiplier, probability = SCENARIOS[name]
        off = k * 3 * T
        costs[off:off + T] = -probability * PRICES
        costs[off + 3*T - 1] = -probability * TERMINAL_VALUE
        bounds += [(0, MAX_RELEASE)] * T + [(0, None)] * T + [(0, CAPACITY)] * T
        for t in range(T):
            row = np.zeros(n)
            row[off+t] = row[off+T+t] = row[off+2*T+t] = 1.0
            if t: row[off+2*T+t-1] = -1.0
            rows.append(row)
            rhs.append(INFLOW[t]*(1.0 if t == 0 else multiplier)+(INITIAL if t == 0 else 0))
    # Non-anticipativity: decisions on day 1 must not depend on future inflows.
    for k in range(1, len(names)):
        for block in (0, T, 2*T):
            row = np.zeros(n)
            row[block], row[k*3*T+block] = 1.0, -1.0
            rows.append(row)
            rhs.append(0.0)
    A, b = np.asarray(rows), np.asarray(rhs)
    result = linprog(costs, A_eq=A, b_eq=b, bounds=bounds, method="highs")
    if not result.success: raise RuntimeError(result.message)
    assert np.allclose(A @ result.x, b, atol=1e-7)
    schedules = {}
    for k, name in enumerate(names):
        x = result.x[k*3*T:(k+1)*3*T]
        q, spill, storage = x[:T], x[T:2*T], x[2*T:]
        schedules[name] = {
            "discharge": q, "spill": spill, "storage": storage,
            "revenue": float(PRICES @ q), "final_storage": float(storage[-1])
        }
    for field in ("discharge", "spill", "storage"):
        assert np.ptp([schedules[name][field][0] for name in names]) < 1e-7
    return {"expected_objective": float(-result.fun), "schedules": schedules}

if __name__ == "__main__":
    results = solve_stochastic()
    print("Expected objective incl. terminal value:", round(results["expected_objective"], 2))
    for name, x in results["schedules"].items():
        print(name, "day-1 release", round(x["discharge"][0], 2),
              "revenue", round(x["revenue"], 2), "terminal storage", round(x["final_storage"], 2))
    print("Non-anticipativity and water-balance checks: PASS")

"""Seven-day deterministic reservoir LP with synthetic inputs, solved by HiGHS."""
import numpy as np
from scipy.optimize import linprog

PRICES = np.array([42, 38, 60, 85, 52, 95, 70.], dtype=float)
INFLOW = np.array([9, 8, 11, 7, 6, 10, 8.], dtype=float)
INITIAL, CAPACITY, MAX_RELEASE, TERMINAL_VALUE = 55., 100., 22., 50.

def solve(inflows=INFLOW, prices=PRICES, terminal_value=TERMINAL_VALUE):
    T = len(prices)
    c = np.r_[-prices, np.zeros(T), np.r_[np.zeros(T-1), -terminal_value]]
    A, b = np.zeros((T, 3*T)), np.asarray(inflows, dtype=float).copy()
    for t in range(T):
        A[t,t] = A[t,T+t] = A[t,2*T+t] = 1.
        if t: A[t,2*T+t-1] = -1.
        else: b[t] += INITIAL
    bounds = [(0, MAX_RELEASE)]*T + [(0, None)]*T + [(0, CAPACITY)]*T
    result = linprog(c, A_eq=A, b_eq=b, bounds=bounds, method="highs")
    if not result.success: raise RuntimeError(result.message)
    assert np.allclose(A @ result.x, b, atol=1e-7)
    q, spill, storage = np.split(result.x, 3)
    return {"revenue": float(prices @ q), "objective": float(-result.fun),
            "discharge": q, "spill": spill, "storage": storage}

if __name__ == "__main__":
    for name, scale in (("dry", .65), ("normal", 1.), ("wet", 1.4)):
        x = solve(INFLOW * scale)
        print(name, "revenue", round(x["revenue"], 2),
              "final storage", round(x["storage"][-1], 2))
    print("Separate perfect-information scenarios, NOT a stochastic programme.")

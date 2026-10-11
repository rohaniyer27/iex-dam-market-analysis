"""
Deterministic rolling-horizon battery arbitrage on IEX Day-Ahead Market prices.

Data: IEX DAM snapshot in ../DATA/DAM_Market Snapshot.xlsx
Purpose: transparent optimisation baseline, not a deployable trading strategy.
"""

from pathlib import Path
import argparse
import pandas as pd
import numpy as np
from scipy.optimize import linprog

DT_H = 0.25
CAPACITY_MWH = 10.0
MAX_POWER_MW = 2.5
INITIAL_SOC_MWH = 5.0
ETA_CHARGE = 0.95
ETA_DISCHARGE = 0.95


def load_prices(path):
    raw = pd.read_excel(path, header=4)
    data = raw.iloc[:96].copy()
    prices = pd.to_numeric(data["MCP (Rs/MWh) *"], errors="coerce")
    if prices.isna().any():
        raise ValueError("Missing/non-numeric MCP values in first 96 trading intervals")
    date = pd.to_datetime(str(data["Date"].iloc[0]), dayfirst=True)
    start_times = data["Time Block"].astype(str).str.split("-").str[0].str.strip()
    timestamps = pd.to_datetime(date.strftime("%Y-%m-%d") + " " + start_times)
    return prices.to_numpy(float), timestamps


def solve_horizon(price_window, start_soc, terminal_floor=None):
    H = len(price_window)
    nv = 3 * H
    c = np.zeros(nv)

    # linprog minimises, so negate arbitrage revenue.
    c[:H] = price_window * DT_H
    c[H:2 * H] = -price_window * DT_H

    A_eq, b_eq = [], []
    for t in range(H):
        row = np.zeros(nv)
        row[t] = -ETA_CHARGE * DT_H
        row[H + t] = DT_H / ETA_DISCHARGE
        row[2 * H + t] = 1.0
        if t == 0:
            rhs = start_soc
        else:
            row[2 * H + t - 1] = -1.0
            rhs = 0.0
        A_eq.append(row)
        b_eq.append(rhs)

    A_ub, b_ub = [], []
    if terminal_floor is not None:
        row = np.zeros(nv)
        row[3 * H - 1] = -1.0
        A_ub.append(row)
        b_ub.append(-terminal_floor)

    bounds = (
        [(0.0, MAX_POWER_MW)] * H
        + [(0.0, MAX_POWER_MW)] * H
        + [(0.0, CAPACITY_MWH)] * H
    )

    res = linprog(
        c,
        A_ub=np.array(A_ub) if A_ub else None,
        b_ub=np.array(b_ub) if A_ub else None,
        A_eq=np.array(A_eq),
        b_eq=np.array(b_eq),
        bounds=bounds,
        method="highs",
    )
    if not res.success:
        raise RuntimeError(res.message)

    x = res.x
    return x[:H], x[H:2 * H], x[2 * H:]


def run_rolling(prices, timestamps, horizon_intervals):
    soc = INITIAL_SOC_MWH
    records = []
    n = len(prices)

    for t in range(n):
        end = min(n, t + horizon_intervals)
        H = end - t

        terminal_floor = None
        if end == n:
            max_reachable = min(
                CAPACITY_MWH,
                soc + H * MAX_POWER_MW * DT_H * ETA_CHARGE,
            )
            terminal_floor = min(INITIAL_SOC_MWH, max_reachable)

        charge, discharge, soc_path = solve_horizon(
            prices[t:end], soc, terminal_floor
        )

        ch = float(charge[0])
        dis = float(discharge[0])
        soc = float(soc_path[0])

        records.append(
            {
                "timestamp": timestamps.iloc[t],
                "price_rs_mwh": prices[t],
                "charge_mw": ch,
                "discharge_mw": dis,
                "soc_mwh": soc,
                "interval_revenue_rs": prices[t] * (dis - ch) * DT_H,
            }
        )

    return pd.DataFrame(records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        default="../DATA/DAM_Market Snapshot.xlsx",
        help="Path to IEX DAM market snapshot workbook",
    )
    parser.add_argument("--horizon-hours", type=float, default=8.0)
    parser.add_argument("--output", default="dispatch_results.csv")
    args = parser.parse_args()

    prices, timestamps = load_prices(args.data)
    horizon_intervals = max(1, int(args.horizon_hours / DT_H))
    result = run_rolling(prices, timestamps, horizon_intervals)
    result.to_csv(args.output, index=False)

    print(f"Horizon: {args.horizon_hours:g} h")
    print(f"Gross arbitrage revenue: Rs {result['interval_revenue_rs'].sum():,.2f}")
    print(f"Ending SOC: {result['soc_mwh'].iloc[-1]:.2f} MWh")


if __name__ == "__main__":
    main()

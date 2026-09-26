"""Reproducible backtest for strategies/IOVA.py.
Run: python3 strategies/IOVA_backtest.py
Options priced with common.bs_price (Black-Scholes), vol = HV20 at entry x IV_MULT,
round-trip spread charged via common.option_trade_return's spread_cost.
Position sizing: 5% of equity in premium per trade (premium = max loss), one trade at a time.
"""
import os
import sys, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
import common
from strategies import IOVA as S

IV_MULT = 1.20          # measured: Nov-26 ATM IV ~92% vs HV30 71% (1.3x); use 1.2 as long-run avg
SPREAD = {"CALL": 0.15, "PUT": 0.20}   # measured bid/ask on Nov-26 monthlies: 16% ATM call, 29% ATM put (mid-ish fills assumed)
RISK = 0.05
VOL_FLOOR = 0.50


def option_path_trade(d, i, kind, dte, mny, tgt, stp, max_hold, flip_exit=True):
    """Enter at close i; mark option daily; exit on target/stop/max-hold/flip. Returns (exit_idx, ret)."""
    e = d.iloc[i]
    vol = max(e.hv20 * IV_MULT, VOL_FLOOR)
    sc = SPREAD[kind]
    last = len(d) - 1
    for j in range(i + 1, min(i + max_hold, last) + 1):
        days = (d.date.iloc[j] - e.date).days
        # mark-to-model value (before costs) to test target/stop
        r = common.option_trade_return(e.close, d.close.iloc[j], kind, dte, days, vol, mny, spread_cost=0.0)
        flip = flip_exit and ((kind == "CALL" and d.close.iloc[j] < d.sma50.iloc[j]) or
                              (kind == "PUT" and d.close.iloc[j] > d.sma50.iloc[j]))
        if r >= tgt or r <= -stp or flip or j == i + max_hold or j == last:
            return j, max(r - sc, -1.0), days
    return i, 0.0, 0


def run(d, start, end, params, baseline=False):
    r2m, pb, mx, tgt, stp, mh = params
    trades, i = [], max(start, 130)
    while i < end:
        row = d.iloc[i]
        if baseline:
            if pd.isna(row.slope_wk):
                i += 1; continue
            kind = "CALL" if row.slope_wk > 0 else "PUT"
            j, r, days = option_path_trade(d, i, kind, 45, 0.0, 99, 99, 21, flip_exit=False)
        else:
            kind, _ = S.raw_signal(row, r2m, pb, mx)
            if kind is None:
                i += 1; continue
            j, r, days = option_path_trade(d, i, kind, S.DTE, S.MONEYNESS, tgt, stp, mh, flip_exit=S.FLIP_EXIT)
        if j <= i:
            break
        trades.append(dict(entry=row.date.date(), exit=d.date.iloc[j].date(), kind=kind,
                           spot_in=row.close, spot_out=d.close.iloc[j], days=days, ret=r))
        i = j + 1
    return pd.DataFrame(trades)


def stats(t):
    if t.empty:
        return dict(n=0)
    eq = (1 + RISK * t.ret.clip(lower=-1)).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    streak = m = 0
    for x in t.ret:
        m = m + 1 if x <= 0 else 0; streak = max(streak, m)
    return dict(n=len(t), calls=int((t.kind == "CALL").sum()), puts=int((t.kind == "PUT").sum()),
                win=round((t.ret > 0).mean(), 2), avg=round(t.ret.mean(), 3), med=round(t.ret.median(), 3),
                total=round(eq.iloc[-1] - 1, 3), maxdd=round(dd, 3), lose_streak=streak)


def main():
    d = S.indicators(common.load("IOVA"))
    split = int(len(d) * 0.70)
    print(f"data {d.date.iloc[0].date()} .. {d.date.iloc[-1].date()}  rows={len(d)}  "
          f"IS < {d.date.iloc[split].date()} <= OOS")
    default = (S.R2_MIN, S.PB_BAND, S.MAX_EXT, S.TARGET_PCT, S.STOP_PCT, S.MAX_HOLD)
    # small in-sample sensitivity grid (selection uses IS only)
    grid = list(itertools.product([0.5, 0.6, 0.7], [0.0, 0.03, 0.06], [0.35], [1.0], [1.0], [20]))
    grid += [(0.6, 0.03, m, t, s, h) for m, t, s, h in
             [(0.35, 0.8, 0.5, 20), (0.35, 0.5, 0.4, 15), (0.35, 1.0, 0.6, 30), (0.35, 9, 9, 20), (9, 1.0, 1.0, 20)]]
    print("\nIS sensitivity (r2, pb, maxext, tgt, stop, hold) -> stats")
    for p in grid:
        s = stats(run(d, 0, split, p)); o = stats(run(d, split, len(d) - 1, p))
        print(p, "IS", s, "| OOS", o)
    print("\n=== CHOSEN (module defaults):", default)
    for name, a, b in [("IN-SAMPLE", 0, split), ("OUT-OF-SAMPLE", split, len(d) - 1), ("FULL", 0, len(d) - 1)]:
        t = run(d, a, b, default); tb = run(d, a, b, default, baseline=True)
        print(f"{name:14s} strategy {stats(t)}")
        print(f"{'':14s} baseline {stats(tb)}")
        if name == "FULL":
            pd.set_option("display.width", 200)
            print(t.round(3).to_string())
    return d


if __name__ == "__main__":
    main()

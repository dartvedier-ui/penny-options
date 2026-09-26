"""Backtest for strategies/SURG.py (hypothetical ATM options priced with Black-Scholes).

Options are priced as if an ATM strike existed. In reality SURG's lowest strike is
$0.50 (spot ~$0.15), so these results describe the *direction signal* only.
Run: python3 strategies/SURG_backtest.py
"""
import os
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common
from strategies import SURG

IV_HV = 1.7         # live: option mid-IV ~4.2-4.9 vs 30d HV ~2.6 -> ~1.7x
SPREAD = 0.30       # round-trip cost as fraction of premium (0.30x0.50 quotes => worse in reality)
RISK = 0.05
SPLIT = 0.70


def run_trades(df, actions, vol):
    c = df["close"].values
    trades, i, n = [], 0, len(df)
    while i < n - 1:
        a = actions[i]
        if a not in ("CALL", "PUT") or np.isnan(vol[i]):
            i += 1
            continue
        s0, v = c[i], max(vol[i] * IV_HV, 0.3)
        buy = common.bs_price(s0, s0, SURG.DTE, v, a)
        exit_j, ret, why = None, None, "max_hold"
        for h in range(1, SURG.MAX_HOLD + 1):
            j = i + h
            if j >= n:
                break
            val = common.bs_price(c[j], s0, SURG.DTE - h * 7 / 5, v, a)
            r = val / buy - 1
            exit_j, ret = j, r
            if r >= SURG.TARGET_PCT:
                why = "target"; break
            if r <= -SURG.STOP_PCT:
                why = "stop"; break
        if exit_j is None:
            break
        if why == "max_hold" and exit_j - i < SURG.MAX_HOLD:
            why = "open_at_end"
        trades.append(dict(entry=df.date.iloc[i], exit=df.date.iloc[exit_j], kind=a,
                           s0=s0, s1=c[exit_j], days=exit_j - i,
                           ret=ret - SPREAD, why=why))
        i = exit_j + 1
    return pd.DataFrame(trades)


def stats(t, label):
    if len(t) == 0:
        return dict(set=label, trades=0)
    eq = np.cumprod(1 + RISK * t.ret.clip(lower=-1).values)
    peak = np.maximum.accumulate(np.concatenate([[1], eq]))
    dd = (np.concatenate([[1], eq]) / peak - 1).min()
    streak = best = 0
    for r in t.ret:
        streak = streak + 1 if r <= 0 else 0
        best = max(best, streak)
    return dict(set=label, trades=len(t), win=round((t.ret > 0).mean(), 2),
                avg=round(t.ret.mean(), 3), med=round(t.ret.median(), 3),
                comp5=round(eq[-1] - 1, 3), maxdd=round(dd, 3), lose_streak=best,
                puts=int((t.kind == "PUT").sum()), calls=int((t.kind == "CALL").sum()),
                stops=int((t.why == "stop").sum()))


def main():
    df = common.load("SURG")
    f = SURG.features(df)
    actions = [SURG.raw_action(r) for r in f.itertuples()]
    vol = f.vol20.values
    # baseline: follow the 13-week (65d) trend sign every time flat
    base = ["PUT" if s < 0 else "CALL" if s > 0 else "NONE" for s in f.slope65.fillna(0)]
    cut = df.date.iloc[int(len(df) * SPLIT)]
    out = []
    for name, acts in (("strategy", actions), ("baseline_13w", base)):
        t = run_trades(df, acts, vol)
        t["name"] = name
        out.append(t)
        for lbl, sub in (("IS", t[t.entry < cut]), ("OOS", t[t.entry >= cut]), ("ALL", t)):
            print(name, stats(sub, lbl))
    print("split date:", cut.date(), "| data", df.date.iloc[0].date(), "->", df.date.iloc[-1].date())
    # sensitivity to cost assumptions
    global SPREAD, IV_HV
    for sp, ivm in ((0.15, 1.3), (0.30, 1.7), (0.50, 2.0)):
        SPREAD, IV_HV = sp, ivm
        t = run_trades(df, actions, vol)
        print(f"sens spread={sp} iv/hv={ivm}:", stats(t[t.entry >= cut], "OOS"), stats(t, "ALL"))
    return pd.concat(out)


if __name__ == "__main__":
    allt = main()
    pd.set_option("display.width", 200)
    print(allt[allt.name == "strategy"].to_string())

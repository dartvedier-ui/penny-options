"""FNGR backtest: weekly trend-following PUT strategy, priced with Black-Scholes (common.py).

Run: python3 strategies/FNGR_backtest.py
Uses the 5-year weekly file (more history than the 2-year daily file). Entries/exits on weekly closes.
"""
import os
import sys, math
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common

IV_HV = 1.10        # IV / realised-vol multiplier (live: IV 203% vs 30d HV 303% vs 2y HV 132%)
SPREAD = 0.30       # round-trip spread+fees as fraction of premium (penny options: tick >= 20% of premium)
DTE = 60            # days to expiry at entry
RISK = 0.05         # fraction of equity risked (premium paid) per trade

P = dict(slope_max=-0.03, r2_min=0.60, stretch_min=-0.30, stop_up=0.25, target_dn=0.30, max_weeks=6)


def features(w):
    w = w.copy()
    L = np.log(w.close.values)
    slope = np.full(len(w), np.nan); r2 = np.full(len(w), np.nan)
    x = np.arange(14)
    for i in range(13, len(w)):
        y = L[i - 13:i + 1]; b, a = np.polyfit(x, y, 1)
        slope[i] = b; r2[i] = np.corrcoef(x, y)[0, 1] ** 2
    w["slope"], w["r2"] = slope, r2
    w["ma10"] = w.close.rolling(10).mean()
    w["stretch"] = w.close / w.ma10 - 1
    w["vol"] = np.log(w.close).diff().rolling(20, min_periods=10).std() * math.sqrt(52)
    return w


def run(w, p=P, start=0, end=None):
    end = len(w) if end is None else end
    trades = []; i = max(start, 20)
    while i < end - 1:
        r = w.iloc[i]
        ok = (r.slope < p["slope_max"] and r.r2 > p["r2_min"] and r.close < r.ma10
              and r.stretch > p["stretch_min"])
        if not ok:
            i += 1; continue
        e = r.close; vol = max(r.vol, 0.8) * IV_HV
        j = i; reason = "time"
        for k in range(1, p["max_weeks"] + 1):
            j = i + k
            if j >= len(w): j = len(w) - 1; reason = "eod"; break
            c = w.close.iloc[j]
            if c >= e * (1 + p["stop_up"]) or c > w.ma10.iloc[j]: reason = "stop"; break
            if c <= e * (1 - p["target_dn"]): reason = "target"; break
        held = (j - i) * 7
        ret = common.option_trade_return(e, w.close.iloc[j], "PUT", DTE, held, vol, 0.0, SPREAD)
        trades.append(dict(entry=w.date.iloc[i].date(), exit=w.date.iloc[j].date(), kind="PUT",
                           s0=e, s1=w.close.iloc[j], weeks=j - i, why=reason, ret=max(ret, -1.0)))
        i = j + 1
    return pd.DataFrame(trades)


def baseline(w, start=0, end=None, hold=4):
    """Naive: every 4 weeks buy ATM PUT if 13-wk slope<0 else CALL, hold 4 weeks."""
    end = len(w) if end is None else end; out = []
    for i in range(max(start, 20), end - hold, hold):
        r = w.iloc[i]; kind = "PUT" if r.slope < 0 else "CALL"
        vol = max(r.vol, 0.8) * IV_HV
        ret = common.option_trade_return(r.close, w.close.iloc[i + hold], kind, DTE, hold * 7, vol, 0.0, SPREAD)
        out.append(dict(entry=w.date.iloc[i].date(), kind=kind, ret=max(ret, -1.0)))
    return pd.DataFrame(out)


def stats(t):
    if len(t) == 0:
        return dict(trades=0)
    eq = np.cumprod(1 + RISK * t.ret.values); peak = np.maximum.accumulate(np.r_[1, eq])
    dd = (np.r_[1, eq] / peak - 1).min()
    streak = m = 0
    for x in t.ret:
        m = m + 1 if x <= 0 else 0; streak = max(streak, m)
    return dict(trades=len(t), win=round((t.ret > 0).mean(), 2), avg=round(t.ret.mean(), 3),
                med=round(t.ret.median(), 3), comp=round(eq[-1] - 1, 3), maxdd=round(dd, 3), lose_streak=streak)


if __name__ == "__main__":
    w = features(common.load("FNGR", "weekly"))
    split = int(len(w) * 0.70)
    print(f"weeks={len(w)}  IS {w.date.iloc[0].date()}..{w.date.iloc[split-1].date()}  OOS {w.date.iloc[split].date()}..{w.date.iloc[-1].date()}")
    for name, s, e in [("IN-SAMPLE", 0, split), ("OUT-OF-SAMPLE", split, None), ("FULL", 0, None)]:
        t = run(w, P, s, e); b = baseline(w, s, e)
        print(f"\n{name}  strategy: {stats(t)}\n{' '*len(name)}  baseline: {stats(b)}")
        if name != "FULL":
            print(t.to_string(index=False) if len(t) else "  (no trades)")
    # sensitivity to cost assumptions (full period)
    print("\nSensitivity (full period):")
    for sp in (0.15, 0.30, 0.45):
        for ivm in (0.9, 1.1, 1.4):
            SPREAD, IV_HV = sp, ivm
            print(f"  spread={sp:.2f} iv/hv={ivm}: {stats(run(w, P))}")

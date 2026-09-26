"""Reproducible backtest for strategies/OPEN.py.

Run:  python3 strategies/OPEN_backtest.py
Data: data/OPEN_weekly.csv (IBKR weekly bars, Sep-2021 .. Sep-2026).
Signals are taken on weekly closes (same rules as OPEN.signal); the option is priced
with common.option_trade_return (Black-Scholes) using 10-week realised vol x IV_HV,
and checked each following week against the weekly high/low for stop/target.
"""
import os
import sys, math
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common
from strategies import OPEN as S

IV_HV = 1.15          # measured: ATM IV ~70-72% vs 30d HV ~61% on 2026-09-24
SPREAD = 0.15         # round-trip bid/ask + commissions as fraction of premium (measured ~4-10% + fees)
RISK = 0.05           # premium paid = 5% of account per trade
SPLIT = 0.70


def opt_ret(e, x, kind, held_days, vol):
    return common.option_trade_return(e, x, kind, S.DTE, held_days, vol,
                                      moneyness=S.MONEYNESS, spread_cost=0.0)


def run(w, params=None, baseline=False):
    p = dict(SLOPE_MIN=S.SLOPE_MIN, R2_MIN=S.R2_MIN, MAX_STRETCH=S.MAX_STRETCH,
             TARGET=S.TARGET, STOP=S.STOP, MAX_HOLD_WEEKS=S.MAX_HOLD_WEEKS)
    if params:
        p.update(params)
    old = {k: getattr(S, k) for k in p}
    for k, v in p.items():
        setattr(S, k, v)
    trades = []
    i = 0
    n = len(w)
    try:
        while i < n - 1:
            row = w.iloc[i]
            if baseline:
                if pd.isna(row["slope13"]):
                    i += 1; continue
                act = "PUT" if row["slope13"] < 0 else "CALL"
            else:
                act, _ = S.decide(row)
            if act == "NONE":
                i += 1; continue
            e = row["close"]
            vol = float(np.clip(row["hv10"] * IV_HV, 0.5, 2.0))
            exit_ret, j, why = None, i, "time"
            for k in range(1, p["MAX_HOLD_WEEKS"] + 1):
                j = i + k
                if j >= n:
                    j = n - 1; break
                b = w.iloc[j]
                days = 7 * k
                adverse = b["high"] if act == "PUT" else b["low"]
                favour = b["low"] if act == "PUT" else b["high"]
                r_open = opt_ret(e, b["open"], act, days - 5, vol)
                if not baseline:
                    if r_open <= -p["STOP"]:            # gapped through stop
                        exit_ret, why = r_open, "stop(gap)"; break
                    if r_open >= p["TARGET"]:
                        exit_ret, why = r_open, "target(gap)"; break
                    if opt_ret(e, adverse, act, days - 2, vol) <= -p["STOP"]:
                        exit_ret, why = -p["STOP"], "stop"; break   # stop checked first (conservative)
                    if opt_ret(e, favour, act, days - 2, vol) >= p["TARGET"]:
                        exit_ret, why = p["TARGET"], "target"; break
                exit_ret = opt_ret(e, b["close"], act, days, vol)
            if exit_ret is None:
                exit_ret = opt_ret(e, w.iloc[j]["close"], act, 7 * (j - i), vol)
            trades.append(dict(entry_date=w.iloc[i]["date"], exit_date=w.iloc[j]["date"], kind=act,
                               entry=e, exit=w.iloc[j]["close"], weeks=j - i, vol=round(vol, 2),
                               ret=exit_ret - SPREAD, why=why))
            i = j if j > i else i + 1
    finally:
        for k, v in old.items():
            setattr(S, k, v)
    return pd.DataFrame(trades)


def stats(t):
    if len(t) == 0:
        return dict(n=0)
    eq = np.cumprod(1 + RISK * t["ret"].values)
    peak = np.maximum.accumulate(np.concatenate([[1.0], eq]))[1:]
    dd = (eq / peak - 1).min()
    streak = best = 0
    for r in t["ret"]:
        streak = streak + 1 if r <= 0 else 0
        best = max(best, streak)
    return dict(n=len(t), puts=int((t.kind == "PUT").sum()), calls=int((t.kind == "CALL").sum()),
                win=round((t.ret > 0).mean() * 100, 1), avg=round(t.ret.mean() * 100, 1),
                med=round(t.ret.median() * 100, 1), total=round((eq[-1] - 1) * 100, 1),
                maxdd=round(dd * 100, 1), lose_streak=best)


def main(verbose=True):
    w = S.weekly_features(common.load("OPEN", "weekly"))
    cut = w["date"].iloc[int(len(w) * SPLIT)]
    t = run(w)
    tb = run(w, baseline=True)
    out = {}
    for name, tt in (("strategy", t), ("baseline_13w_trend", tb)):
        for seg, m in (("in-sample", tt.entry_date < cut), ("out-of-sample", tt.entry_date >= cut), ("all", slice(None))):
            out[(name, seg)] = stats(tt[m] if not isinstance(m, slice) else tt)
    res = pd.DataFrame(out).T
    if verbose:
        print(f"weekly bars {w.date.iloc[0].date()} .. {w.date.iloc[-1].date()}  split at {cut.date()}")
        print(res.to_string())
        print("\nStrategy trades:")
        print(t.assign(ret=(t.ret * 100).round(1)).to_string(index=False))
        # sensitivity (all data) -- shows whether the result depends on exact parameters
        print("\nSensitivity (full sample, avg%/total%/n):")
        for sm in (0.01, 0.015, 0.025):
            for ms in (0.15, 0.20, 0.30):
                tt = run(w, dict(SLOPE_MIN=sm, MAX_STRETCH=ms))
                s_is = stats(tt[tt.entry_date < cut]); s_os = stats(tt[tt.entry_date >= cut])
                print(f"  slope>={sm:.3f} stretch<={ms:.2f}: IS avg {s_is.get('avg')} tot {s_is.get('total')} n {s_is.get('n')} | "
                      f"OOS avg {s_os.get('avg')} tot {s_os.get('total')} n {s_os.get('n')}")
        print("\nPuts only vs calls only (all):")
        print("  puts ", stats(t[t.kind == "PUT"]))
        print("  calls", stats(t[t.kind == "CALL"]))
    return res, t, tb


if __name__ == "__main__":
    main()

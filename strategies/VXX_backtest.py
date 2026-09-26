"""Reproducible backtest for the VXX long-put / long-call strategy.

Run:  python3 strategies/VXX_backtest.py
Data: data/VXX_daily.csv (IBKR, split-adjusted; 1:4 reverse splits 2023-03-07 and 2024-07-24).

Option model: Black-Scholes via common.bs_price. Implied vol is modelled as
IV = max(IV_MULT * HV20, IV_FLOOR), re-evaluated at exit (so IV expands on spikes).
Spread: round-trip cost as % of premium measured from the live IBKR chain (Sep-2026).
Sizing: 5% of account equity in premium per trade (premium = max loss).
"""
import os
import sys, math, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
import common
from strategies import VXX as S

IV_MULT, IV_FLOOR = S.IV_MULT, S.IV_FLOOR
SPREAD = {"PUT": 0.12, "CALL": 0.15}
RISK = 0.05


IV_CAP = 1.2  # without a cap, HV-spikes (Aug-2024) inflate modelled put IV to 150%+ and create a vega windfall


def iv_at(hv):
    return min(max(IV_MULT * hv, IV_FLOOR), IV_CAP)


def run(df, start, end, p=None, sig_fn=None, fixed_vol=False):
    """Simulate trades whose entry index is in [start, end). One position at a time."""
    p = {**S.PARAMS, **(p or {})}
    sig_fn = sig_fn or S.raw_signal
    feats = S.features(df)
    c = df.close.values
    trades, i = [], max(start, 70)
    while i < end - 1:
        act = sig_fn(feats, i, p)
        if act == "NONE":
            i += 1; continue
        kind = act
        dte = p["dte"]; m = p["moneyness"]
        spot0 = c[i]
        strike = spot0 * (1 - m) if kind == "CALL" else spot0 * (1 + m)
        v0 = iv_at(feats.hv20.iloc[i])
        prem0 = common.bs_price(spot0, strike, dte, v0, kind)
        exit_j, why = None, "maxhold"
        for j in range(i + 1, min(i + 1 + p["max_hold"], len(c))):
            days = (df.date.iloc[j] - df.date.iloc[i]).days
            v1 = v0 if fixed_vol else iv_at(feats.hv20.iloc[j])
            val = common.bs_price(c[j], strike, dte - days, v1, kind)
            ret = val / prem0 - 1
            exit_j = j
            if ret >= p["target"]:
                why = "target"; break
            if ret <= -p["stop"]:
                why = "stop"; break
        if exit_j is None:
            break
        if why == "maxhold" and exit_j - i < p["max_hold"]:
            break  # trade still open at end of data - not counted
        ret_net = ret - SPREAD[kind]
        trades.append(dict(entry=df.date.iloc[i].date(), exit=df.date.iloc[exit_j].date(), kind=kind,
                           spot0=spot0, spot1=c[exit_j], ret=ret_net, why=why, days=exit_j - i))
        i = exit_j + 1
    return pd.DataFrame(trades)


def baseline(df, start, end, p=None):
    """Naive: every time flat, follow the sign of the 13-week (65d) log slope: PUT if down, CALL if up."""
    def sig(feats, i, p):
        return "PUT" if feats.slope65.iloc[i] < 0 else "CALL"
    return run(df, start, end, p, sig_fn=sig)


def stats(t):
    if len(t) == 0:
        return dict(n=0)
    r = t.ret.values
    eq = np.cumprod(1 + RISK * r)
    peak = np.maximum.accumulate(np.concatenate([[1], eq]))[1:]
    dd = (eq / peak - 1).min()
    streak = mx = 0
    for x in r:
        streak = streak + 1 if x <= 0 else 0; mx = max(mx, streak)
    return dict(n=len(r), win=round((r > 0).mean(), 3), avg=round(r.mean(), 3), med=round(np.median(r), 3),
                total=round(eq[-1] - 1, 3), maxdd=round(dd, 3), lose_streak=mx,
                puts=int((t.kind == "PUT").sum()), calls=int((t.kind == "CALL").sum()))


if __name__ == "__main__":
    df = common.load("VXX")
    n = len(df); split = int(n * 0.7)
    print(f"rows {n}  IS {df.date.iloc[0].date()}..{df.date.iloc[split-1].date()}  OOS {df.date.iloc[split].date()}..{df.date.iloc[-1].date()}")
    rows = []
    for name, rng in [("IS", (0, split)), ("OOS", (split, n)), ("ALL", (0, n))]:
        t = run(df, *rng)
        rows.append({"set": name, "strategy": "VXX rules", **stats(t)})
        for k in ["PUT", "CALL"]:
            rows.append({"set": name, "strategy": f"  {k} only", **(stats(t[t.kind == k]) if len(t) else {})})
        rows.append({"set": name, "strategy": "VXX rules (fixed-vol, common.option_trade_return-style)", **stats(run(df, *rng, fixed_vol=True))})
        rows.append({"set": name, "strategy": "Baseline 13wk trend", **stats(baseline(df, *rng))})
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 200); pd.set_option("display.max_columns", 20)
    print(out.to_string(index=False))
    t = run(df, 0, n)
    print(t.to_string())
    globals()["IV_CAP"] = 9.9
    print("\nSensitivity - no IV cap:", "IS", stats(run(df, 0, split)), "OOS", stats(run(df, split, n)))
    if "--grid" in sys.argv:  # sensitivity, IN-SAMPLE ONLY
        for sp, tg, st, mh in itertools.product([0.10, 0.15, 0.20], [0.5, 0.8], [0.4, 0.5], [15, 25]):
            p = dict(spike=sp, target=tg, stop=st, max_hold=mh)
            print(p, stats(run(df, 0, split, p)), "| OOS", stats(run(df, split, n, p)))

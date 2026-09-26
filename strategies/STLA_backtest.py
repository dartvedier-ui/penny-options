"""Backtest for strategies/STLA.py.  Run: python3 strategies/STLA_backtest.py

Pricing: common.bs_price with vol = max(HV20, 0.15) x IV_MULT, re-marked daily at the then-current HV
(so vol expansion/crush on the underlying is partly captured). Entry at the signal-day close,
exit at the close of the exit day. Round-trip spread+fees `cost` is deducted from each trade's %
return. One position at a time. IS = first 70% of dates, OOS = last 30%.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import common
from strategies import STLA

COST = 0.12       # measured: Jan-27 5P 0.75/0.80, Nov-26 5P 0.65/0.70, Oct-30 4.5P 0.25/0.30 -> 7-18%
COST_STRESS = 0.20


def simulate(df, sig, dte, mny, target, max_hold, ivm=STLA.IV_MULT, cost=COST, stop=None,
             und_stop=None):
    c = df.close.values
    d = df.date.values
    hv = (np.log(df.close).diff().rolling(20).std() * np.sqrt(252)).values
    n = len(c)
    out = []
    i = 60
    while i < n - 1:
        k = sig[i]
        if k not in ("CALL", "PUT"):
            i += 1
            continue
        s0 = c[i]
        strike = s0 * (1 - mny) if k == "CALL" else s0 * (1 + mny)
        p0 = common.bs_price(s0, strike, dte, max(hv[i], 0.15) * ivm, k)
        for j in range(i + 1, n):
            days = int((d[j] - d[i]) / np.timedelta64(1, "D"))
            p = common.bs_price(c[j], strike, dte - days, max(hv[j], 0.15) * ivm, k)
            r = p / p0 - 1
            why = None
            if r >= target:
                why = "target"
            elif stop is not None and r <= -stop:
                why = "stop"
            elif und_stop is not None and und_stop(j, k):
                why = "und_stop"
            elif j - i >= max_hold:
                why = "time"
            elif j == n - 1:
                why = "open(last bar)"
            if why:
                out.append(dict(entry=pd.Timestamp(d[i]).date(), exit=pd.Timestamp(d[j]).date(), kind=k,
                                spot_in=round(s0, 2), spot_out=round(c[j], 2), held=j - i,
                                ret=r - cost, why=why))
                break
        i = j + 1
    return pd.DataFrame(out)


def md(t):
    cols = list(t.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in t.fillna("").values]
    return "\n".join(lines)


def stats(t, risk=0.05):
    if len(t) == 0:
        return dict(trades=0)
    r = t.ret.values
    eq = np.cumprod(1 + risk * np.maximum(r, -1))
    dd = (eq / np.maximum.accumulate(eq) - 1).min()
    ls = m = 0
    for x in r:
        m = m + 1 if x <= 0 else 0
        ls = max(ls, m)
    return dict(trades=len(r), win=f"{np.mean(r > 0):.0%}", avg=f"{r.mean():+.1%}",
                median=f"{np.median(r):+.1%}", comp5=f"{eq[-1] - 1:+.1%}", maxDD=f"{dd:.1%}", lose_streak=ls)


def split_stats(df, t, label):
    cut = df.date.iloc[int(len(df) * 0.7)].date()
    rows = []
    for name, sub in [("ALL", t), ("IS", t[t.entry < cut] if len(t) else t),
                      ("OOS", t[t.entry >= cut] if len(t) else t)]:
        rows.append(dict(strategy=label, sample=name, **stats(sub)))
    return rows, cut


def main():
    df = common.load("STLA")
    p = STLA.PARAMS
    f = STLA.features(df, p["win"])
    sig = np.array([STLA.raw_signal(f, i, p) for i in range(len(f))], dtype=object)
    c = df.close
    ret13 = (c / c.shift(65) - 1).fillna(0).values
    base = np.where(ret13 > 0, "CALL", np.where(ret13 < 0, "PUT", "NONE"))
    pc = dict(p, calls=True)
    sig_calls = np.array([STLA.raw_signal(f, i, pc) for i in range(len(f))], dtype=object)
    allput = np.array(["PUT"] * len(df), dtype=object)
    ma50 = f.ma50.values
    und = lambda j, k: (k == "PUT" and c.values[j] > ma50[j]) or (k == "CALL" and c.values[j] < ma50[j])

    runs = [
        ("STLA rule (120DTE 5%ITM put, +100%/60d)", simulate(df, sig, p["dte"], p["moneyness"], p["target"], p["max_hold"])),
        ("  same, cost 20% & IV 1.4xHV", simulate(df, sig, p["dte"], p["moneyness"], p["target"], p["max_hold"], ivm=1.4, cost=COST_STRESS)),
        ("  same, 90DTE / 40d hold", simulate(df, sig, 90, p["moneyness"], p["target"], 40)),
        ("  same, + exit if close > SMA50", simulate(df, sig, p["dte"], p["moneyness"], p["target"], p["max_hold"], und_stop=und)),
        ("  same, calls enabled (mirror)", simulate(df, sig_calls, p["dte"], p["moneyness"], p["target"], p["max_hold"])),
        ("Baseline: 13w-trend sign, 45DTE ATM, hold 20d", simulate(df, base, 45, 0.0, 99, 20)),
        ("Always-put, 45DTE ATM, hold 20d", simulate(df, allput, 45, 0.0, 99, 20)),
    ]
    rows = []
    for label, t in runs:
        r, cut = split_stats(df, t, label)
        rows += r
    table = pd.DataFrame(rows)
    print(f"Data {df.date.iloc[0].date()} -> {df.date.iloc[-1].date()} ({len(df)} bars); IS/OOS cut {cut}")
    print(md(table))
    print("\nTrade list (main rule):")
    t = runs[0][1].copy()
    t["ret"] = t.ret.map(lambda x: f"{x:+.1%}")
    print(md(t))
    return table, runs


if __name__ == "__main__":
    main()

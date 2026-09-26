"""TLT long-call / long-put backtest (final rules live in strategies/TLT.py).

Run:  python3 strategies/TLT_backtest.py

Pricing: Black-Scholes-Merton built on common.bs_price (TLT distribution yield q
handled via rate=r-q and an exp(-q t) scale; price data are NOT dividend-adjusted,
so ex-date drops are in the series). common.option_trade_return (no dividend) is
reported as a cross-check. IV = 20d realised vol x IV_MULT (floor 9%), constant
over the trade; round-trip cost SPREAD. Positions marked daily on closes.
"""
import os
import sys, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
import common
from strategies import TLT as S

R, Q = 0.04, 0.045
IV_MULT, IV_FLOOR = 1.15, 0.09
SPREAD = 0.04          # measured 1.3-2.9% bid/ask on 60-90 DTE ATM-ITM + commission/slippage
RISK = 0.05
SPLIT = "2025-03-01"   # IS 2022-07..2025-02 (~65-70% of tradable days), OOS 2025-03..2026-09


def bsm(spot, strike, days, vol, kind):
    t = max(days, 0) / 365
    if t <= 0:
        return common.bs_price(spot, strike, 0, vol, kind)
    return common.bs_price(spot, strike, days, vol, kind, rate=R - Q) * math.exp(-Q * t)


def features(df):
    d = S.features(df)
    c = d.close
    d["sma50"] = c.rolling(50).mean()
    d["ret65"] = c / c.shift(65) - 1
    d["lo20"] = d.low.rolling(20).min().shift(1)
    return d


# ---- rules: final + baselines + rejected alternatives ----
def r_final(d, i):
    return S.rule(d, i)

def r_final_calls(d, i):        # final rule with the call leg switched on
    S.ENABLE_CALLS = True
    try:
        return S.rule(d, i)
    finally:
        S.ENABLE_CALLS = False

def r_naive13w(d, i):           # baseline: follow sign of 13-wk return, always in market
    return "PUT" if d.ret65.iat[i] < 0 else "CALL"

def r_alwaysput(d, i):          # structural baseline: always hold a put
    return "PUT"

def r_trend_ma(d, i):           # rejected: close<SMA50<SMA200 & 13wk<0 -> PUT (mirror CALL)
    x = d.iloc[i]
    if x.close < x.sma50 < x.sma200 and x.ret65 < 0: return "PUT"
    if x.close > x.sma50 > x.sma200 and x.ret65 > 0: return "CALL"
    return None

def r_breakdown(d, i):          # rejected: fresh 20d low inside a down-stack
    x = d.iloc[i]
    return "PUT" if (x.sma50 < x.sma200 and x.close < x.lo20) else None

RULES = dict(final=r_final, final_with_calls=r_final_calls, naive13w=r_naive13w, alwaysput=r_alwaysput,
             trend_ma=r_trend_ma, breakdown=r_breakdown)


def backtest(df, rule="final", dte=S.DTE, mny=S.MONEYNESS, target=S.TARGET, stop=S.STOP,
             max_hold=S.MAX_HOLD, start=None, end=None, spread=SPREAD, iv_mult=IV_MULT,
             regime_exit=True):
    d = features(df)
    f = RULES[rule] if isinstance(rule, str) else rule
    n = len(d)
    lo = 200 if start is None else max(200, int(d.index[d.date >= start][0]))
    hi = n - 1 if end is None else int(d.index[d.date < end][-1])
    trades, i = [], lo
    while i < hi:
        kind = f(d, i)
        if kind is None:
            i += 1; continue
        s0 = d.close.iat[i]
        vol = max(d.hv20.iat[i] * iv_mult, IV_FLOOR)
        K = s0 * (1 - mny) if kind == "CALL" else s0 * (1 + mny)
        p0 = bsm(s0, K, dte, vol, kind)
        j, why = i, "maxhold"
        while True:
            j += 1
            cal = (d.date.iat[j] - d.date.iat[i]).days
            ret = bsm(d.close.iat[j], K, dte - cal, vol, kind) / p0 - 1
            if j >= hi: why = "end"; break
            if ret >= target: why = "target"; break
            if ret <= stop: why = "stop"; break
            if regime_exit and str(rule).startswith("final") and ((kind == "PUT" and d.slope26.iat[j] > 0) or
                                                    (kind == "CALL" and d.slope26.iat[j] < 0)):
                why = "regime"; break
            if j - i >= max_hold: break
        trades.append(dict(entry=d.date.iat[i].date(), exit=d.date.iat[j].date(), kind=kind,
                           s0=s0, s1=d.close.iat[j], K=round(K, 2), iv=round(vol, 3), days=j - i,
                           why=why, ret=ret - spread,
                           ret_common=common.option_trade_return(s0, d.close.iat[j], kind, dte, cal,
                                                                 vol, mny, spread)))
        i = j + 1
    return pd.DataFrame(trades)


def stats(t, risk=RISK):
    if t is None or len(t) == 0:
        return dict(n=0)
    r = t.ret.clip(lower=-1).values
    eq = np.cumprod(1 + risk * r)
    dd = (eq / np.maximum.accumulate(np.concatenate([[1.0], eq]))[1:] - 1).min()
    streak = mx = 0
    for v in r:
        streak = streak + 1 if v <= 0 else 0; mx = max(mx, streak)
    return dict(n=len(t), puts=int((t.kind == "PUT").sum()), calls=int((t.kind == "CALL").sum()),
                win=round((r > 0).mean(), 3), avg=round(r.mean(), 3), med=round(float(np.median(r)), 3),
                comp5=round(eq[-1] - 1, 3), maxdd=round(min(dd, 0), 3), lose_streak=mx,
                avg_days=round(t.days.mean(), 1))


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    df = common.load("TLT")
    print("data", df.date.iat[0].date(), "->", df.date.iat[-1].date(), len(df),
          "daily rows; trading starts after 200-day warm-up; split", SPLIT)
    out = []
    for name in RULES:
        for per, a, b in [("IS", None, SPLIT), ("OOS", SPLIT, None), ("ALL", None, None)]:
            out.append(dict(strategy=name, period=per, **stats(backtest(df, name, start=a, end=b))))
    print("\nAll rules with the SAME option config (90 DTE, 5% ITM, +100%/-40%, 40d max):")
    print(pd.DataFrame(out).to_string(index=False))

    t = backtest(df, "final")
    print("\nFinal-rule trades:\n", t.round(3).to_string(index=False))
    print("\nexit reasons:", t.why.value_counts().to_dict())
    print("cross-check common.option_trade_return (no dividend): avg",
          round(t.ret_common.mean(), 3), "vs BSM w/ dividend", round(t.ret.mean(), 3))

    print("\nSensitivity of final rule (ALL / OOS avg per trade):")
    rows = []
    for dte in (60, 90, 120):
        for mny in (0.0, 0.03, 0.05, 0.08):
            for tgt, stp in ((0.5, -0.4), (1.0, -0.4), (1.0, -0.6)):
                a = stats(backtest(df, "final", dte, mny, tgt, stp))
                b = stats(backtest(df, "final", dte, mny, tgt, stp, start=SPLIT))
                rows.append(dict(dte=dte, mny=mny, tgt=tgt, stop=stp, n=a["n"], all_avg=a["avg"],
                                 all_win=a["win"], all_comp5=a["comp5"], oos_n=b["n"], oos_avg=b["avg"]))
    sens = pd.DataFrame(rows)
    print(sens.to_string(index=False))
    print("share of configs with ALL avg > 0:", round((sens.all_avg > 0).mean(), 2))
    for m in (1.0, 1.15, 1.3):
        for sp in (0.03, 0.06):
            s = stats(backtest(df, "final", iv_mult=m, spread=sp))
            print(f"iv_mult={m} spread={sp}: n={s['n']} win={s['win']} avg={s['avg']} comp5={s['comp5']}")

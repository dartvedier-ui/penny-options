"""Re-test every option-tradeable strategy with SHORT-dated options (15-25 DTE).

Entry signals come from each ticker's own strategy module (unchanged).  Only the
option structure changes: DTE in {15, 21, 25}, moneyness, target/stop, and a max
hold that exits >= 5 calendar days before expiry.  Parameters are picked on the
in-sample 70% only; the out-of-sample 30% is reported untouched.
Short-dated options have wider spreads relative to premium, so costs are higher
than in the original long-DTE tests.
Run: python3 short_dte_backtest.py
"""
import os
import sys, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import common
from strategies import VXX, TLT, OPEN, STLA, IOVA, NKE, NIO

RISK = 0.05
DTES = (15, 21, 25)
MNY = (0.0, 0.03, 0.05)
TGT = (0.5, 1.0)
STP = (0.5, 1.0)          # 1.0 = no stop (premium is the risk)

# (spread as fraction of premium for ~3-week options, IV/HV multiplier, IV floor)
COST = dict(VXX=(0.15, 1.3, 0.55), TLT=(0.06, 1.15, 0.09), OPEN=(0.20, 1.15, 0.50),
            STLA=(0.20, 1.25, 0.20), IOVA=(0.25, 1.2, 0.50), NKE=(0.07, 1.2, 0.15),
            NIO=(0.15, 1.25, 0.35))


def signals(t, df):
    """Daily array of 'PUT'/'CALL'/None from the ticker's own entry rule (+ extra block mask)."""
    n = len(df)
    sig = np.array([None] * n, dtype=object)
    block = np.zeros(n, dtype=bool)          # days where an open trade must be closed (NKE earnings)
    if t == "VXX":
        f = VXX.features(df)
        for i in range(n):
            a = VXX.raw_signal(f, i, VXX.PARAMS); sig[i] = None if a == "NONE" else a
    elif t == "TLT":
        d = TLT.features(df)
        for i in range(n):
            sig[i] = TLT.rule(d, i)
    elif t == "STLA":
        f = STLA.features(df, STLA.PARAMS["win"])
        for i in range(n):
            a = STLA.raw_signal(f, i, STLA.PARAMS); sig[i] = None if a == "NONE" else a
    elif t == "IOVA":
        d = IOVA.indicators(df)
        for i in range(n):
            sig[i] = IOVA.raw_signal(d.iloc[i])[0]
    elif t == "NIO":
        f = NIO.features(df)
        sig[f.put.values] = "PUT"; sig[f.call.values] = "CALL"
    elif t == "NKE":
        d = NKE.features(df, NKE.P)
        for i in range(n):
            if d.days_to_earn.iat[i] >= 3:     # short options: only need expiry/exit before the report
                sig[i] = NKE.raw_signal(d.iloc[i], NKE.P)
        block = (d.days_to_earn.values <= 1)   # exit by the close before the reaction day
    elif t == "OPEN":
        # weekly rule, applied on each Friday close of the daily series
        w = OPEN.weekly_features(OPEN.to_weekly(df))
        wk = {r["date"].normalize(): OPEN.decide(r)[0] for _, r in w.iterrows()}
        for i, dt in enumerate(df.date):
            a = wk.get(dt.normalize())
            sig[i] = None if a in (None, "NONE") else a
    return sig, block


def simulate(df, sig, block, dte, mny, tgt, stp, spread, ivm, floor, start, end):
    c = df.close.values; d = df.date.values
    hv = (np.log(df.close).diff().rolling(20).std() * np.sqrt(252)).values
    out, i = [], max(start, 60)
    while i < end - 1:
        k = sig[i]
        if k is None or np.isnan(hv[i]):
            i += 1; continue
        vol = max(hv[i] * ivm, floor)
        K = c[i] * (1 - mny) if k == "CALL" else c[i] * (1 + mny)
        p0 = common.bs_price(c[i], K, dte, vol, k)
        j = i; why = "time"
        while j < len(c) - 1:
            j += 1
            cal = int((d[j] - d[i]) / np.timedelta64(1, "D"))
            r = common.bs_price(c[j], K, dte - cal, vol, k) / p0 - 1
            if r >= tgt: why = "target"; break
            if r <= -stp: why = "stop"; break
            if block[j] or cal >= dte - 5: break
        out.append(dict(entry=pd.Timestamp(d[i]).date(), kind=k, days=j - i, why=why, ret=max(r - spread, -1.0)))
        i = j + 1
    return pd.DataFrame(out)


def stats(t):
    if len(t) == 0:
        return dict(n=0, win=np.nan, avg=np.nan, med=np.nan, comp=0.0, dd=0.0)
    eq = np.cumprod(1 + RISK * t.ret.values)
    dd = (eq / np.maximum.accumulate(np.r_[1, eq])[1:] - 1).min()
    return dict(n=len(t), win=round((t.ret > 0).mean(), 2), avg=round(t.ret.mean(), 3),
                med=round(t.ret.median(), 3), comp=round(eq[-1] - 1, 3), dd=round(min(dd, 0), 3))


def main():
    rows, best = [], {}
    for t in COST:
        df = common.load(t)
        sig, block = signals(t, df)
        sp, ivm, fl = COST[t]
        cut = int(len(df) * 0.7)
        grid = []
        for dte, m, tg, st in itertools.product(DTES, MNY, TGT, STP):
            a = stats(simulate(df, sig, block, dte, m, tg, st, sp, ivm, fl, 0, cut))
            b = stats(simulate(df, sig, block, dte, m, tg, st, sp, ivm, fl, cut, len(df)))
            grid.append(dict(t=t, dte=dte, mny=m, tgt=tg, stop=st, **{f"is_{k}": v for k, v in a.items()},
                             **{f"oos_{k}": v for k, v in b.items()}))
        g = pd.DataFrame(grid)
        g = g[g.is_n >= 3]
        pick = g.sort_values("is_comp", ascending=False).iloc[0]
        best[t] = pick
        by_dte = g.groupby("dte")[["is_avg", "oos_avg"]].median().round(3).to_dict("index")
        rows.append(dict(t=t, **{k: pick[k] for k in ("dte", "mny", "tgt", "stop", "is_n", "is_win", "is_avg",
                                                      "is_comp", "oos_n", "oos_win", "oos_avg", "oos_comp", "oos_dd")},
                         share_oos_pos=round((g.oos_avg > 0).mean(), 2), median_by_dte=by_dte))
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
    print(pd.DataFrame(rows).to_string(index=False))
    return best


if __name__ == "__main__":
    main()

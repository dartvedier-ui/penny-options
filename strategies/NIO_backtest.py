"""Reproducible backtest for strategies/NIO.py.

Run: python3 strategies/NIO_backtest.py
- Daily data (data/NIO_daily.csv, IBKR, ~2y) : main test, IS = first 70% of bars, OOS = last 30%.
- Weekly data (data/NIO_weekly.csv, 5y): robustness check of the same logic on weekly bars
  (SMA4/SMA10 weeks, re-cross of SMA4, max hold 5 weeks).
Option pricing: common.option_trade_return / bs_price, vol = HV20 * IV_HV_MULT (held constant
over the trade), spread cost applied once round-trip. Exits checked on closes.
"""
import os
import sys, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
import common
from strategies import NIO as S

RISK = 0.05  # fraction of account paid as premium per trade (= max loss)


def entries_daily(f, mode):
    down = (f.sma_f < f.sma_s) & (f.slope < 0)
    up = (f.sma_f > f.sma_s) & (f.slope > 0)
    if mode == "breakout":
        return f.put.values, f.call.values
    if mode == "state":
        return down.values, up.values
    if mode == "pullback":  # in trend, close crosses back through SMA20 after a bounce
        c, s = f.close, f.sma_f
        p = down & (c < s) & (c.shift() >= s.shift())
        q = up & (c > s) & (c.shift() <= s.shift())
        return p.values, q.values
    raise ValueError(mode)


def simulate(df, f, puts, calls, dte, mny, tgt, stp, hold, spread, mult=S.IV_HV_MULT,
             start=0, end=None, allow=("PUT", "CALL")):
    end = len(df) if end is None else end
    c = df.close.values; dates = df.date.values
    trades = []; i = max(start, S.SLOW + S.SLOPE_LB)
    while i < end - 1:
        kind = "PUT" if puts[i] else ("CALL" if calls[i] else None)
        if kind is None or kind not in allow or np.isnan(f.hv20.iloc[i]):
            i += 1; continue
        vol = float(np.clip(f.hv20.iloc[i] * mult, 0.35, 1.3))
        s0 = c[i]; k = s0 * (1 - mny) if kind == "CALL" else s0 * (1 + mny)
        p0 = common.bs_price(s0, k, dte, vol, kind)
        j = i; why = "time"
        for j in range(i + 1, min(i + hold, end - 1) + 1):
            cal = int((dates[j] - dates[i]) / np.timedelta64(1, "D"))
            v = common.bs_price(c[j], k, dte - cal, vol, kind)
            if v >= p0 * (1 + tgt): why = "target"; break
            if v <= p0 * (1 - stp): why = "stop"; break
        cal = int((dates[j] - dates[i]) / np.timedelta64(1, "D"))
        ret = common.option_trade_return(s0, c[j], kind, dte, cal, vol, mny, spread)
        trades.append(dict(entry=pd.Timestamp(dates[i]).date(), exit=pd.Timestamp(dates[j]).date(),
                           kind=kind, s0=s0, s1=c[j], days=j - i, why=why, ret=ret))
        i = j + 1
    return pd.DataFrame(trades)


def stats(t):
    if len(t) == 0:
        return dict(n=0, win=np.nan, avg=np.nan, med=np.nan, total=0.0, maxdd=0.0, streak=0)
    eq = np.cumprod(1 + RISK * t.ret.values); peak = np.maximum.accumulate(np.r_[1, eq])[1:]
    dd = (eq / peak - 1).min()
    streak = m = 0
    for r in t.ret:
        m = m + 1 if r <= 0 else 0; streak = max(streak, m)
    return dict(n=len(t), win=round((t.ret > 0).mean(), 2), avg=round(t.ret.mean(), 3),
                med=round(t.ret.median(), 3), total=round(eq[-1] - 1, 3), maxdd=round(min(dd, 0), 3),
                streak=streak)


def baseline(df, dte, mny, spread, hold=20, start=0, end=None, step=None):
    """Naive: every `hold` bars buy an option in the direction of the 13-week (65-bar)
    log-linear slope; hold to `hold` bars; no target/stop."""
    end = len(df) if end is None else end
    lc = np.log(df.close.values); c = df.close.values; d = df.date.values
    r = np.log(df.close).diff(); hv = (r.rolling(20).std() * np.sqrt(252)).values
    out = []; i = max(start, 65)
    while i + 1 < end:
        sl = np.polyfit(np.arange(65), lc[i - 64:i + 1], 1)[0]
        kind = "CALL" if sl > 0 else "PUT"; j = min(i + hold, end - 1)
        vol = float(np.clip(hv[i] * S.IV_HV_MULT, 0.35, 1.3))
        cal = int((d[j] - d[i]) / np.timedelta64(1, "D"))
        out.append(dict(entry=pd.Timestamp(d[i]).date(), kind=kind,
                        ret=common.option_trade_return(c[i], c[j], kind, dte, cal, vol, mny, spread)))
        i = j + (step or 1) - 1 if step else j + 1
    return pd.DataFrame(out)


def main():
    df = common.load("NIO"); f = S.features(df)
    n = len(df); cut = int(n * 0.7)
    print(f"Daily bars {n}: {df.date.iloc[0].date()} .. {df.date.iloc[-1].date()}; "
          f"IS < {df.date.iloc[cut].date()} <= OOS")

    # ---- 1. small parameter grid, chosen on IS only ----
    rows = []
    for mode, tgt, stp, hold, mny in itertools.product(
            ["breakout", "state", "pullback"], [0.6, 1.0], [0.4, 0.6], [15, 25], [0.0, 0.05]):
        p, q = entries_daily(f, mode)
        a = stats(simulate(df, f, p, q, S.DTE, mny, tgt, stp, hold, S.SPREAD_COST, end=cut))
        b = stats(simulate(df, f, p, q, S.DTE, mny, tgt, stp, hold, S.SPREAD_COST, start=cut))
        rows.append(dict(mode=mode, tgt=tgt, stp=stp, hold=hold, mny=mny,
                         IS_n=a["n"], IS_avg=a["avg"], IS_tot=a["total"],
                         OOS_n=b["n"], OOS_avg=b["avg"], OOS_tot=b["total"]))
    g = pd.DataFrame(rows).sort_values("IS_tot", ascending=False)
    pd.set_option("display.width", 200)
    print("\nGrid (sorted by IS total return, 5% risk/trade):\n", g.head(12).to_string(index=False))
    print("\nGrid medians by entry mode (OOS avg / OOS total):")
    print(g.groupby("mode")[["IS_avg", "IS_tot", "OOS_avg", "OOS_tot"]].median().round(3))

    # ---- 2. chosen configuration (as in strategies/NIO.py) ----
    p, q = f.put.values, f.call.values
    cfg = dict(dte=S.DTE, mny=S.MONEYNESS, tgt=S.TARGET_PCT, stp=S.STOP_PCT, hold=S.MAX_HOLD,
               spread=S.SPREAD_COST)
    print("\nChosen config:", cfg)
    res = {}
    for name, a, b in [("IS", 0, cut), ("OOS", cut, n), ("ALL", 0, n)]:
        t = simulate(df, f, p, q, start=a, end=b, **cfg); res[name] = t
        bl = baseline(df, S.DTE, S.MONEYNESS, S.SPREAD_COST, start=a, end=b)
        print(f"{name:4s} strategy {stats(t)}")
        print(f"{name:4s} baseline {stats(bl)}")
    print("\nAll trades:\n", res["ALL"].round(3).to_string(index=False))
    for name in ["IS", "OOS"]:
        t = res[name]
        if len(t):
            print(name, "by side:", t.groupby("kind").ret.agg(["count", "mean", "median"]).round(3).to_dict("index"))

    # ---- 3. sensitivity: spread cost and IV multiplier ----
    print("\nSensitivity (ALL period):")
    for sp in [0.08, 0.12, 0.20]:
        for mult in [1.0, 1.25, 1.5]:
            t = simulate(df, f, p, q, S.DTE, S.MONEYNESS, S.TARGET_PCT, S.STOP_PCT, S.MAX_HOLD, sp, mult)
            print(f" spread {sp:.2f} ivmult {mult:.2f}: {stats(t)}")
    print(" PUT-only:", stats(simulate(df, f, p, q, allow=("PUT",), **cfg)))

    # ---- 4. weekly 5-year robustness (same logic, weekly bars) ----
    w = common.load("NIO", "weekly"); c = w.close
    fw = pd.DataFrame({"close": c, "sma_f": c.rolling(4).mean(), "sma_s": c.rolling(10).mean()})
    fw["slope"] = fw.sma_s / fw.sma_s.shift(2) - 1
    fw["hv20"] = np.log(c).diff().rolling(10).std() * np.sqrt(52)
    dn = (fw.sma_f < fw.sma_s) & (fw.slope < 0); up = (fw.sma_f > fw.sma_s) & (fw.slope > 0)
    s4 = fw.sma_f
    pw = (dn & (c < s4) & (c.shift() >= s4.shift())).values
    qw = (up & (c > s4) & (c.shift() <= s4.shift())).values
    old = S.SLOW, S.SLOPE_LB; S.SLOW, S.SLOPE_LB = 10, 2
    tw = simulate(w, fw, pw, qw, S.DTE, S.MONEYNESS, S.TARGET_PCT, S.STOP_PCT, 5, S.SPREAD_COST)
    S.SLOW, S.SLOPE_LB = old
    print("\nWeekly 5y robustness:", stats(tw))
    if len(tw):
        tw["year"] = pd.to_datetime(tw.entry).dt.year
        print(tw.groupby("year").ret.agg(["count", "mean", lambda x: (x > 0).mean()]).round(3))
        print(" by side:", tw.groupby("kind").ret.agg(["count", "mean", "median"]).round(3).to_dict("index"))
    blw = baseline(w, S.DTE, S.MONEYNESS, S.SPREAD_COST, hold=4)
    print("Weekly 5y baseline (13-wk slope, 4-wk hold):", stats(blw))


if __name__ == "__main__":
    main()

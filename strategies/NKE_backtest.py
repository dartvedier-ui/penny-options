"""Study + backtest for the NKE long call / long put strategy.

Run:  python3 strategies/NKE_backtest.py
"""
import os
import sys, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import common
from strategies import NKE

P = dict(NKE.P)
SPLIT = 0.70
RISK = 0.05


# ---------------------------------------------------------------- study
def study(d):
    out = []
    r = np.log(d.close).diff()
    out.append(f"Daily bars: {len(d)} ({d.date.iloc[0].date()} .. {d.date.iloc[-1].date()})")
    out.append(f"Ann. vol (all): {r.std()*math.sqrt(252):.1%}; median HV20: {d.hv20.median():.1%}; "
               f"HV20 now: {d.hv20.iloc[-1]:.1%}")
    # earnings gaps
    rows = []
    for e in NKE.EARN:
        if e not in set(d.date):
            continue
        i = d.index[d.date == e][0]
        pre = d.close.iloc[i - 1]
        gap = d.open.iloc[i] / pre - 1
        day = d.close.iloc[i] / pre - 1
        tr = d.slope_wk.iloc[i - 1]
        after10 = d.close.iloc[min(i + 10, len(d) - 1)] / d.close.iloc[i] - 1
        rows.append(dict(date=e.date(), pre_trend_wk=tr, gap=gap, day=day, next10=after10,
                         with_trend=np.sign(day) == np.sign(tr)))
    er = pd.DataFrame(rows)
    return out, er


# ---------------------------------------------------------------- engine
def run(d, p, mode="strategy", hold_through=False):
    trades = []
    i = P["reg_len"] + 5
    n = len(d)
    while i < n - 1:
        row = d.iloc[i]
        if mode == "strategy":
            s = NKE.raw_signal(row, p)
            if s is None or (not hold_through and row.days_to_earn < p["earn_blackout"]):
                i += 1
                continue
        else:  # baseline: follow the 13-week trend, re-enter every max_hold days
            if pd.isna(row.slope_wk):
                i += 1
                continue
            s = "CALL" if row.slope_wk > 0 else "PUT"
        spot0 = row.close
        vol = max(row.hv20, 0.15) * p["iv_mult"]
        k = spot0 * (1 - p["moneyness"]) if s == "CALL" else spot0 * (1 + p["moneyness"])
        crosses = False
        ev = 0.08  # 1-sd earnings move priced in (from Oct-2 straddle, ~8%)
        # entry vol: add event variance if the expiry spans earnings
        def ivol(day_idx, spot_day_to_exp):
            return vol
        dte0 = p["dte"]
        de = int(row.days_to_earn)
        entry_vol = vol
        if hold_through and de * 1.4 < dte0:
            t = dte0 / 365
            entry_vol = math.sqrt(vol ** 2 + ev ** 2 / t)
        buy = common.bs_price(spot0, k, dte0, entry_vol, s)
        j_exit, why = None, "time"
        for h in range(1, p["max_hold"] + 1):
            j = i + h
            if j >= n:
                j_exit, why = n - 1, "eod"
                break
            cal = (d.date.iloc[j] - d.date.iloc[i]).days
            if (not hold_through and mode == "strategy"
                    and d.days_to_earn.iloc[j] == 0):  # reaction day -> exit day before
                j_exit, why = j - 1, "pre-earn"
                break
            v = entry_vol
            if hold_through and de * 1.4 < dte0:
                after = d.days_to_earn.iloc[j] > de  # event passed
                v = vol if after else math.sqrt(vol ** 2 + ev ** 2 / max((dte0 - cal) / 365, 1e-3))
            val = common.bs_price(d.close.iloc[j], k, dte0 - cal, v, s)
            rr = val / buy - 1
            if mode == "strategy" and rr >= p["target"]:
                j_exit, why = j, "target"
                break
            if mode == "strategy" and rr <= p["stop"]:
                j_exit, why = j, "stop"
                break
            j_exit = j
        cal = (d.date.iloc[j_exit] - d.date.iloc[i]).days
        if hold_through:
            after = d.days_to_earn.iloc[j_exit] > de
            v = vol if (after or not de * 1.4 < dte0) else math.sqrt(vol ** 2 + ev ** 2 / max((dte0 - cal) / 365, 1e-3))
            sell = common.bs_price(d.close.iloc[j_exit], k, dte0 - cal, v, s)
            ret = sell / buy - 1 - p["spread_cost"]
        else:
            ret = common.option_trade_return(spot0, d.close.iloc[j_exit], s, dte0, cal, vol,
                                             moneyness=p["moneyness"], spread_cost=p["spread_cost"])
        ret = max(ret, -1.0)
        trades.append(dict(entry=d.date.iloc[i], exit=d.date.iloc[j_exit], kind=s, spot0=spot0,
                           spot1=d.close.iloc[j_exit], days=j_exit - i, why=why, ret=ret,
                           stock=(d.close.iloc[j_exit] / spot0 - 1)))
        i = j_exit + 1
    return pd.DataFrame(trades)


def metrics(t, label):
    if len(t) == 0:
        return dict(set=label, trades=0)
    eq = np.cumprod(1 + RISK * t.ret.values)
    peak = np.maximum.accumulate(np.concatenate([[1], eq]))[1:]
    dd = (eq / peak - 1).min()
    streak = m = 0
    for x in t.ret:
        streak = streak + 1 if x <= 0 else 0
        m = max(m, streak)
    return dict(set=label, trades=len(t), win=f"{(t.ret > 0).mean():.0%}",
                avg=f"{t.ret.mean():+.1%}", med=f"{t.ret.median():+.1%}",
                comp5=f"{eq[-1]-1:+.1%}", maxDD=f"{dd:.1%}", lose_streak=m,
                calls=int((t.kind == "CALL").sum()), puts=int((t.kind == "PUT").sum()))


def split(t, cut):
    return t[t.entry < cut], t[t.entry >= cut]


def main(verbose=True):
    df = common.load("NKE")
    d = NKE.features(df, P)
    cut = d.date.iloc[int(len(d) * SPLIT)]
    lines, er = study(d)
    res = {}
    variants = {
        "STRATEGY (no earnings hold)": dict(mode="strategy"),
        "same rules, HOLD through earnings": dict(mode="strategy", hold_through=True),
        "BASELINE follow 13w trend": dict(mode="baseline"),
    }
    table = []
    for name, kw in variants.items():
        t = run(d, P, **kw)
        res[name] = t
        a, b = split(t, cut)
        for lab, x in (("ALL", t), ("IS", a), ("OOS", b)):
            m = metrics(x, lab)
            m["variant"] = name
            table.append(m)
    tab = pd.DataFrame(table)[["variant", "set", "trades", "win", "avg", "med", "comp5",
                               "maxDD", "lose_streak", "calls", "puts"]]
    # sensitivity (strategy, OOS & ALL avg)
    sens = []
    for key, vals in (("moneyness", [0.0, 0.03, 0.06]), ("iv_mult", [1.0, 1.2, 1.4]),
                      ("min_r2", [0.0, 0.4, 0.6]), ("put_hi", [0.0, 0.03, 0.05]), ("put_lo", [-0.06, -0.04, -0.02]),
                      ("call_stretch", [-0.15, -0.12, -0.10]), ("target", [0.4, 0.6, 1.0]), ("stop", [-0.3, -0.4, -0.6]), ("max_hold", [10, 15, 20]), ("dte", [30, 45, 60]),
                      ("spread_cost", [0.03, 0.05, 0.10])):
        for v in vals:
            q = dict(P); q[key] = v
            t = run(d, q, mode="strategy")
            a, b = split(t, cut)
            sens.append(dict(param=key, value=v, n=len(t), avg_all=f"{t.ret.mean():+.1%}",
                             win_all=f"{(t.ret>0).mean():.0%}",
                             n_oos=len(b), avg_oos=f"{b.ret.mean():+.1%}" if len(b) else "-"))
    sens = pd.DataFrame(sens)
    if verbose:
        print("\n".join(lines))
        print(f"IS/OOS cut: {cut.date()}")
        print("\nEarnings reactions:\n", er.round(3).to_string(index=False))
        print(f"mean |day| {er.day.abs().mean():.1%}, median |day| {er.day.abs().median():.1%}, "
              f"with prior trend {er.with_trend.mean():.0%}, down {np.mean(er.day<0):.0%}")
        print("\n", tab.to_string(index=False))
        print("\nSensitivity:\n", sens.to_string(index=False))
        t = res["STRATEGY (no earnings hold)"]
        print("\nStrategy trades:\n", t.assign(ret=t.ret.round(3), stock=t.stock.round(3)).to_string(index=False))
    return d, er, tab, sens, res, cut


if __name__ == "__main__":
    main()

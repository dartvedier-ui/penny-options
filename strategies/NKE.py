"""NKE (Nike Inc Class B) long call / long put strategy.

Style: fade-the-stretch between earnings (short into SMA50 resistance in a downtrend,
buy calls when >12% below SMA50) with a hard earnings blackout.

Rules (evaluated on each daily close):
  Trend    : 63-day (13-week) log-price regression slope (per week) and R^2.
  PUT      : slope < -0.25%/wk, R^2 >= 0.40 and close within -4%..+3% of SMA50
             (a rally back into the 50-day in a downtrend -> fade it).
  CALL     : close >= 12% below SMA50 (stretched; NKE snaps back between reports).
  Earnings : no new position if the next earnings report is < EARN_BLACKOUT
             trading days away; any open position is sold on the close
             BEFORE the report (never hold through earnings).
  Option   : ~45 DTE, strike ~3% in the money, one position at a time.
  Exit     : option +100% (target) / -30% (stop) / 15 trading days / pre-earnings.
"""
import math
import numpy as np
import pandas as pd

# Earnings REACTION days (first session after Nike's after-close report).
EARNINGS_REACTION_DAYS = [
    "2021-12-21", "2022-03-22", "2022-06-28", "2022-09-30", "2022-12-21",
    "2023-03-22", "2023-06-30", "2023-09-29", "2023-12-22", "2024-03-22",
    "2024-06-28", "2024-10-02", "2024-12-20", "2025-03-21", "2025-06-27",
    "2025-10-01", "2025-12-19", "2026-04-01", "2026-07-01",
    # confirmed: FQ1 FY27 report Thu 2026-10-01 after close -> reaction 10-02
    "2026-10-02",
    # projected (Nike's usual cadence; confirm when announced)
    "2026-12-18", "2027-03-19", "2027-06-25", "2027-10-01",
]
EARN = pd.to_datetime(EARNINGS_REACTION_DAYS)

P = dict(
    reg_len=63, min_r2=0.40, min_slope_wk=0.0025, sma_long=50, sma_fast=10,
    put_lo=-0.04, put_hi=0.03, call_stretch=-0.12,
    dte=45, moneyness=0.03, target=1.00, stop=-0.30, max_hold=15,
    earn_blackout=12,  # trading days
    iv_mult=1.20, spread_cost=0.05,
)


def _regress(logp):
    n = len(logp)
    x = np.arange(n, dtype=float)
    xm, ym = x.mean(), logp.mean()
    sxx = ((x - xm) ** 2).sum()
    b = ((x - xm) * (logp - ym)).sum() / sxx
    resid = logp - (ym + b * (x - xm))
    sst = ((logp - ym) ** 2).sum()
    r2 = 1 - (resid ** 2).sum() / sst if sst > 0 else 0.0
    return b, r2


def features(df, p=P):
    d = df.copy().reset_index(drop=True)
    d["date"] = pd.to_datetime(d["date"])
    lp = np.log(d["close"].values)
    n = p["reg_len"]
    slope = np.full(len(d), np.nan)
    r2 = np.full(len(d), np.nan)
    for i in range(n - 1, len(d)):
        b, r = _regress(lp[i - n + 1:i + 1])
        slope[i], r2[i] = b * 5, r  # per week
    d["slope_wk"], d["r2"] = slope, r2
    d["sma_long"] = d["close"].rolling(p["sma_long"]).mean()
    d["sma_fast"] = d["close"].rolling(p["sma_fast"]).mean()
    d["hv20"] = np.log(d["close"]).diff().rolling(20).std() * math.sqrt(252)
    # trading days (approx, business days) until next earnings reaction day
    bd = []
    for dt in d["date"]:
        nxt = EARN[EARN > dt]
        bd.append(np.busday_count(dt.date(), nxt[0].date()) if len(nxt) else 999)
    d["days_to_earn"] = bd
    return d


def raw_signal(row, p=P):
    """Return 'CALL'/'PUT'/None for one feature row (no earnings filter)."""
    if any(pd.isna(row[c]) for c in ("slope_wk", "r2", "sma_long", "sma_fast")):
        return None
    dist = row["close"] / row["sma_long"] - 1
    # PUT: downtrend + price has rallied back into the SMA50 zone (resistance)
    if (row["slope_wk"] < -p["min_slope_wk"] and row["r2"] >= p["min_r2"]
            and p["put_lo"] <= dist <= p["put_hi"]):
        return "PUT"
    # CALL: price stretched far below SMA50 -> between-earnings snap-back
    if dist <= p["call_stretch"]:
        return "CALL"
    return None


def signal(df):
    p = P
    d = features(df, p)
    row = d.iloc[-1]
    c = float(row["close"])
    base = dict(action="NONE", strength=0.0, entry=c, stop=c, target=c, dte=p["dte"], reason="")
    trend = ("DOWN" if row["slope_wk"] < -p["min_slope_wk"] else
             "UP" if row["slope_wk"] > p["min_slope_wk"] else "FLAT")
    ctx = (f"13w slope {row['slope_wk']*100:+.2f}%/wk R2 {row['r2']:.2f}, close {c:.2f} "
           f"vs SMA10 {row['sma_fast']:.2f} / SMA50 {row['sma_long']:.2f}, "
           f"next earnings reaction in {int(row['days_to_earn'])} trading days")
    if row["days_to_earn"] < p["earn_blackout"]:
        base["reason"] = (f"STAND ASIDE: earnings blackout (trend {trend}). "
                          "Re-evaluate after the report; " + ctx)
        return base
    s = raw_signal(row, p)
    if s is None:
        base["reason"] = f"No setup (trend {trend}, waiting for regime + pullback). " + ctx
        return base
    hv = float(row["hv20"])
    move = c * hv * math.sqrt(p["max_hold"] / 252)  # ~1 sd move over the hold
    strength = float(min(1.0, max(0.0, (row["r2"] - p["min_r2"]) / (1 - p["min_r2"]) * 0.5
                                  + min(abs(row["slope_wk"]) / 0.02, 1) * 0.5)))
    if s == "PUT":
        return dict(action="PUT", strength=round(strength, 2), entry=c,
                    stop=round(float(row["sma_long"]), 2), target=round(c - move, 2),
                    dte=p["dte"], reason=f"Downtrend rally into the SMA50 zone (fade it): buy ~{p['dte']}DTE put, "
                    f"strike ~{c*(1+p['moneyness']):.1f}; " + ctx)
    return dict(action="CALL", strength=round(strength, 2), entry=c,
                stop=round(float(row["sma_long"]), 2), target=round(c + move, 2),
                dte=p["dte"], reason=f"Stretched >=12% below SMA50 (between-earnings snap-back): buy ~{p['dte']}DTE call, "
                f"strike ~{c*(1-p['moneyness']):.1f}; " + ctx)

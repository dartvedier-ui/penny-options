"""STLA (Stellantis) long-option strategy: 26-week down-trend PUT, bought on a bounce. No calls.

Why this shape (see reports/STLA.md):
  * STLA has a persistent negative drift (-1.5%/month on average over 2021-2026, -85% from the
    2024 high) but strong SHORT-term mean reversion (20-day momentum has negative autocorrelation).
    Short-dated trend-following puts bought after a drop get chopped up by bounces.
  * The 26-week (130-day) log-trend is the horizon where persistence shows up:
    when R^2 > 0.6 and slope < 0, the next 60 days averaged -9% (72% down).
  * Up-trends did NOT persist (R^2 > 0.6 up-trend: next 60d +1.3%, 49% up) -> calls disabled.

Rules (daily closes):
  PUT  : 130-day log-regression R^2 >= 0.60 and slope < 0, close < 50d SMA,
         and close >= 0.98 x 20d SMA (wait for a bounce - don't buy after a flush).
  CALL : disabled (no edge found).
  Option: ~120 DTE (next monthly 100-130 DTE), ~5% ITM put (strike ~ 1.05 x spot, nearest listed).
  Exit : +100% option gain, or 60 trading days, whichever first. No option stop (tight stops were
         the main loss driver in testing); position size = the risk (5% of account).
  Thesis-invalid level reported as `stop`: close above the 130-day regression line + 1 sd
         (informational; not used in the backtest).
"""
import math
import numpy as np
import pandas as pd

PARAMS = dict(r2_min=0.60, win=130, bounce=0.98, dte=120, moneyness=0.05, target=1.0,
              max_hold=60, calls=False)
IV_MULT = 1.25  # measured: option mid IV ~53% vs 30d HV ~42% on 2026-09-24


def _reg(y):
    x = np.arange(len(y), dtype=float)
    b, a = np.polyfit(x, y, 1)
    yh = a + b * x
    ss = ((y - y.mean()) ** 2).sum()
    r2 = 1 - ((y - yh) ** 2).sum() / ss if ss > 0 else 0.0
    return b, a + b * x[-1], r2, (y - yh).std()


def features(df, win=130):
    c = df.close.astype(float).reset_index(drop=True)
    lc = np.log(c).values
    n = len(c)
    sl, r2, fit, sd = (np.full(n, np.nan) for _ in range(4))
    for i in range(win - 1, n):
        sl[i], fit[i], r2[i], sd[i] = _reg(lc[i - win + 1:i + 1])
    f = pd.DataFrame({"close": c, "slope": sl, "r2": r2, "fit": fit, "sd": sd})
    f["ma20"] = c.rolling(20).mean()
    f["ma50"] = c.rolling(50).mean()
    f["hv20"] = np.log(c).diff().rolling(20).std() * np.sqrt(252)
    return f


def raw_signal(f, i, p=PARAMS):
    row = f.iloc[i]
    if row[["slope", "r2", "ma50", "ma20"]].isna().any():
        return "NONE"
    if (row.r2 >= p["r2_min"] and row.slope < 0 and row.close < row.ma50
            and row.close >= p["bounce"] * row.ma20):
        return "PUT"
    if (p["calls"] and row.r2 >= p["r2_min"] and row.slope > 0 and row.close > row.ma50
            and row.close <= (2 - p["bounce"]) * row.ma20):
        return "CALL"
    return "NONE"


def _bs_put(s, k, days, vol, r=0.04):
    t = max(days, 0) / 365
    if t <= 0:
        return max(k - s, 0)
    d1 = (math.log(s / k) + (r + vol * vol / 2) * t) / (vol * math.sqrt(t))
    d2 = d1 - vol * math.sqrt(t)
    N = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    return k * math.exp(-r * t) * N(-d2) - s * N(-d1)


def signal(df):
    p = PARAMS
    f = features(df, p["win"])
    i = len(f) - 1
    row = f.iloc[i]
    act = raw_signal(f, i, p)
    spot = float(row.close)
    stop = float(math.exp(row.fit + row.sd)) if not np.isnan(row.fit) else spot * 1.15
    vol = max(float(row.hv20), 0.2) * IV_MULT
    k = spot * (1 + p["moneyness"])
    p0 = _bs_put(spot, k, p["dte"], vol)
    # underlying level at which the put is worth +100% after ~30 calendar days
    lo, hi = spot * 0.3, spot
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _bs_put(mid, k, p["dte"] - 30, vol) > 2 * p0 else (lo, mid)
    target = round(lo, 2)
    in_trend = (row.r2 >= p["r2_min"]) and row.slope < 0 and row.close < row.ma50
    strength = 0.0
    if act == "PUT":
        strength = float(min(1.0, (row.r2 - p["r2_min"]) / (1 - p["r2_min"]) * 0.5 + 0.5))
    if act == "PUT":
        reason = (f"130d log-trend down {row.slope*5:+.2%}/wk, R2={row.r2:.2f}; close {spot:.2f} < SMA50 "
                  f"{row.ma50:.2f} and bounced to >= 98% of SMA20 {row.ma20:.2f}. Buy ~{p['dte']}DTE put, "
                  f"strike ~{k:.2f} (nearest listed), exit +100% or 60 trading days.")
    elif in_trend:
        reason = (f"Down-trend qualifies (R2={row.r2:.2f}, {row.slope*5:+.2%}/wk, below SMA50 {row.ma50:.2f}) "
                  f"but close {spot:.2f} is {spot/row.ma20-1:+.1%} vs SMA20 {row.ma20:.2f} - stretched; "
                  f"wait for a bounce to >= {0.98*row.ma20:.2f} before buying puts.")
    else:
        reason = (f"No qualifying trend (R2={row.r2:.2f}, slope {row.slope*5:+.2%}/wk, "
                  f"SMA50 {row.ma50:.2f}); stand aside. Calls disabled for STLA.")
    return dict(action=act, strength=round(strength, 2), entry=round(spot, 2), stop=round(stop, 2),
                target=target, dte=p["dte"], reason=reason)

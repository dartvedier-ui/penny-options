"""OPEN (Opendoor) -- weekly trend-following long put / long call strategy.

signal(df) -> dict(action, strength, entry, stop, target, dte, reason)
df: daily OHLC DataFrame from common.load("OPEN").

Rules (evaluated on completed weekly bars, resampled from daily):
  slope13 = OLS slope of ln(weekly close) over the last 13 weeks (per week)
  r2_13   = R^2 of that fit
  stretch = weekly close / 10-week SMA - 1
  PUT  if slope13 <= -SLOPE_MIN and r2_13 >= R2_MIN and close < SMA10
          and stretch >= -MAX_STRETCH      (do not chase an already-crashed tape)
  CALL if slope13 >= +SLOPE_MIN and r2_13 >= R2_MIN and close > SMA10
          and stretch <= +MAX_STRETCH
  else NONE.
Trade: ATM option, ~DTE calendar days; exit at +TARGET% / -STOP% on the option
premium, or after MAX_HOLD_WEEKS, whichever first.
"""
import numpy as np
import pandas as pd

SLOPE_MIN = 0.015      # 1.5% per week
R2_MIN = 0.60
MAX_STRETCH = 0.20     # max distance from 10-week SMA at entry
DTE = 25               # short-dated (user preference 15-25 DTE); retested 2026-09-24
TARGET = 2.00          # +200% on premium (let winners run)
STOP = 0.50            # -50% on premium
MAX_HOLD_WEEKS = 2
MONEYNESS = 0.0        # ATM


def to_weekly(df):
    """Resample daily bars to weekly (week ending Friday)."""
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])
    w = d.set_index("date").resample("W-FRI").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    return w.reset_index()


def weekly_features(w):
    """Add slope13, r2_13, sma10, stretch, hv10 to a weekly OHLC frame."""
    w = w.copy().reset_index(drop=True)
    lc = np.log(w["close"].values)
    n = 13
    t = np.arange(n)
    slope = np.full(len(w), np.nan)
    r2 = np.full(len(w), np.nan)
    for i in range(n - 1, len(w)):
        y = lc[i - n + 1:i + 1]
        b, a = np.polyfit(t, y, 1)
        p = a + b * t
        ss = ((y - y.mean()) ** 2).sum()
        slope[i] = b
        r2[i] = 1 - ((y - p) ** 2).sum() / ss if ss > 0 else 0.0
    w["slope13"] = slope
    w["r2_13"] = r2
    w["sma10"] = w["close"].rolling(10).mean()
    w["stretch"] = w["close"] / w["sma10"] - 1
    w["hv10"] = pd.Series(lc).diff().rolling(10).std().values * np.sqrt(52)
    return w


def decide(row):
    """Return (action, reason) for one weekly feature row."""
    s, r2, st = row["slope13"], row["r2_13"], row["stretch"]
    if any(pd.isna(x) for x in (s, r2, st)):
        return "NONE", "insufficient history"
    if s <= -SLOPE_MIN and r2 >= R2_MIN and st < 0:
        if st < -MAX_STRETCH:
            return "NONE", (f"downtrend ({s*100:.1f}%/wk, R2 {r2:.2f}) but price {st*100:.0f}% "
                            f"below 10w SMA: too stretched, bounce/squeeze risk -- wait")
        return "PUT", f"13w downtrend {s*100:.1f}%/wk R2 {r2:.2f}, {st*100:.0f}% vs 10w SMA"
    if s >= SLOPE_MIN and r2 >= R2_MIN and st > 0:
        if st > MAX_STRETCH:
            return "NONE", (f"uptrend ({s*100:.1f}%/wk, R2 {r2:.2f}) but {st*100:.0f}% above "
                            f"10w SMA: too extended -- wait")
        return "CALL", f"13w uptrend {s*100:.1f}%/wk R2 {r2:.2f}, {st*100:.0f}% vs 10w SMA"
    return "NONE", f"no clean trend (slope {s*100:.1f}%/wk, R2 {r2:.2f}, stretch {st*100:.0f}%)"


def signal(df):
    w = weekly_features(to_weekly(df))
    row = w.iloc[-1]
    action, reason = decide(row)
    entry = float(df["close"].iloc[-1])
    # underlying levels roughly equivalent to the option stop/target for an ATM ~45 DTE option
    # (delta ~0.5, so +60%/-50% premium ~ a 1-sigma-over-2-weeks move); informational only
    hv = float(row["hv10"]) if not pd.isna(row["hv10"]) else 0.8
    mv = min(max(hv * np.sqrt(10 / 252), 0.08), 0.25)
    if action == "PUT":
        stop, target = entry * (1 + mv), entry * (1 - 1.2 * mv)
    elif action == "CALL":
        stop, target = entry * (1 - mv), entry * (1 + 1.2 * mv)
    else:
        stop = target = entry
    strength = 0.0
    if action != "NONE":
        strength = float(min(1.0, (abs(row["slope13"]) / (2 * SLOPE_MIN)) * row["r2_13"]))
    return dict(action=action, strength=round(strength, 2), entry=round(entry, 4),
                stop=round(float(stop), 4), target=round(float(target), 4), dte=DTE,
                reason=reason + f"; option exit +{int(TARGET*100)}%/-{int(STOP*100)}% premium "
                                f"or {MAX_HOLD_WEEKS} weeks")

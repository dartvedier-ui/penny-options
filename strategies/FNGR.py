"""FNGR (FingerMotion) long-option signal.

Rules (weekly bars built from the daily df):
  PUT  when 13-week log-price slope < -3%/wk AND 13-week R^2 > 0.60 AND close < 10-wk MA
       AND close no more than 30% below the 10-wk MA (avoid selling into an exhausted, squeeze-prone low).
       ATM put, ~60 DTE. Exit: underlying -30% (target) / weekly close > entry*1.25 or > 10-wk MA (stop) / 6 weeks.
  CALL never: FNGR uptrends faded (13-wk uptrend -> median 6-wk return negative); spikes are unpredictable squeezes.
  Otherwise NONE.

OPTION TRADEABILITY (checked 2026-09-24 via IBKR): the lowest listed strike is $0.50 (Jan-27) and $1.00 for
Oct/Nov-26, versus a ~$0.145 stock. Nothing is near the money: the $1 calls have no bid, the $1 puts are
~$0.86 intrinsic-only. => NOT OPTION-TRADEABLE. The function therefore always returns action "NONE" and
reports the raw rule in `reason`. Backtest (synthetic ATM puts) was also negative in- and out-of-sample.
"""
import math
import numpy as np
import pandas as pd

OPTION_TRADEABLE = False
SLOPE_MAX, R2_MIN, STRETCH_MIN = -0.03, 0.60, -0.30
STOP_UP, TARGET_DN, DTE = 0.25, 0.30, 60


def _weekly(df):
    d = df.copy(); d["date"] = pd.to_datetime(d["date"])
    w = d.set_index("date").resample("W-FRI").agg({"open": "first", "high": "max", "low": "min", "close": "last"})
    return w.dropna().reset_index()


def signal(df):
    w = _weekly(df)
    base = dict(action="NONE", strength=0.0, entry=float(df["close"].iloc[-1]), stop=0.0, target=0.0, dte=DTE)
    if len(w) < 14:
        return {**base, "reason": "insufficient history"}
    y = np.log(w.close.values[-14:]); x = np.arange(14)
    slope, _ = np.polyfit(x, y, 1); r2 = float(np.corrcoef(x, y)[0, 1] ** 2)
    ma10 = float(w.close.iloc[-10:].mean()); c = float(w.close.iloc[-1]); stretch = c / ma10 - 1

    raw = "NONE"
    if slope < SLOPE_MAX and r2 > R2_MIN and c < ma10:
        raw = "PUT" if stretch > STRETCH_MIN else "NONE"
    why = (f"13wk slope {slope*100:.1f}%/wk, R2 {r2:.2f}, close {c:.4f} is {stretch*100:.0f}% vs 10wk MA {ma10:.4f}; ")
    if raw == "PUT":
        why += "raw rule = PUT (ATM, 60 DTE, stop close>+25% or >10wk MA, target -30%, max 6 wks)"
    elif slope < SLOPE_MAX and r2 > R2_MIN and c < ma10:
        why += "raw rule = NONE (downtrend but >30% below 10wk MA: too stretched, squeeze risk)"
    else:
        why += "raw rule = NONE (no qualifying trend)"
    why += ("; backtest negative IS & OOS (synthetic ATM puts, 30% spread)")
    if not OPTION_TRADEABLE:
        why += "; NOT OPTION-TRADEABLE: lowest strikes $0.50-$1.00 vs ~$0.15 stock, no near-money contracts"
        return {**base, "entry": c, "reason": why}
    if raw == "PUT":
        strength = float(min(1.0, r2 * min(1.0, -slope / 0.08)))
        return dict(action="PUT", strength=strength, entry=c, stop=round(c * (1 + STOP_UP), 4),
                    target=round(c * (1 - TARGET_DN), 4), dte=DTE, reason=why)
    return {**base, "entry": c, "reason": why}

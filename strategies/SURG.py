"""SURG (SurgePays) long call / long put signal.

Trend-following, put-biased rule on daily bars:
  PUT  : close < SMA20 < SMA50, 65-day log-price regression slope < 0,
         and no >+25% up-spike close in the last 3 sessions (let promo spikes
         settle first; they usually fade but the first days are violent).
  CALL : close > SMA20 > SMA50 and 65-day slope > 0 (rare on this name).
  else : NONE.
Option plan: ~45 DTE, nearest-ATM strike, take profit +60% on premium,
stop -50% on premium, max hold 20 trading days.

IMPORTANT: as of 2026-09-24 SURG's listed chain is NOT practically tradeable.
Lowest listed strike is $0.50 with the stock at ~$0.15 (3.4x spot). The
$0.50 puts quote ~0.30 x 0.50 (OI 2-4, zero volume): paying the 0.50 ask for a
put whose max value is its 0.50 strike gives zero upside. The $0.50 calls have
no bid (0.05 ask). The signal is therefore a stock-direction signal only.
"""
import numpy as np
import pandas as pd

OPTION_TRADEABLE = False
TRADEABILITY_NOTE = ("NOT OPTION-TRADEABLE: lowest strike $0.50 vs spot ~$0.15; "
                     "0.50 puts ~0.30x0.50, OI<5, no volume; calls no bid. "
                     "Use as stock-direction signal only.")

DTE = 45
TARGET_PCT = 0.60    # option premium take-profit
STOP_PCT = 0.50      # option premium stop
MAX_HOLD = 20        # trading days
SPIKE = 0.25         # daily close-to-close jump treated as promo spike


def _slope(logc):
    y = np.asarray(logc)
    x = np.arange(len(y))
    return np.polyfit(x, y, 1)[0]


def features(df):
    c = df["close"].astype(float)
    f = pd.DataFrame(index=df.index)
    f["close"] = c
    f["sma20"] = c.rolling(20).mean()
    f["sma50"] = c.rolling(50).mean()
    f["slope65"] = np.log(c).rolling(65).apply(_slope, raw=True)
    r = np.log(c).diff()
    f["vol20"] = r.rolling(20).std() * np.sqrt(252)
    f["spike3"] = (c.pct_change() > SPIKE).rolling(3).max().fillna(0).astype(bool)
    return f


def raw_action(row):
    if any(pd.isna(getattr(row, k)) for k in ("sma20", "sma50", "slope65")):
        return "NONE"
    if row.close < row.sma20 < row.sma50 and row.slope65 < 0 and not row.spike3:
        return "PUT"
    if row.close > row.sma20 > row.sma50 and row.slope65 > 0:
        return "CALL"
    return "NONE"


def signal(df):
    f = features(df)
    row = f.iloc[-1]
    action = raw_action(row)
    px = float(row.close)
    vol = float(row.vol20) if not pd.isna(row.vol20) else 1.5
    # stock-level stop/target approximating the option exits over ~20 days
    move = max(0.15, min(0.40, vol * np.sqrt(20 / 252) * 0.8))
    wk = (row.slope65 * 5 * 100) if not pd.isna(row.slope65) else float("nan")
    base = (f"close {px:.4f}, SMA20 {row.sma20:.4f}, SMA50 {row.sma50:.4f}, "
            f"65d trend {wk:+.1f}%/wk, 20d vol {vol:.0%}")
    if action == "PUT":
        stop, target = px * (1 + move), px * (1 - move)
        strength = float(min(1.0, abs(wk) / 10))
        reason = "Downtrend intact (close<SMA20<SMA50, negative slope, no fresh spike): " + base
    elif action == "CALL":
        stop, target = px * (1 - move), px * (1 + move)
        strength = float(min(1.0, abs(wk) / 10))
        reason = "Uptrend (close>SMA20>SMA50, positive slope): " + base
    else:
        stop = target = px
        strength = 0.0
        reason = "No aligned trend / post-spike cooling: " + base
    if not OPTION_TRADEABLE:
        reason = TRADEABILITY_NOTE + " | " + reason
        strength = strength * 0.25   # heavily discounted: cannot be expressed in options
    return dict(action=action, strength=round(strength, 2), entry=round(px, 4),
                stop=round(float(stop), 4), target=round(float(target), 4),
                dte=DTE, reason=reason)

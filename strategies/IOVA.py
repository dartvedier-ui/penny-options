"""IOVA long call / long put strategy (trend-regime + pullback entry).

Rules (daily bars, evaluated at the close):
  Regime  : 65-day (13-week) log-price linear fit -> slope & R^2.
            UP   = slope > 0, R^2 >= R2_MIN, close > SMA50
            DOWN = slope < 0, R^2 >= R2_MIN, close < SMA50
            else = stand aside.
  Entry   : CALL in UP regime when price has pulled back: close <= EMA10 * (1+PB_BAND)
            (i.e. not more than PB_BAND above the 10-day EMA) and close > SMA50.
            PUT in DOWN regime when price has bounced: close >= EMA10 * (1-PB_BAND)
            and close < SMA50.
            Stand aside if price is > MAX_EXT above the 50-day SMA (calls)
            or > MAX_EXT below it (puts): too extended, blow-off/dilution risk.
  Option  : ~45 DTE, at-the-money (use the nearest monthly strike), vol unknown.
  Exit    : option +100% (take profit) or MAX_HOLD = 20 trading days (time stop).
            No premium stop-loss: size so the whole premium = 5% of account.
            (The 'stop' price returned by signal() is only a thesis-invalidation
            level for discretionary review; it is NOT used in the backtest.)
"""
import numpy as np
import pandas as pd

R2_MIN = 0.60
PB_BAND = 0.03      # entry only within 3% of EMA10 (buy pullbacks, not spikes)
MAX_EXT = 0.35      # skip if >35% away from SMA50
DTE = 21          # short-dated (user preference 15-25 DTE); retested 2026-09-24
MONEYNESS = 0.0
TARGET_PCT = 1.00   # +100% on premium (take profit)
STOP_PCT = 1.00     # no premium stop: premium (5% of account) IS the risk;
                    # tested -50% stops / SMA50-flip exits were whipsawed by gaps
FLIP_EXIT = False
MAX_HOLD = 11       # trading days (exit >=5 calendar days before expiry)


def indicators(df):
    d = df.copy()
    lc = np.log(d["close"].astype(float))
    n = 65
    t = np.arange(n)
    tm = t - t.mean()
    slope = lc.rolling(n).apply(lambda y: np.dot(tm, y - y.mean()) / np.dot(tm, tm), raw=True)
    r2 = lc.rolling(n).apply(lambda y: np.corrcoef(t, y)[0, 1] ** 2, raw=True)
    d["slope_wk"] = slope * 5            # log-return per week
    d["r2"] = r2
    d["sma50"] = d["close"].rolling(50).mean()
    d["ema10"] = d["close"].ewm(span=10, adjust=False).mean()
    d["hv20"] = lc.diff().rolling(20).std() * np.sqrt(252)
    d["atr14"] = (pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(),
                             (d.low - d.close.shift()).abs()], axis=1).max(axis=1)).rolling(14).mean()
    return d


def raw_signal(row, r2_min=R2_MIN, pb=PB_BAND, max_ext=MAX_EXT):
    """Return 'CALL' / 'PUT' / None and a reason for one indicator row."""
    if any(pd.isna(row[k]) for k in ("slope_wk", "r2", "sma50", "ema10")):
        return None, "insufficient history"
    c, s, e = row.close, row.sma50, row.ema10
    ext = c / s - 1
    if row.slope_wk > 0 and row.r2 >= r2_min and c > s:
        if ext > max_ext:
            return None, f"uptrend but {ext:.0%} above SMA50 (too extended)"
        if c <= e * (1 + pb):
            return "CALL", "uptrend pullback to EMA10"
        return None, f"uptrend, waiting for pullback (close {c/e-1:+.1%} vs EMA10)"
    if row.slope_wk < 0 and row.r2 >= r2_min and c < s:
        if ext < -max_ext:
            return None, f"downtrend but {ext:.0%} below SMA50 (too extended)"
        if c >= e * (1 - pb):
            return "PUT", "downtrend bounce to EMA10"
        return None, f"downtrend, waiting for bounce (close {c/e-1:+.1%} vs EMA10)"
    return None, f"no clean trend (slope {row.slope_wk:+.1%}/wk, R2 {row.r2:.2f})"


def signal(df):
    d = indicators(df)
    row = d.iloc[-1]
    act, why = raw_signal(row)
    c = float(row.close)
    atr = float(row.atr14) if not pd.isna(row.atr14) else 0.05 * c
    r2 = 0.0 if pd.isna(row.r2) else float(row.r2)
    strength = max(0.0, min(1.0, (r2 - R2_MIN) / (1 - R2_MIN))) if act else 0.0
    if act == "CALL":
        stop, target = max(float(row.sma50), c - 2 * atr), c + 3 * atr
    elif act == "PUT":
        stop, target = min(float(row.sma50), c + 2 * atr), c - 3 * atr
    else:
        stop = target = c
    return dict(action=act or "NONE", strength=round(strength, 2), entry=round(c, 2),
                stop=round(stop, 2), target=round(target, 2), dte=DTE,
                reason=f"{why}; 13w slope {row.slope_wk:+.1%}/wk, R2 {r2:.2f}, "
                       f"close/SMA50 {c/row.sma50-1:+.0%}, HV20 {row.hv20:.0%}. "
                       f"Option exits: +{TARGET_PCT:.0%} on premium or {MAX_HOLD} trading days; no premium stop.")

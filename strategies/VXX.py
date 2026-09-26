"""VXX long-option strategy (long PUT bias; calls only on volatility breakouts).

VXX decays structurally (futures contango roll, ~ -60%/yr log drift over 2021-2026)
but spikes violently when equities sell off. Spikes mean-revert fast.

Rules (evaluated on daily closes, see reports/VXX.md):
  PUT-TREND : 13-week log-slope < 0, close < 20d MA, and 5-day return < +5% (no spike under way)
  PUT-FADE  : VXX rose > `spike` above its 50d MA within the last 10 days, and today closes
              down >= 5% from that 10-day peak (spike rolling over)
  CALL      : only if `calls` enabled (disabled by default - no out-of-sample edge found)
  Otherwise : NONE.
FINAL (tested) configuration: PUT-TREND only (fade and calls disabled - both lost money in-sample).
Option: ~90 DTE put, ~10% in the money (strike = 1.10 x spot), take profit at +100% option gain,
stop at -70% option loss, otherwise exit after 40 trading days.
"""
import os
import numpy as np
import pandas as pd

PARAMS = dict(spike=0.15, dte=90, moneyness=0.10, target=1.0, stop=0.7, max_hold=40, calls=False,
              trend=True, fade=False)
IV_MULT, IV_FLOOR = 1.3, 0.55  # modelled implied vol = max(IV_MULT*HV20, IV_FLOOR)


def features(df):
    c = df.close.astype(float)
    lc = np.log(c)
    f = pd.DataFrame(index=df.index)
    f["close"] = c
    f["ma20"] = c.rolling(20).mean()
    f["ma50"] = c.rolling(50).mean()
    f["r5"] = lc.diff(5)
    f["hv20"] = lc.diff().rolling(20).std() * np.sqrt(252)
    x = np.arange(65) - 32.0
    f["slope65"] = lc.rolling(65).apply(lambda y: np.dot(x, y - y.mean()) / np.dot(x, x), raw=True)
    f["peak10"] = c.rolling(10).max()
    f["peak_vs_ma50"] = (c.rolling(10).max() / f["ma50"]) - 1
    f["hi20"] = c.shift(1).rolling(20).max()
    return f


def raw_signal(f, i, p):
    """Return 'PUT' | 'CALL' | 'NONE' for bar i given feature frame f."""
    row = f.iloc[i]
    if row[["ma50", "slope65", "hv20"]].isna().any():
        return "NONE"
    fade = row.peak_vs_ma50 > p["spike"] and row.close <= row.peak10 * 0.95 and row.close < f.close.iloc[i - 1]
    if p.get("fade", True) and fade:
        return "PUT"
    in_spike = row.r5 > 0.05 or row.peak_vs_ma50 > p["spike"]
    if p.get("trend", True) and row.slope65 < 0 and row.close < row.ma20 and not in_spike:
        return "PUT"
    if p.get("calls", False) and row.close > row.hi20 and row.r5 > 0.10 and row.hv20 < 0.6:
        return "CALL"
    return "NONE"


def _spot_for_option_value(strike, days, vol, value, kind="PUT"):
    """Underlying price at which the option would be worth `value` (bisection)."""
    import common
    lo, hi = strike * 0.2, strike * 3
    for _ in range(80):
        mid = (lo + hi) / 2
        v = common.bs_price(mid, strike, days, vol, kind)
        if (v > value) == (kind == "PUT"):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def signal(df):
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import common
    p = PARAMS
    f = features(df)
    i = len(df) - 1
    act = raw_signal(f, i, p)
    row = f.iloc[i]
    spot = float(row.close)
    if act == "NONE":
        why = []
        if row.slope65 >= 0: why.append("13wk slope not negative")
        if row.close >= row.ma20: why.append(f"close {spot:.2f} >= 20d MA {row.ma20:.2f}")
        if row.r5 > 0.05: why.append(f"5d return {row.r5:+.1%} (spike may be starting)")
        if row.peak_vs_ma50 > p["spike"]: why.append("recent spike >15% above 50d MA")
        return dict(action="NONE", strength=0.0, entry=round(spot, 2), stop=0.0, target=0.0, dte=p["dte"],
                    reason="Stand aside: " + "; ".join(why or ["no trigger"]))
    kind = act
    strike = spot * (1 + p["moneyness"]) if kind == "PUT" else spot * (1 - p["moneyness"])
    vol = max(IV_MULT * float(row.hv20), IV_FLOOR)
    prem = common.bs_price(spot, strike, p["dte"], vol, kind)
    days_in = 28  # ~20 trading days into the trade
    tgt_px = _spot_for_option_value(strike, p["dte"] - days_in, vol, prem * (1 + p["target"]), kind)
    stop_px = _spot_for_option_value(strike, p["dte"] - days_in, vol, prem * (1 - p["stop"]), kind)
    # strength: steeper downtrend and deeper below the 20d MA -> stronger (capped at 1)
    strength = min(1.0, 0.4 + min(0.4, -float(row.slope65) * 5 * 10) + min(0.2, (row.ma20 / spot - 1) * 4))
    reason = (f"PUT-TREND: 13wk slope {row.slope65*5:+.2%}/wk, close {spot:.2f} < 20d MA {row.ma20:.2f}, "
              f"5d {row.r5:+.1%}, no spike. Buy ~{p['dte']}DTE put, strike ~{strike:.1f} (10% ITM), "
              f"model premium ~{prem:.2f} at IV {vol:.0%}. Exit at +{p['target']:.0%} option gain, "
              f"-{p['stop']:.0%} option loss, or after {p['max_hold']} trading days. "
              f"stop/target are approximate VXX levels ~4 weeks in.")
    return dict(action=act, strength=round(float(strength), 2), entry=round(spot, 2), stop=round(stop_px, 2),
                target=round(tgt_px, 2), dte=p["dte"], reason=reason)

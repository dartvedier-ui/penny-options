"""NIO long call / long put strategy (trend + pullback re-entry through SMA20).

signal(df) -> dict(action, strength, entry, stop, target, dte, reason)
df = common.load("NIO") daily OHLC.

Rules (see reports/NIO.md):
  Trend   : SMA20 vs SMA50, and SMA50 slope over 10 sessions.
  PUT     : SMA20 < SMA50, SMA50 falling, and after a bounce the close crosses
            back BELOW SMA20 (yesterday close >= SMA20, today close < SMA20).
  CALL    : SMA20 > SMA50, SMA50 rising, and after a dip the close crosses
            back ABOVE SMA20.
  Else    : NONE (stand aside).
  Option  : ~45 DTE, strike ~5% in the money (nearest listed strike).
  Exit    : option +TARGET_PCT (take profit), option -STOP_PCT (stop),
            or MAX_HOLD trading days, whichever first.
"""
import numpy as np
import pandas as pd

FAST, SLOW, SLOPE_LB, BRK = 20, 50, 10, 20
DTE = 21               # short-dated (user preference 15-25 DTE); retested 2026-09-24
MONEYNESS = 0.05       # 5% ITM
TARGET_PCT = 1.00      # take profit on option +100%
STOP_PCT = 1.00        # no premium stop at short DTE (best in-sample)
MAX_HOLD = 11          # trading days (exit >=5 calendar days before expiry)
IV_HV_MULT = 1.25      # option IV ~ 1.25x realised vol (measured 2026-09-24: IV 46-55% vs HV20 32-39%)
SPREAD_COST = 0.12     # round-trip bid/ask + commissions as fraction of premium


def features(df):
    c = df["close"].astype(float)
    out = pd.DataFrame(index=df.index)
    out["close"] = c
    out["sma_f"] = c.rolling(FAST).mean()
    out["sma_s"] = c.rolling(SLOW).mean()
    out["slope"] = out["sma_s"] / out["sma_s"].shift(SLOPE_LB) - 1
    out["hi"] = c.rolling(BRK).max()
    out["lo"] = c.rolling(BRK).min()
    r = np.log(c).diff()
    out["hv20"] = r.rolling(20).std() * np.sqrt(252)
    down = (out.sma_f < out.sma_s) & (out.slope < 0)
    up = (out.sma_f > out.sma_s) & (out.slope > 0)
    s20 = out.sma_f
    out["put"] = down & (c < s20) & (c.shift() >= s20.shift())
    out["call"] = up & (c > s20) & (c.shift() <= s20.shift())
    out["regime"] = np.where(down, "down", np.where(up, "up", "none"))
    return out


def option_vol(hv):
    return float(np.clip(hv * IV_HV_MULT, 0.35, 1.3))


def signal(df):
    f = features(df)
    row = f.iloc[-1]
    px = float(row.close)
    base = dict(action="NONE", strength=0.0, entry=px, stop=float("nan"),
                target=float("nan"), dte=DTE, reason="")
    if np.isnan(row.sma_s):
        base["reason"] = "not enough history"
        return base
    vol = option_vol(row.hv20)
    # underlying move that roughly corresponds to the option stop/target
    # (ITM option delta ~0.6-0.65, leverage ~ delta*S/premium)
    from common import bs_price
    kind = "PUT" if row.put else ("CALL" if row.call else None)
    if kind is None:
        base["reason"] = (f"regime={row.regime}; no SMA20 re-cross today "
                          f"(close {px:.2f}, SMA20 {row.sma_f:.2f}, SMA50 {row.sma_s:.2f}, "
                          f"SMA50 {row.slope:+.1%}/10d, HV20 {row.hv20:.0%})")
        if row.regime == "down":
            base["reason"] += (f"; PUT would arm after a close >= SMA20 (~{row.sma_f:.2f}) "
                               f"followed by a close back below it. Backtest edge is weak/negative.")
        return base
    strike = px * (1 - MONEYNESS) if kind == "CALL" else px * (1 + MONEYNESS)
    prem = bs_price(px, strike, DTE, vol, kind)
    # solve underlying levels for option stop/target via simple scan (days held ~5)
    grid = np.linspace(px * 0.6, px * 1.4, 801)
    vals = np.array([bs_price(s, strike, DTE - 5, vol, kind) for s in grid])
    tgt_v, stp_v = prem * (1 + TARGET_PCT), prem * (1 - STOP_PCT)
    if kind == "PUT":
        target = grid[vals >= tgt_v].max(); stop = grid[vals <= stp_v].min()
    else:
        target = grid[vals >= tgt_v].min(); stop = grid[vals <= stp_v].max()
    strength = float(np.clip(abs(row.slope) / 0.10, 0, 1))
    return dict(action=kind, strength=round(strength, 2), entry=px,
                stop=round(float(stop), 2), target=round(float(target), 2), dte=DTE,
                reason=(f"{row.regime}trend (SMA20 {row.sma_f:.2f} vs SMA50 {row.sma_s:.2f}, "
                        f"SMA50 {row.slope:+.1%}/10d) + close re-crossed SMA20 {'down' if kind=='PUT' else 'up'}; "
                        f"buy ~{DTE}DTE {strike:.2f} {kind} (5% ITM), exit +{TARGET_PCT:.0%} on the option "
                        f"or {MAX_HOLD} trading days, no premium stop"))

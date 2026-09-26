"""TLT long-put / long-call strategy: "bear-regime structural put, don't chase".

Research (2021-09 .. 2026-09, see reports/TLT.md) found NO timing edge from
momentum / breakout / MA-cross rules on TLT - 20-65 day returns are slightly
mean-reverting, and entries on fresh lows had ~zero follow-through.  What paid
was simply owning ITM puts while the 26-week log-trend was down (TLT's slow
decline + monthly distribution drops).  Rules:

  PUT  : 26-wk log-price regression slope < 0
         AND close is not stretched below its 20-day mean by more than 1x the
         20-day expected move (z20 >= -1)  -> don't chase breakdowns.
  CALL : 26-wk slope > 0 AND 13-wk slope > 0 AND close > SMA200 AND z20 <= +1.
         Call leg is OFF by default (ENABLE_CALLS=False): 6 of 7 call trades
         lost in the backtest. If enabled, strength is capped at 0.2.
  NONE : otherwise.
Option: ~90 DTE, ~5% in the money. Target +100% on premium, stop -40% on
premium, max hold 40 trading days (~56 calendar days), also exit if regime flips.
"""
import math
import numpy as np

# short-dated (user preference 15-25 DTE); retested 2026-09-24: ~break-even, very low confidence
DTE, MONEYNESS, TARGET, STOP, MAX_HOLD = 25, 0.0, 1.0, -1.0, 14
ENABLE_CALLS = False   # call leg lost 6/7 trades in the backtest; set True to trade it anyway


def _slope(logp, n):
    x = np.arange(n); xm = x - x.mean()
    return logp.rolling(n).apply(lambda y: (xm * (y - y.mean())).sum() / (xm ** 2).sum(), raw=True) * 5


def features(df):
    d = df.copy()
    c = d.close
    lc = np.log(c)
    d["r"] = lc.diff()
    d["hv20"] = d.r.rolling(20).std() * math.sqrt(252)
    d["sma20"] = c.rolling(20).mean()
    d["sma200"] = c.rolling(200).mean()
    d["slope26"] = _slope(lc, 130)   # log-slope per week
    d["slope13"] = _slope(lc, 65)
    d["z20"] = (c - d.sma20) / (c * d.hv20 * math.sqrt(20 / 252))
    return d


def rule(d, i):
    """Return 'PUT', 'CALL' or None for row i of a features() frame."""
    x = d.iloc[i]
    if any(map(lambda v: v != v, (x.slope26, x.slope13, x.z20, x.sma200))):
        return None
    if x.slope26 < 0 and x.z20 >= -1:
        return "PUT"
    if ENABLE_CALLS and x.slope26 > 0 and x.slope13 > 0 and x.close > x.sma200 and x.z20 <= 1:
        return "CALL"
    return None


def _levels(px, vol, kind, days_fwd=14):
    """Underlying prices at which the option (bought today) would hit STOP / TARGET
    about two weeks from now (Black-Scholes-Merton, 4.5% distribution yield)."""
    import common
    q, r = 0.045, 0.04
    K = px * (1 + MONEYNESS) if kind == "PUT" else px * (1 - MONEYNESS)
    val = lambda s, d: common.bs_price(s, K, d, vol, kind, rate=r - q) * math.exp(-q * d / 365)
    p0 = val(px, DTE)
    grid = [px * (1 + k / 1000) for k in range(-250, 251)]
    vals = [(abs(val(s, DTE - days_fwd) - p0 * (1 + STOP)), s) for s in grid]
    stop_px = min(vals)[1]
    vals = [(abs(val(s, DTE - days_fwd) - p0 * (1 + TARGET)), s) for s in grid]
    return round(stop_px, 2), round(min(vals)[1], 2)


def signal(df):
    d = features(df)
    i = len(d) - 1
    x = d.iloc[i]
    kind = rule(d, i)
    px = float(x.close)
    base = dict(slope26_pct_wk=round(float(x.slope26) * 100, 3), slope13_pct_wk=round(float(x.slope13) * 100, 3),
                z20=round(float(x.z20), 2), hv20=round(float(x.hv20), 3))
    if kind == "PUT":
        strength = float(min(1.0, 0.3 + abs(x.slope26) * 100) * 0.6)   # historically modest edge
        stop_px, tgt_px = _levels(px, max(x.hv20 * 1.15, 0.09), "PUT")
        if STOP <= -1.0:
            stop_px = 0.0   # no premium stop at short DTE
        return dict(action="PUT", strength=round(strength, 2), entry=px,
                    stop=stop_px, target=tgt_px, dte=DTE,
                    reason=(f"26-wk trend down {x.slope26*100:.2f}%/wk, not over-extended (z20={x.z20:.2f}). "
                            f"Buy ~{DTE} DTE put, strike ~{px*(1+MONEYNESS):.0f} (at the money); "
                            f"exit +100% on premium or {MAX_HOLD} trading days, no premium stop. {base}"))
    if kind == "CALL":
        stop_px, tgt_px = _levels(px, max(x.hv20 * 1.15, 0.09), "CALL")
        return dict(action="CALL", strength=0.2, entry=px, stop=stop_px, target=tgt_px, dte=DTE,
                    reason=f"26/13-wk trends up, above SMA200 (calls lost in backtest - small size). {base}")
    why = ("down-trend but stretched below 20d mean - wait for a bounce toward SMA20"
           if x.slope26 < 0 else "no qualifying regime")
    return dict(action="NONE", strength=0.0, entry=px, stop=0.0, target=0.0, dte=DTE,
                reason=f"{why}. {base}")

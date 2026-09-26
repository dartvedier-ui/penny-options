"""Shared helpers for the Penny Option strategy research.

Every per-ticker strategy lives in strategies/<TICKER>.py and must expose:
    signal(df) -> dict(action="CALL"|"PUT"|"NONE", strength=0..1, entry=float,
                       stop=float, target=float, dte=int, reason=str)
where df is the daily OHLC DataFrame returned by load(ticker).
"""
import os
import math
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))


def load(ticker, freq="daily"):
    """Load data/<TICKER>_<freq>.csv (columns: date,open,high,low,close[,volume])."""
    df = pd.read_csv(f"{ROOT}/data/{ticker}_{freq}.csv", parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


def _ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def bs_price(spot, strike, days, vol, kind, rate=0.04):
    """Black-Scholes price of a European call/put. vol is annualised (0.45 = 45%)."""
    t = max(days, 0) / 365
    if t <= 0 or vol <= 0:
        return max(spot - strike, 0) if kind == "CALL" else max(strike - spot, 0)
    d1 = (math.log(spot / strike) + (rate + vol * vol / 2) * t) / (vol * math.sqrt(t))
    d2 = d1 - vol * math.sqrt(t)
    if kind == "CALL":
        return spot * _ncdf(d1) - strike * math.exp(-rate * t) * _ncdf(d2)
    return strike * math.exp(-rate * t) * _ncdf(-d2) - spot * _ncdf(-d1)


def option_trade_return(entry_spot, exit_spot, kind, dte, held_days, vol,
                        moneyness=0.0, spread_cost=0.08):
    """Approximate % return of buying an option and selling it after held_days.

    moneyness: 0 = at the money; +0.05 = 5% in the money.
    spread_cost: round-trip bid/ask + fees as a fraction of premium
                 (≈0.05 liquid names, 0.10-0.20 thin/penny names).
    """
    strike = entry_spot * (1 - moneyness) if kind == "CALL" else entry_spot * (1 + moneyness)
    buy = bs_price(entry_spot, strike, dte, vol, kind)
    sell = bs_price(exit_spot, strike, dte - held_days, vol, kind)
    if buy <= 0:
        return 0.0
    return (sell - buy) / buy - spread_cost

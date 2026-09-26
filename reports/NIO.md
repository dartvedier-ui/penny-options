# NIO (NIO Inc ADR) — long call / long put study

Date: 2026-09-24. Spot $3.61–3.62 (daily bar close / live snapshot), at its 52-week low ($3.55).

## Data
- `data/NIO_daily.csv`: 501 IBKR daily bars, 2024-09-25 to 2026-09-24. The last bar is today's partial session.
- `data/NIO_weekly.csv`: 262 IBKR weekly bars, 2021-09-27 to 2026-09-21. The partial week is merged into the final row.
- Last close matches the live snapshot (3.61 on the bar vs 3.62 on the snapshot, bid/ask 3.61/3.62). Four bars show a 1-cent OHLC inconsistency in IBKR's own data. I left them as delivered.

## Options check (live, 2026-09-24)
| Contract | Bid/Ask | Width as % of mid | OI | IV |
|---|---|---|---|---|
| Oct 30 '26 3.5C (36 DTE) | 0.27/0.31 | 14% | 672 | 49% |
| Oct 30 '26 4P | 0.44/0.48 | 9% | 626 | 49% |
| Oct 30 '26 3.5P | 0.14/0.17 | 19% | 1,356 | 48% |
| Nov 20 '26 4P (57 DTE, monthly) | 0.50/0.56 | 11% | 36,000 | 53% |
| Nov 20 '26 4C | 0.18/0.19 | 5% | 51,000 | 55% |

- Weeklies trade at $0.50 strikes. Monthlies near spot trade at $1 strikes only (3/4/5).
- Liquidity is concentrated in the monthlies (tens of thousands of OI).
- Round-trip cost: the full spread plus about $1.30 in commissions on a $30–50 premium comes to roughly 10–15%. The backtest uses **12%** and stress-tests 8% and 20%.
- Option IV is about 48–55% against a 20-day realised vol of 32% (30-day HV 39%). IV/HV is about 1.25–1.5, so the backtest uses **1.25×** and stress-tests 1.0× and 1.5×.

## Behaviour study (what the data says)
- **The trend is descriptive, not predictive.** On 5 years of weekly bars, the sign of the 13-week log-linear slope called the next 4 weeks' direction **49%** of the time. That is a coin flip, and the hit rate is ≤47.5% since 2023. The 13-week return has a **−0.15** correlation with the next 4-week return, which points to mild mean reversion, not momentum.
- **The drift is real but small next to the volatility.** Unconditional 20-day forward return is −1.9% and 59% of 20-day windows were down. When the close was below SMA50, the next 20 days were down 63–65% of the time, but the average move was only −1.6% to −2.1%. That is much less than the ~15% the option has to recover in theta plus spread.
- **Bounces kill puts.** On downtrend days (below a falling SMA50), the stock traded **≥10% higher within 20 days 45%** of the time. Median rally off the 10-day low is 2.4%, the 90th percentile is 8%, and the maximum is 27%.
- **Volatility regime.** HV20 averaged 58% over 2 years (range 29–96%). It is now 32%, the 3rd percentile of the past year: an extreme squeeze. IBKR IV percentile is about 0–2% (13-, 26- and 52-week). Options are historically cheap, but compression usually ends with a big move in an unknown direction.
- **Gaps.** 23 opening gaps larger than 5% in 2 years, 35 daily moves larger than 7%. Examples: +18% on 2024-09-30 (China stimulus), about −8% around capital raises and earnings (2025-09-10, 2025-10-16). The first 2 trading days of each month (delivery reports) are **no more volatile** than other days (2.9% vs 2.9% average absolute move).
- **Regime swings are violent.** $3.43 (Jun 2025) to $7.89 (Oct 2025) is +130% in 4 months, then back down to $3.61. A multi-month trend fit can flip within weeks.

## Strategy rules (strategies/NIO.py)
1. **Regime.**
   - Downtrend = SMA20 < SMA50 and SMA50 lower than 10 sessions ago.
   - Uptrend = SMA20 > SMA50 and SMA50 rising.
   - Otherwise stand aside.
2. **Entry (pullback re-entry).**
   - Buy a PUT in a downtrend on the day the close drops back **below SMA20** after closing at or above it the day before (the bounce failed).
   - Buy a CALL in an uptrend on the mirror-image cross back above SMA20.
3. **Contract.** About 45 DTE, strike about 5% in the money (the nearest listed strike; prefer the liquid monthly).
4. **Exit.** The first of: option **+100%** (take profit), option **−60%** (stop), or **25 trading days**.
5. **Size.** Premium = 5% of the account. One position at a time.

I compared three entry styles on in-sample data only: always-in-trend, 20-day breakout and pullback re-entry, each across a 16-combination grid of target, stop, hold and moneyness. Pullback re-entry lost least in-sample, so it was chosen. **Every one of the 48 configurations lost money in-sample.**

## Backtest (5% of account risked per trade, 12% spread, IV = 1.25 × HV20)
IS = 2024-09-25 to 2026-02-18 (first 70% of bars). OOS = 2026-02-19 to 2026-09-24.

| | Trades | Win % | Avg ret/trade | Median | Total (compounded) | Max DD | Longest losing streak |
|---|---|---|---|---|---|---|---|
| Strategy IS | 8 | 38% | −8.8% | −45.8% | −4.0% | −9.2% | 3 |
| Strategy OOS | 4 | 25% | −15.9% | −13.6% | −3.2% | −5.2% | 2 |
| Strategy all | 12 | 33% | −11.1% | −27.6% | −7.1% | −11.7% | 4 |
| Baseline IS (follow 13-wk slope, 20-day hold) | 14 | 29% | −29.7% | −31.6% | −19.4% | −19.4% | 4 |
| Baseline OOS | 8 | 25% | −9.0% | −20.2% | −4.3% | −12.0% | 4 |
| Weekly 5-yr check (same logic on weekly bars) | 18 | 39% | −19.8% | −30.2% | −17.3% | −26.4% | 4 |
| Weekly 5-yr baseline | 40 | 20% | −37.2% | −42.2% | −53.2% | −53.2% | 10 |

**Sensitivity (all daily data):**
- At IV = 1.0 × HV (options priced at realised vol) the strategy is slightly positive: +4.9% total, 50% wins.
- At 1.25× it is −7%; at 1.5× it is −15%.
- A 20% spread makes it −11.5%.
- The result depends on how rich the options are priced, not on the direction call.

Every result here, the strategy's included, is negative after realistic costs. The rules lose **less** than the naive trend-following baseline. The main reason is that they stand aside more (12 trades vs 21), not that they show a clear edge. The sample is tiny (12 daily trades), so no statistic here is significant.

## Key risks
- **Theta + spread hurdle.** A flat stock over 25 days costs a 45 DTE option about 30–60%. NIO's −2%/week drift is not enough to cover that.
- **Violent short squeezes and bounces.** China stimulus headlines have produced +18% gaps and +130% rallies. Puts get stopped out often.
- **Event gaps.** Capital raises, earnings and policy news can move the stock 7–18% overnight, straight through stops.
- **Penny-premium options.** Spreads of 10–20% of premium, and only $1 strikes on the monthlies.
- **Model risk.** Black-Scholes with constant vol, close-only exits, no real IV history (IV rank today is near 0, the cheapest in a year).

## Today's signal (2026-09-24)
**NONE — stand aside.**
- Regime is a downtrend: close 3.61 < SMA20 3.81 < SMA50 4.32, and SMA50 is down 5.5% over 10 days.
- There was no bounce-and-fail cross today.
- A PUT would arm only after a close at or above about $3.81 followed by a close back below SMA20.
- Given the backtest, even that signal carries **low confidence**.
- HV and IV are at 1-year lows. Options are cheap, but the next large move is as likely to be a squeeze higher from the 52-week low as a continuation lower.

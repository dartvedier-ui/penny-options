# IOVA (Iovance Biotherapeutics): long call / long put strategy

*Research date 2026-09-24. Data: IBKR daily bars 2021-09-27 to 2026-09-24 (1,254 rows) and weekly bars (262 rows). Last close 10.75 matches the live IBKR snapshot (10.75, bid 10.73 / ask 10.75).*

## Today's signal: **NONE (stand aside and wait for a pullback)**
- The trend is very clean: 13-week slope is +8.4%/wk and R² is 0.90. Price is above the 50-day SMA (7.29).
- Price is **48% above the 50-day SMA**, which is past the 35% cap. It is also 8% above the 10-day EMA (9.96).
- History at this level of extension is poor. In the uptrend regime, when price was more than 35% above the SMA50, the median 20-day forward return was -4% and only 28% of those cases rose. Biotech after a 5x rally also carries a real risk of a dilutive offering.
- **Trigger to watch:** buy a CALL when the close is ≤ 1.03 × EMA10 and ≤ 1.35 × SMA50 while the trend filter still holds. At today's levels that means a close at or below about **$9.84**. The level rises daily as the averages catch up.

## Rules (mechanical, checked at the daily close)
1. **Regime.** Fit a linear regression to the last 65 daily log closes (13 weeks).
   - **UP:** slope > 0, R² ≥ 0.60, close > SMA50.
   - **DOWN:** slope < 0, R² ≥ 0.60, close < SMA50.
   - Anything else: **stand aside.**
2. **Entry (pullback, not breakout).**
   - **CALL:** in UP, when the close is no more than 3% above the 10-day EMA.
   - **PUT:** in DOWN, when the close is no more than 3% below the 10-day EMA (a bounce into resistance).
   - Skip either side if price is more than 35% away from the SMA50 (too extended).
3. **Contract.** Nearest-to-ATM strike, about 45 DTE. Use the **monthly** expiry: weeklies are nearly untraded, with bid/ask of 0.60/2.80.
4. **Size.** The premium paid is 5% of the account. The premium is the whole risk.
5. **Exit.** Take profit at +100% on the premium, or exit after 20 trading days (time stop). One position at a time.
   - There is **no premium stop-loss**. In testing, -50% premium stops and "close crosses SMA50" exits were whipsawed by overnight gaps and made results worse in-sample.
   - The `stop` price that `signal()` returns is only a level for discretionary review.

## Options reality check (IBKR, 2026-09-24)
| Contract (Nov 20 '26, 57 DTE) | Bid / Ask | Spread % of mid | OI | Mid IV |
|---|---|---|---|---|
| 10 C | 1.75 / 2.05 | 16% | 1,187 | 92% |
| 12.5 C | 0.80 / 1.05 | 27% | 1,055 | 91% |
| 10 P | 1.05 / 1.40 | 29% | 107 | 92% |
| Oct 30 weekly 10.5 C / 11 C | 0.75/1.40, 0.60/2.80 | 60–130% | 70 / 4 | – |

- Underlying averages about 13.3k calls and 2.8k puts per day.
- IV is 83%, against 30-day HV of 71% (IV/HV about 1.2–1.3). The IV percentile is low (6% on 52 weeks).
- **Modelled round-trip cost:** 15% of premium for calls and 20% for puts. This assumes mid-ish limit fills on monthlies. Puts are thinner.

## Behaviour study (5 years)
- **Two regimes.**
  - 2021–2025: a long downtrend from $26 to a low of $1.64 in May 2025. HV20 averaged 80–100%.
  - 2026: a clean uptrend from $2.2 to $10.75.
- Daily-bar split of the regime filter: UP 124 days, DOWN 348, stand-aside 653.
- **Gaps.** There were 21 opening gaps larger than 10% and 9 larger than 20%. Examples: -66% in May 2022, -49% in May 2025, +32% in Aug 2026. There were 25 days with moves above 15%. The stock is news-driven.
- **Trend persistence is asymmetric.**
  - DOWN regime: 60% of 20-day forward returns were negative (median -6%).
  - UP regime: only 44% were positive (median +1.4%). Rallies are spiky, and gains come from a few gap days.
- **Pullbacks in uptrends.** The median drawdown from the 20-day high was -8.6%. The largest in the 2026 rally was -39%.
  - 57% of ATM calls bought on UP-regime days would have hit a -50% premium stop within 20 days. This is why the strategy uses no premium stop.
- The naive "always follow the 13-week trend" rule gets whipsawed badly. See the baseline rows below.

## Backtest
- **Pricing.** Black-Scholes through `common.option_trade_return`. Vol = HV20 × 1.2 (floor 50%), held constant, so **IV crush is not modelled**. Cost is 15% (call) or 20% (put) of premium.
- **Sizing.** 5% of equity in premium per trade.
- **Split.** In-sample: 2021-09 to 2025-03-25 (70%). Out-of-sample: 2025-03-26 to 2026-09-24.
- **Parameter search.** A small grid was checked on in-sample data only.
- **Baseline.** Every 21 trading days, buy a 45-DTE ATM call if the 13-week slope is > 0, otherwise a put. Hold 21 days.

| Period | System | Trades (C/P) | Win % | Avg ret | Median ret | Compounded (5% risk) | Max DD | Longest losing streak |
|---|---|---|---|---|---|---|---|---|
| In-sample | **Strategy** | 20 (5/15) | 40% | +8.7% | -26% | **+6.7%** | -15.7% | 4 |
| In-sample | Baseline | 34 (15/19) | 18% | -22.6% | -75% | -38.2% | -46.1% | 9 |
| Out-of-sample | **Strategy** | 6 (2/4) | 50% | +28.8% | +19% | **+8.1%** | -7.6% | 2 |
| Out-of-sample | Baseline | 18 (12/6) | 33% | +8.2% | -39% | +4.7% | -16.0% | 4 |
| Full 5y | Strategy | 25 (7/18) | 44% | +14.5% | -26% | +16.4% | -15.7% | 4 |

Out-of-sample trades:
- PUT 2025-03-24: -17%.
- PUT 2025-04-23: +165% (the -49% gap).
- PUT 2025-06-03: -54%.
- PUT 2025-07-03: -100%.
- CALL 2026-07-24: +88%.
- CALL 2026-09-10: +90%.

**Sensitivity** (average return per trade, in-sample / out-of-sample):
| IV/HV | Spread 10/15% | Spread 15/20% | Spread 25/30% |
|---|---|---|---|
| 1.0 | +19% / +48% | +15% / +44% | +6% / +35% |
| 1.2 | +13% / +33% | +9% / +29% | 0% / +20% |
| 1.4 | -3% / +27% | -7% / +22% | -15% / +14% |

Grid robustness:
- Out-of-sample was positive for every variant tested.
- In-sample was negative for about 40% of variants, especially when entries were required right at the EMA10 (pb = 0) or when a tight stop was used.

## Honest assessment and key risks
- **The edge is weak and statistically insignificant.** There are 25 trades in 5 years, and the t-stat of the average return is about 0.7. Profits come from a handful of +90–165% trades, and the median trade loses. The main value of the rules is **avoiding the baseline's heavy bleed** (-38% in-sample): it trades less, and only on clean trends and pullbacks.
- **Out-of-sample has only 6 trades.** Treat the +8% as "did not fail", not as proof.
- **Binary and dilution risk.** Overnight gaps of 30–65% happen. A long option caps the loss at the premium, but it can go to zero overnight. Offerings are likely after big rallies, which is exactly today's setup.
- **Pricing is modelled, not real.** Real IV spikes before catalysts and collapses after them. Put liquidity is thin (OI of about 100), so real fills may be worse than modelled.
- **Low trade frequency.** Most of the time the answer is NONE.

## Files
- `strategies/IOVA.py`: `signal(df)`.
- `strategies/IOVA_backtest.py`: reproducible backtest. Run it with `python3 strategies/IOVA_backtest.py`.
- `data/IOVA_daily.csv`, `data/IOVA_weekly.csv`.

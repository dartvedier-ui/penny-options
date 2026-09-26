# VXX — long-put trend strategy (research 2026-09-24)

**Today's signal: PUT** (strength 0.74). VXX 17.53, 13-wk slope −2.3%/wk, close < 20d MA (17.99), 5-day −1.1%, no spike under way.
Suggested contract: ~60–90 DTE put about 8–10% in the money, e.g. **Nov-20-2026 19P** (bid/ask 2.49/3.00, IV ~69%) or **Dec-18-2026 19P** (2.62/3.25, IV ~64%). The ITM quotes are wide, so work a limit order near mid. Model exit levels: target ≈ VXX 13.5 (+100% on the option), stop ≈ VXX 21.6 (−70%), otherwise exit after 40 trading days (~20 Nov 2026).

## Data
- IBKR daily bars 2021-09-27 → 2026-09-24 (1,254 rows) and weekly bars (261 rows). Split-adjusted for the 1:4 reverse splits on 2023-03-07 and 2024-07-24; no jumps at those dates. Last close 17.53 matches the live snapshot (17.52).
- Cleaning: a bad print (high 666.40 on 2022-03-15) was capped; ~30 bars where close sat a few cents outside the high/low were clipped.

## Behaviour (5 years)
- Drift about −63%/yr (log), or about −47%/yr compounded; it fell every calendar year. Annualised vol is 65%.
- Forward returns are negative 64% of the time over 5 days, 67% over 21 days and 71% over 42 days. The median 21-day move is −6.3%.
- **Spikes:** 26 days of +10% or more; 42 opening gaps above +5%. From any given day, VXX rallied more than 15% at some point in the next 30 days **30% of the time**, and more than 25% 17% of the time. That is what wipes out naive short-dated ATM puts.
- After a 5-day gain of more than 15%, VXX was lower 10 days later 88% of the time (mean −16%). A "fade the spike" put still lost money in the backtest, because the modelled IV is very high at those moments.
- Moving averages: being above the 20d/50d MA does **not** predict a rise (forward 21-day returns are more negative when above). There is no usable call signal.

## Options reality check (live, 2026-09-24)
| Contract | Bid/Ask | Spread % of mid | OI | IV |
|---|---|---|---|---|
| Nov-20 17P (ATM) | 1.26/1.36 | 7.6% | 371 | 61% |
| Nov-20 18P | 1.87/2.05 | 9.2% | 848 | 64% |
| Nov-20 19P (8% ITM) | 2.49/3.00 | 18.6% | 261 | 69% |
| Dec-18 19P (8% ITM) | 2.62/3.25 | 21% | 236 | 64% |
| Nov-20 18C | 1.53/1.75 | 13% | 1,923 | 64% |
| Oct-30 17P | 0.80/0.98 | 20% | 624 | 55% |

Monthly expiries plus weeklies exist. Underlying IV is ~53% against 30-day HV of 31%, so IV runs about 1.7× realised vol right now.
Backtest cost assumption: **12% round trip for puts** (reachable only with mid-price limit orders) and 15% for calls. Crossing the full spread on ITM strikes costs about 20%; see the sensitivity section.

## Rules
1. **Only puts.** Calls never showed an edge (breakout calls in-sample: 7 trades, 14% win rate, avg −58%).
2. **Entry (PUT):** all three must hold at the daily close:
   - the 13-week (65-day) log-price regression slope is negative;
   - the close is below the 20-day SMA;
   - no spike is under way: 5-day return ≤ +5%, and the 10-day high is not more than 15% above the 50-day SMA.
3. **Contract:** about 90 DTE (60–90 is acceptable), strike about 10% in the money (strike ≈ 1.10 × spot). ITM and long-dated keeps theta and vega small compared with the −5%/month drift.
4. **Exit:** +100% option gain (target), −70% option loss (disaster stop; gaps can make it worse), or 40 trading days, whichever comes first. Hold one position at a time and re-check the entry the next day.
5. **Otherwise stand aside.** Size each trade at 5% of the account in premium.

## Backtest
Pricing uses Black-Scholes (`common.bs_price`) with IV = max(1.3×HV20, 55%), capped at 120%, re-marked daily so IV rises in spikes. Put spread is 12%. The split is 70/30 by bars. Run `python3 strategies/VXX_backtest.py`.

| Set | Strategy | Trades | Win % | Avg | Median | Total (5%/trade) | Max DD | Longest losing streak |
|---|---|---|---|---|---|---|---|---|
| IS 2021-09→2025-03 | **VXX rules** | 17 | 59% | +0.5% | +8.2% | **−0.2%** | −8.4% | 2 |
| IS | Fixed-vol (option_trade_return style) | 17 | 53% | −7.5% | +7.5% | −6.8% | −11.6% | 3 |
| IS | Baseline: always follow 13-wk trend (same option structure) | 21 | 43% | −3.0% | −5.3% | −4.0% | −13.7% | 4 |
| OOS 2025-03→2026-09 | **VXX rules** | 7 | 71% | +13.6% | +14.6% | **+4.6%** | −4.5% | 2 |
| OOS | Fixed-vol | 7 | 57% | +16.3% | +20.8% | +5.6% | −4.7% | 3 |
| OOS | Baseline 13-wk trend | 10 | 50% | −15.8% | −10.7% | −8.1% | −13.9% | 3 |
| ALL | **VXX rules** | 24 | 63% | +4.3% | +11.0% | +4.4% | −8.9% | 2 |

The baseline with 45-DTE ATM options and a −50% stop (the first design) was much worse: −50% total over all 5 years.

**Sensitivity:**
- Without the IV cap, IS is +9.7%. That comes from one Aug-2024 trade whose put gained from an IV explosion, which is not reliable.
- With a 20% spread instead of 12%, IS is +2%, OOS +2%.
- With IV floor 75% / multiplier 1.5, IS is +0.3%, OOS +1.6%.
- Across a grid of 60–90 DTE, 10–20% ITM and 30–60-day holds, nearly every variant was slightly positive in both periods. With 45 DTE ATM strikes and a −50% stop, almost every variant lost.

## Assessment
- The only real edge is VXX's structural decay. Long, ITM puts capture it, and entry timing adds little: "enter any time the slope is negative" performed about the same.
- Typical trade: +10–35%. About 1 trade in 8 is a spike loss of −80% to −90% (Jan-2022, Aug-2024, Feb-2025, Mar-2026). These are unavoidable and they set the drawdown.
- Out-of-sample: 7 trades with a positive result, but the sample is tiny. In-sample, the result was roughly breakeven after realistic IV assumptions.
- **Confidence: LOW–MEDIUM.** The direction is highly predictable, but VXX option IV (55–70%) prices most of the decay in. Returns depend heavily on the IV and spread assumptions. Keep size small and use limit orders.

## Key risks
- Volatility spikes (for example, a market sell-off) gap straight through the stop.
- Put IV is already rich.
- ITM strikes have wide spreads and modest OI (a few hundred contracts).
- Rolling and contango regimes can flip. In 2022 the steady decay stalled for months.
- ETN issuer risk and possible further reverse splits (they adjust option contracts).

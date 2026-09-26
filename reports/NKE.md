# NKE (Nike Inc, Class B): long call / long put strategy

*Researched 2026-09-24. Data: IBKR daily bars 2021-09-27 to 2026-09-24 (1,254 bars) in `data/NKE_daily.csv`. Weekly bars (`data/NKE_weekly.csv`, 261) are rebuilt from the daily bars, because IBKR's own weekly bars had misaligned labels before 2024. Last close is 35.77, matching the live snapshot.*

## Bottom line
- **Next earnings:** fiscal Q1 FY27 results come out **Thu 2026-10-01 after the close**, so the price reaction is on **Fri 2026-10-02**. This date is confirmed in Nike's press release.
- **Today's signal: NONE. Stand aside because of the earnings blackout.** The report is 6 trading days away. If you hold the call the model opened on 2026-09-16, sell it at the 2026-10-01 close.
- **After the report:**
  - A gap down that leaves NKE ≥12% below its 50-day average (about 34.9 today; the average is falling) gives a CALL for a snap-back.
  - A gap up into −4%…+3% of the 50-day (about 38.3–41) while the 13-week slope is still negative gives a PUT.
- **Confidence: LOW.** The out-of-sample result is about break-even (+2.2% per trade on 17 trades). Parameter tests show no stable edge.

## Key finding: the downtrend comes from earnings gaps, not the weeks in between
Here is NKE's 15-day forward return when the 15-day window does **not** include an earnings report (912 days):

| Close vs SMA50 | n | mean fwd 15d | % up | IS mean | OOS mean |
|---|---|---|---|---|---|
| ≤ −12% | 118 | **+3.8%** | 78% | +5.5% | +2.0% |
| −12…−8% | 110 | +0.4% | 55% | | |
| −8…−4% | 174 | −0.6% | 51% | | |
| −4…0% | 225 | **−2.8%** | 31% | −2.5% | −3.7% |
| 0…+4% | 133 | **−4.4%** | 20% | −4.0% | −5.4% |
| > +8% | 87 | +1.5% | 62% | | |

- In a downtrend (13-week slope < 0, R² > 0.6), the forward return with no earnings in the window was **+1.9%**, and the price fell only 39% of the time. The classic "sell the bounce to the 10-day average" setup therefore **lost money**: my first version averaged −24% per trade.
- A rally back up to the 50-day average **fails** reliably. A move stretched far below the 50-day **snaps back**.
- This pattern held in both the in-sample and out-of-sample periods.

## Earnings behaviour (19 reports, 2021-12 to 2026-07)
- **Size:** reaction-day moves average **|8.3|%** (median 6.8%). The largest were −20.0% (Jun-24), −15.5% (Apr-26), +15.2% (Jun-25), −12.8% (Sep-22), +12.2% (Dec-22) and −11.8% (Dec-23).
- **Direction:** 63% were down, but the move went **with** the prior 13-week trend only 47% of the time. Direction is a coin flip relative to the trend.
- **The next 10 days:** mixed. After a gap the stock continued about half the time and reversed about half the time. There is no usable post-earnings drift.
- **Priced in now:** the Oct-2 weekly options trade at about 70% IV, versus about 51% for Oct-16 and 45% for Nov-20. The 36-strike straddle costs about 2.97, an implied move of **±8.3%**. That equals the historical average, so the options are fairly priced to slightly rich.
- **Rule:** never hold through earnings. The backtest variant that held through the report (with a modelled IV premium and crush) was worse overall: +1.6% per trade versus +10.3%.

## Options reality check (live, 2026-09-24, spot 35.75)

| Contract | Bid/Ask | Width % of mid | Mid IV | OI |
|---|---|---|---|---|
| Nov-20 35C (57 DTE) | 2.98 / 3.10 | 3.9% | 45.0% | 5,530 |
| Nov-20 35P | 2.00 / 2.04 | 2.0% | 44.0% | 11,673 |
| Oct-16 36C (22 DTE) | 1.72 / 1.76 | 2.3% | 52.0% | 581 |
| Oct-16 36P | 1.88 / 1.94 | 3.1% | 50.8% | 9,548 |
| Oct-02 36C (earnings wk) | 1.37 / 1.39 | 1.4% | 70.4% | 1,678 |
| Oct-02 36P | 1.55 / 1.62 | 4.4% | 68.4% | 3,948 |

- **Round-trip cost:** 2–4% spread plus commissions, so the backtest uses **5%**.
- **Volatility:** IV of the whole chain is 46.8% (IV rank about 77–83%), HV30 is 30.3% and HV20 is 24.2%. With the earnings premium removed, Nov IV is about 38%, which is **about 1.5× HV20**. The backtest assumes 1.2× HV. Options are currently expensive relative to what the backtest assumed.

## Rules (`strategies/NKE.py`)
1. **Trend:** the slope and R² of a 63-day log-price regression. The slope is expressed per week.
2. **PUT:** slope < −0.25%/wk, R² ≥ 0.40, and the close is between −4% and +3% of the SMA50. This fades a rally back into the 50-day average.
3. **CALL:** the close is ≥12% below the SMA50. This buys the snap-back from a stretched level.
4. **Earnings:** no new entry if the next report is fewer than 12 trading days away. Any open option is sold at the close before the reaction day.
5. **Trade:** buy an option about 45 DTE with the strike about 3% in the money. Hold one position at a time. Exit at +100% on the option, −30% on the option (checked at the close), after 15 trading days, or before earnings, whichever comes first.

## Backtest
- **Method:** options are priced with `common.bs_price` / `option_trade_return`, using vol = max(HV20, 15%) × 1.2 and a 5% round-trip cost. The equity figures ("Comp @5%") assume 5% of equity is risked per trade.
- **Split:** in-sample (IS) runs from 2021-12 to 2025-03-25 and out-of-sample (OOS) from 2025-03-26 to 2026-09-24.
- **Parameter choice:** target and stop were chosen as the best **in-sample** cell of a 108-cell grid.

| Variant | Set | Trades | Win | Avg | Median | Comp @5% | Max DD | Lose streak |
|---|---|---|---|---|---|---|---|---|
| **Strategy** | ALL | 39 | 41% | +10.3% | −18.6% | +19.8% | −12.7% | 5 |
| | IS | 22 | 45% | +16.5% | −15.8% | +18.4% | −9.8% | 4 |
| | **OOS** | **17** | **35%** | **+2.2%** | **−26.6%** | **+1.2%** | **−10.8%** | **5** |
| Same rules, hold through earnings | ALL | 43 | 35% | +1.6% | −17.2% | +1.4% | −18.5% | 6 |
| | OOS | 18 | 39% | +3.6% | −17.2% | +2.2% | −10.3% | 4 |
| Baseline: follow the 13-week trend (45 DTE ATM, 15-day hold) | ALL | 75 | 37% | −8.8% | −32.0% | −31.9% | −49.1% | 9 |
| | IS | 51 | 31% | −14.3% | −39.3% | −33.0% | −36.8% | 9 |
| | OOS | 24 | 50% | +2.9% | −1.3% | +1.7% | −19.4% | 8 |
| v1: trend pullback (rejected) | ALL | 27 | 22% | −24.3% | −44.3% | −28.5% | −29.3% | 11 |

**Results by leg:**
- CALLs: IS 9 trades, +21.8% average. OOS 12 trades, **−9.6%**. The Apr-2025 tariff crash and the post-Apr-2026 slide kept extending the stretch.
- PUTs: IS 13 trades, +12.9%. OOS 5 trades, +30.6%.

**Robustness warning:**
- Across the 108-cell grid (target × stop × hold × moneyness), IS and OOS results were **uncorrelated** (ρ ≈ −0.03). The median OOS cell lost −5.5% per trade.
- One-at-a-time sensitivities swing the OOS average between −13% and +11%.
- At IV = 1.4× HV (closer to today's actual pricing) the strategy averages −5% per trade overall.
- The results are highly sensitive to the parameters. Treat the positive in-sample figure as mostly curve fit.

## Risks and caveats
- **Few trades:** 17 OOS trades is statistically weak. Much of the "trend" edge sits in a handful of earnings gaps that this strategy deliberately avoids.
- **Constant IV in the backtest:** IV is held constant from entry to exit, so there is no vega P&L. In reality, buying at IV rank about 80% carries crush risk even outside earnings.
- **Stops fill worse than −30%:** stops are checked at the close, so gap-throughs produced fills of −35% to −88%.
- **Stretched can stay stretched:** in a structural decline like the current one (52-week low, −1.6%/wk slope), "≥12% below the 50-day" can keep extending. The OOS calls failed for exactly this reason.
- **Earnings calendar:** `signal()` needs an up-to-date list (`EARNINGS_REACTION_DAYS`). The Dec-2026 and later dates are projections. Confirm each one when Nike announces it, about 4 weeks ahead.

## Today's signal (`python3 -c "... NKE.signal(common.load('NKE'))"`)
```
action NONE: STAND ASIDE: earnings blackout (trend DOWN). 13w slope −1.61%/wk R² 0.81,
close 35.77 vs SMA10 36.17 / SMA50 39.85 (−10.2%), next earnings reaction in 6 trading days
```

Source for the earnings date: [Nike IR / BusinessWire, "NIKE, Inc. Announces First Quarter Fiscal 2027 Earnings and Conference Call"](https://www.businesswire.com/news/home/20260828161061/en/NIKE-Inc.-Announces-First-Quarter-Fiscal-2027-Earnings-and-Conference-Call)

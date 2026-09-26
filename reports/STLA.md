# STLA (Stellantis) — long-option strategy

*Research date 2026-09-24. Data: IBKR daily bars 2021-09-27 → 2026-09-24 (1,254 bars), plus weekly bars resampled from the daily (261 weeks, week ending Friday). Last close 4.50, which matches the live IBKR snapshot (last 4.50, bid/ask 4.50/4.51).*

## Today's signal: **NONE (for a new position). The trend still points down, but the price is too stretched to sell right now.**
- The 130-day log trend is falling −2.0%/wk with R² 0.78, and the close is below the 50-day SMA (5.40). The trend condition is met.
- But the close is **−12.7% below the 20-day SMA (5.16)**. The rule only buys puts after a bounce to **≥ 5.05** (98% of the SMA20). In a down-trend, a rally of ≥10% within 20 days happened 27% of the time, so waiting for one is part of the plan and doesn't cost much of the trend.
- If you had followed the rule already, the put entered on **2026-09-01 at 5.35** would still be open. It is modelled at about +40%. Keep holding it to +100% or the 60-day time exit (≈ late Nov).
- The level where the trade idea stops working (regression line + 1 sd) is ≈ 5.32. The rough target for the underlying is ≈ 3.5, which is roughly where a new put would double.

## Rules
1. **Trend filter:** fit a log-linear regression to the last 130 daily closes (26 weeks). The filter is met when R² ≥ 0.60, the slope is < 0 and the close is < SMA50.
2. **Entry (PUT):** the trend filter is met **and** the close is ≥ 0.98 × SMA20. That means you buy on a bounce, never after a flush.
3. **Contract:** buy a put about 5% in the money (strike ≈ 1.05 × spot, nearest listed; right now that's the $5 strike), with **~120 DTE** (the monthly 100–130 DTE out, e.g. Jan-27).
4. **Exit:** at +100% on the option, or after 60 trading days, whichever comes first. **There is no option stop.** Size each trade at 5% of the account and treat the whole premium as the risk.
5. **CALLs: disabled.** Up-trends didn't persist. A 26w up-trend with R² > 0.6 was followed by +1.3% over the next 60 days, and was up only 49% of the time. Stand aside at all other times.

## Options reality check (2026-09-24)
| Contract | Bid/Ask | Spread / mid | OI | Mid IV |
|---|---|---|---|---|
| Oct-30 4.5P (36 DTE) | 0.25/0.30 | 18% | 44 | 51% |
| Nov-20 5P (57 DTE) | 0.65/0.70 | 7% | 147 | 53% |
| Nov-20 4C | 0.70/0.80 | 13% | 33 | 60% |
| Jan-15-27 5P (113 DTE) | 0.75/0.80 | 6.5% | 4,794 | 53% |
| Jan-15-27 4C | 0.80/0.95 | 17% | 374 | 56% |

- Monthly expiries list **$1 strikes** near the money, so there's no 4.5 in Nov or Jan. The $0.05 tick is large next to premiums under $1.
- Underlying: IV 47%, 30-day HV 42%, and IV percentile about 28–45%. The backtest models option IV as **1.25 × HV20**.
- Round-trip cost assumed in the backtest: **12% of premium** (full spread plus fees on the Jan 5P). A stress case uses **20%** with IV at 1.4 × HV.

## Behaviour study (2021-09 → 2026-09)
- **Drift:** the stock went from 29.5 (Mar-2024) to 4.50, down 85%. The average 20-day return was −1.5% (sd 11%). By year: 2022 −24%, 2023 +64%, 2024 −44%, 2025 −17%, 2026 YTD −59%.
- **Short-term mean reversion:** the 20-day and 40-day past returns were *negatively* correlated with the next 20 days (−0.09 and −0.08). Momentum only helps from about 65–130 days out. When the price was more than 10% below the SMA20, the next 20 days averaged +2%. When it was more than 5% above, they averaged −3%. So selling after a flush loses and selling rallies works.
- **26-week trend:** the down-trend state (R² > 0.6, slope < 0) was in force 26% of the time. The next 60 days averaged −9% and were down 72% of the time. Bounces inside down-trends were typically +7% within 20 days (p75 10%, p90 14%).
- **Stop-outs:** short-dated (45 DTE ATM) trend puts with a −50% option stop were stopped out on most trades (median trade −64%). Exiting when the close crossed back above the SMA50 also cut win rate to 19%. **Tight stops were the main thing that lost money.**
- **Volatility:** HV20 median 37% (10–90%: 25–55%). Now 42%.
- **Gaps:** 161 opening gaps > 3% and 35 > 5% in 5 years. The largest was **−25% on 2026-02-06** (results and guidance). Others include −12.7% on 2024-09-30 (guidance cut) and −8% to −9% in Apr-2025 (tariffs).
- **Dividend ex-dates** (opening drop not caused by the trend): 2022-04-19 −6.1% (€1.04), 2023-04-24 −7.0% (€1.34), 2024-04-22 −4.5% (€1.55), 2025-04-23 −3.8% (€0.68). IBKR now shows a 0% dividend yield and no 2026 ex-date, which suggests the dividend is suspended. None of the backtest put trades held across an ex-date, so dividends don't inflate the results.

## Backtest
Pricing: Black-Scholes (`common.bs_price`), re-marked daily with the then-current HV20 × 1.25. Entry and exit are at the close, one position at a time. In-sample (IS) is the first 70% of the data, before 2025-03-26. Out-of-sample (OOS) is from 2025-03-26 on. "Comp5" is the compounded return when risking 5% of the account per trade. Reproduce with `python3 strategies/STLA_backtest.py`.

| Strategy | Sample | Trades | Win | Avg | Median | Comp5 | MaxDD | Longest losing streak |
|---|---|---|---|---|---|---|---|---|
| **STLA rule** | IS | 4 | 50% | +22.8% | +24.8% | +4.3% | −3.5% | 1 |
| **STLA rule** | **OOS** | **3** | **67%** | **+33.1%** | **+40.0%** | **+4.9%** | **0.0%** | **1** |
| rule, 20% cost & IV 1.4×HV | IS / OOS | 4 / 3 | 50% / 67% | +7.5% / +9.4% | | +1.2% / +1.4% | | |
| rule with 90 DTE / 40-day hold | IS / OOS | 5 / 4 | 40% / 25% | −15.9% / −24.3% | | −4.2% / −4.9% | | 2 / 3 |
| rule + exit on close > SMA50 | IS / OOS | 8 / 8 | 25% / 12% | −2.4% / −9.8% | | | | 4 / 7 |
| rule with mirror calls on | IS / OOS | 8 / 3 | 50% / 67% | +10.4% / +33.1% | | | | |
| Baseline: sign of the 13w trend, 45 DTE ATM, hold 20d | IS | 39 | 36% | −11.4% | −58.5% | −22.7% | −33.7% | 5 |
| Baseline | OOS | 18 | 33% | −7.5% | −55.9% | −8.8% | −20.8% | 3 |
| Always buy a put, 45 DTE ATM, hold 20d | IS / OOS | 39 / 18 | 33% / 50% | −14.1% / +3.9% | | −24.4% / +1.2% | −45% / −19% | |

Trades from the main rule:

| Entry | Exit | Spot in → out | Days held | Return | Exit reason |
|---|---|---|---|---|---|
| 2022-05-04 | 2022-08-01 | 14.11 → 14.62 | 60 | −52% | time |
| 2024-08-19 | 2024-10-03 | 16.29 → 13.08 | 32 | +102% | target |
| 2024-10-23 | 2025-01-22 | 13.31 → 13.11 | 60 | −70% | time |
| 2025-02-05 | 2025-04-03 | 12.93 → 10.21 | 40 | +111% | target |
| 2025-05-23 | 2025-08-20 | 9.89 → 9.77 | 60 | −37% | time |
| 2026-04-07 | 2026-06-29 | 7.42 → 5.57 | 57 | +97% | target |
| 2026-09-01 | open | 5.35 → 4.50 | 16 | +40% (marked, still open) | — |

## Honest assessment. Confidence: **LOW**
- **Too few trades to prove an edge.** There are only 7 trades in 5 years, with 3 of them OOS, and one of those is still open. A single loss changes the averages a lot.
- **The result depends on the settings.** The same signal with 90 DTE and a 40-day hold loses money in both samples. The edge only shows up when you give the trade a long runway (120 DTE, 60 days) and use no stop. That fits the behaviour study (a slow drift, and bounces that shake out tight stops), but it is still partly a parameter choice.
- **It beats the naive baseline clearly.** The 13-week trend baseline loses −11% per trade in IS and −7.5% in OOS once spreads and IV premium are paid. That is the main finding: **on STLA, short-dated trend-following options lose money.** If you trade it at all, use long-dated, in-the-money puts bought into bounces.
- **Event risk:** tariff headlines, monthly and European registration data, earnings and guidance, and dividend or capital-return decisions. A positive shock such as a tariff relief rally or a restructuring announcement can make the stock gap up 7–10% (for example +10% on 2022-03-09 and +8% on 2025-05-12).
- **Liquidity:** some strikes carry only tens of contracts of open interest. Use limit orders at or near the mid. Only the Jan-27 5P showed meaningful open interest.
- **Mean reversion risk:** after a −59% year to date the stock is at its 52-week low and 13% below the SMA20. Short-term reversals have been the norm, which is exactly why the rule waits for a bounce.

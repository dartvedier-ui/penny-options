# TLT (iShares 20+ Yr Treasury) — long put / long call strategy

*Research date 2026-09-24. Data: IBKR daily bars 2021-09-27 → 2026-09-24 (1,254 rows), weekly bars (262 rows). Prices are not adjusted for distributions. Last close in the file is 79.66, which matches the live snapshot (79.67, bid/ask 79.65/79.67). Code: `strategies/TLT.py`, `strategies/TLT_backtest.py`.*

## Bottom line
- **Momentum timing does not work on TLT.** Over 5 years, the sign of the past 20/40/65/130-day return predicts the next 20–60 days no better than a coin flip (hit rate 49–52%). The correlation is slightly negative (−0.13 to −0.23 at 40–60 days), so returns tend to mean-revert a little. Breakdown entries (a fresh 20-day low inside a downtrend) had almost no follow-through: the next 40 days were down only 48% of the time.
- **What paid was the regime.** Holding in-the-money puts while the 26-week log-trend points down worked. That profit comes from the long bond bear market plus the monthly distribution drops. It is not a timing skill.
- **Calls never worked in this sample.** 6 of 7 call trades lost, and every "up" state was a bull trap. The call leg is **off by default**.
- The edge is **small**: about +3–4% per trade after costs, with a ~46% win rate. It disappears if implied vol stays ~30% above realised vol, which is where it is today.

## Rules (final, puts only by default)
| | Rule |
|---|---|
| Regime | 26-week (130-day) regression slope of log(close) **< 0** |
| Entry filter | Don't chase: z20 = (close − SMA20) / (close·HV20·√(20/252)) must be **≥ −1**. When TLT is stretched below its 20-day mean, stand aside and wait for a bounce. |
| PUT | Regime down AND filter OK → buy a put with **~90 DTE**, strike **~5% ITM** (spot × 1.05) |
| CALL | (disabled) 26-wk and 13-wk slopes > 0 AND close > SMA200 AND z20 ≤ +1 |
| Exit | First of: **+100%** on premium · **−40%** on premium · **40 trading days** (~56 calendar days, so ~35 DTE is left) · regime flips (26-wk slope turns > 0) |
| Re-entry | Next day, if the rule still says PUT |
| Size | 5% of equity in premium per trade |

## Options reality check (2026-09-24, spot 79.67)
| Contract | Bid/Ask | Mid IV | OI | Round-trip spread as % of premium |
|---|---|---|---|---|
| Nov-20-26 80P (57 DTE) | 1.94/1.97 | 13.6% | 18.2k | 1.5% |
| Nov-20-26 82P | 3.20/3.25 | 13.2% | 51.3k | 1.6% |
| Dec-18-26 76P (85 DTE) | 0.89/0.91 | 14.6% | 24.6k | 2.2% |
| Dec-18-26 80P | 2.39/2.42 | 13.4% | 49.9k | 1.2% |
| Dec-18-26 82P | 3.60/3.70 | 13.3% | 43.4k | 2.7% |
| Dec-18-26 84P (≈5% ITM) | 5.10/5.25 | 12.9% | 25.0k | 2.9% |
| Dec-18-26 80C | 1.83/1.86 | 13.4% | 11.9k | 1.6% |
| Dec-18-26 77C | 3.65/3.70 | 14.3% | 0.4k | 1.4% |

Spreads and liquidity are excellent. The backtest uses **4% round-trip**: the spread plus commissions and slippage. Underlying IV is 13.6% against HV30 of 10.9% (IV/HV ≈ 1.25, IV percentile 97% over 52 weeks). The backtest prices options at IV = HV20 × 1.15 (floor 9%) using Black-Scholes-Merton with a 4.5% distribution yield. Plain `common.option_trade_return`, which has no dividend term, flatters puts by ~6 points per trade; it is shown as a cross-check.

## Behaviour study
- **Volatility regime:** HV20 was 17–22% in 2022–23, 13–15% in 2024–25, and is ~9–10% in 2026. The slow grind means a 90-DTE ATM option costs ~2.3% of spot, while the 20-day drift is only ~0.8%. Time decay beats the trend unless the option is ITM and held for weeks.
- **Counter-trend rallies are large.** Examples: +11% (Oct–Dec 2022), +19% (Oct–Dec 2023), +9% (Apr–Aug 2024). Most stop-outs happened in these rallies (12 of 28 exits hit the −40% stop).
- **Moving averages:** the "close < SMA50 < SMA200" state was followed by *smaller* declines (−0.3% per 20 days) than the unconditional drift (−0.8%). The biggest declines started from rallies *above* the SMA200 (−1.5% per 20 days, 71% down).
- **Macro events:** jobs-report Fridays average |move| 1.01% vs 0.76% on other days (+33%). FOMC days average 0.80%, about normal on the day, but the post-FOMC press conference and dot-plot days drive trend changes. Largest z-moves: 2022-03-02, 2024-08-02 (weak NFP, +3.1%), 2024-11-06 (election, −2.8%), 2025-04-07 (tariff shock, −3.1%).
- **Distributions:** ex-date is around the first business day of each month (~$0.30, ~0.4%). This helps puts and hurts calls.

## Backtest — same option config for all rules (90 DTE, 5% ITM, +100% / −40%, 40-day max, 4% cost)
IS = 2022-07 → 2025-02 (after a 200-day warm-up); OOS = 2025-03 → 2026-09.

| Strategy | Period | Trades | Win % | Avg % | Median % | Compounded @5% risk | Max DD | Longest losing streak |
|---|---|---|---|---|---|---|---|---|
| **Final (puts only)** | IS | 19 | 42% | +3.2% | −44% | +2.2% | −8.9% | 3 |
| **Final (puts only)** | **OOS** | **10** | **50%** | **+3.4%** | **+2.6%** | **+1.6%** | **−5.5%** | **3** |
| Final (puts only) | ALL | 28 | 46% | +4.4% | −6% | +5.2% | −10.9% | 3 |
| Final with call leg | ALL | 35 | 40% | −4.0% | −39% | −7.9% | −20% | 3 |
| Naive 13-wk trend (baseline) | IS | 26 | 31% | −14.5% | −44% | −17.9% | −24% | 6 |
| Naive 13-wk trend (baseline) | OOS | 14 | 29% | −21.3% | −45% | −14.1% | −16% | 4 |
| Always hold a put | ALL | 33 | 49% | +3.8% | −4% | +5.2% | −11% | 4 |
| MA-stack trend (rejected) | ALL | 28 | 36% | −6.5% | −38% | −9.6% | −18% | 4 |
| Breakdown to 20-day low (rejected) | ALL | 19 | 42% | −6.7% | −29% | −6.7% | −13% | 4 |

**Robustness:** across 36 option configs (DTE 60/90/120 × moneyness 0/3/5/8% × three target/stop pairs), 35 of 36 had a positive average for the full period. Most configs also stayed positive out of sample, but all of them are small (+1% to +6% per trade).

**Cost and IV sensitivity (full period):**

| IV/HV | Spread | Avg per trade |
|---|---|---|
| 1.00 | 3% | +8.4% |
| 1.15 | 6% | +2.4% |
| 1.30 | 3% | +2.6% |
| 1.30 | 6% | **−0.4%** |

The rule is essentially "always own a put, minus the worst chasing entries". It adds little over the always-put baseline. The honest conclusion: **the edge is the bond bear market itself, not the timing.**

## Risks
1. **Regime risk (the main one).** Five years of data cover a single secular bond bear market. A dovish Fed pivot, a recession scare or a flight to quality (Aug 2024, Nov–Dec 2023) can rally TLT 10–20% within weeks. The 26-week slope reacts slowly, so the rule will keep buying puts into the first part of such a turn.
2. **Expensive options now.** IV rank is ~97% and IV/HV ≈ 1.25–1.35. At that ratio the backtested edge is roughly zero. A long put also carries vega risk: if IV mean-reverts from 13.6% toward 11%, a 90-DTE put loses about 8–10% of its value even if the price stays flat.
3. **Low win rate with −40% stops.** Expect runs of 3 stop-outs in a row.
4. **Small sample:** 28 trades, 10 of them OOS. The confidence interval easily includes zero.

## Macro events: do not open new positions the day before, and expect gaps through them
- **CPI** (~10th–15th of the month) and **PCE** (end of month)
- **Nonfarm payrolls** (first Friday): the biggest average move of any day type
- **FOMC** decision, press conference and dot plot (next: 2026-10-28, 2026-12-09)
- **Treasury refunding** announcement (early Nov) and **10-yr / 30-yr auctions** (2nd week of the month)
- Month-end index extension and the **distribution ex-date** (~1st business day, which favours puts)
- Tight stops are hit most often on these days. The −40% stop is judged on the **close**, not intraday.

## Today's signal (2026-09-24)
`TLT.signal(common.load('TLT'))` → **PUT**, strength 0.34

- **Regime:** 26-week slope −0.27%/wk, 13-week slope −0.49%/wk (down).
- **Entry filter:** z20 = −0.86, so TLT is not yet over-extended.
- **Suggested contract:** the Dec-18-26 84P (85 DTE, ~5% ITM) at about 5.10/5.25. A cheaper alternative is the 82P at 3.60/3.70.
- **Approximate underlying exit levels** (two weeks out): stop if TLT closes above **~82.0**; +100% target near **~74.6**. Otherwise hold 40 trading days or until the 26-week slope turns up.
- **Caveats:**
  - TLT has already broken its 52-week low, and fresh-low entries had poor follow-through.
  - IV is at its 97th percentile.
  - Consider **half size**, or waiting for a bounce toward SMA20 (~81.6) for a better entry.
  - Avoid opening right before the next CPI (mid-October) or payrolls (2026-10-02).

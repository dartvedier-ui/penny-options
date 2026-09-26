# SURG (SurgePays Inc, NASDAQ): long call / long put study, 2026-09-24

## Verdict: NOT OPTION-TRADEABLE

The options chain was checked live through IBKR on 2026-09-24. The stock was at $0.1495 (bid 0.1471, ask 0.1498).

| Item | Finding |
|---|---|
| Expiries listed | Oct 16 2026 (22 DTE), Nov 20 2026 (57 DTE), Feb 19 2027, May 21 2027 |
| Lowest strike | **$0.50**, which is 3.4x spot. Strikes run 0.5, 1, 1.5, 2, 2.5 and none are near the money |
| Nov 20 0.50 put | bid 0.30 / ask 0.50, last 0.36, OI 2, volume 0 (mid IV ~419%) |
| Oct 16 0.50 put | bid 0.30 / ask 0.45, OI 4, volume 0 |
| Nov 20 0.50 call | no bid / ask 0.05, OI 1,332, volume 0 |
| Oct 16 0.50 call | no bid / ask 0.05, OI 27 |
| Underlying | 30d HV ~260%, implied vol ~509%, avg option volume ~580 calls / ~380 puts per day |

The only put anyone could buy is the deep-ITM $0.50 put. Its most it can ever be worth is $0.50, and that only happens if SURG goes to $0. At the 0.50 ask the trade has **zero upside**. At mid (~0.40) the most it can make is +25%, and only if the stock goes to zero. The calls need a >240% rally just to reach the strike. **Use the signal below only as a stock-direction signal.** Shorting SURG stock is also hard: it trades under $1 and is likely hard-to-borrow.

## Data
- Daily: `data/SURG_daily.csv`, 501 bars, 2024-09-25 to 2026-09-24 (IBKR, RTH). The last close of 0.1495 matches the live snapshot.
- Weekly: `data/SURG_weekly.csv`, 262 bars, 2021-09-27 to 2026-09-21. IBKR reports a split dated 2021-11-02 (factor 0.02). The daily window has **no corporate actions**, so the backtest window is clean.

## Behaviour
- The stock fell from $1.56 to $0.15 (-90%) over the 2 years. It rallied to ~$3.4 in Mar–Jul 2025, then declined steadily.
- Daily realised vol: 115% annualised over the full window, 163% over the last 60 days. There were 43 days with a move of more than 10% and 12 days with more than 20%. 17 opening gaps exceeded 10%.
- Spikes on promotions and news are frequent and violent: +53% on 2025-03-26, +32% on 2026-07-02 (122M shares), +37% on 2026-08-06 (100M shares). They mostly fade within days. Losses also come in sharp gaps: -44% on 2026-01-21, -41% on 2026-04-15, -34% on 2026-08-20.
- Trend persistence: when the 65-day slope is negative, the 20-day forward return is down 72% of the time (median -14%). But the whole sample is a downtrend, so bullish states also fell (66% of the time). Daily return autocorrelation is -0.08, a mild mean reversion.
- **Stop-out risk:** on the 201 days with a put signal, the stock traded **+20% above entry within 20 days 50% of the time**, and +40% above 24% of the time. The stock ended lower 79% of the time, but the average 20-day move was only -5.1% because of the spikes.

## Rules (`strategies/SURG.py`)
- **PUT:** close < SMA20 < SMA50, 65-day log-price regression slope < 0, and no +25% daily spike in the last 3 sessions.
- **CALL:** close > SMA20 > SMA50 and slope > 0. This fired only in 2025 and every call lost.
- **Option plan (hypothetical):** ATM strike, 45 DTE. Take profit at +60% on premium, stop at -50% on premium, maximum hold 20 trading days, one position at a time.
- **Stand aside** otherwise. In practice, stand aside on options regardless of signal, because no near-the-money strikes exist.

## Backtest (`strategies/SURG_backtest.py`)
- Pricing: Black-Scholes, with IV = 1.7 x 20-day realised vol. The live option IV is 4.2–4.9 against HV of 2.6.
- Round-trip cost: 30% of premium. The live quotes are 0.30 x 0.50, which is 50% of mid, so this assumption is generous.
- Split: in-sample is the 70% of bars before 2026-02-19, out-of-sample is the 30% after.

| Set | Trades | Win % | Avg ret | Median | Compounded @5% risk | Max DD | Longest losing streak |
|---|---|---|---|---|---|---|---|
| Strategy IS | 13 | 8% | -59% | -66% | -32% | -32% | 10 |
| **Strategy OOS** | 8 (all puts) | 12% | -35% | -32% | -13% | -13% | 6 |
| Baseline 13-wk trend IS | 22 | 23% | -53% | -83% | -44% | -45% | 6 |
| Baseline 13-wk trend OOS | 10 | 10% | -53% | -58% | -24% | -24% | 6 |

Cost sensitivity, out-of-sample:

| Spread | IV/HV multiplier | Win % | Avg ret |
|---|---|---|---|
| 15% | 1.3 | 30% | -36% |
| 50% | 2.0 | 0% | -66% |

Changing the exits did not help. A 60-DTE / 40-day hold with no stop still lost -3% on average out-of-sample (4 trades) and -64% over the full window. A short 30-DTE / 10-day version lost -45%.

**As a stock-direction signal** (gain if the stock moved the right way from entry to exit):

| Set | Win % | Avg | Median |
|---|---|---|---|
| In-sample | 54% | -7.7% | +1.1% |
| Out-of-sample | 75% | +13.4% | +17.3% |

The direction was right out-of-sample, but paying 150–280% implied vol plus a wide spread cost more than the drift of about -6.5% a week delivered.

## Risks
- **Delisting / reverse split:** the stock has been under $1 since about Jan 2026, so a Nasdaq minimum-bid deficiency and a reverse split are likely. A reverse split creates adjusted, non-standard option deliverables (illiquid, hard to price) and a break in the price series. Reverse splits in penny names often lead to sharp moves in either direction.
- **Promotion spikes:** a +30–50% day can occur on 100M+ shares with no warning. Stops on the underlying will gap.
- **Liquidity:** OI is at most a few thousand contracts, concentrated in worthless calls, with zero daily option volume. You may not be able to exit.
- **Sample bias:** there are only 2 clean years, and almost all of it is a one-way decline. The regression R² reflects that decline, not a repeatable edge.

## Today's signal (2026-09-24)
`PUT` (strength 0.21, discounted for non-tradeability). Entry is 0.1495, the stock-level stop is 0.1756 and the target is 0.1234. Close 0.1495 < SMA20 0.1613 < SMA50 0.2143, and the 65-day trend is -8.6%/wk.
**Action: NONE on options.** No usable strike exists. The trend is down, but it cannot be expressed through long options at a positive expected value.

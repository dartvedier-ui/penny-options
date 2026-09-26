# OPEN (Opendoor Technologies): long put / long call trend strategy

*Built 2026-09-24. Data: IBKR weekly bars from Sep 2021 to Sep 2026 (261 weeks) and daily bars from Sep 2024 to Sep 2026 (501 days). The two sets cross-check: 97 overlapping weekly closes, 0 mismatches. The last close of $2.555 matches the live snapshot (bid 2.55 / ask 2.56).*

## Today's signal: **NONE (stand aside, but be ready to buy a PUT)**
- 13-week log-price trend: **−5.4%/week, R² 0.96**. This is a clean downtrend.
- Price is **−21.6% below its 10-week SMA** ($3.26). That is past the −20% "don't chase" limit.
- Trigger: a PUT fires if this Friday's weekly close is **≥ about $2.61** while the trend stays intact. That is a small bounce, which moves price back to within 20% of the SMA. The SMA is falling, so the trigger level drops a little each week.
- If it triggers, buy a ~60-DTE ATM put. Today that would be the **Nov 20 '26 $3P** or a nearer strike. The Nov monthly only lists $2/$3/$4 strikes. The weekly Oct 30 expiry has $0.50 strikes.

## Rules (evaluated once a week on the weekly close)
1. **Trend filter:** Fit an OLS line to ln(close) over the last 13 weekly closes. The trend counts only if |slope| ≥ 1.5%/week and R² ≥ 0.60.
2. **PUT:** Buy when the slope is negative, the close is below the 10-week SMA, and the close is **no more than 20% below** that SMA. The last condition keeps you from shorting a capitulation low, which on this stock is where squeezes start.
3. **CALL:** The mirror rule. Slope positive, close above the 10-week SMA, and no more than 20% above it.
4. **Otherwise stand aside.**
5. **Option:** At the money, about 60 calendar days to expiry.
6. **Exits:** Sell at **+200%** on premium, at **−50%** on premium (checked against intraweek extremes), or after **6 weeks**, whichever comes first. You may re-enter at the next weekly close if the signal is still on.
7. **Size:** The premium paid is 5% of the account.

## Options reality check (2026-09-24)
| Contract | Bid/Ask | Mid IV | OI |
|---|---|---|---|
| Oct 30 $2.5 P | 0.19 / 0.21 | 73% | 974 |
| Oct 30 $2.5 C | 0.26 / 0.27 | 72% | 261 |
| Oct 30 $3 C | 0.10 / 0.11 | 77% | 2,466 |
| Nov 20 $3 P | 0.64 / 0.68 | 95% | 2,910 |
| Nov 20 $3 C | 0.23 / 0.24 | 96% | 8,228 |
| Nov 20 $2 P | 0.10 / 0.16 | 96% | 2,310 (avoid: 46% wide) |

- The underlying's IV is 70% and its 30-day HV is 61%, so IV/HV ≈ 1.15. The 52-week IV percentile is 6%.
- Nov IV is about 95%, most likely because early-November earnings fall inside that expiry. Expect IV to be crushed after the print.
- The bid/ask width on near-ATM contracts is 4–10% of premium. Commissions add a few percent more on premiums of $20–70 per contract.
- **The backtest uses a 15% round-trip cost.**

## Behaviour study (5 years of weekly bars)
- **Secular decline with violent squeezes.** The stock fell from $24 to $0.51 (2021 to Jun 2025), squeezed about 20× to $10.87 (Jul–Sep 2025), then fell again to $2.55.
- There were 9 weeks with a gain above +30%. Four were in 2023 and five in Jul–Sep 2025.
- In the last 2 years there were 18 days up more than 15% and 6 days down more than 15%. The right tail is fatter than the left, which is bad for puts.
- Realised vol is about 108% annualised on weekly returns. Recently, 10-week HV is 40–60%.
- **Forward returns after a 13-week downtrend (1.5–4%/week):** the median 8-week return is −18%.
- **After a steep downtrend (more than 4%/week):** the median 4-week return is −12%, but the mean is +4% because of squeeze tails.
- **When price is more than 20% below the 10-week SMA,** the 8-week mean is +5% and the median −5%. The drift is gone and squeeze risk is high. This is why the strategy stands aside at stretched lows.
- **When price is 0–20% below the SMA,** the 8-week median is −20% to −21%. This is the best place to own puts.
- With a tight −50% stop, the stop fires quickly. In the first design (target +60%, 4-week hold), about half of all put entries were stopped out, mostly within 1–2 weeks. Taking profits early lost money after costs. Letting winners run is what makes the strategy work.

## Backtest (weekly bars, Black-Scholes, vol = 10-week HV × 1.15, clipped to 50–200%, 15% round-trip cost)
In-sample runs from Dec 2021 to Mar 2025 (first 70% of the data). Out-of-sample runs from Mar 2025 to Sep 2026 and includes the 2025 squeeze.

| | Trades (P/C) | Win % | Avg % | Median % | Total return (5% risk) | Max DD | Longest losing streak |
|---|---|---|---|---|---|---|---|
| **Strategy, in-sample** | 14 (13/1) | 50.0 | +12.7 | −31.2 | **+7.8%** | −10.5% | 3 |
| **Strategy, out-of-sample** | 6 (5/1) | 50.0 | +45.2 | +15.6 | **+13.3%** | −9.4% | 3 |
| Strategy, all | 20 (18/2) | 50.0 | +22.5 | −31.2 | +22.1% | −10.5% | 3 |
| Baseline (always follow 13-week slope sign, ATM, hold 4–6 weeks), in-sample | 29 | 41.4 | +0.4 | −12.8 | −2.1% | −27.5% | 5 |
| Baseline, out-of-sample | 13 | 53.8 | +0.2 | +6.5 | −1.4% | −17.2% | 3 |

- Puts only: 18 trades, 56% wins, average +32%. Calls: 2 trades, both stopped out (−65% each after costs). **The call leg is unproven.**
- **Sensitivity:** Across slope thresholds of 1.0–2.5%/week and stretch caps of 15–30%, 8 of 9 in-sample cells and 9 of 9 out-of-sample cells were positive. The one exception was in-sample at the 15% cap, which was −0.2%.
- **Parameter search (disclosed):** I tested 144 exit/filter variants. 78% were positive in-sample and 67% out-of-sample, but the correlation between in-sample and out-of-sample results was only 0.24.
- **How the final exits were chosen:** DTE = 60 was fixed in advance so a 6-week hold stays out of expiry week. Target (+200%) and hold (6 weeks) were then picked because they had the best in-sample result at 60 DTE. The first design (target +60%, 4-week hold) lost money: −12% in-sample and +1% out-of-sample.
- **The honest read:** the edge comes from a handful of big put winners (+185%, +141%, +112%) during persistent downtrends. The sample is small (20 trades), so the confidence interval is wide.

## Key risks
- **Squeeze risk.** OPEN is a meme/retail name. The Jul 2025 move was about 20× in 10 weeks. A put held through that kind of move goes to zero. The −50% stop assumes you can exit, and a gap can go straight through it (the backtest charges gap fills at the open).
- **Earnings and IV.** Nov expiries carry about 95% IV into earnings. Buying before the print and holding through the crush hurts even when the direction is right. Prefer an expiry that avoids the print, or accept that the model understates the cost.
- **Small sample and weekly resolution.** Stops and targets are checked on weekly high/low, with stop assumed first when both are touched, and the model assumes a constant IV. Real fills on $0.10–0.25 options move in $0.01 ticks, which is 4–10% per tick.
- **Coarse strikes.** Monthly expiries only list $1 strikes near $2.55. Use the weekly expiries with $0.50 strikes to stay near the money.
- **Low price.** Nasdaq listing rules and a reverse split could change contract terms.

## Files
- Strategy: `/home/user/trading/strategies/OPEN.py` (`signal(df)`)
- Backtest: `/home/user/trading/strategies/OPEN_backtest.py` (`python3 strategies/OPEN_backtest.py`)
- Data: `/home/user/trading/data/OPEN_daily.csv`, `/home/user/trading/data/OPEN_weekly.csv` (raw IBKR JSON in `data/raw/`)

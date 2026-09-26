# FNGR (FingerMotion) — long call / long put study

**Verdict: NOT OPTION-TRADEABLE. Today's signal: NONE.** Confidence in the verdict: high. Confidence in any options edge: low (the backtest shows none).

## 1. Can you actually trade the options? (IBKR, checked 2026-09-24)
Stock: last $0.1452 (bid 0.1450 / ask 0.1452), 27M shares today. 30-day HV 303%, underlying IV 203%. Average option volume about 460 calls and 75 puts a day, almost all of it in the $1 calls, which trade as lottery tickets.

| Expiry (DTE) | Listed strikes ≤ $1.50 | $1 call | $1 put |
|---|---|---|---|
| 16 Oct 26 (22) | $1 only | no bid / 0.05 ask, OI 2,839 | 0.85 / 0.95, OI 21 (≈ intrinsic 0.855) |
| 20 Nov 26 (57) | $1 only | no bid / 0.05 ask, OI 3,237 | 0.85 / 1.45, OI 55 |
| 15 Jan 27 (113) | $0.50, $1, $1.50 | — | — |

- The nearest strike is **$1.00, 590% above spot** ($0.50 from Jan-27 onwards). No contract is near the money.
- The $1 put is a deep-ITM, stock-like position with a wide spread. Its bid sits below intrinsic value. It gives no leverage and no convexity.
- The $1 call needs the stock to go up 7× before expiry, so it is a pure lottery ticket.
- No new lower strikes are likely to be listed while the stock stays under $1.

## 2. Data
- `data/FNGR_daily.csv`: 501 daily bars from 2024-09-25 to 2026-09-24 (IBKR, RTH, 2 years).
- `data/FNGR_weekly.csv`: 262 weekly bars from 2021-09-27 to 2026-09-21 (5 years).
- The last close, 0.1452, matches the live snapshot. Weekly and daily closes agree in all 97 overlapping weeks.
- IBKR reported no corporate actions and the data shows no reverse split in 5 years.
- Six daily bars had a close marginally outside the high/low range (closing-auction prints). I clipped high and low to contain open and close.

## 3. Behaviour (5-year weekly)
- **Trend persistence is weak.** Weekly return autocorrelation is 0.05, and 0.12 for 4-week returns.
- The stock spent 69% of weeks below its 10-week MA. Median 6-week return overall is −8% (log), and 65% of 6-week windows were negative.
- **The squeezes are violent:**
  - Sep–Oct 2022: $0.66 to $7.38 in 2 weeks, with a weekly high 5.7× the prior close.
  - Jun–Jul 2023: $1.32 to $5.70.
  - Mar 2025: $1.30 to $4.57.
  - Aug 2026: an intraday spike to $0.71 on 906M shares, from $0.17.
  - Ten weeks gained more than 30%; only four fell more than 30%.
- **Put stop-outs are frequent.** In strong-downtrend weeks (13-week slope below −3%/wk and R² above 0.6):
  - Median 6-week return was −15%.
  - **46% of the time the price rallied more than 25% above entry within 6 weeks.** A put with a +25% stop is stopped out about half the time.
- **Stretched lows bounce.** When the close was more than 30% below the 10-week MA, the next 4 weeks had a median of +4% and a mean of +18% (skewed by squeezes).
- **Uptrends fade.** After a 13-week uptrend the mean 6-week return was −23%, and only 29% of cases were positive. Calls have no trend edge here.
- Daily volatility is 132% annualised over 2 years; the last 20 days ran at 379%. There were 6 daily gaps larger than 15%.

## 4. Rules (pre-specified; see `strategies/FNGR.py`)
- **PUT:**
  - Entry conditions (weekly close): 13-week log slope below −3%/wk, R² above 0.60, close below the 10-week MA, and close no more than 30% below that MA.
  - Contract: ATM put, 60 DTE.
  - Target: underlying −30%.
  - Stop: weekly close above entry × 1.25, or above the 10-week MA.
  - Max hold: 6 weeks.
- **CALL:** never. Uptrends faded, and the spikes could not be predicted from price.
- **NONE:** otherwise, and **always** while no near-money options exist.

## 5. Backtest (weekly, 2021-09 to 2026-09)
Assumptions:
- Options priced with Black-Scholes (`common.option_trade_return`).
- IV = 1.1 × 20-week realised volatility, with a floor of 80%.
- **30% round-trip spread**, 60 DTE, ATM.
- 5% of equity risked per trade.
- In-sample: first 70% (to 2025-03-17). Out-of-sample: 2025-03-24 to 2026-09-21.

| Period | Strategy | Trades | Win % | Avg ret | Median ret | Compounded @5% | Max DD | Longest losing streak |
|---|---|---|---|---|---|---|---|---|
| In-sample | Trend PUT | 12 | 25% | −44% | −68% | −23.9% | −23.9% | 4 |
| In-sample | Baseline (13-wk trend, hold 4 wk) | 40 | 30% | −23% | −43% | −39.9% | −43.2% | 7 |
| **Out-of-sample** | **Trend PUT** | **3** | **33%** | **−9%** | **−79%** | **−1.8%** | **−5.0%** | 1 |
| Out-of-sample | Baseline | 19 | 42% | +10% | −28% | +7.0% | −23.4% | 5 |
| Full | Trend PUT | 15 | 27% | −37% | −73% | −25.3% | −26.9% | 5 |
| Full | Baseline | 60 | 30% | −17% | −39% | −44.3% | −54.3% | 8 |

Out-of-sample trades:
- Jul 2025 put: stopped, −79%.
- May 2026 put: target hit, +152%.
- Aug 2026 put: wiped out (−100%) by the 938M-share squeeze.

**Sensitivity check.** I re-ran the full period with spread from 15% to 45% and IV/HV from 0.9 to 1.4. Every combination was negative, from −12% to −36% compounded.

**Parameter grid check.** I tested 64 variants chosen on in-sample data (moneyness, stop, target, hold, stretch, MA filter). The best in-sample variant (+11%) lost money out-of-sample on its only trade. The baseline's positive out-of-sample result comes from a handful of crash weeks in 2026, not from a stable edge.

**Why it fails.** The drift of roughly −8%/wk is real, but options priced at 130–300% volatility already charge for it. The periodic squeezes then wipe out the puts.

## 6. Risks
- **Nasdaq minimum bid ($1):** the stock has been below $1 since about Apr 2026. A **reverse split** is very likely, and so is a delisting notice. After a reverse split, options are adjusted to non-standard deliverables (for example, 100 shares becomes 100/N shares), which makes them even more illiquid.
- **Squeeze and dilution cycles:**
  - Retail squeezes of 3–10× have happened 3–4 times in 5 years.
  - Share issuance is likely at these prices.
  - Either one invalidates trend assumptions within days.
- **Model risk:** Black-Scholes badly understates the fat tails. The real options don't exist near the money, so every return above is hypothetical.

## 7. Today (2026-09-24)
- 13-week slope is −7.8%/wk with R² 0.72.
- The close of 0.1452 is 40% below the 10-week MA of 0.241.
- **The raw rule is NONE** because the price is too stretched and squeeze risk is high.
- **Final signal: NONE (NOT OPTION-TRADEABLE).**

Reproduce: `cd /home/user/trading && python3 strategies/FNGR_backtest.py`

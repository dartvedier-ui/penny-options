# Watchlist groups and setups

Last updated: 2026-09-26. IBKR watchlist "Penny Option" (16 tickers) is ordered in these groups.

## Market gauge (top of the list)
| Ticker | Role | Latest read (2026-09-25 close) |
|---|---|---|
| XSP | Mini-S&P 500 index (1/10 of SPX), IBKR contract 137851301, type IND, exchange CBOE. Sets the market bias for all setups; trade only as small debit spreads. | 774.34. 26w +0.44%/wk (R2 0.68), 13w +0.30%/wk (R2 0.48), 6w flat. Score 0.58 = WATCH. IV 11.6% (6th pct, cheap). Bias: mildly up / sideways. |

## Active (open trades)
| Ticker | Position | See |
|---|---|---|
| PFE | Long Oct 16 '26 28 call, 1 contract @ $0.75 (other broker) | `journal/trades.csv` |

## Stock trades (shares, traded at the user's other broker)
| Ticker | Rule | Status (2026-09-25 close) |
|---|---|---|
| TQQQ | 3x Nasdaq-100 ETF, shares only. HOLD while the Friday weekly close is above its 40-week average; SELL on the first weekly close below it. Size about $200 (fractional shares). Swing trade only, never buy and sell the same day (PDT). Don't pair with an XSP call spread (same bet). | Close 79.60 vs 40-week avg 63.36: rule says HOLD/BUY. Caution: market flat 6 weeks, 9% below high 87.89. Not bought yet. |

## Setups (waiting for a trigger)
| Ticker | Direction | Trigger | Planned trade | Confidence | Notes |
|---|---|---|---|---|---|
| TLT | Put | Can enter now | Oct 23 '26 80/78 put debit spread, ~$0.91 debit (or Oct 23 82 put ~$3.25, −40% stop) | Low–Med | Take profit ~$1.65, close by Oct 16–18, half size |
| XLF | Put | Close below $53.20 | 53/51 put spread, ~28 DTE | Low–Med | |
| XLE | Call | Close above ~$64 | 64/67 call spread | Low–Med | |
| F | Put | Failed bounce toward ~$13.30 | 13 put | Low–Med | |
| NIO | Put | Close above ~$3.81, then back below | 21 DTE put, ~5% ITM | Low | Backtest edge weak |
| KHC | Put | Bounce to ~$24.50 that fails | 24.5/23 put spread | Low–Med | |
| OPEN | Put | Friday close ≥ ~$2.61 | Oct 16 '26 3 put | Low | Too stretched now |
| IOVA | Call | Close ≤ ~$9.84 | 21 DTE ATM call | Low | Too extended now |
| STLA | Put | Bounce to ≥ $5.05 | Jan 15 '27 5 put | Low–Med | Long DTE by design |
| CCL | Put | AFTER earnings Tue 2026-09-29 (9:15 AM ET): bounce toward $22.75–23.50 that fails | Oct 23 '26 22 put, or 22/20 put spread if IV still high | Low–Med | Best new trend: 6-wk −4.2%/wk R² 0.90. Do NOT trade before earnings |
| KRE | Put | Bounce to ~$73 (SMA20) that fails | Oct 23 '26 72 put | Low | 26w/13w trends disagree; cheap IV. Regional bank earnings mid/late Oct |

## Strategy tickers (backtested strategy, no setup right now)
| Ticker | Why |
|---|---|
| VXX | 60-90 DTE put strategy. Signal ON as of 2026-09-24, but the planned 90-DTE put costs ~$280+; look for a cheaper spread. Options ~42k/day, IV 17th pct. |
| NKE | Earnings blackout; FQ1 report Thu 2026-10-01 after close, re-check after the Oct 2 reaction. Options ~183k/day. |

## Bench (removed from IBKR 2026-09-26, recheck monthly; next ~2026-10-26)
Weekly-bar score = avg of 26w and 13w R2, 0 if their slopes disagree. Avg option volume = contracts/day.
| Ticker | Score | Avg opt vol | Reason removed |
|---|---|---|---|
| SOFI | 0.00 | 335k | 26w up vs 13w down (6w down, R2 0.95) |
| AAL | 0.00 | 124k | 26w up vs 13w down |
| RIVN | 0.00 | 95k | 26w flat vs 13w down |
| HIMS | 0.00 | 81k | 26w up vs 13w down, very volatile (IV ~67%) |
| BAC | 0.00 | 194k | News-driven drop, trends conflict, earnings mid-Oct |
| SLV | 0.00 | 409k | Trends conflict |
| NOK | 0.05 | 156k | No trend |
| NU | 0.07 | 100k | No trend |
| UNG | 0.11 | 48k | No trend |
| KMI | 0.29 | 10.6k | Weak trend |
| EEM | 0.33 | 115k | Weak trend |
| VALE | 0.37 | 27k | Weak 13w trend |
| ET | 0.57 | 29k | Borderline; slow (~0.5%/wk) and 6w turning down |
| BEN | - | ~0.7k | Options barely trade |
| VTRS | - | ~1.1k | Options barely trade |

## Retired
- SURG, FNGR (removed 2026-09-26): stock ~$0.15 vs lowest strikes $0.50–$1, not option-tradeable.

## Other watchlists screened
- US Stable (SCHD, SCHG, SCHF, SCHE, SCHY, DGRO), 2026-09-26: no candidates. Moves too slow and
  options too thin. SCHG is watch only: call on a pullback to ~$35.3 that turns up, Low confidence.

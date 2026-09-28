# Watchlist groups and setups

Last updated: 2026-09-28 (first full subagent scan). IBKR watchlist "Penny Option" (16 tickers) is ordered in these groups.

## Market gauge (top of the list)
| Ticker | Role | Latest read (2026-09-25 close) |
|---|---|---|
| XSP | Mini-S&P 500 index (1/10 of SPX), IBKR contract 137851301, type IND, exchange CBOE. Sets the market bias for all setups; trade only as small debit spreads. | 2026-09-28: 774.34, score 0.58 = WATCH. 13w +0.30%/wk (R2 0.48), 6w flat. Bias: SIDEWAYS -> no confidence adjustment. |

## Active (open trades)
| Ticker | Position | See |
|---|---|---|
| PFE | Long Oct 16 '26 28 call, 1 contract @ $0.75 (other broker) | `journal/trades.csv` |
| TLT | Oct 30 '26 79/77 put debit spread, 1 @ $0.80 (other broker), opened 2026-09-28 | `journal/trades.csv` |

## Stock trades (shares, traded at the user's other broker)
| Ticker | Rule | Status (2026-09-25 close) |
|---|---|---|
| TQQQ | 3x Nasdaq-100 ETF, shares only. HOLD while the Friday weekly close is above its 40-week average; SELL on the first weekly close below it. Size about $200 (fractional shares). Swing trade only, never buy and sell the same day (PDT). Don't pair with an XSP call spread (same bet). | Fri 9/25 close 79.60 vs 40-week avg 63.36 (+25.6%): BUY/HOLD. 77.71 on 9/28 morning. Not bought yet. |

## Setups (scan 2026-09-28; order = IBKR watchlist order)
| Ticker | Score | Direction | Trigger / status | Planned trade | Confidence |
|---|---|---|---|---|---|
| VXX | 0.92 | Put | READY (13w down, below SMA20, no spike). 17.54 | Nov 20 '26 (53 DTE) 18/16 put spread, ~$1.18 at Fri close (over $80 flag), max value $2.00. Exit +50% or on a vol spike close above ~19 | Low-Med |
| OPEN | 0.87 | Put | CLOSE: needs a Friday close >= ~2.61 (2.47 now, falling) | Oct 16 '26 3 put, re-price when triggered | Low |
| NIO | 0.85 | Put | NOT YET: needs close > ~3.81 then back below (3.63 now) | 21 DTE put ~5% ITM | Low |
| CCL | 0.39 | Put | BLACKOUT: earnings Tue 9/29 9:15 AM ET, implied move ~7.5%. After: bounce toward 22.75-23.50 that fails | Oct 23 '26 22 put or 22/20 spread | Low |
| XLE | 0.53 | Call | NOT YET: close > ~64 (62.34 now) | 64/67 call spread | Low |
| IOVA | 0.87 | Call | NOT YET: close <= ~9.84 (10.90 now, strong uptrend; Goldman Buy $15 on 9/24). Earnings Nov 5 | 21 DTE ATM call | Low |
| STLA | 0.78 | Put | NOT YET: bounce to >= 5.05 (4.70 now). Earnings Oct 28 | Jan 15 '27 5 put | Low-Med |
| NKE | 0.80 | Either | BLACKOUT: earnings Thu 10/1 after close; re-check after the Oct 2 reaction | 45 DTE per strategy | - |

## Trend gone (scan 2026-09-28) - candidates to move to the Bench (ask the user)
| Ticker | Score | Note |
|---|---|---|
| XLF | 0.37 | 13w flat, 6w down; trigger 53.20 (54.51 now) |
| KHC | 0.00 | Weak/conflicting trends; earnings ~late Oct |
| F | 0.00 | Weak trends; -3.4% in 3 days on recalls/China scrutiny; earnings ~mid/late Oct |
| KRE | 0.00 | Flat 13w (R2 0.42); no real trend |

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

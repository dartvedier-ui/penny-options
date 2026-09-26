# Penny Option Trading System — standing instructions

Read this first in every session. Then read `WATCHLIST.md` (setups + triggers) and `journal/trades.csv` (open trades).

## Who / what
- The user trades simple LONG CALLS, LONG PUTS and (when IV is high) DEBIT SPREADS.
- Account: IBKR, about $800. Some trades are placed at another broker (noted in the journal).
- Max 2–3 open trades at once; one contract ≈ 5–10% of the account. Warn if a trade is larger.
- Tickers are chosen for PREDICTABILITY of price movement — nothing more, nothing less.
- The user checks in with no fixed schedule, often from a phone. Keep answers short, tables welcome.

## Before ANY trade idea
1. Check economic news and the macro calendar (CPI, PCE, FOMC, jobs, Treasury auctions).
2. Check earnings dates / recent reports for every ticker recommended. No holding through earnings
   unless the user explicitly asks.
3. Pull live option quotes from IBKR (bid/ask, IV, IV percentile).

## Every recommendation must state
- Expiration date **and** DTE
- Specific strikes with live bid/ask
- Confidence level (High / Medium / Low, usually Low–Medium) with the reason
- Exit rules (take profit, stop, time exit)

## DTE policy ("hybrid", chosen by the user 2026-09-24)
- Default 15–25 DTE. TLT put spreads: ~28–30 DTE (backtest: 71% of variants positive in both
  periods at 28 DTE vs 38% at 21 DTE).
- Kept longer because short DTE lost money in `short_dte_backtest.py`: VXX 60–90 DTE, STLA ~120 DTE, NKE ~45 DTE.

## Structure picker
- Clean trend + cheap options (low IV percentile) → long option, slightly ITM, ~21–28 DTE.
- Clean trend + expensive options (high IV percentile) → debit spread.
- No clean trend → no trade.
- Short-DTE check: expected 3-week trend move ÷ ATM 21-DTE option cost (≈ 0.4 × IV × √(21/365)) should be ≥ 1.0.

## Predictability score
Average of the 26-week and 13-week weekly log-price trend R²; 0 if the two slopes disagree in sign.
Also look at the 6-week trend for turns.

## Watchlists (IBKR)
- **Penny Option** (id 10): the working universe, ordered Active → Setups → Scan list (see `WATCHLIST.md`).
- **Penny Setups** (id 119) and **Penny Active** (id 120) exist on the server but do not show in the
  user's IBKR mobile app, so the grouping is kept by ORDER inside Penny Option and in `WATCHLIST.md`.
- `edit_watchlist` is full-replace: always `get_watchlist` first.

## Journal
`journal/trades.csv` — one row per trade. Update it whenever the user reports a fill or an exit.
Record the user's actual fill price, never an estimate.

## Code
- `common.py` data loader + Black-Scholes option-return model.
- `strategies/<TICKER>.py` exposes `signal(df)`; `<TICKER>_backtest.py` reproduces the study.
- `scan.py` ranks today's signals: `python3 scan.py` (needs pandas, numpy; refresh `data/*.csv` from IBKR first).
- `reports/<TICKER>.md` full write-ups. Reports for tickers added later (PFE, XLF, KHC, F, XLE, CCL, KRE)
  are not written yet.

## Storage
- This GitHub repo is the source of truth for code, rules, setups and the journal.
- Google Drive "CLAUDE PROJECTS / Penny Option Trading System" holds older read-only copies of the reports.

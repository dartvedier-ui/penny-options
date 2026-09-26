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

## XSP (market gauge)
- XSP = Mini-S&P 500 index options, 1/10 of SPX, European style, cash-settled (no early assignment).
- One at-the-money XSP option ~3 weeks out costs roughly $800+, more than the account. Trade XSP ONLY as
  debit spreads 2-3 points wide (about $100-150 risk), 21-28 DTE, and only when its trend score is 0.6+.
- Market-bias filter for every setup: if XSP's 13-week trend is clearly up, lower put setups one confidence
  step; if clearly down, lower call setups one step.

## Stock trades (shares)
- TQQQ is traded as SHARES at the user's other broker (to avoid PDT flags at IBKR), not options.
- Rule: hold while the weekly (Friday) close is above the 40-week average; sell on the first weekly close
  below it. Backtest 2022-07..2026-09 on weekly closes: x3.45 vs x5.70 buy-and-hold, but worst drop -31% vs -54%.
- About $200 max (fractional shares), swing only (no same-day round trips). Not together with XSP call spreads.

## Predictability score
Average of the 26-week and 13-week weekly log-price trend R²; 0 if the two slopes disagree in sign.
Also look at the 6-week trend for turns.

## Watchlists (IBKR)
- **Penny Option** (id 10): the working universe, ordered Active → Setups → Scan list (see `WATCHLIST.md`).
- **Penny Setups** (id 119) and **Penny Active** (id 120) exist on the server but do not show in the
  user's IBKR mobile app, so the grouping is kept by ORDER inside Penny Option and in `WATCHLIST.md`.
- `edit_watchlist` is full-replace: always `get_watchlist` first.

## Scan workflow (who does what)
- **Daily briefing (Routine, 8:45 AM NY):** one agent, no subagents. It only checks the open trades and the
  setup triggers, which is cheap.
- **Full universe scan (weekly, or when the user asks):** split the Penny Option watchlist into batches of
  about 10 and launch one `penny-scanner` subagent per batch IN PARALLEL (`.claude/agents/penny-scanner.md`,
  runs on Sonnet to save usage). Each returns one table. The main session merges the tables, ranks them,
  then updates WATCHLIST.md, the Penny Option order, and the daily briefing prompt.
- **Deep check when a trigger fires:** one `penny-scanner` per triggered ticker (news, earnings, IV).
  The main session pulls the live option chain and writes the final trade ticket (expiry + DTE, strikes
  with bid/ask, exits, confidence).
- Subagents use MORE total usage than one agent, so use them only for the full scan and deep checks.
- `screen.py` does the trend math so every subagent computes it the same way.

## Daily briefing Routine
"Penny daily briefing" (trig_018283RxTbwpmWM6DbKKupGv) runs 8:45 AM New York time on weekdays with IBKR attached.
Its prompt embeds a COPY of the open trades, setups and rules, because a scheduled run may not be able to
open this private repo. Whenever WATCHLIST.md or journal/trades.csv changes, update that Routine's prompt too
(update_trigger with the full new prompt).

## Journal
`journal/trades.csv` — one row per trade. Update it whenever the user reports a fill or an exit.
Record the user's actual fill price, never an estimate.

## Code
- `common.py` data loader + Black-Scholes option-return model.
- `strategies/<TICKER>.py` exposes `signal(df)`; `<TICKER>_backtest.py` reproduces the study.
- `screen.py` predictability screen for any tickers from a JSON of closes (score, 26w/13w/6w trends,
  HV20, short-DTE ratio, CANDIDATE/WATCH/SKIP).
- `scan.py` ranks today's signals: `python3 scan.py` (needs pandas, numpy; refresh `data/*.csv` from IBKR first).
- `reports/<TICKER>.md` full write-ups. Reports for tickers added later (PFE, XLF, KHC, F, XLE, CCL, KRE)
  are not written yet.

## Storage
- This GitHub repo is the source of truth for code, rules, setups and the journal.
- Google Drive "CLAUDE PROJECTS / Penny Option Trading System" holds older read-only copies of the reports.

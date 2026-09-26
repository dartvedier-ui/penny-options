# penny-options

Long call / long put / debit spread system for the IBKR "Penny Option" watchlist.
Tickers are chosen for predictability of price movement.

- `CLAUDE.md` — standing rules (read first)
- `WATCHLIST.md` — Active / Setups / Scan groups with entry triggers
- `journal/trades.csv` — trade journal
- `scan.py` — daily signal scanner (`pip install -r requirements.txt && python3 scan.py`)
- `strategies/` — per-ticker rules (`<TICKER>.py`) and backtests (`<TICKER>_backtest.py`)
- `short_dte_backtest.py` — retest of every strategy at 15/21/25 DTE
- `reports/` — per-ticker research write-ups
- `data/` — IBKR daily/weekly price history (up to 5 years, through 2026-09-24)

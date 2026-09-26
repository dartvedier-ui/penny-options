"""Daily scan: run every ticker's strategy on its latest data and rank the setups.

Usage: python3 scan.py
Refresh data/<TICKER>_daily.csv first (append today's bars from IBKR).
"""
import os
import importlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

TICKERS = ["VXX", "NIO", "OPEN", "IOVA", "TLT", "NKE", "STLA"]  # SURG, FNGR retired 2026-09-26: not option-tradeable


def main():
    rows = []
    for t in TICKERS:
        try:
            mod = importlib.import_module(f"strategies.{t}")
            df = common.load(t)
            sig = mod.signal(df)
            rows.append((t, df["date"].iloc[-1].date(), sig))
        except Exception as e:  # strategy or data missing
            rows.append((t, None, {"action": "ERROR", "strength": 0, "reason": str(e)}))
    rows.sort(key=lambda r: (r[2]["action"] in ("NONE", "ERROR"), -r[2].get("strength", 0)))
    for t, d, s in rows:
        print(f"{t:5} {str(d):10} {s['action']:5} strength={s.get('strength', 0):.2f} "
              f"entry={s.get('entry')} stop={s.get('stop')} target={s.get('target')} "
              f"dte={s.get('dte')} | {s.get('reason', '')}")


if __name__ == "__main__":
    main()

"""Predictability screen for any list of tickers (used by the penny-scanner subagents).

Input: a JSON file mapping ticker -> daily closes (oldest first), or ticker ->
{"closes": [...], "iv": 0.35} to also get the short-DTE ratio. Six months of IBKR daily
bars (get_price_history ONE_DAY / SIX_MONTHS, ~125 closes) is enough.
Run: python3 screen.py closes.json
"""
import json
import sys
import numpy as np


def trend(closes):
    """Slope (% per step) and R^2 of a straight-line fit to log price."""
    y = np.log(np.asarray(closes, dtype=float))
    x = np.arange(len(y))
    b, a = np.polyfit(x, y, 1)
    resid = y - (a + b * x)
    return b * 100, 1 - resid.var() / y.var()


def screen(closes, iv=None):
    c = np.asarray(closes, dtype=float)
    weekly = c[::-1][::5][::-1]                      # every 5th close, ending on the latest
    s26, r26 = trend(weekly[-26:])
    s13, r13 = trend(weekly[-13:])
    s6, r6 = trend(c[-30:])
    s6 *= 5                                          # daily slope -> per week
    score = (r26 + r13) / 2 if np.sign(s26) == np.sign(s13) else 0.0
    hv20 = np.log(c[1:] / c[:-1])[-20:].std() * np.sqrt(252)
    ratio = None
    if iv:
        ratio = abs(s13) * 3 / (0.4 * iv * np.sqrt(21 / 365) * 100)
    if score >= 0.6 and (ratio is None or ratio >= 1.0):
        verdict = "CANDIDATE"
    elif score >= 0.4:
        verdict = "WATCH"
    else:
        verdict = "SKIP"
    return dict(price=c[-1], s26=s26, r26=r26, s13=s13, r13=r13, s6=s6, r6=r6, score=score,
                hv20=hv20, vs_sma20=c[-1] / c[-20:].mean() - 1, vs_sma50=c[-1] / c[-50:].mean() - 1,
                ratio=ratio, verdict=verdict)


def main(path):
    data = json.load(open(path))
    rows = []
    for t, v in data.items():
        closes, iv = (v["closes"], v.get("iv")) if isinstance(v, dict) else (v, None)
        rows.append((t, screen(closes, iv)))
    rows.sort(key=lambda r: -r[1]["score"])
    print("ticker  price    26w %/wk R2   13w %/wk R2   6w %/wk R2    score  HV20  vsSMA20 vsSMA50  ratio  verdict")
    for t, m in rows:
        ratio = f"{m['ratio']:5.2f}" if m["ratio"] is not None else "   - "
        print(f"{t:6} {m['price']:8.2f}  {m['s26']:+6.2f} {m['r26']:.2f}  {m['s13']:+6.2f} {m['r13']:.2f}  "
              f"{m['s6']:+6.2f} {m['r6']:.2f}   {m['score']:.2f}  {m['hv20']:4.0%}  {m['vs_sma20']:+6.1%} "
              f"{m['vs_sma50']:+6.1%}  {ratio}  {m['verdict']}")


if __name__ == "__main__":
    main(sys.argv[1])

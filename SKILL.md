---
name: orb-breakout-scanner-skill
description: ORB scanner for US stocks/ETFs via Yahoo Finance. Use when user asks about opening range breakouts, market-open scans, or breakout candidates. Reports entry/SL/TP, no auto-trading.
compatibility:
  python_packages:
    - yfinance>=0.2.0
    - pandas>=1.5.0
    - pytz>=2023.3
---

# ORB Scanner Skill

This skill implements the **Opening Range Breakout (ORB)** scan for US stocks and ETFs (NYSE/NASDAQ).
It monitors price data, detects ORB patterns, and reports qualified setups to the user.
**No automated trading** – detection and notification only.

## When to use

Use this skill when the user asks about ORB setups, Opening Range Breakouts,
market open analysis, or trading scanners. Typical requests:
"Which stocks have an ORB pattern today?", "Scan the market for breakouts",
"ORB candidates for today", or "Show me breakout stocks after market open".

---

## Workflow Overview

```
1. Load watchlist / receive from user
2. Fetch intraday data via Yahoo Finance (1m + 5m)
3. Calculate Opening Range (first 15-min candle)
4. Check for confirmed breakout on the 5-min chart
5. Classify entry scenario (Breakout / Retest / Reversal)
6. Calculate SL/TP levels
7. Format result and notify user
```

---

## Step 1 – Determine Watchlist

If the user does not provide a watchlist, ask briefly or use the default:

**Default Watchlist (representative US stocks + ETFs):**
```python
DEFAULT_WATCHLIST = [
    # ETFs
    "SPY", "QQQ", "IWM", "DIA",
    # Technology
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META",
    # Further Large Caps
    "JPM", "BAC", "XOM", "UNH"
]
```

The user can supply a custom list at any time, e.g.:
> "Only scan AAPL, TSLA and QQQ"

---

## Step 2 – Fetch Data

Run the scan script located at `scripts/orb_scan.py`.
**Read the reference file `references/orb_logic.md` for all calculation details.**

```bash
pip install yfinance pandas pytz --quiet
python scripts/orb_scan.py --tickers "SPY,QQQ,AAPL,TSLA" --output /tmp/orb_results.json
```

Without `--tickers`, the default watchlist is used:
```bash
python scripts/orb_scan.py --output /tmp/orb_results.json
```

---

## Step 3 – Interpret and Present Results

Read `/tmp/orb_results.json` and format the output for the user as follows:

### Format for a signal found:

```
📊 ORB SIGNAL: [TICKER]
━━━━━━━━━━━━━━━━━━━━━━━━
Direction:    📈 LONG  /  📉 SHORT
Scenario:     Breakout | Retest | Reversal
Time (ET):    HH:MM
Price:        $XXX.XX

Opening Range:
  High:   $XXX.XX
  Low:    $XXX.XX
  Width:  $X.XX  (X.X%)

Suggested Levels (2:1 RRR):
  Entry:       $XXX.XX
  Stop Loss:   $XXX.XX  (–$X.XX)
  Take Profit: $XXX.XX  (+$X.XX)

Note: [Context, e.g. "Clean breakout with above-average volume"]
```

### No signal found:
```
🔍 ORB Scan complete – [timestamp]
Tickers scanned: X
Active ORB signals: None

Possible reasons: Market still within the Opening Range,
no confirmed breakout on the 5-min chart yet.
```

---

## Step 4 – Important Notes for the User

**Always** append this disclaimer at the end:

```
⚠️  RISK DISCLAIMER
This signal is for informational purposes only and does not
constitute investment advice. ORB setups can fail when
algorithms deliberately trigger stops just outside the
Opening Range ("stop hunt"). Independent analysis and
risk management remain essential.
Recommendation: Max 1 trade per day, RRR ≥ 2:1.
```

---

## Timezone & Market Hours

| Event                        | US Eastern Time | Central Europe (CET/CEST) |
|------------------------------|-----------------|---------------------------|
| NYSE/NASDAQ Market Open      | 09:30 ET        | 15:30 CET / 14:30 CEST    |
| Opening Range End            | 09:45 ET        | 15:45 CET / 14:45 CEST    |
| Best Breakout Window         | 09:45–11:30 ET  | 15:45–17:30 CET           |
| Market Close                 | 16:00 ET        | 22:00 CET                 |

Always verify whether the market is currently open before scanning.
Outside trading hours: display a notice, do not start the scan.

---

## Error Handling

| Problem                          | Response                                             |
|----------------------------------|------------------------------------------------------|
| Market closed                    | Display notice, offer to scan last trading day       |
| Yahoo Finance returns no data    | Skip ticker, list at end of output                   |
| Opening Range too wide (>5%)     | Warning: "High-volatility day, elevated risk"        |
| Fewer than 3 candles after OR    | Too early for confirmation – do not emit signal      |

---

## References

- Full ORB logic and calculation details: `references/orb_logic.md`
- Scan script with all parameters: `scripts/orb_scan.py`

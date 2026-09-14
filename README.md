# orb-breakout-scanner-skill

Opening Range Breakout (ORB) scanner for US stocks and ETFs (NYSE/NASDAQ) as a Claude.ai skill.

Upload it once to Claude.ai, then just chat — Claude detects ORB setups after the market open and replies with concrete entry / stop-loss / take-profit levels. **Detection and notification only — no automated trading.**

## Compatibility

- **Claude.ai** (Free, Pro, Max, Team, Enterprise) — primary target.
- Requires **Code Execution enabled** (Claude uses it to run `scripts/orb_scan.py` and fetch Yahoo Finance data).
- Data source: Yahoo Finance, US market hours only (09:30–16:00 ET).

## Install on Claude.ai

1. Download this repo (`Code > Download ZIP` on GitHub, or `git clone`), then re-zip so the archive looks like:
   ```
   orb-breakout-scanner-skill/
   ├── SKILL.md
   ├── scripts/orb_scan.py
   └── references/orb_logic.md
   ```
   `SKILL.md` must be at the top level of the skill folder (folder name matches `name:` in `SKILL.md`).
2. In Claude.ai go to **Settings > Skills > Upload skill** and upload the ZIP.
3. Make sure the skill is **enabled** and **Code Execution is on**.
4. Start a new chat — no manual selection needed, Claude loads the skill automatically when you ask about ORBs or breakouts.

## How to use: your own watchlist by just telling Claude

You never edit a config file. You define the watchlist **in plain language in the chat**.

**1. Use the default watchlist (no setup):**
> Scan the market for ORB breakouts today

Claude scans the built-in list (SPY, QQQ, IWM, DIA, AAPL, MSFT, NVDA, TSLA, AMZN, GOOGL, META, JPM, BAC, XOM, UNH).

**2. Scan a one-off custom list:**
> Only scan AAPL, TSLA and QQQ for ORBs today

> Scan NVDA, AMD, SMCI and SOXL for opening range breakouts

**3. Set a persistent watchlist for the conversation:**
> My watchlist is SPY, NVDA, META, JPM and XLE — remember it for today and scan it for ORBs every time I ask

> I only trade tech: AAPL, MSFT, NVDA, AVGO, QQQ. Use that as my ORB watchlist from now on.

Tip: keep lists to ~5–15 tickers for the cleanest results. Use valid US tickers (stocks + ETFs). The list applies to the current chat — just paste it again in a new chat.

**Other useful prompts:**
- `Which stocks have an ORB pattern right now?`
- `ORB candidates for today from my watchlist?`
- `Show me breakout stocks after market open`
- `Check SPY and QQQ — LONG setups only, 2:1 RRR`

## When to scan

| Event | US Eastern Time |
|-------|-----------------|
| Market open | 09:30 ET |
| Opening Range end (first 15-min candle) | 09:45 ET |
| Best breakout window | 09:45–11:30 ET |
| Market close | 16:00 ET |

Before 09:45 ET there is no confirmed signal yet. Outside trading hours Claude will tell you the market is closed and offer to review the last trading day instead.

## What you get back

Signal example:
```
📊 ORB SIGNAL: NVDA
Direction:    📈 LONG
Scenario:     Breakout | Retest | Reversal
Time (ET):    10:05
Price:        $XXX.XX
Opening Range: High $XXX.XX / Low $XXX.XX
Suggested Levels (2:1 RRR):
  Entry: $XXX.XX / Stop Loss: $XXX.XX / Take Profit: $XXX.XX
```

Every signal ends with a risk disclaimer: ORB setups can fail on stop-hunts outside the Opening Range. Max 1 trade per day, RRR ≥ 2:1 recommended. This is information only, not investment advice.

No signal:
```
🔍 ORB Scan complete – tickers scanned: X, Active ORB signals: None
Possible reasons: market still within the Opening Range, no confirmed breakout on the 5-min chart yet.
```

## Troubleshooting

| Problem | What to do |
|---------|------------|
| Skill didn't trigger | Use a trigger phrase like “ORB”, “opening range breakout”, or “scan for breakouts” |
| Market closed notice | Expected outside 09:30–16:00 ET — ask for the last trading day |
| Ticker skipped / no data | Check spelling, use NYSE/NASDAQ symbols only |
| “Wide Opening Range” warning | >5% range = high-volatility day, elevated risk |
| Too early, no signal | Wait until after 09:45 ET for confirmation |

## Repo layout

- `SKILL.md` — instructions Claude follows (workflow, watchlist handling, output format). Frontmatter `name` matches folder name and `description` is under Claude.ai's 200-character limit.
- `scripts/orb_scan.py` — fetches 1m/5m Yahoo Finance data, calculates Opening Range, confirmation, scenarios, SL/TP.
- `references/orb_logic.md` — full ORB calculation details (Opening Range, FVG, retest, reversal, 2:1 RRR).
- `LICENSE` — MIT.

## License / disclaimer

MIT. No automated trading. Signals are for informational purposes only and do not constitute investment advice.

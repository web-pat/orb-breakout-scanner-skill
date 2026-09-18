# orb-breakout-scanner-skill

A Claude.ai skill that runs a one-time Opening Range Breakout (ORB) scan for a supplied list of US ticker symbols. It downloads same-day 1-minute and 5-minute data from Yahoo Finance, calculates the 09:30-09:45 ET opening range, and reports the first qualifying 5-minute breakout found for each symbol.

The scanner is informational only. It does not place trades, monitor continuously, send alerts, store a watchlist, validate ticker eligibility, or determine whether a previously detected setup is still actionable.

## What it does

For each ticker, the scanner:

1. Downloads same-day 5-minute and 1-minute Yahoo Finance data.
2. Builds the opening range from 5-minute bars timestamped from 09:30 through 09:44 ET.
3. Finds the first later 5-minute bar whose full range is outside that opening range.
4. Labels the detected setup as `breakout`, `retest`, or `reversal` using a short 1-minute-bar heuristic.
5. Calculates an entry at the detected 5-minute bar's close, a stop loss, and a fixed 2:1 reward-to-risk take-profit level.
6. Writes the result to JSON and prints scan progress to standard output.

The scan is a snapshot, not a live signal service. A returned signal may have occurred earlier in the day and may subsequently have failed, reached its target or stop, or otherwise become unsuitable for trading.

## Requirements

- A Claude.ai plan and workspace that support custom Skills and have Code Execution enabled.
- Python 3.10 or later.
- Internet access and permission to install Python packages in the execution environment.
- `yfinance`, `pandas`, and `pytz`.
- A writable location for the JSON output file.

Yahoo Finance is a third-party data source. Intraday data can be delayed, incomplete, unavailable, or revised. Do not rely on its prices as an execution-price source.

## Install on Claude.ai

1. Download this repository, then create a ZIP whose top-level folder contains:

   ```text
   orb-breakout-scanner-skill/
   |- SKILL.md
   |- scripts/orb_scan.py
   `- references/orb_logic.md
   ```

2. In Claude.ai, open **Settings > Skills**, upload the ZIP, and enable the skill and Code Execution.
3. Start a chat and ask for an opening-range-breakout or market-open scan. Skill selection is determined by Claude and is not guaranteed for every prompt.

## Using the skill

Ask Claude to scan specific symbols or use the built-in default list.

```text
Scan AAPL, TSLA, and QQQ for opening range breakouts.
```

```text
Scan the default ORB watchlist.
```

The default watchlist is:

```text
SPY, QQQ, IWM, DIA, AAPL, MSFT, NVDA, TSLA, AMZN, GOOGL, META, JPM, BAC, XOM, UNH
```

The underlying script accepts only these options:

```bash
python scripts/orb_scan.py --tickers "SPY,QQQ,AAPL" --output /tmp/orb_results.json
```

```bash
python scripts/orb_scan.py --output /tmp/orb_results.json
```

`--tickers` is a comma-separated list. Omitting it uses the default watchlist. `--output` sets the JSON output path and defaults to `/tmp/orb_results.json`.

The scanner does not support long-only or short-only filtering, custom reward-to-risk ratios, historical dates, alerts, scheduling, or saved watchlists. It attempts every supplied symbol; intended use is US stocks and ETFs, but the script does not enforce exchange or asset-class restrictions.

## Timing and market status

| Event | US Eastern Time |
|---|---:|
| Opening range starts | 09:30 ET |
| Opening range ends | 09:45 ET |
| Market close used by the script | 16:00 ET |

The scanner can run before, during, or after those hours. Outside 09:30-16:00 ET, it records a market-closed warning and still attempts a scan using Yahoo Finance's `period="1d"` data. It has no historical-date option and does not validate weekends, holidays, early closes, or the completeness of the latest candle.

The commonly used 09:45-11:30 ET breakout period is a trading preference, not a cutoff enforced by this scanner; it searches available 5-minute bars from 09:45 onward.

## Output

The output JSON contains:

```text
scan_time_et       Scan timestamp in Eastern Time
market_open        Time-of-day market-status check
tickers_scanned    Number of requested ticker strings
signals            Detected breakout records
no_signal          Tickers still inside the range or without confirmation
errors             Tickers without sufficient data or an opening range
warning            Present when the time-of-day check reports market closed
```

A signal includes the ticker, direction, scenario label, opening range, confirmation time and close, calculated levels, and notes. `confirm_time_et` is the timestamp of the detected 5-minute bar; it is not a current quote.

The scenario labels are heuristic. The `breakout` label is also used when the short follow-up analysis does not identify a retest or reversal. The scanner does not rank signals, apply volume analysis, or validate that a setup remains active.

## Limitations and risk

- The scan uses the first qualifying breakout for the day, not necessarily the most recent or best setup.
- A confirmation can be based on an in-progress data bar because the script does not verify bar completion.
- Market status is based on clock time only, not an exchange calendar.
- Invalid, duplicate, or non-US symbols are not filtered before the Yahoo Finance request.
- Network and data-provider failures can produce missing-data results.

No automated trading is performed. Output is for informational purposes only and is not investment advice. Independently verify market status, data quality, prices, and risk before making any trading decision.

## Repository layout

- `SKILL.md`: Instructions and metadata for Claude.ai.
- `scripts/orb_scan.py`: Scanner implementation and supported CLI parameters.
- `references/orb_logic.md`: Background ORB methodology. Where it differs from the script, `scripts/orb_scan.py` defines the behavior actually executed.
- `LICENSE`: MIT license.

## License

MIT.

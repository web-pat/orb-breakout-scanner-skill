#!/usr/bin/env python3
"""
ORB Scanner – Opening Range Breakout Detector
Uses Yahoo Finance (yfinance) for US stocks and ETFs.
No automated trading – identification and output only.

Usage:
    python orb_scan.py --tickers "SPY,QQQ,AAPL" --output /tmp/orb_results.json
    python orb_scan.py  # uses the default watchlist
"""

import argparse
import json
import sys
from datetime import datetime, time as dtime

import pandas as pd
import pytz
import yfinance as yf

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
DEFAULT_WATCHLIST = [
    # ETFs
    "SPY", "QQQ", "IWM", "DIA",
    # Technology
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META",
    # Further Large Caps
    "JPM", "BAC", "XOM", "UNH",
]

ET = pytz.timezone("America/New_York")
MARKET_OPEN  = dtime(9, 30)
OR_END       = dtime(9, 45)   # End of Opening Range
MARKET_CLOSE = dtime(16, 0)
MAX_OR_WIDTH_PCT = 0.05        # 5% – wider is considered very volatile
RRR = 2.0                      # Risk/Reward Ratio


# ──────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────
def market_is_open() -> bool:
    """Returns True if the US market is currently open."""
    now_et = datetime.now(ET).time()
    return MARKET_OPEN <= now_et <= MARKET_CLOSE


def fetch_intraday(ticker: str, interval: str) -> pd.DataFrame | None:
    """Fetches intraday data from Yahoo Finance and converts index to ET."""
    try:
        df = yf.download(
            ticker,
            period="1d",
            interval=interval,
            auto_adjust=True,
            progress=False,
            timeout=10,
        )
        if df.empty:
            return None
        # Flatten MultiIndex if present (yfinance >= 0.2 with multiple tickers)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        df.index = df.index.tz_convert(ET)
        return df
    except Exception as e:
        return None


def get_opening_range(df_5m: pd.DataFrame) -> dict | None:
    """Extracts the Opening Range from the 5-minute chart."""
    or_candles = df_5m[
        (df_5m.index.time >= MARKET_OPEN) &
        (df_5m.index.time < OR_END)
    ]
    if or_candles.empty:
        return None

    or_high = float(or_candles["High"].max())
    or_low  = float(or_candles["Low"].min())
    or_width = or_high - or_low
    or_width_pct = or_width / or_low if or_low > 0 else 0

    return {
        "high": round(or_high, 4),
        "low":  round(or_low,  4),
        "width": round(or_width, 4),
        "width_pct": round(or_width_pct * 100, 2),
        "wide_warning": or_width_pct >= MAX_OR_WIDTH_PCT,
    }


def find_confirmation(df_5m: pd.DataFrame, or_range: dict) -> dict | None:
    """
    Finds the first 5-min candle that closes entirely outside the OR.
    Returns dict with direction, candle_time, close_price or None.
    """
    post_or = df_5m[df_5m.index.time >= OR_END].copy()
    if post_or.empty:
        return None

    for ts, row in post_or.iterrows():
        # LONG: entire candle above OR_HIGH
        if float(row["Low"]) > or_range["high"] and float(row["Close"]) > or_range["high"]:
            return {
                "direction": "LONG",
                "time_et": ts.strftime("%H:%M"),
                "close": round(float(row["Close"]), 4),
                "volume": int(row["Volume"]),
            }
        # SHORT: entire candle below OR_LOW
        if float(row["High"]) < or_range["low"] and float(row["Close"]) < or_range["low"]:
            return {
                "direction": "SHORT",
                "time_et": ts.strftime("%H:%M"),
                "close": round(float(row["Close"]), 4),
                "volume": int(row["Volume"]),
            }
    return None


def detect_scenario(df_1m: pd.DataFrame, confirmation: dict, or_range: dict) -> str:
    """
    Classifies the entry scenario:
    - breakout  (Fair Value Gap / Momentum)
    - retest    (pullback to OR edge)
    - reversal  (failed breakout)
    """
    direction = confirmation["direction"]
    or_ref = or_range["high"] if direction == "LONG" else or_range["low"]
    tolerance = or_range["width"] * 0.1

    # Candles after confirmation on the 1-min chart
    post_confirm = df_1m[df_1m.index.time >= dtime(
        int(confirmation["time_et"].split(":")[0]),
        int(confirmation["time_et"].split(":")[1])
    )].head(10)

    if post_confirm.empty or len(post_confirm) < 3:
        return "breakout"

    candles = post_confirm.reset_index(drop=True)

    # Reversal: price returns into the OR
    for _, c in candles.iterrows():
        if direction == "LONG" and float(c["Low"]) < or_range["high"]:
            return "reversal"
        if direction == "SHORT" and float(c["High"]) > or_range["low"]:
            return "reversal"

    # Retest: price approaches OR edge again (within tolerance)
    for _, c in candles.iterrows():
        if direction == "LONG":
            if abs(float(c["Low"]) - or_ref) <= tolerance:
                return "retest"
        else:
            if abs(float(c["High"]) - or_ref) <= tolerance:
                return "retest"

    # Check for Fair Value Gap (FVG)
    if len(candles) >= 3:
        c1, c2, c3 = candles.iloc[0], candles.iloc[1], candles.iloc[2]
        if direction == "LONG" and float(c3["Low"]) > float(c1["High"]):
            return "breakout"  # FVG upward
        if direction == "SHORT" and float(c3["High"]) < float(c1["Low"]):
            return "breakout"  # FVG downward

    return "breakout"


def calculate_levels(confirmation: dict, or_range: dict, scenario: str) -> dict:
    """Calculates entry, stop loss and take profit levels."""
    direction = confirmation["direction"]
    close = confirmation["close"]
    or_w = or_range["width"]

    if direction == "LONG":
        entry = close
        if scenario == "reversal":
            sl = or_range["low"] - or_w * 0.2
        else:
            sl = or_range["high"] - or_w * 0.3
        sl = round(sl, 4)
        risk = entry - sl
        tp = round(entry + risk * RRR, 4)
    else:
        entry = close
        if scenario == "reversal":
            sl = or_range["high"] + or_w * 0.2
        else:
            sl = or_range["low"] + or_w * 0.3
        sl = round(sl, 4)
        risk = sl - entry
        tp = round(entry - risk * RRR, 4)

    return {
        "entry": round(entry, 4),
        "stop_loss": sl,
        "take_profit": tp,
        "risk": round(abs(risk), 4),
        "reward": round(abs(tp - entry), 4),
    }


def scan_ticker(ticker: str) -> dict:
    """Full scan for a single ticker. Returns a dict with the result."""
    result = {"ticker": ticker, "status": "no_signal", "error": None}

    df_5m = fetch_intraday(ticker, "5m")
    if df_5m is None or len(df_5m) < 4:
        result["status"] = "no_data"
        result["error"] = "No 5-min data available"
        return result

    df_1m = fetch_intraday(ticker, "1m")
    if df_1m is None or len(df_1m) < 5:
        result["status"] = "no_data"
        result["error"] = "No 1-min data available"
        return result

    # Opening Range
    or_range = get_opening_range(df_5m)
    if or_range is None:
        result["status"] = "no_or"
        result["error"] = "Opening Range not yet available (too early after market open)"
        return result

    result["opening_range"] = or_range

    # Search for confirmation
    confirmation = find_confirmation(df_5m, or_range)
    if confirmation is None:
        result["status"] = "in_range"
        return result

    # Scenario + levels
    scenario = detect_scenario(df_1m, confirmation, or_range)
    levels   = calculate_levels(confirmation, or_range, scenario)

    result.update({
        "status": "signal",
        "direction": confirmation["direction"],
        "scenario": scenario,
        "confirm_time_et": confirmation["time_et"],
        "confirm_close": confirmation["close"],
        "levels": levels,
        "notes": _build_notes(or_range, confirmation, scenario),
    })
    return result


def _build_notes(or_range: dict, confirmation: dict, scenario: str) -> str:
    notes = []
    if or_range["wide_warning"]:
        notes.append(f"⚠️ Wide Opening Range ({or_range['width_pct']}%) – elevated risk")
    if scenario == "retest":
        notes.append("Retest of OR edge – wait for confirmation candle before entry")
    elif scenario == "reversal":
        notes.append("Failed breakout detected – enter only when counter-move high/low is broken")
    elif scenario == "breakout":
        notes.append("Momentum breakout – entry at close of middle FVG candle")
    return " | ".join(notes) if notes else "Clean setup"


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="ORB Scanner")
    parser.add_argument("--tickers", type=str, default=None,
                        help="Comma-separated ticker list (e.g. SPY,QQQ,AAPL)")
    parser.add_argument("--output", type=str, default="/tmp/orb_results.json",
                        help="Output path for JSON results")
    args = parser.parse_args()

    # Check market hours
    now_et = datetime.now(ET)
    is_open = market_is_open()

    tickers = (
        [t.strip().upper() for t in args.tickers.split(",")]
        if args.tickers
        else DEFAULT_WATCHLIST
    )

    summary = {
        "scan_time_et": now_et.strftime("%Y-%m-%d %H:%M:%S ET"),
        "market_open": is_open,
        "tickers_scanned": len(tickers),
        "signals": [],
        "no_signal": [],
        "errors": [],
    }

    if not is_open:
        summary["warning"] = (
            "Market is currently closed. "
            "Next open: next trading day 09:30 ET (15:30 CET)"
        )
        # Scan anyway for testing / post-market analysis
        print("⚠️  Market closed – running scan anyway (historical day data).")

    print(f"🔍 Starting ORB scan for {len(tickers)} ticker(s)...")

    for ticker in tickers:
        print(f"   → {ticker}", end=" ", flush=True)
        res = scan_ticker(ticker)
        if res["status"] == "signal":
            summary["signals"].append(res)
            print(f"✅ SIGNAL ({res['direction']}, {res['scenario']})")
        elif res["status"] in ("no_data", "no_or"):
            summary["errors"].append(res)
            print(f"❌ {res.get('error', 'Error')}")
        else:
            summary["no_signal"].append({"ticker": ticker, "status": res["status"]})
            print("– no signal")

    # Save JSON
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Scan complete. {len(summary['signals'])} signal(s) found.")
    print(f"   Results saved: {args.output}")


if __name__ == "__main__":
    main()

"""
markets.py — market data section via Yahoo Finance v8 chart API.
No third-party dependencies: stdlib urllib only.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from typing import Dict, List, Optional

# ── ANSI colour constants (set by updateme.py) ───────────────────────────────
GREEN = ""
RED = ""
RESET = ""


def pct_change(closes: List[float], n: int) -> Optional[float]:
    """Return percentage change over the last n days.

    Requires at least n+1 data points. Returns None if insufficient data
    or if the base price is zero.
    """
    if len(closes) <= n:
        return None
    base = closes[-(n + 1)]
    if base == 0:
        return None
    return (closes[-1] - base) / base * 100


def fmt_pct(v: Optional[float]) -> str:
    """Format a percentage value as '+1.23%' or 'N/A'."""
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"


def parse_ticker_response(data: dict, ticker: str) -> dict:
    """Extract name, price, and closes list from a Yahoo Finance v8 chart response.

    Filters out None and bool values from the closes list (Yahoo sometimes
    returns null entries for non-trading days).

    Returns a dict with keys: ticker, name, price, closes.
    On any parse error returns a dict with empty/fallback values.
    """
    try:
        result = data["chart"]["result"][0]
        meta = result["meta"]
        raw_closes = result["indicators"]["quote"][0]["close"]
        closes = [c for c in raw_closes if isinstance(c, (int, float)) and not isinstance(c, bool)]
        name = (meta.get("shortName") or meta.get("longName") or meta.get("symbol") or ticker)[:25]
        price = meta.get("regularMarketPrice") or (closes[-1] if closes else None)
    except Exception:
        return {"ticker": ticker, "name": ticker, "price": None, "closes": []}

    return {"ticker": ticker, "name": name, "price": price, "closes": closes}


def _colored_pct(val_str: str, use_color: bool) -> str:
    """Wrap a formatted percentage string in ANSI colour codes."""
    if not use_color:
        return val_str
    if val_str.startswith("+"):
        return f"{GREEN}{val_str}{RESET}"
    if val_str.startswith("-"):
        return f"{RED}{val_str}{RESET}"
    return val_str


def _fetch_ticker_data(ticker: str) -> Optional[dict]:
    """Fetch raw JSON from Yahoo Finance for a single ticker. Returns None on error."""
    import urllib.parse
    encoded = urllib.parse.quote(ticker)
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}"
        "?interval=1d&range=2y"
    )
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; updateme/2.0)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def show_markets(cfg) -> None:
    """Fetch and print the markets section."""
    from updateme import section_header, warn  # type: ignore

    section_header("MARKETS")

    # Set module-level colour vars from cfg
    global GREEN, RED, RESET
    if cfg.use_color and sys.stdout.isatty():
        GREEN = "\033[32m"
        RED = "\033[31m"
        RESET = "\033[0m"

    all_tickers = ["^GSPC", "^IXIC"] + list(cfg.tickers)

    periods = [
        ("1 WK", cfg.period_week),
        ("1 MO", cfg.period_month),
        ("3 MO", cfg.period_quarter),
        ("1 YR", cfg.period_year),
    ]

    header = f"  {'TICKER':<10} {'NAME':<24} {'PRICE':>11}"
    for label, _ in periods:
        header += f"  {label:>9}"
    print(header)
    print("  " + "-" * 80)

    for ticker in all_tickers:
        if not ticker:
            continue
        raw = _fetch_ticker_data(ticker)
        if raw is None:
            row = {"ticker": ticker, "name": ticker, "price": None, "closes": []}
        else:
            row = parse_ticker_response(raw, ticker)

        price_str = f"${row['price']:,.2f}" if row["price"] is not None else "N/A"
        line = f"  {row['ticker']:<10} {row['name']:<24} {price_str:>11}"

        for _, n in periods:
            val = pct_change(row["closes"], n)
            fmt = fmt_pct(val)
            colored = _colored_pct(fmt, cfg.use_color and sys.stdout.isatty())
            # Right-align the raw (uncoloured) text in a 9-char field, then prepend colour
            pad = 9 - len(fmt)
            line += "  " + " " * max(pad, 0) + colored

        print(line)

    print()

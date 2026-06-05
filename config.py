"""
updateme — user configuration
Edit this file to customise your daily briefing.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    # ── Weather ──────────────────────────────────────────────────────────────
    # City name, airport code, or "lat,lon" (e.g. "51.5074,-0.1278")
    location: str = "Houston, Texas"

    # Number of forecast days to show (1-7)
    forecast_days: int = 5

    # ── News headlines ────────────────────────────────────────────────────────
    # Optional: paste a free NewsAPI.org key here to get real-time headlines.
    # Leave blank to fall back to BBC News RSS (no key needed).
    # Get a free key at https://newsapi.org/register
    news_api_key: str = ""

    # Number of headlines to display
    headline_count: int = 8

    # NewsAPI country code (used only when news_api_key is set)
    news_country: str = "us"

    # ── Market data ───────────────────────────────────────────────────────────
    # Additional tickers beyond S&P 500 (^GSPC) and NASDAQ (^IXIC).
    # Use Yahoo Finance symbols. Examples: AAPL, MSFT, BTC-USD, GC=F (gold)
    tickers: List[str] = field(default_factory=lambda: ["BTC-USD"])

    # Lookback periods in trading days (approximate)
    # Week=5, Month=21, Quarter=63, Year=252
    period_week: int = 5
    period_month: int = 21
    period_quarter: int = 63
    period_year: int = 252

    # ── Display ───────────────────────────────────────────────────────────────
    # Set to False to disable colour output (e.g. if piping to a file)
    use_color: bool = True


# Singleton — import and edit this object to configure updateme
config = Config()

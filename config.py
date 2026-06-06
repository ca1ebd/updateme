"""
updateme — configuration loader
Reads config.yml from the same directory as this file.
"""
from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

_CONFIG_PATH = Path(__file__).parent / "config.yml"


@dataclass
class Config:
    location: str = "Houston, Texas"
    forecast_days: int = 5
    news_api_key: str = ""
    headline_count: int = 8
    news_country: str = "us"
    tickers: List[str] = field(default_factory=lambda: ["BTC-USD"])
    period_week: int = 5
    period_month: int = 21
    period_quarter: int = 63
    period_year: int = 252
    use_color: bool = True


def _load() -> Config:
    if not _CONFIG_PATH.exists():
        return Config()
    with _CONFIG_PATH.open() as f:
        data = yaml.safe_load(f) or {}
    return Config(**{k: v for k, v in data.items() if hasattr(Config, k)})


# Singleton — imported by updateme.py and the modules
config = _load()

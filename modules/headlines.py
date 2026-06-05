"""
headlines.py — headlines section via NewsAPI.org or BBC News RSS fallback.
No third-party dependencies: stdlib urllib + xml.etree.ElementTree.
"""
from __future__ import annotations

import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, List


def parse_rss(xml: str, count: int) -> List[dict]:
    """Parse BBC RSS XML into a list of {title, url} dicts (up to count items).

    Handles namespace stripping so ElementTree findall works without prefix.
    Returns an empty list on malformed XML or missing fields.
    """
    # Strip default namespace so findall(".//item") works without prefix
    xml = xml.replace(' xmlns="', ' xmlnsx="')
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []

    items = root.findall(".//item")
    results = []
    for item in items:
        if len(results) >= count:
            break
        title_el = item.find("title")
        link_el = item.find("link")
        if title_el is None or link_el is None:
            continue
        title = (title_el.text or "").strip()
        url = (link_el.text or "").strip()
        if title and url:
            results.append({"title": title, "url": url})
    return results


def parse_newsapi(data: dict, count: int) -> List[dict]:
    """Parse NewsAPI.org top-headlines JSON into a list of {title, url} dicts."""
    results = []
    for article in data.get("articles", [])[:count]:
        title = (article.get("title") or "").strip()
        url = (article.get("url") or "").strip()
        if title and url:
            results.append({"title": title, "url": url})
    return results


def _hyperlink(url: str, text: str, use_color: bool) -> str:
    """Return an OSC 8 clickable hyperlink string, or 'text <url>' fallback."""
    if use_color:
        return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"
    return f"{text}  <{url}>"


def _fetch_newsapi(key: str, country: str, count: int) -> List[dict]:
    """Fetch from NewsAPI.org. Returns parsed items or empty list on error."""
    url = (
        f"https://newsapi.org/v2/top-headlines"
        f"?country={country}&pageSize={count}&apiKey={key}"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("status") != "ok":
            return []
        return parse_newsapi(data, count)
    except Exception:
        return []


def _fetch_bbc_rss(count: int) -> List[dict]:
    """Fetch BBC News RSS feed. Returns parsed items or empty list on error."""
    req = urllib.request.Request(
        "https://feeds.bbci.co.uk/news/rss.xml",
        headers={"User-Agent": "updateme/2.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml = resp.read().decode("utf-8", errors="replace")
        return parse_rss(xml, count)
    except Exception:
        return []


def show_headlines(cfg) -> None:
    """Fetch and print the headlines section."""
    from updateme import section_header, warn  # type: ignore

    section_header("HEADLINES")

    use_color = cfg.use_color and sys.stdout.isatty()
    items: List[dict] = []
    source_label = ""

    if cfg.news_api_key:
        items = _fetch_newsapi(cfg.news_api_key, cfg.news_country, cfg.headline_count)
        source_label = "NewsAPI.org"

    if not items:
        items = _fetch_bbc_rss(cfg.headline_count)
        source_label = "BBC News RSS"

    if not items:
        warn("Could not fetch headlines. Check your network connection.")
        return

    for i, item in enumerate(items, start=1):
        link = _hyperlink(item["url"], item["title"], use_color)
        print(f"  {i:2}. {link}")

    dim = "\033[2m" if use_color else ""
    reset = "\033[0m" if use_color else ""
    print(f"\n  {dim}Source: {source_label}{reset}\n")

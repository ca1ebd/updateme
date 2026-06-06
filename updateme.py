#!/usr/bin/env python3
"""
updateme — daily terminal briefing
Weather  |  Headlines  |  Market data

Usage:
  ./updateme.py             run the full briefing
  ./updateme.py --weather   weather only
  ./updateme.py --news      headlines only
  ./updateme.py --markets   markets only
  ./updateme.py --help      show this message
"""
from __future__ import annotations

import argparse
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ── Public colour constants (used by modules too) ────────────────────────────
BOLD = ""
DIM = ""
RESET = ""
GREEN = ""
RED = ""
CYAN = ""
YELLOW = ""


def _init_colors(enabled: bool) -> None:
    global BOLD, DIM, RESET, GREEN, RED, CYAN, YELLOW
    if enabled and sys.stdout.isatty():
        BOLD   = "\033[1m"
        DIM    = "\033[2m"
        RESET  = "\033[0m"
        GREEN  = "\033[32m"
        RED    = "\033[31m"
        CYAN   = "\033[36m"
        YELLOW = "\033[33m"
    else:
        BOLD = DIM = RESET = GREEN = RED = CYAN = YELLOW = ""


# ── Shared helpers ────────────────────────────────────────────────────────────

def section_header(title: str) -> None:
    bar = "─" * 88
    print(f"\n{BOLD}{CYAN}{bar}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{bar}{RESET}\n")


def warn(msg: str) -> None:
    print(f"{YELLOW}  ⚠  {msg}{RESET}", file=sys.stderr)


# ── Argument parsing ──────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="updateme",
        description="Daily terminal briefing: weather, headlines, markets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "  (no flags)   Full briefing\n"
            "  --weather    Weather forecast only\n"
            "  --news       Headlines only\n"
            "  --markets    Market data only\n\n"
            "  Configuration: edit config.yml"
        ),
    )
    p.add_argument("--weather", action="store_true", help="Weather forecast only")
    p.add_argument("--news",    action="store_true", help="Headlines only")
    p.add_argument("--markets", action="store_true", help="Market data only")
    return p


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # If no section flag given, run all
    run_all = not (args.weather or args.news or args.markets)
    run_weather = run_all or args.weather
    run_news    = run_all or args.news
    run_markets = run_all or args.markets

    # Import config after arg parse so --help works without config errors
    from config import config  # type: ignore
    _init_colors(config.use_color)

    # Import modules (after color init so they see the colour globals)
    from modules.weather   import show_weather
    from modules.headlines import show_headlines
    from modules.markets   import show_markets

    # Date/time header
    now = datetime.now()
    time_str = now.strftime("%-I:%M %p") if config.time_format == "12h" else now.strftime("%H:%M")
    print(f"\n{BOLD}  {now.strftime('%A, %B %-d %Y')}  —  {time_str} {now.strftime('%Z')}{RESET}")

    # Build list of tasks to run in parallel
    tasks = []
    if run_weather:
        tasks.append(("weather",   show_weather,   config))
    if run_news:
        tasks.append(("headlines", show_headlines, config))
    if run_markets:
        tasks.append(("markets",   show_markets,   config))

    # Parallel fetch; output is captured per section and printed in order.
    # contextlib.redirect_stdout is NOT thread-safe (it mutates the global
    # sys.stdout), so we use a thread-local proxy instead.
    import io

    _tls = threading.local()

    class _TLSStdout:
        """Routes writes to a per-thread StringIO, or the real stdout."""
        def write(self, s):
            buf = getattr(_tls, "capture", None)
            return buf.write(s) if buf is not None else sys.__stdout__.write(s)
        def flush(self):
            buf = getattr(_tls, "capture", None)
            (buf if buf is not None else sys.__stdout__).flush()
        def isatty(self):
            return bool(sys.__stdout__ and sys.__stdout__.isatty())

    _real_stdout = sys.stdout
    sys.stdout = _TLSStdout()

    results: dict[str, str] = {}

    def run_section(name: str, fn, cfg) -> tuple[str, str]:
        buf = io.StringIO()
        _tls.capture = buf
        try:
            fn(cfg)
        except Exception as exc:
            return name, f"  ⚠  {name} failed: {exc}\n"
        finally:
            _tls.capture = None
        return name, buf.getvalue()

    order = [t[0] for t in tasks]

    with ThreadPoolExecutor(max_workers=len(tasks) or 1) as pool:
        futures = {
            pool.submit(run_section, name, fn, cfg): name
            for name, fn, cfg in tasks
        }
        for future in as_completed(futures):
            name, output = future.result()
            results[name] = output

    sys.stdout = _real_stdout

    # Print in canonical order
    for name in order:
        sys.stdout.write(results.get(name, ""))

    print()


if __name__ == "__main__":
    main()

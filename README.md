# updateme

A WSL bash morning briefing: weather, headlines, and market data — all in your terminal.

## Quick start

```bash
cd ~/Development/spikes/updateme   # or wherever you cloned/copied it
chmod +x updateme.sh
./updateme.sh
```

## Configuration

Open `config.sh` and adjust:

| Variable | Default | Description |
|---|---|---|
| `LOCATION` | `"New York"` | City, airport code, or `"lat,lon"` |
| `FORECAST_DAYS` | `7` | Days of weather forecast (1–7) |
| `NEWS_API_KEY` | *(blank)* | Optional [NewsAPI.org](https://newsapi.org/register) key |
| `HEADLINE_COUNT` | `8` | How many headlines to show |
| `TICKERS` | `(AAPL MSFT NVDA)` | Extra tickers beyond S&P 500 and NASDAQ |

### Adding tickers

Edit the `TICKERS` array in `config.sh`. Any [Yahoo Finance symbol](https://finance.yahoo.com) works:

```bash
TICKERS=(
  "AAPL"
  "TSLA"
  "BTC-USD"   # Bitcoin
  "GC=F"      # Gold futures
  "EURUSD=X"  # EUR/USD FX
)
```

### News: key vs. RSS fallback

- **With a NewsAPI key** — US top headlines via NewsAPI.org (free tier: 100 req/day)
- **Without a key** — BBC News RSS feed, parsed locally with python3, no account needed

Headlines are clickable hyperlinks in terminals that support OSC 8 (Windows Terminal, iTerm2, Kitty, WezTerm). In Windows Terminal, Ctrl+click opens the article.

## Usage

```
./updateme.sh              Full briefing
./updateme.sh --weather    Weather only
./updateme.sh --news       Headlines only
./updateme.sh --markets    Markets only
./updateme.sh --help       Help
```

## Run automatically on WSL login

Add to the bottom of your `~/.bashrc`:

```bash
# Show daily briefing once per shell session
if [[ -z "${BRIEFING_SHOWN:-}" ]]; then
  export BRIEFING_SHOWN=1
  ~/Development/spikes/updateme/updateme.sh
fi
```

## Dependencies

All standard in WSL (Ubuntu):

- `bash` 4+
- `curl`
- `python3` (for JSON parsing and RSS)
- `jq` (optional, used for JSON if available — faster than python3 inline)

No pip packages required.

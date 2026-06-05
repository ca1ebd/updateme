# updateme

A daily terminal briefing: weather, headlines, and market data — in one command.

```
  Friday, June 6 2026  —  09:00 CDT

  WEATHER -- Houston, Texas
  Now: Partly cloudy              82F  (feels 88F)  Wind 9mph  Humidity 78%

  Date           Condition                      High    Low   Rain
  -------------- ---------------------------- ------ ------ ------
  Fri Jun 6      Partly cloudy                  87°F   75°F    73%
  Sat Jun 7      Thunderstorm                   92°F   77°F    59%
  ...

  HEADLINES
   1. Title of article here          (clickable link in supported terminals)
   ...

  MARKETS
  TICKER     NAME                       PRICE      1 WK      1 MO      3 MO      1 YR
  ^GSPC      S&P 500                $5,012.34    +1.23%    +3.45%    +7.89%   +23.10%
  ...
```

## Install

### One-liner (macOS / Linux / WSL)

```bash
curl -fsSL https://raw.githubusercontent.com/ca1ebd/updateme/main/install.sh | bash
```

Then reload your shell and run `updateme`.

> **macOS note:** macOS ships with bash 3.2, which is too old. Install bash 4+ first:
> ```bash
> brew install bash
> ```
> Then re-run the installer.

### Manual install

```bash
git clone https://github.com/ca1ebd/updateme.git ~/.local/share/updateme
mkdir -p ~/.local/bin
cat > ~/.local/bin/updateme << 'EOF'
#!/usr/bin/env bash
exec bash "$HOME/.local/share/updateme/updateme.sh" "$@"
EOF
chmod +x ~/.local/bin/updateme
```

Make sure `~/.local/bin` is in your PATH (add to `~/.zshrc`, `~/.bashrc`, or `~/.bash_profile`):

```bash
export PATH="${HOME}/.local/bin:${PATH}"
```

## Configuration

Edit `~/.local/share/updateme/config.sh`:

| Variable | Default | Description |
|---|---|---|
| `LOCATION` | `"New York"` | City name, airport code, or `"lat,lon"` |
| `FORECAST_DAYS` | `7` | Days of forecast shown (1–5) |
| `NEWS_API_KEY` | *(blank)* | Optional [NewsAPI.org](https://newsapi.org/register) key — falls back to BBC RSS if blank |
| `HEADLINE_COUNT` | `8` | Number of headlines |
| `TICKERS` | `(AAPL MSFT NVDA)` | Additional tickers beyond S&P 500 and NASDAQ |

### Adding tickers

Any [Yahoo Finance](https://finance.yahoo.com) symbol works:

```bash
TICKERS=(
  "AAPL"
  "TSLA"
  "BTC-USD"   # Bitcoin
  "GC=F"      # Gold futures
  "EURUSD=X"  # EUR/USD
)
```

## Usage

```
updateme              Full briefing
updateme --weather    Weather only
updateme --news       Headlines only
updateme --markets    Markets only
updateme --help       Help
```

## Run automatically on login

**zsh** (`~/.zshrc`):
```bash
if [[ -z "${BRIEFING_SHOWN:-}" ]]; then
  export BRIEFING_SHOWN=1
  updateme
fi
```

**bash** (`~/.bashrc` or `~/.bash_profile`):
```bash
[ -z "${BRIEFING_SHOWN:-}" ] && export BRIEFING_SHOWN=1 && updateme
```

## Requirements

| Dependency | macOS | Linux / WSL |
|---|---|---|
| bash 4+ | `brew install bash` | Usually pre-installed |
| curl | Pre-installed | Usually pre-installed |
| python3 | `brew install python` or Xcode CLI tools | Usually pre-installed |

Headline links are clickable in terminals that support OSC 8: **iTerm2**, **WezTerm**, **Kitty**, **Windows Terminal**.

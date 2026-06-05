#!/usr/bin/env bash
# Markets module -- Yahoo Finance, no API key required

_fetch_ticker() {
  local ticker="$1"
  local encoded_ticker
  encoded_ticker=$(python3 -c \
    "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" \
    "$ticker")

  # Use 2y range so the 1Y (~252d) lookback always has enough data
  local url="https://query1.finance.yahoo.com/v8/finance/chart/${encoded_ticker}?interval=1d&range=2y"

  local resp
  resp=$(curl -fsSL --max-time 15 \
    -H "User-Agent: Mozilla/5.0 (compatible; updateme/1.0)" \
    "$url" 2>/dev/null)

  if [[ $? -ne 0 || -z "$resp" ]]; then
    echo -e "${ticker}\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A"
    return 1
  fi

  MARKET_JSON="$resp" python3 - \
    "$ticker" \
    "${PERIOD_WEEK:-5}" \
    "${PERIOD_MONTH:-21}" \
    "${PERIOD_QUARTER:-63}" \
    "${PERIOD_YEAR:-252}" <<'PYEOF'
import sys, os, json

ticker = sys.argv[1]
p_week = int(sys.argv[2])
p_month = int(sys.argv[3])
p_qtr  = int(sys.argv[4])
p_year = int(sys.argv[5])

try:
    data   = json.loads(os.environ.get("MARKET_JSON", "{}"))
    result = data["chart"]["result"][0]
    meta   = result["meta"]
    closes = result["indicators"]["quote"][0]["close"]
    closes = [c for c in closes if isinstance(c, (int, float))]
    name   = (meta.get("shortName") or meta.get("symbol") or ticker)[:22]
    price  = meta.get("regularMarketPrice") or closes[-1]
except Exception:
    print(f"{ticker}\t???\t???\t???\t???\t???\t???")
    sys.exit(0)

def pct(closes, n):
    if len(closes) <= n:
        return None
    old = closes[-(n+1)]
    if old == 0:
        return None
    return (closes[-1] - old) / old * 100

def fmt(v):
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"

print(f"{ticker}\t{name}\t${price:,.2f}\t{fmt(pct(closes,p_week))}\t{fmt(pct(closes,p_month))}\t{fmt(pct(closes,p_qtr))}\t{fmt(pct(closes,p_year))}")
PYEOF
}

# Print a right-aligned pct cell of fixed width, with colour
_pct_cell() {
  local val="$1"
  local width="${2:-9}"
  local colored
  if [[ "${USE_COLOR:-1}" -eq 1 ]]; then
    case "$val" in
      +*) colored="${GREEN:-}${val}${RESET:-}" ;;
      -*) colored="${RED:-}${val}${RESET:-}" ;;
      *)  colored="$val" ;;
    esac
  else
    colored="$val"
  fi
  # Right-align the visible text; pad before the colour codes
  local pad=$(( width - ${#val} ))
  printf '%*s%s' "$pad" '' "$colored"
}

show_markets() {
  section_header "MARKETS"

  local all_tickers=("^GSPC" "^IXIC" "${TICKERS[@]}")

  printf '  %-10s %-23s %11s  %9s  %9s  %9s  %9s\n' \
    "TICKER" "NAME" "PRICE" "1 WK" "1 MO" "3 MO" "1 YR"
  printf '  %s\n' "$(printf -- '-%.0s' {1..80})"

  for ticker in "${all_tickers[@]}"; do
    [[ -z "$ticker" ]] && continue
    local row
    row=$(_fetch_ticker "$ticker")
    IFS=$'\t' read -r sym name price w m q y <<< "$row"

    printf '  %-10s %-23s %11s' "$sym" "$name" "$price"
    printf '  '
    _pct_cell "$w" 9
    printf '  '
    _pct_cell "$m" 9
    printf '  '
    _pct_cell "$q" 9
    printf '  '
    _pct_cell "$y" 9
    printf '\n'
  done
  echo
}

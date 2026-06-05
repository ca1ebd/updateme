#!/usr/bin/env bash
# Weather module -- 5-day forecast via Open-Meteo (free, no key required)
# Current conditions via wttr.in JSON

show_weather() {
  local location="${LOCATION:-New York}"

  section_header "WEATHER -- ${location}"

  local encoded
  encoded=$(python3 -c \
    "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" \
    "$location")

  # For geocoding, use only the city portion (text before first comma)
  local city_only
  city_only=$(python3 -c \
    "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1].split(',')[0].strip()))" \
    "$location")

  # --- Geocode via Open-Meteo ---
  local geo
  geo=$(curl -fsSL --max-time 10 \
    -H "User-Agent: curl/updateme-1.0" \
    "https://geocoding-api.open-meteo.com/v1/search?name=${city_only}&count=1&language=en&format=json" \
    2>/dev/null)

  if [[ $? -ne 0 || -z "$geo" ]]; then
    warn "Could not geocode location: ${location}"
    return 1
  fi

  # --- Current conditions via wttr.in ---
  local wttr
  wttr=$(curl -fsSL --max-time 10 \
    -H "User-Agent: curl/updateme-1.0" \
    "https://wttr.in/${encoded}?format=j1" 2>/dev/null)

  # --- Render ---
  GEO_JSON="$geo" WTTR_JSON="$wttr" python3 <<'PYEOF'
import os, json, urllib.request, urllib.parse
from datetime import datetime

geo_raw  = os.environ.get("GEO_JSON", "{}")
wttr_raw = os.environ.get("WTTR_JSON", "{}")

try:
    results = json.loads(geo_raw).get("results") or []
    if not results:
        print("  (could not find location -- try a simpler city name in config.sh)")
        exit(0)
    r   = results[0]
    lat = r["latitude"]
    lon = r["longitude"]
    tz  = r.get("timezone", "UTC")
except Exception as e:
    print(f"  (geocode error: {e})")
    exit(0)

params = urllib.parse.urlencode({
    "latitude": lat, "longitude": lon,
    "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
    "temperature_unit": "fahrenheit",
    "forecast_days": 5,
    "timezone": tz,
})
try:
    with urllib.request.urlopen(
        f"https://api.open-meteo.com/v1/forecast?{params}", timeout=10
    ) as resp:
        daily = json.loads(resp.read()).get("daily", {})
    dates    = daily.get("time", [])
    codes    = daily.get("weathercode", [])
    hi_arr   = daily.get("temperature_2m_max", [])
    lo_arr   = daily.get("temperature_2m_min", [])
    rain_arr = daily.get("precipitation_probability_max", [])
except Exception as e:
    print(f"  (forecast error: {e})")
    exit(0)

WMO = {
    0:"Clear sky", 1:"Mainly clear", 2:"Partly cloudy", 3:"Overcast",
    45:"Fog", 48:"Icy fog",
    51:"Light drizzle", 53:"Drizzle", 55:"Heavy drizzle",
    61:"Light rain", 63:"Rain", 65:"Heavy rain",
    71:"Light snow", 73:"Snow", 75:"Heavy snow", 77:"Snow grains",
    80:"Light showers", 81:"Showers", 82:"Heavy showers",
    85:"Slight snow showers", 86:"Heavy snow showers",
    95:"Thunderstorm", 96:"Thunderstorm + hail", 99:"Thunderstorm + heavy hail",
}

# Current conditions from wttr.in
try:
    cur = (json.loads(wttr_raw).get("current_condition") or [{}])[0]
    desc  = ((cur.get("weatherDesc") or [{}])[0]).get("value", "")
    temp  = cur.get("temp_F", "?")
    feels = cur.get("FeelsLikeF", "?")
    wind  = cur.get("windspeedMiles", "?")
    humid = cur.get("humidity", "?")
    print(f"  Now: {desc:<26}  {temp}F  (feels {feels}F)  Wind {wind}mph  Humidity {humid}%")
except Exception:
    pass

print()
print(f"  {'Date':<14} {'Condition':<28} {'High':>6} {'Low':>6} {'Rain':>6}")
print(f"  {'-'*14} {'-'*28} {'-'*6} {'-'*6} {'-'*6}")

for i, date_str in enumerate(dates):
    try:
        label = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a %b %-d")
    except Exception:
        label = date_str
    code = codes[i] if i < len(codes) else 0
    desc = WMO.get(code, f"WMO {code}")[:27]
    hi   = f"{hi_arr[i]:.0f}"   if i < len(hi_arr)   and hi_arr[i]   is not None else "?"
    lo   = f"{lo_arr[i]:.0f}"   if i < len(lo_arr)   and lo_arr[i]   is not None else "?"
    rain = f"{int(rain_arr[i])}" if i < len(rain_arr) and rain_arr[i] is not None else "?"
    print(f"  {label:<14} {desc:<28} {hi+chr(176)+'F':>6} {lo+chr(176)+'F':>6} {rain+'%':>6}")

print()
PYEOF
}

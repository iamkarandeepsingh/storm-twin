"""Turn a weather blob into the two numbers the rules use.

Accepts the replay input's `weather` ({"daily": ..., "hourly": ...}) in either list-of-records or
column (Open-Meteo style: {"time": [...], "temperature_2m": [...]}) form, plus our own simple form
used in config/weather/*.json: {"min_temp_c": -14, "snow_cm": 20}.

weather_min_temp_c : coldest temperature from 12 h before the callout to 6 h after (hourly if given),
                     else the daily minimum of the callout date (and the day before if the callout is before 06:00).
weather_snow_cm    : total snowfall for the storm (sum over the window / storm days).
"""
from datetime import datetime, timedelta

TEMP_KEYS = ("temp_c", "temperature_c", "temperature_2m", "temperature", "temp", "air_temp_c")
TMIN_KEYS = ("min_temp_c", "tmin_c", "temp_min_c", "temperature_2m_min", "min_temp", "low_c", "tmin", "min_c",
             "temperature_min", "temp_min", "low", "min_temperature_c", "min_temperature")
PRECIP_KEYS = ("precip_mm", "precipitation_mm", "precipitation", "total_precip_mm", "precipitation_sum", "precip")
SNOW_KEYS = ("snow_cm", "snowfall_cm", "total_snow_cm", "snowfall_sum", "snowfall", "snow", "new_snow_cm",
             "snow_total_cm", "total_snow", "snow_accumulation_cm")
TIME_KEYS = ("time", "datetime", "date", "time_local", "local", "date_local", "datetime_local")


def _records(block):
    if block is None:
        return []
    if isinstance(block, dict) and block and all(isinstance(v, dict) for v in block.values()):
        return [dict(v, date=v.get("date", k)) for k, v in block.items()]  # {"2026-01-15": {...}}
    if isinstance(block, list):
        return [r for r in block if isinstance(r, dict)]
    if isinstance(block, dict):
        cols = {k: v for k, v in block.items() if isinstance(v, list)}
        if cols:
            n = max(len(v) for v in cols.values())
            return [{k: (v[i] if i < len(v) else None) for k, v in cols.items()} for i in range(n)]
        return [block]
    return []


def _get(r, keys):
    for k in keys:
        if r.get(k) is not None:
            return r[k]
    for k, v in r.items():  # tolerate unit suffixes like "temperature_2m (°C)"
        if v is not None and any(k.lower().startswith(p) for p in keys):
            return v
    return None


def _t(r):
    s = _get(r, TIME_KEYS)
    if not s:
        return None
    s = str(s).replace("Z", "")
    try:
        return datetime.fromisoformat(s[:19] if "T" in s or " " in s else s[:10])
    except ValueError:
        return None


def summarize(weather, callout_local):
    w = weather or {}
    out = {"weather_min_temp_c": None, "weather_snow_cm": None, "weather_source": None}
    if not isinstance(w, dict):
        return out
    # simple override form
    if _get(w, TMIN_KEYS) is not None or _get(w, SNOW_KEYS) is not None:
        out.update(weather_min_temp_c=_get(w, TMIN_KEYS), weather_snow_cm=_get(w, SNOW_KEYS), weather_source="simple")
    c = datetime.fromisoformat(callout_local) if callout_local else None
    hourly = _records(w.get("hourly"))
    if hourly and c:
        win = [r for r in hourly if _t(r) and c - timedelta(hours=12) <= _t(r) <= c + timedelta(hours=6)]
        temps = [_get(r, TEMP_KEYS) for r in win if _get(r, TEMP_KEYS) is not None]
        if temps:
            out["weather_min_temp_c"] = min(temps)
            out["weather_source"] = "hourly"
        storm = [r for r in hourly if _t(r) and c - timedelta(hours=6) <= _t(r) <= c + timedelta(hours=24)]
        snow = [_get(r, SNOW_KEYS) for r in storm if _get(r, SNOW_KEYS) is not None]
        if snow and out["weather_snow_cm"] is None:
            out["weather_snow_cm"] = round(sum(snow), 1)
    daily = _records(w.get("daily"))
    if daily:
        days = {(_t(r).date() if _t(r) else None): r for r in daily}
        pick = [r for d, r in days.items() if c is None or d is None or d == c.date()
                or (c.hour < 6 and d == (c - timedelta(days=1)).date())]
        pick = pick or daily
        if out["weather_min_temp_c"] is None:
            mins = [_get(r, TMIN_KEYS) for r in pick if _get(r, TMIN_KEYS) is not None]
            if mins:
                out["weather_min_temp_c"] = min(mins)
                out["weather_source"] = out["weather_source"] or "daily"
        if out["weather_snow_cm"] is None:
            # snowfall on the callout date (backtest: the next day's snow belongs to the next storm)
            same = [r for d, r in days.items() if c is None or d is None or d == c.date()] or daily
            snow = [_get(r, SNOW_KEYS) for r in same if _get(r, SNOW_KEYS) is not None]
            if snow:
                out["weather_snow_cm"] = round(sum(snow), 1)
    if out["weather_snow_cm"] is None and c is not None:
        pr = [_get(r, PRECIP_KEYS) for r in hourly if _t(r) and c - timedelta(hours=6) <= _t(r) <= c + timedelta(hours=24)]
        if not [x for x in pr if x is not None] and daily:
            pr = [_get(r, PRECIP_KEYS) for r in daily if _t(r) and _t(r).date() == c.date()]
        pr = [x for x in pr if isinstance(x, (int, float))]
        cold = out["weather_min_temp_c"] is not None and out["weather_min_temp_c"] <= 0
        if pr and cold:
            out["weather_snow_cm"] = round(sum(pr), 1)
            out["weather_source"] = (out["weather_source"] or "") + "+snow_from_precip(1mm~1cm)"
    for k in ("weather_min_temp_c", "weather_snow_cm"):
        if out[k] is not None and not isinstance(out[k], (int, float)):
            try:
                out[k] = float(out[k])
            except (TypeError, ValueError):
                out[k] = None
    return out


def warnings(summary):
    w = []
    if summary.get("weather_min_temp_c") is None:
        w.append("WARNING: no temperature found in weather input -> cold no-start rule cannot fire")
    if summary.get("weather_snow_cm") is None:
        w.append("WARNING: no snowfall found in weather input -> hydraulic rule cannot fire")
    return w

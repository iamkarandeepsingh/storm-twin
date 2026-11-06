"""Prediction engine: data + weather + scenario -> per-truck label, reason, action."""
import copy
from datetime import timedelta

from . import features, rules, weather as wx


def apply_scenario(feats, scenario):
    """What-if changes, stated as explicit assumptions (a repair is assumed fully effective)."""
    s = scenario or {}
    if feats["truck"] in s.get("battery_replaced", []):
        feats["battery_v_latest"] = s.get("assumed_new_battery_v", 12.75)
        feats["scenario"] = feats.get("scenario", []) + ["battery replaced (assumed)"]
    if feats["truck"] in s.get("hydraulic_serviced", []):
        feats["pto_since_hyd_service"] = 0.0
        feats["scenario"] = feats.get("scenario", []) + ["hydraulic service (assumed)"]
    return feats


def action_for(label, feats, cfg):
    a = cfg.get("actions", {})
    if label == "no_start":
        return a.get("no_start", "Replace/charge batteries before callout; else hold")
    if label == "hydraulic":
        return a.get("hydraulic", "Hydraulic service before callout; else hold")
    m = cfg.get("watch_margins", {})
    v, p = feats.get("battery_v_latest"), feats.get("pto_since_hyd_service")
    if (v is not None and v <= m.get("battery_v", 12.30)) or (p is not None and p >= m.get("pto_since_hyd_service", 170)):
        return a.get("watch", "Deploy; inspect first (near a failure threshold)")
    return a.get("ok", "Deploy")


def predict(data, cfg, callout_local, weather, trucks=None, scenario=None, index=None):
    tz = cfg["timezone"]
    as_of = features.local_to_utc(callout_local, tz)
    idx = index or features.TruckIndex(data, tz)
    w = wx.summarize(weather, callout_local)
    s = scenario or {}
    w_over = s.get("weather_override") or {}
    for k in ("weather_min_temp_c", "weather_snow_cm"):
        if w_over.get(k) is not None:
            w[k] = w_over[k]
    names = trucks or sorted({v.get("name") or v.get("id") for v in data.get("Vehicle", [])})
    names = [n for n in names if n not in s.get("removed", [])]
    out = {}
    for n in names:
        f = idx.features(n, as_of)
        f.update(w)
        f = apply_scenario(f, s)
        label, why = rules.classify(f, cfg["rules"])
        out[n] = {"label": label, "reasons": why, "action": action_for(label, f, cfg), "features": f}
    return out, w

"""stormtwin CLI.

  python -m stormtwin fetch                                   # online, needs FLEET_API_KEY
  python -m stormtwin replay --input X.json --output Y.json   # offline, REPLAY_COMMAND
"""
import argparse
import json
from pathlib import Path

from . import features, rules

ROOT = Path(__file__).resolve().parent.parent


def load_cfg(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_raw(cfg):
    raw = ROOT / cfg["raw_dir"]
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in raw.glob("*.json") if not p.stem.startswith("_")}


def weather_features(weather):
    """PROVISIONAL: replay input weather has `daily` and `hourly`; exact keys to confirm."""
    out = {}
    temps = []
    for h in (weather or {}).get("hourly", []) or []:
        for k in ("temp_c", "temperature_c", "temp", "temperature"):
            if isinstance(h, dict) and h.get(k) is not None:
                temps.append(h[k]); break
    if not temps:
        for d in (weather or {}).get("daily", []) or ([weather.get("daily")] if isinstance((weather or {}).get("daily"), dict) else []):
            for k in ("min_temp_c", "tmin_c", "min_temp", "low_c"):
                if isinstance(d, dict) and d.get(k) is not None:
                    temps.append(d[k]); break
    out["weather_min_temp_c"] = min(temps) if temps else None
    return out


def predict(inp, cfg, data):
    tz = cfg["timezone"]
    as_of = features.local_to_utc(inp["callout_local"], tz)
    extra = inp.get("records_since_your_data_ends", {}) or {}
    merged = {k: list(data.get(k, [])) + list(extra.get(k, [])) for k in set(data) | set(extra)}
    dev_map = features.device_for_truck(merged.get("DeviceAssignment", []), as_of)
    wx = weather_features(inp.get("weather"))
    trucks = inp.get("trucks") or sorted(dev_map)
    names = [t if isinstance(t, str) else (t.get("name") or t.get("truck")) for t in trucks]
    labels, detail = {}, {}
    for name in names:
        f = features.truck_features(name, dev_map.get(name), merged, as_of, tz)
        f.update(wx)
        label, why = rules.classify(f, cfg["rules"])
        labels[name] = label
        detail[name] = {"label": label, "reasons": why, "features": f}
    return labels, detail


def main(argv=None):
    ap = argparse.ArgumentParser(prog="stormtwin")
    ap.add_argument("--config", default=str(ROOT / "config" / "settings.json"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch")
    rp = sub.add_parser("replay")
    rp.add_argument("--input", required=True)
    rp.add_argument("--output", required=True)
    rp.add_argument("--explain", help="optional path for per-truck features and reasons")
    a = ap.parse_args(argv)
    cfg = load_cfg(a.config)

    if a.cmd == "fetch":
        from . import fetch
        fetch.run(cfg, ROOT)
    elif a.cmd == "replay":
        inp = json.loads(Path(a.input).read_text(encoding="utf-8"))
        labels, detail = predict(inp, cfg, load_raw(cfg))
        Path(a.output).parent.mkdir(parents=True, exist_ok=True)
        Path(a.output).write_text(json.dumps({"persona": "maintenance", "trucks": labels}, indent=2), encoding="utf-8")
        if a.explain:
            Path(a.explain).write_text(json.dumps(detail, indent=2, default=str), encoding="utf-8")
        print(json.dumps({k: sum(v == k for v in labels.values()) for k in ("ok", "no_start", "hydraulic")}))


if __name__ == "__main__":
    main()

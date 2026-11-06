"""stormtwin: maintenance-lead what-if engine for the Credit Valley snowplow fleet.

  python -m stormtwin fetch                                    # online, needs FLEET_API_KEY
  python -m stormtwin replay --input X.json --output Y.json    # offline; the REPLAY_COMMAND
  python -m stormtwin backtest                                 # score the rules on last winter
  python -m stormtwin whatif --weather config/weather/tonight.json [--scenario scenarios/x.json]
"""
import argparse
import sys
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

from . import engine, features, report, weather as wxmod

ROOT = Path(__file__).resolve().parent.parent


def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def load_raw(cfg):
    raw = ROOT / cfg["raw_dir"]
    return {p.stem: load_json(p) for p in raw.glob("*.json") if not p.stem.startswith("_")}


def merge(data, extra):
    extra = extra or {}
    return {k: list(data.get(k, [])) + list(extra.get(k, []) or []) for k in set(data) | set(extra)}


def truck_names(trucks):
    if isinstance(trucks, dict):
        return sorted(trucks)
    out = []
    for t in trucks or []:
        out.append(t if isinstance(t, str) else (t.get("name") or t.get("truck") or t.get("vehicleName") or t.get("id")))
    return out or None


def historical_weather(cfg):
    rows = []
    for p in sorted((ROOT / cfg["weather_dir"]).glob("*.csv")):
        with open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                def num(k):
                    try:
                        return float(r[k])
                    except (TypeError, ValueError, KeyError):
                        return None
                rows.append({"date": r["date"], "min_temp_c": num("min_c"), "snow_cm": num("snow_cm")})
    return {"daily": rows}


def write(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


def table(res, base=None):
    lines = [f"{'truck':6} {'label':9} {'battV':>6} {'PTOsvc':>7}  action" + ("   [baseline]" if base else "")]
    order = {"no_start": 0, "hydraulic": 1, "ok": 2}
    for n, r in sorted(res.items(), key=lambda kv: (order[kv[1]["label"]], kv[0])):
        f = r["features"]
        v = "-" if f.get("battery_v_latest") is None else f"{f['battery_v_latest']:.2f}"
        p = "-" if f.get("pto_since_hyd_service") is None else f"{f['pto_since_hyd_service']:.1f}"
        b = f"   [{base[n]['label']}]" if base and n in base and base[n]["label"] != r["label"] else ""
        lines.append(f"{n:6} {r['label']:9} {v:>6} {p:>7}  {r['action']}{b}")
    return "\n".join(lines)


def cmd_replay(a, cfg):
    inp = load_json(a.input)
    data = merge(load_raw(cfg), inp.get("records_since_your_data_ends"))
    res, w = engine.predict(data, cfg, inp["callout_local"], inp.get("weather"), truck_names(inp.get("trucks")))
    write(a.output, {"persona": "maintenance", "trucks": {n: r["label"] for n, r in res.items()}})
    warn = wxmod.warnings(w)
    for m in warn:
        print(m, file=sys.stderr)
    if a.explain:
        write(a.explain, {"weather_used": w, "warnings": warn, "trucks": res})
    print(json.dumps({"weather_used": w, "counts": {k: sum(r["label"] == k for r in res.values()) for k in ("ok", "no_start", "hydraulic")}}))


def cmd_backtest(a, cfg):
    data = load_raw(cfg)
    idx = features.TruckIndex(data, cfg["timezone"])
    weather = historical_weather(cfg)
    wo, da = data["WorkOrder"], data["DispatchAssignment"]
    rows, tot = [], {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for c in sorted(data["Callout"], key=lambda c: c["calloutLocal"]):
        cl = datetime.fromisoformat(c["calloutLocal"])
        called = sorted({d["vehicleName"] for d in da if d["calloutId"] == c["id"]})
        actual = {n: "ok" for n in called}
        for w in wo:  # no-starts reported around the callout (trucks that never went out are not in dispatch)
            if w.get("reason") == "NO_START" and abs(datetime.fromisoformat(w["openedLocal"]) - cl) <= timedelta(hours=3):
                actual[w["vehicleName"]] = "no_start"
        for d in da:
            if d["calloutId"] == c["id"] and d["status"] == "BROKEN_DOWN":
                actual[d["vehicleName"]] = "hydraulic"
        res, w = engine.predict(data, cfg, c["calloutLocal"], weather, sorted(actual), index=idx)
        for n, act in actual.items():
            pred = res[n]["label"]
            k = ("tp" if pred == act else "fn") if act != "ok" else ("fp" if pred != "ok" else "tn")
            if pred != "ok" and act != "ok" and pred != act:
                k = "fn"
            tot[k] += 1
            if act != "ok" or pred != "ok":
                rows.append(f"  {c['calloutLocal']}  {n}  actual={act:9} pred={pred:9} {'OK' if pred == act else 'MISS'}"
                            f"  V={res[n]['features'].get('battery_v_latest')} PTOsvc={res[n]['features'].get('pto_since_hyd_service')}"
                            f"  Tmin={w['weather_min_temp_c']} snow={w['weather_snow_cm']}")
    print("Callout nights (last winter, rules from config):")
    print("\n".join(rows))
    print(f"truck-nights={sum(tot.values())}  correct failures={tot['tp']}  missed={tot['fn']}  false alarms={tot['fp']}  correct ok={tot['tn']}")

    # every morning start (05:00) of last winter: tests the cold no-start rule on far more days
    ns = {(w["vehicleName"], w["openedLocal"][:10]) for w in wo if w.get("reason") == "NO_START"}
    trucks = sorted({v["name"] for v in data["Vehicle"]})
    m = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    misses = []
    for day in weather["daily"]:
        if not ("2025-12-02" <= day["date"] <= "2026-01-23"):
            continue
        res, w = engine.predict(data, cfg, day["date"] + "T05:00:00", {"daily": [day]}, trucks, index=idx)
        for n in trucks:
            act, pred = (n, day["date"]) in ns, res[n]["label"] == "no_start"
            k = {(True, True): "tp", (False, True): "fp", (True, False): "fn", (False, False): "tn"}[(act, pred)]
            m[k] += 1
            if k in ("fp", "fn"):
                misses.append(f"  {day['date']} {n} {k} V={res[n]['features'].get('battery_v_latest')} Tmin={w['weather_min_temp_c']}")
    print(f"\nEvery morning start Dec 2-Jan 23 (no-start rule): no-starts caught={m['tp']}/{m['tp'] + m['fn']}  false alarms={m['fp']}  truck-days={sum(m.values())}")
    print("\n".join(misses))


def cmd_whatif(a, cfg):
    data = load_raw(cfg)
    callout = a.callout or cfg["tonight"]["callout_local"]
    weather = load_json(a.weather) if a.weather else load_json(ROOT / cfg["tonight"]["weather_file"])
    idx = features.TruckIndex(data, cfg["timezone"])
    base, wb = engine.predict(data, cfg, callout, weather, index=idx)
    if a.scenario:
        sc = load_json(a.scenario)
        res, w = engine.predict(data, cfg, callout, weather, scenario=sc, index=idx)
        print(f"SCENARIO {a.scenario}: {sc.get('description', '')}")
    else:
        res, w = base, wb
        print("BASELINE")
    print(f"callout {callout}  weather used: min {w['weather_min_temp_c']} C, snow {w['weather_snow_cm']} cm ({w['weather_source']})")
    counts = {k: sum(r["label"] == k for r in res.values()) for k in ("ok", "no_start", "hydraulic")}
    print(f"ready={counts['ok']}  no_start={counts['no_start']}  hydraulic={counts['hydraulic']}  removed={len(base) - len(res)}")
    print(table(res, base if a.scenario else None))
    for m in wxmod.warnings(w):
        print(m)
    if a.out:
        write(a.out, {"callout_local": callout, "weather_used": w, "counts": counts, "trucks": res})
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(report.render(callout, w, res, cfg, base if a.scenario else None,
                                                sc if a.scenario else None), encoding="utf-8")
        print(f"report written: {a.report}")


def cmd_ui(a, cfg):
    from . import ui
    presets = []
    for p in cfg.get("ui_presets", []):
        w = load_json(ROOT / p["weather_file"])
        presets.append({"name": p["name"], "callout_local": w.get("callout_local") or p.get("callout_local") or cfg["tonight"]["callout_local"],
                        "weather": w})
    html = ui.build(load_raw(cfg), cfg, presets)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(html, encoding="utf-8")
    print(f"dashboard written: {a.out}  (open it in a browser)")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="stormtwin")
    ap.add_argument("--config", default=str(ROOT / "config" / "settings.json"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch")
    rp = sub.add_parser("replay")
    rp.add_argument("--input", required=True)
    rp.add_argument("--output", required=True)
    rp.add_argument("--explain")
    sub.add_parser("backtest")
    wp = sub.add_parser("whatif")
    wp.add_argument("--weather", help="weather JSON (default: tonight's file from config)")
    wp.add_argument("--scenario", help="scenario JSON: battery_replaced, hydraulic_serviced, removed, weather_override")
    wp.add_argument("--callout", help="callout local time (default from config)")
    wp.add_argument("--out", help="write full JSON result here")
    wp.add_argument("--report", help="write a one-page Markdown report here")
    up = sub.add_parser("ui", help="write a single-file HTML dashboard for the live what-if")
    up.add_argument("--out", default=str(ROOT / "reports" / "dashboard.html"))
    a = ap.parse_args(argv)
    cfg = load_json(a.config)
    if a.cmd == "fetch":
        from . import fetch
        fetch.run(cfg, ROOT)
    else:
        {"replay": cmd_replay, "backtest": cmd_backtest, "whatif": cmd_whatif, "ui": cmd_ui}[a.cmd](a, cfg)


if __name__ == "__main__":
    main()

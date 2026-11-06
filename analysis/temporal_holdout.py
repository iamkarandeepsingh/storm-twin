"""Chronological holdout: hydraulic thresholds chosen from December 2025 callouts only, evaluated on January 2026.
Run: python analysis/temporal_holdout.py   (read-only; prints results)"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from stormtwin import engine, features, rules  # noqa: E402
from stormtwin.__main__ import historical_weather, load_json, load_raw  # noqa: E402

cfg = load_json(Path(__file__).resolve().parent.parent / "config" / "settings.json")
data = load_raw(cfg)
idx = features.TruckIndex(data, cfg["timezone"])
W = historical_weather(cfg)


def label_rows(lo, hi):
    rows = []
    for c in data["Callout"]:
        if not (lo <= c["calloutLocal"][:10] < hi):
            continue
        cl = datetime.fromisoformat(c["calloutLocal"])
        actual = {d["vehicleName"]: "ok" for d in data["DispatchAssignment"] if d["calloutId"] == c["id"]}
        for w in data["WorkOrder"]:
            if w.get("reason") == "NO_START" and abs(datetime.fromisoformat(w["openedLocal"]) - cl) <= timedelta(hours=3):
                actual[w["vehicleName"]] = "no_start"
        for d in data["DispatchAssignment"]:
            if d["calloutId"] == c["id"] and d["status"] == "BROKEN_DOWN":
                actual[d["vehicleName"]] = "hydraulic"
        res, _ = engine.predict(data, cfg, c["calloutLocal"], W, sorted(actual), index=idx)
        rows += [(c["calloutLocal"], n, a, res[n]["features"]) for n, a in actual.items()]
    return rows


train, test = label_rows("2025-12-01", "2026-01-01"), label_rows("2026-01-01", "2026-02-01")
fv = [f["pto_since_hyd_service"] for _, _, a, f in train if a == "hydraulic"]
heavy = [f["weather_snow_cm"] for _, _, a, f in train if a == "hydraulic"]
surv = [f["pto_since_hyd_service"] for _, _, a, f in train
        if a == "ok" and f["weather_snow_cm"] >= min(heavy) and f["pto_since_hyd_service"] is not None]
light = [f["weather_snow_cm"] for _, _, a, f in train if a == "ok" and (f["pto_since_hyd_service"] or 0) >= min(fv)]
pto_t = round((max(surv) + min(fv)) / 2, 1)
snow_t = round(((max(light) if light else 0) + min(heavy)) / 2, 1)
print(f"TRAIN Dec callouts ({len(train)} truck-nights): hydraulic failures={len(fv)} -> PTO {pto_t} h, snow {snow_t} cm")
print("TRAIN has 0 callout-night no-starts (Dec no-starts were non-callout mornings): no-start rule kept from config.")
rc = json.loads(json.dumps(cfg["rules"]))
rc["hydraulic"][0]["all"][0]["value"] = pto_t
rc["hydraulic"][0]["all"][1]["value"] = snow_t
labels = ["ok", "no_start", "hydraulic"]
M = {(a, p): 0 for a in labels for p in labels}
for _, n, a, f in test:
    M[(a, rules.classify(f, rc)[0])] += 1
print(f"\nTEST Jan callouts ({len(test)} truck-nights), rows=actual cols=predicted")
print(" " * 12 + "".join(f"{p:>10}" for p in labels))
for a in labels:
    print(f"{a:>12}" + "".join(f"{M[(a, p)]:>10}" for p in labels))
for k in ("no_start", "hydraulic"):
    tp = M[(k, k)]
    fn = sum(M[(k, p)] for p in labels if p != k)
    fp = sum(M[(a, k)] for a in labels if a != k)
    print(f"{k}: recall {tp}/{tp + fn}  precision {tp}/{tp + fp}  false positives {fp}")
print("\nCaveat: 6 hydraulic + 3 callout no-start failures in total, so these rates are very uncertain.")

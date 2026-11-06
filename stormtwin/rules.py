"""Config-driven rule evaluation. Rules live in config/config.json, never in code.

Rule shape:
  {"name": "...", "all": [{"feature": "battery_v_latest", "op": "<", "value": 12.3},
                          {"feature": "weather_min_temp_c", "op": "<=", "value": -10}]}
A truck gets a label if ANY rule for that label fires. no_start beats hydraulic (a truck that won't start
can't lose hydraulics).
"""
import operator

OPS = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "==": operator.eq, "!=": operator.ne}


def fires(rule, feats):
    for c in rule["all"]:
        v = feats.get(c["feature"])
        if v is None or not OPS[c["op"]](v, c["value"]):
            return False
    return True


def classify(feats, rules_cfg):
    reasons = {"no_start": [r["name"] for r in rules_cfg.get("no_start", []) if fires(r, feats)],
               "hydraulic": [r["name"] for r in rules_cfg.get("hydraulic", []) if fires(r, feats)]}
    label = "no_start" if reasons["no_start"] else "hydraulic" if reasons["hydraulic"] else "ok"
    return label, reasons

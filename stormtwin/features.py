"""Per-truck feature extraction as of a decision time.

PROVISIONAL: row field names below follow API_DOCS (device.id, diagnostic.id, dateTime) but the value
field ("data" vs "value") and WorkOrder shape must be confirmed against data/raw once fetched.
Only records strictly before `as_of_utc` are used (no time leakage).
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

DIAG_V = "DiagnosticBatteryRestingVoltageId"
DIAG_PTO = "DiagnosticPtoHoursId"
DIAG_ENG = "DiagnosticEngineHoursId"


def _id(x):
    return x.get("id") if isinstance(x, dict) else x


def _val(row):
    for k in ("data", "value"):
        if k in row:
            return row[k]
    return None


def parse_utc(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def local_to_utc(s, tz):
    return datetime.fromisoformat(s).replace(tzinfo=ZoneInfo(tz)).astimezone(timezone.utc)


def device_for_truck(assignments, as_of_utc):
    """Map truck name -> device id active at as_of_utc, using DeviceAssignment.activeFrom."""
    current = {}
    for a in sorted(assignments, key=lambda a: a.get("activeFrom", "")):
        if parse_utc(a["activeFrom"]) <= as_of_utc:
            veh = a.get("vehicleName") or _id(a.get("vehicle"))
            dev = _id(a.get("device")) or a.get("deviceId")
            # one device per vehicle: drop any older mapping of this device to another truck
            for k in [k for k, v in current.items() if v == dev]:
                del current[k]
            current[veh] = dev
    return current


def truck_features(truck, dev, data, as_of_utc, tz):
    status = [r for r in data.get("StatusData", []) if _id(r.get("device")) == dev and parse_utc(r["dateTime"]) < as_of_utc]
    by_diag = {}
    for r in sorted(status, key=lambda r: r["dateTime"]):
        by_diag.setdefault(_id(r.get("diagnostic")), []).append((parse_utc(r["dateTime"]), _val(r)))

    f = {"truck": truck, "device": dev}
    volts = by_diag.get(DIAG_V, [])
    f["battery_v_latest"] = volts[-1][1] if volts else None
    week = [v for t, v in volts if t >= as_of_utc - timedelta(days=7) and v is not None]
    f["battery_v_min_7d"] = min(week) if week else None
    f["battery_v_drop_7d"] = (week[0] - week[-1]) if len(week) >= 2 else None

    pto = by_diag.get(DIAG_PTO, [])
    f["pto_hours_latest"] = pto[-1][1] if pto else None

    faults = [r for r in data.get("FaultData", []) if _id(r.get("device")) == dev and parse_utc(r["dateTime"]) < as_of_utc]
    recent = [r for r in faults if parse_utc(r["dateTime"]) >= as_of_utc - timedelta(days=14)]
    f["faults_14d"] = len(recent)
    f["fault_codes_14d"] = sorted({str(_id(r.get("diagnostic")) or r.get("code")) for r in recent})

    wos = [w for w in data.get("WorkOrder", []) if (w.get("vehicleName") or w.get("truck")) == truck
           and w.get("openedLocal") and local_to_utc(w["openedLocal"], tz) < as_of_utc]
    for wtype, key in (("BATTERY_REPLACED", "days_since_battery"), ("HYDRAULIC_SERVICE", "days_since_hyd_service"),
                       ("HYDRAULIC_REPAIR", "days_since_hyd_repair"), ("PM_INSPECTION", "days_since_pm")):
        ts = [local_to_utc(w["openedLocal"], tz) for w in wos if w.get("type") == wtype]
        f[key] = round((as_of_utc - max(ts)).total_seconds() / 86400, 1) if ts else None
    return f

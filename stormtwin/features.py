"""Per-truck feature extraction as of a decision time (the callout).

Only records strictly before `as_of_utc` are used (no time leakage).
Telematics rows are keyed by device; they are mapped to trucks with DeviceAssignment at the reading time
(devices b3B/b46 were swapped between T-118 and T-129 on 2026-01-08).
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

DIAG_V = "DiagnosticBatteryRestingVoltageId"
DIAG_PTO = "DiagnosticPtoHoursId"
HYD_TYPES = ("HYDRAULIC_SERVICE", "HYDRAULIC_REPAIR")


def _id(x):
    return x.get("id") if isinstance(x, dict) else x


def parse_utc(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def local_to_utc(s, tz):
    return datetime.fromisoformat(s).replace(tzinfo=ZoneInfo(tz)).astimezone(timezone.utc)


class TruckIndex:
    """Pre-indexes merged API rows by truck so features are cheap to compute for many dates."""

    def __init__(self, data, tz):
        self.tz = tz
        self.assign = [(a["device"]["id"], a.get("vehicleName"), parse_utc(a["activeFrom"]),
                        parse_utc(a.get("activeTo") or "2100-01-01T00:00:00Z")) for a in data.get("DeviceAssignment", [])]
        self.status = {}
        for r in data.get("StatusData", []):
            t = parse_utc(r["dateTime"])
            truck = self.truck_of(_id(r.get("device")), t)
            if truck:
                self.status.setdefault((truck, _id(r.get("diagnostic"))), []).append((t, r.get("data")))
        for v in self.status.values():
            v.sort(key=lambda x: x[0])
        self.workorders = {}
        for w in data.get("WorkOrder", []):
            if w.get("openedLocal"):
                closed = local_to_utc(w["closedLocal"], tz) if w.get("closedLocal") else None  # no closure = not completed
                self.workorders.setdefault(w.get("vehicleName"), []).append((local_to_utc(w["openedLocal"], tz), closed, w))
        for v in self.workorders.values():
            v.sort(key=lambda x: x[0])

    def truck_of(self, dev, t):
        for d, truck, a, b in self.assign:
            if d == dev and a <= t < b:
                return truck
        return None

    def series(self, truck, diag, before):
        return [(t, v) for t, v in self.status.get((truck, diag), []) if t < before and v is not None]

    def features(self, truck, as_of):
        f = {"truck": truck}
        wos = [x for x in self.workorders.get(truck, []) if x[0] < as_of]
        done = [x for x in wos if x[1] is not None and x[1] <= as_of]  # repairs only count once completed before the callout

        # --- battery ---
        volts = self.series(truck, DIAG_V, as_of)
        if volts:
            t_v, v = volts[-1]
            f["battery_v_latest"] = v
            f["battery_v_reading_local"] = t_v.astimezone(ZoneInfo(self.tz)).strftime("%Y-%m-%dT%H:%M")
            replaced = [w for t, tc, w in done if w.get("type") == "BATTERY_REPLACED" and tc > t_v]
            if replaced:  # new battery after the last reading: old voltage no longer describes the truck
                f["battery_replaced_after_reading"] = replaced[-1]["id"]
                f["battery_v_latest"] = None
        else:
            f["battery_v_latest"] = None

        # --- hydraulics: PTO hours since last hydraulic service / repair ---
        pto = self.series(truck, DIAG_PTO, as_of)
        hyd = [(t, tc, w) for t, tc, w in done if w.get("type") in HYD_TYPES]
        f["pto_hours_latest"] = pto[-1][1] if pto else None
        f["pto_since_hyd_service"] = None
        if hyd:
            t_open, t_close, w = hyd[-1]
            f["last_hyd_work_order"] = w["id"]
            base = (w.get("meterReadings") or {}).get("ptoHours")
            if base is None:  # mechanic left meters blank: use first telematics reading after the job
                after = [v for t, v in self.series(truck, DIAG_PTO, as_of) if t >= t_close]
                base = after[0] if after else None
                if base is None and pto and pto[-1][0] < t_open:
                    base = pto[-1][1]  # serviced after the last reading
            if base is not None and pto:
                f["pto_since_hyd_service"] = round(max(0.0, pto[-1][1] - base), 1)

        # --- context (reported, not used by the default rules) ---
        f["road_calls_before"] = sum(1 for _, _, w in wos if w.get("type") == "ROAD_CALL")
        return f

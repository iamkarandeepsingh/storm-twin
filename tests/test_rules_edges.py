from datetime import datetime, timezone
from stormtwin import features, rules, weather as wx
import json
from pathlib import Path

CFG = json.loads((Path(__file__).resolve().parent.parent / "config" / "settings.json").read_text())


def lab(v, t, p, s):
    return rules.classify({"battery_v_latest": v, "weather_min_temp_c": t, "pto_since_hyd_service": p, "weather_snow_cm": s}, CFG["rules"])[0]


def test_battery_boundary():
    assert lab(12.24, -10.5, 0, 0) == "no_start"
    assert lab(12.25, -20, 0, 0) == "ok"
    assert lab(12.0, -10.4, 0, 0) == "ok"


def test_pto_boundary():
    assert lab(12.7, -5, 181.0, 8.0) == "hydraulic"
    assert lab(12.7, -5, 180.9, 30) == "ok"
    assert lab(12.7, -5, 200, 7.9) == "ok"


def _data(wo_close):
    return {"DeviceAssignment": [{"device": {"id": "d1"}, "vehicleName": "T-1", "activeFrom": "2025-01-01T00:00:00Z", "activeTo": "2026-01-10T00:00:00Z"},
                                 {"device": {"id": "d1"}, "vehicleName": "T-2", "activeFrom": "2026-01-10T00:00:00Z", "activeTo": "2050-01-01T00:00:00Z"}],
            "StatusData": [{"device": {"id": "d1"}, "diagnostic": {"id": features.DIAG_V}, "dateTime": "2026-01-09T23:00:00Z", "data": 12.1},
                           {"device": {"id": "d1"}, "diagnostic": {"id": features.DIAG_V}, "dateTime": "2026-01-11T23:00:00Z", "data": 12.0},
                           {"device": {"id": "d1"}, "diagnostic": {"id": features.DIAG_V}, "dateTime": "2026-01-20T23:00:00Z", "data": 11.0}],
            "WorkOrder": [{"id": "w1", "vehicleName": "T-1", "type": "BATTERY_REPLACED", "openedLocal": "2026-01-09T20:00:00",
                           "closedLocal": wo_close}]}


def test_repair_closed_after_callout_does_not_count():
    as_of = datetime(2026, 1, 10, 6, 0, tzinfo=timezone.utc)  # callout 01:00 local Jan 10
    f = features.TruckIndex(_data("2026-01-10T09:00:00"), "America/Toronto").features("T-1", as_of)
    assert f["battery_v_latest"] == 12.1  # repair not finished by callout -> old weak battery still applies
    f = features.TruckIndex(_data("2026-01-09T22:00:00"), "America/Toronto").features("T-1", as_of)
    assert f["battery_v_latest"] is None  # finished before callout -> old reading no longer describes the truck


def test_device_swap_and_no_future_telemetry():
    idx = features.TruckIndex(_data("2026-01-09T22:00:00"), "America/Toronto")
    as_of = datetime(2026, 1, 12, 6, 0, tzinfo=timezone.utc)
    assert idx.features("T-2", as_of)["battery_v_latest"] == 12.0   # reading after the move belongs to T-2
    assert idx.features("T-1", as_of).get("battery_v_reading_local", "").startswith("2026-01-09")  # T-1 keeps only its own
    assert idx.features("T-2", as_of)["battery_v_latest"] != 11.0   # Jan 20 reading is in the future


def test_snow_from_precip_fallback_and_missing_warns():
    w = wx.summarize({"hourly": {"time": ["2026-01-15T01:00", "2026-01-15T04:00"], "temperature_2m": [-12, -14],
                                 "precipitation": [6.0, 7.0]}}, "2026-01-15T00:00:00")
    assert w["weather_snow_cm"] == 13.0 and w["weather_min_temp_c"] == -14
    w0 = wx.summarize({"daily": [{"date": "2026-01-15", "min_temp_c": -3, "snow_cm": 0}]}, "2026-01-15T00:00:00")
    assert w0["weather_snow_cm"] == 0 and not wx.warnings(w0)  # valid zero snow is not "missing"
    assert len(wx.warnings(wx.summarize({"foo": 1}, "2026-01-15T00:00:00"))) == 2

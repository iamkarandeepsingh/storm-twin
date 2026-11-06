import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from stormtwin import features, weather as wx

ROOT = Path(__file__).resolve().parent.parent
TZ = "America/Toronto"
AS_OF = datetime(2026, 1, 10, 6, 0, tzinfo=timezone.utc)  # 01:00 local Jan 10


def idx(closed):
    wo = {"id": "w1", "vehicleName": "T-1", "type": "HYDRAULIC_REPAIR", "openedLocal": "2026-01-09T08:00:00",
          "meterReadings": {"ptoHours": 1000.0}}
    if closed is not None:
        wo["closedLocal"] = closed
    return features.TruckIndex({
        "DeviceAssignment": [{"device": {"id": "d"}, "vehicleName": "T-1", "activeFrom": "2025-01-01T00:00:00Z"}],
        "StatusData": [{"device": {"id": "d"}, "diagnostic": {"id": features.DIAG_PTO}, "dateTime": "2026-01-09T23:00:00Z", "data": 1190.0}],
        "WorkOrder": [{"id": "w0", "vehicleName": "T-1", "type": "HYDRAULIC_SERVICE", "openedLocal": "2025-09-01T09:00:00",
                       "closedLocal": "2025-09-01T14:00:00", "meterReadings": {"ptoHours": 1000.0}}, wo]}, TZ)


def test_completed_repair_counts():
    assert idx("2026-01-09T14:00:00").features("T-1", AS_OF)["last_hyd_work_order"] == "w1"


def test_missing_closure_is_not_completed():
    f = idx(None).features("T-1", AS_OF)
    assert f["last_hyd_work_order"] == "w0" and f["pto_since_hyd_service"] == 190.0


def test_future_completed_repair_not_counted():
    assert idx("2026-01-10T10:00:00").features("T-1", AS_OF)["last_hyd_work_order"] == "w0"


def test_supplied_snow_preferred_and_estimate_flagged():
    both = wx.summarize({"hourly": {"time": ["2026-01-15T01:00"], "temperature_2m": [-12], "snowfall": [3.0], "precipitation": [9.0]}}, "2026-01-15T00:00:00")
    assert both["weather_snow_cm"] == 3.0 and both["weather_snow_estimated"] is False
    est = wx.summarize({"hourly": {"time": ["2026-01-15T01:00"], "temperature_2m": [-12], "precipitation": [9.0]}}, "2026-01-15T00:00:00")
    assert est["weather_snow_estimated"] is True and any("estimated" in m for m in wx.warnings(est))


def test_missing_weather_error_mode_exits_nonzero(tmp_path):
    cfg = json.loads((ROOT / "config" / "settings.json").read_text())
    cfg["replay_missing_weather"] = "error"
    (tmp_path / "c.json").write_text(json.dumps(cfg))
    (tmp_path / "i.json").write_text(json.dumps({"callout_local": "2026-01-15T00:00:00", "weather": {"foo": 1}, "trucks": ["T-111"]}))
    r = subprocess.run([sys.executable, "-m", "stormtwin", "--config", str(tmp_path / "c.json"), "replay", "--input", str(tmp_path / "i.json"),
                        "--output", str(tmp_path / "o.json")], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 2 and "required weather missing" in r.stderr and not (tmp_path / "o.json").exists()


def test_missing_weather_default_warns_but_writes(tmp_path):
    (tmp_path / "i.json").write_text(json.dumps({"callout_local": "2026-01-15T00:00:00", "weather": {"foo": 1}, "trucks": ["T-111"]}))
    r = subprocess.run([sys.executable, "-m", "stormtwin", "replay", "--input", str(tmp_path / "i.json"), "--output", str(tmp_path / "o.json")],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0 and "WARNING" in r.stderr and (tmp_path / "o.json").exists()

import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_replay(tmp_path, inp):
    i, o = tmp_path / "in.json", tmp_path / "out.json"
    i.write_text(json.dumps(inp))
    cmd = (ROOT / "REPLAY_COMMAND").read_text().strip().format(input=i, output=o).split()
    subprocess.run([sys.executable if c == "python" else c for c in cmd], cwd=ROOT, check=True, capture_output=True)
    return json.loads(o.read_text())


def test_jan15_night_reproduces_history(tmp_path):
    inp = {"night": "2026-01-15", "callout_local": "2026-01-15T00:00:00",
           "weather": {"daily": [{"date": "2026-01-14", "min_temp_c": -9.8, "snow_cm": 2.6},
                                 {"date": "2026-01-15", "min_temp_c": -14.3, "snow_cm": 20.2}]},
           "trucks": ["T-108", "T-111", "T-112", "T-119", "T-120", "T-125", "T-101"],
           "records_since_your_data_ends": {"StatusData": [], "FaultData": [], "WorkOrder": []}}
    out = run_replay(tmp_path, inp)
    assert out["persona"] == "maintenance"
    assert out["trucks"] == {"T-108": "hydraulic", "T-111": "no_start", "T-112": "no_start", "T-119": "no_start",
                             "T-120": "hydraulic", "T-125": "hydraulic", "T-101": "ok"}


def test_mild_light_night_is_all_ok(tmp_path):
    inp = {"callout_local": "2026-01-15T00:00:00",
           "weather": {"hourly": {"time": ["2026-01-14T22:00", "2026-01-15T03:00"], "temperature_2m": [-3, -4],
                                  "snowfall": [0.5, 0.5]}},
           "trucks": ["T-108", "T-111"], "records_since_your_data_ends": {}}
    assert set(run_replay(tmp_path, inp)["trucks"].values()) == {"ok"}


def test_replay_is_deterministic(tmp_path):
    inp = {"callout_local": "2026-01-15T00:00:00", "weather": {"min_temp_c": -14, "snow_cm": 20}, "trucks": ["T-111"]}
    assert run_replay(tmp_path, inp) == run_replay(tmp_path, inp)

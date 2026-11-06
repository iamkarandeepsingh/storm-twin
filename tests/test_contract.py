import copy, json, socket, subprocess, sys
from pathlib import Path
from stormtwin import engine
from stormtwin.__main__ import load_raw, load_json

ROOT = Path(__file__).resolve().parent.parent
CFG = load_json(ROOT / "config" / "settings.json")


def test_replay_offline_with_network_blocked(tmp_path):
    inp = {"callout_local": "2026-01-15T00:00:00", "weather": {"min_temp_c": -14.3, "snow_cm": 20.2}, "trucks": ["T-111", "T-125"]}
    (tmp_path / "i.json").write_text(json.dumps(inp))
    guard = tmp_path / "sitecustomize.py"
    guard.write_text("import socket\ndef _b(*a, **k): raise RuntimeError('network blocked')\nsocket.socket.connect = _b\nsocket.create_connection = _b\n")
    env = {"PYTHONPATH": f"{tmp_path}{__import__('os').pathsep}{ROOT}", "PATH": __import__('os').environ.get("PATH", ""),
           "SYSTEMROOT": __import__('os').environ.get("SYSTEMROOT", "")}
    r = subprocess.run([sys.executable, "-m", "stormtwin", "replay", "--input", str(tmp_path / "i.json"), "--output", str(tmp_path / "o.json")],
                       cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert json.loads((tmp_path / "o.json").read_text())["trucks"] == {"T-111": "no_start", "T-125": "hydraulic"}


def test_unexpected_shapes_still_produce_valid_labels(tmp_path):
    for trucks in (["T-101"], [{"name": "T-101"}], {"T-101": {"yard": "YARD-N"}}, None):
        inp = {"callout_local": "2026-01-15T00:00:00", "weather": {"daily": {"2026-01-15": {"tmin": -14.3, "snowfall": 20.2}}}, "trucks": trucks}
        (tmp_path / "i.json").write_text(json.dumps(inp))
        subprocess.run([sys.executable, "-m", "stormtwin", "replay", "--input", str(tmp_path / "i.json"), "--output", str(tmp_path / "o.json")],
                       cwd=ROOT, check=True, capture_output=True)
        out = json.loads((tmp_path / "o.json").read_text())
        assert out["persona"] == "maintenance" and set(out["trucks"].values()) <= {"ok", "no_start", "hydraulic"}


def test_repair_scenario_does_not_mutate_source_data():
    data = load_raw(CFG)
    before = copy.deepcopy(data["StatusData"][:50]), len(data["WorkOrder"])
    w = {"min_temp_c": -14, "snow_cm": 20}
    base, _ = engine.predict(data, CFG, "2026-12-16T02:00:00", w)
    sc, _ = engine.predict(data, CFG, "2026-12-16T02:00:00", w, scenario={"battery_replaced": ["T-109"], "hydraulic_serviced": ["T-114"]})
    assert (data["StatusData"][:50], len(data["WorkOrder"])) == before
    assert base["T-109"]["label"] == "no_start" and sc["T-109"]["label"] == "ok"
    assert "battery replaced (assumed)" in sc["T-109"]["features"]["scenario"]
    again, _ = engine.predict(data, CFG, "2026-12-16T02:00:00", w)
    assert {k: v["label"] for k, v in again.items()} == {k: v["label"] for k, v in base.items()}

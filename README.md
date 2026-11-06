# Storm Twin – Karandeep

Persona: Maintenance lead

## Run it (a judge must be able to do this from a fresh clone)

```bash
# 1. install: Python 3.10+, standard library only (see requirements.txt)
# 2. load: download the fleet API into data/raw/  (needs FLEET_API_KEY)
python -m stormtwin fetch
# 3. replay: offline from data/ (exact command in REPLAY_COMMAND)
python -m stormtwin replay --input replay/input.json --output replay/output.json --explain replay/explain.json
```

## How it works (5 lines max)
1. `fetch` saves every API entity to `data/raw/<Entity>.json`.
2. `replay` maps devices to trucks at callout time (DeviceAssignment), merges the input's day-before records.
3. Builds per-truck features using only records before the callout (no leakage).
4. Applies the rules in `config/settings.json` (thresholds found from last winter) -> ok / no_start / hydraulic.

## What I'd do next

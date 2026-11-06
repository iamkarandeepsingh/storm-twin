# Storm Twin – Karandeep

Persona: **Maintenance lead**. Which trucks go out tonight, which get fixed first?

## Run it (from a fresh clone; Python 3.10+, standard library only; pytest optional)

```bash
python -m stormtwin fetch          # 1. load: API -> data/raw/  (needs FLEET_API_KEY; already committed)
python -m stormtwin backtest       # 2. score the discovered rules on last winter
python -m stormtwin replay --input replay/input.json --output replay/output.json --explain replay/explain.json   # 3. replay (= REPLAY_COMMAND), offline
python -m stormtwin whatif --report reports/tonight_baseline.md        # 4. tonight, bulletin weather (+ one-page report)
python -m stormtwin whatif --weather config/weather/update_2130.json --callout 2026-12-16T00:30:00 --report reports/update_2130_baseline.md   # 2:15 forecast update: new JSON file, no code change
python -m stormtwin whatif --scenario scenarios/fix_priority_trucks.json  # repair what-if vs baseline
python -m stormtwin ui                                                  # optional: reports/dashboard.html, sliders + repair checkboxes (same rules)
python -m pytest -q
```

## How it works (5 lines max)
1. `data/raw/` = API snapshot; `data/weather/` = Environment Canada daily data (Toronto Pearson) for last winter.
2. Telematics is mapped device -> truck with DeviceAssignment at reading time; only records before the callout are used.
3. Per truck: evening battery resting voltage; PTO hours since last hydraulic service/repair (battery swap / hydraulic repair reset them).
4. Rules + thresholds live in `config/settings.json`: no_start = V <= 12.24 and low <= -10.5 C; hydraulic = PTO-since-service >= 181 h and snow >= 8 cm.
5. Backtest on 11 callouts: 9/9 failures caught, 0 false alarms (327 truck-nights). Details in PERSONA.md.

## What I'd do next
Hourly temperatures at start-up time (the Dec 31 vs Jan 18 cold-threshold ambiguity); a repair-capacity limit in scenarios.

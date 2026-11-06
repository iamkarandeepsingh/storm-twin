# Persona

**I build for:** Maintenance lead

**The decision my persona makes tonight:** Which of the 30 trucks go out for the 02:00 callout, and which get fixed or inspected first (battery / hydraulics) before then.

**What my system tells them (the actual output they'd act on):** For every truck: `ok`, `no_start` or `hydraulic`, with the evidence (latest battery resting voltage, PTO hours since last hydraulic service, recent faults, work-order history) and the rule that fired. Plus a repair-first list, and a re-run under the 2:15 forecast or a "what if we replace T-xxx's battery" change, driven by config, not code.

**The rules I believe the fleet follows (with the numbers I found):**
1. (pending data: no-start vs battery voltage x overnight low)
2. (pending data: hydraulic failure vs PTO hours since hydraulic service)
3.

**What I am NOT sure about, and how I'd check:** (pending data profiling)

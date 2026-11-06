# Persona

**I build for:** Maintenance lead

**The decision my persona makes tonight:** Which of the 30 trucks go out for the 02:00 callout, and which get a battery swap or hydraulic service first.

**What my system tells them (the actual output they'd act on):** For every truck: `ok`, `no_start` or `hydraulic`, with the evidence (evening battery resting voltage, PTO hours since last hydraulic service, the night's low and snowfall) and the rule that fired. Plus a repair-first list, and a re-run under the 2:15 forecast or "what if we swap T-xxx's battery", driven by config, not code.

**The rules I believe the fleet follows (with the numbers I found):**
1. **Cold no-start = weak battery + cold morning.** All 11 no-starts (ROAD_CALL NO_START, last winter) had evening resting voltage <= 12.24 V the night before (range 11.65-12.24). On the 6 no-start mornings, EVERY truck at <= 12.24 V failed (11/11); trucks at 12.25 V started (T-101 Dec 3, T-106 Jan 18). Those mornings had Pearson daily lows of -10.7 to -15.3 C. Low-voltage trucks started fine on milder days (e.g. 4 trucks at 11.99-12.16 V on Dec 17-30, lows -9.3 C or warmer).
2. **Hydraulic failure = overdue hydraulic service + heavy snow night.** All 6 mid-route hydraulic failures (BROKEN_DOWN / ROAD_CALL HYDRAULIC_FAILURE) had 181.8-191.4 PTO hours since their last hydraulic service, and all happened on the 3 heaviest-snow callouts (Dec 23 9.8 cm, Dec 26 12.0 cm, Jan 15 20.2 cm). Trucks with 180-189 h survived light-snow callouts (2.0-4.8 cm).
3. **Repairs reset the clock:** every no-start was followed by BATTERY_REPLACED (voltage back to ~12.7-12.8 V next evening); every hydraulic failure by HYDRAULIC_REPAIR (PTO-since-service back to 0).

**What I am NOT sure about, and how I'd check:**
- Exact cold cut-off: Dec 31 (daily low -10.8 C) had 4 low-voltage trucks that started, while Jan 18 (-10.7 C) had one that failed. Daily lows don't capture the hour of the low; the replay input has hourly weather, so the rule should use the temperature at start-up time.
- Exact snow cut-off (between 4.8 and 9.8 cm) and PTO cut-off (between 180.0 and 181.8 h) are only bracketed by a few cases.
- HYD-PRESS-LOW faults (251 rows) look like noise: failures and non-failures have similar counts.
- Trap handled: devices b3B/b46 swapped between T-118 and T-129 on 2026-01-08; telematics is mapped to trucks by DeviceAssignment at the reading time.

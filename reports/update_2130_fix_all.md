# Storm Twin: maintenance answer for callout 2026-12-16T00:30:00

Weather used: low **-19 C**, snow **27.5 cm** (simple).
Generated 2026-11-06 14:15. Decision support, not a safety clearance.

**Scenario:** Updated forecast: swap batteries on T-109, T-110, T-116 and service hydraulics on T-114, T-119, T-128, T-111 before the 00:30 callout (repairs assumed fully effective)

## Bottom line: 30 of 30 trucks ready
- Will not start: **0**   - Will lose hydraulics mid-route: **0**   - Deploy but inspect first: **3**

## Repair first (in this order)

| # | Truck | Predicted failure | Fix | Evidence |
|---|---|---|---|---|
| - | none | - | - | - |

## Deploy, inspect first (near a threshold)

- T-108: battery 12.58 V (2026-12-15T18:00); 171.0 PTO h since hydraulic work (wo008468)
- T-127: battery 12.65 V (2026-12-15T18:07); 176.5 PTO h since hydraulic work (wo000027)
- T-130: battery 12.29 V (2026-12-15T18:09); 2.9 PTO h since hydraulic work (wo901807)

## Change vs baseline

- T-109: no_start -> **ok**
- T-110: no_start -> **ok**
- T-111: hydraulic -> **ok**
- T-114: hydraulic -> **ok**
- T-116: no_start -> **ok**
- T-119: hydraulic -> **ok**
- T-128: hydraulic -> **ok**

## Why (rules found in last winter's data)

- **No-start** if evening battery resting voltage <= 12.24 V and overnight low <= -10.5 C. Last winter: all 11 no-starts matched; on those mornings every truck at or below 12.24 V failed.
- **Hydraulic** if PTO hours since last hydraulic service >= 181.0 and snowfall >= 8.0 cm. Last winter: all 6 failures matched (181.8-191.4 h, 9.8-20.2 cm snow); same hours survived 2-5 cm nights.
- Backtest on 11 callouts: 9/9 failures caught, 0 false alarms. Thresholds in config/settings.json.

## All trucks

| Truck | Label | Action | Evidence |
|---|---|---|---|
| T-101 | ok | DEPLOY | battery 12.69 V (2026-12-15T18:05); 0.0 PTO h since hydraulic work (wo900002) |
| T-102 | ok | DEPLOY | battery 12.70 V (2026-12-15T18:03); 0.0 PTO h since hydraulic work (wo900065) |
| T-103 | ok | DEPLOY | battery 12.71 V (2026-12-15T18:04); 0.0 PTO h since hydraulic work (wo900128) |
| T-104 | ok | DEPLOY | battery 12.63 V (2026-12-15T18:06); 0.0 PTO h since hydraulic work (wo900190) |
| T-105 | ok | DEPLOY | battery 12.64 V (2026-12-15T18:09); 0.0 PTO h since hydraulic work (wo900253) |
| T-106 | ok | DEPLOY | battery 12.40 V (2026-12-15T18:03); 0.3 PTO h since hydraulic work (wo900315) |
| T-107 | ok | DEPLOY | battery 12.73 V (2026-12-15T18:09); 0.0 PTO h since hydraulic work (wo900377) |
| T-108 | ok | DEPLOY, inspect first: near a failure threshold | battery 12.58 V (2026-12-15T18:00); 171.0 PTO h since hydraulic work (wo008468) |
| T-109 | ok | DEPLOY | battery 12.75 V (2026-12-15T18:06); 1.1 PTO h since hydraulic work (wo900503) |
| T-110 | ok | DEPLOY | battery 12.75 V (2026-12-15T18:07); 1.0 PTO h since hydraulic work (wo900566) |
| T-111 | ok | DEPLOY | battery 12.59 V (2026-12-15T18:05); 0.0 PTO h since hydraulic work (wo000011) |
| T-112 | ok | DEPLOY | battery 12.59 V (2026-12-15T18:04); 1.9 PTO h since hydraulic work (wo900692) |
| T-113 | ok | DEPLOY | battery 12.64 V (2026-12-15T18:01); 0.0 PTO h since hydraulic work (wo900755) |
| T-114 | ok | DEPLOY | battery 12.75 V (2026-12-15T18:02); 0.0 PTO h since hydraulic work (wo004585) |
| T-115 | ok | DEPLOY | battery 12.68 V (2026-12-15T18:07); 0.0 PTO h since hydraulic work (wo900880) |
| T-116 | ok | DEPLOY | battery 12.75 V (2026-12-15T18:01); 2.2 PTO h since hydraulic work (wo900943) |
| T-117 | ok | DEPLOY | battery 12.67 V (2026-12-15T18:03); 2.1 PTO h since hydraulic work (wo901005) |
| T-118 | ok | DEPLOY | battery 12.63 V (2026-12-15T18:00); 1.2 PTO h since hydraulic work (wo901067) |
| T-119 | ok | DEPLOY | battery 12.56 V (2026-12-15T18:07); 0.0 PTO h since hydraulic work (wo000019) |
| T-120 | ok | DEPLOY | battery 12.59 V (2026-12-15T18:02); 0.9 PTO h since hydraulic work (wo901191) |
| T-121 | ok | DEPLOY | battery 12.42 V (2026-12-15T18:03); 1.1 PTO h since hydraulic work (wo901253) |
| T-122 | ok | DEPLOY | battery 12.33 V (2026-12-15T18:08); 0.0 PTO h since hydraulic work (wo901315) |
| T-123 | ok | DEPLOY | battery 12.55 V (2026-12-15T18:03); 0.0 PTO h since hydraulic work (wo901377) |
| T-124 | ok | DEPLOY | battery 12.57 V (2026-12-15T18:09); 2.1 PTO h since hydraulic work (wo901439) |
| T-125 | ok | DEPLOY | battery 12.56 V (2026-12-15T18:01); 2.9 PTO h since hydraulic work (wo901502) |
| T-126 | ok | DEPLOY | battery 12.37 V (2026-12-15T18:04); 1.7 PTO h since hydraulic work (wo901564) |
| T-127 | ok | DEPLOY, inspect first: near a failure threshold | battery 12.65 V (2026-12-15T18:07); 176.5 PTO h since hydraulic work (wo000027) |
| T-128 | ok | DEPLOY | battery 12.53 V (2026-12-15T18:05); 0.0 PTO h since hydraulic work (wo002135) |
| T-129 | ok | DEPLOY | battery 12.31 V (2026-12-13T18:00); 1.7 PTO h since hydraulic work (wo901753) |
| T-130 | ok | DEPLOY, inspect first: near a failure threshold | battery 12.29 V (2026-12-15T18:09); 2.9 PTO h since hydraulic work (wo901807) |

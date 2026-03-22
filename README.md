# Sea Power Hosted WEGO Planner

This repository now contains a hosted browser-based planner for turn-based PvP Sea Power scenarios.

## What It Does

- creates a two-player WEGO session from a JSON scenario seed
- generates separate secret links for the Blue and Red players
- generates a full-truth admin link for referee oversight and corrections
- tracks per-side resources, build catalogs, and spawn points
- lets each player submit fleet movement orders with waypoint chains
- lets each side spend resources to build new fleets during the open turn
- resolves movement simultaneously on the server
- computes rule-based fog of war with visible and last-known contacts
- keeps seaborne units on water and land-based units on land using a coarse world land mask
- exports the full resolved state as a Sea Power scenario `.ini`

## Run It

```sh
python3 run_planner.py --host 0.0.0.0 --port 8000
```

Then open:

```text
http://<host>:8000/
```

## Seed Data

Use the example scenario at [scenario_seed.json](/home/specter/Documents/GitHub/Sea%20Power/examples/scenario_seed.json) as a starting point.

Important seed fields:

- `scenario_name`
- `turn_duration_minutes`
- `map_center.lat`
- `map_center.lon`
- `sides.Blue` / `sides.Red`
- `fleets[]`

Each side can define:

- `resources`
- `income_per_turn`
- `spawn_point.lat`
- `spawn_point.lon`
- `build_catalog[]`

Each fleet should include:

- `id`
- `sp_id`
- `name`
- `side`
- `unit_type`
- `lat`
- `lon`
- `heading_deg`
- `speed_kts`
- `detection_radius_nm`
- `resource_cost`
- `composition[]`
- Sea Power export fields such as `sea_power_type`, `variant_reference`, `station_role`, `crew_skill`, and `telegraph`

Each build catalog entry can define:

- `id`
- `name`
- `cost`
- `unit_type`
- `speed_kts`
- `detection_radius_nm`
- `composition[]`

## API

- `POST /sessions`
- `GET /sessions/{id}/view?token=...`
- `GET /sessions/{id}/admin/view?admin_token=...`
- `POST /sessions/{id}/turns/{side}?token=...`
- `POST /sessions/{id}/builds/{side}?token=...`
- `POST /sessions/{id}/admin/fleets/{fleet_id}?admin_token=...`
- `POST /sessions/{id}/resolve?admin_token=...`
- `GET /sessions/{id}/export/scenario.ini?admin_token=...`

## Notes

- The server is authoritative for the full truth state.
- Player views are redacted by side.
- Admin views can see every fleet and directly edit fleet state if a referee correction is needed.
- New builds spawn at the configured side spawn point.
- Surface/subsurface/naval unit types are kept on water; land/ground/coastal types are kept on land.
- v1 only resolves movement and visibility. It does not model combat, doctrine, EMCON, AI, weather effects, or terrain masking.

## Workflow

- Use atomic commits: each commit should contain one logical change only.

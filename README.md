# Sea Power Local Campaign Planner

This repository contains a browser-based local campaign planner for turn-based Sea Power scenarios.

## What It Does

- loads one local campaign from `data/current_campaign.json`
- falls back to the most recent legacy SQLite session if no JSON campaign exists yet
- creates a blank campaign shell automatically if no save exists
- starts with a simple `Red`, `Blue`, or `ADMIN` team selection flow
- tracks per-side resources, ports, reserve ships, fleets, repairs, and rearm jobs
- surfaces points and income clearly in Overview and Economy management views
- lets each side create ships, assemble fleets, transfer ships, dock/undock, and manage logistics
- lets each player submit fleet movement orders with waypoint chains
- lets admin resolve turns explicitly after both sides are ready
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

Optional launcher flags:

```sh
python3 run_planner.py --campaign data/current_campaign.json --legacy-db data/planner.sqlite3
```

## Save And Import Data

The planner now uses a single local JSON campaign file as its source of truth. Admin can also import a Sea Power save file from the web UI.

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

## API

- `GET /api/campaign/view?role=Blue|Red|Admin`
- `POST /api/campaign/import-save?role=Admin`
- `POST /api/campaign/reset?role=Admin`
- `POST /api/campaign/resolve?role=Admin`
- `GET /api/campaign/export/scenario.ini?role=Admin`
- `POST /api/ports?role=...`
- `POST /api/ports/{id}?role=...`
- `POST /api/sides/{side}?role=Admin`
- `POST /api/fleets?role=...`
- `POST /api/fleets/{id}?role=...`
- `POST /api/fleets/{id}/dock?role=...`
- `POST /api/fleets/{id}/merge?role=...`
- `POST /api/ships?role=...`
- `POST /api/ships/{id}?role=...`
- `POST /api/ships/{id}/transfer?role=...`
- `POST /api/ships/{id}/rearm?role=...`
- `POST /api/ships/{id}/repair?role=...`
- `POST /api/turns/{side}?role=Blue|Red|Admin`

## Notes

- The server is authoritative for the full truth state.
- Player views are redacted by side.
- Admin views can see every fleet and directly edit both sides.
- Blue and Red can fully manage their own side assets without authentication; role selection is just a local UX mode.
- Surface/subsurface/naval unit types are kept on water; land/ground/coastal types are kept on land.
- v1 only resolves movement and visibility. It does not model combat, doctrine, EMCON, AI, weather effects, or terrain masking.

## Testing

```sh
python -m unittest discover -s tests -v
```

## Workflow

- Use atomic commits: each commit should contain one logical change only.

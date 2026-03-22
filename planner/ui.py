INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Sea Power Planner</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
  <style>
    :root {
      --bg: #e8ece6;
      --panel: #f7f5ee;
      --ink: #1b2b34;
      --muted: #55656f;
      --blue: #2b6bc4;
      --red: #c43434;
      --neutral: #6f7780;
      --accent: #c48b2b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Palatino Linotype", serif;
      color: var(--ink);
      background: linear-gradient(180deg, #d8e1dc 0%, var(--bg) 100%);
    }
    header {
      padding: 14px 18px;
      border-bottom: 1px solid rgba(27, 43, 52, 0.15);
      background: rgba(247, 245, 238, 0.88);
      backdrop-filter: blur(6px);
    }
    h1 { margin: 0; font-size: 1.3rem; }
    main { display: grid; grid-template-columns: 360px 1fr; min-height: calc(100vh - 64px); }
    aside {
      border-right: 1px solid rgba(27, 43, 52, 0.15);
      background: var(--panel);
      overflow-y: auto;
      padding: 16px;
    }
    #map { min-height: calc(100vh - 64px); width: 100%; }
    section {
      margin-bottom: 18px;
      padding: 14px;
      border: 1px solid rgba(27, 43, 52, 0.12);
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.62);
    }
    h2 { margin: 0 0 8px; font-size: 1rem; }
    label { display: block; font-size: 0.86rem; margin-bottom: 6px; color: var(--muted); }
    textarea, input, button, select {
      width: 100%;
      padding: 10px;
      border-radius: 10px;
      border: 1px solid rgba(27, 43, 52, 0.18);
      font: inherit;
    }
    textarea { min-height: 180px; resize: vertical; }
    button {
      cursor: pointer;
      background: var(--ink);
      color: white;
      border: none;
    }
    button.secondary {
      background: transparent;
      color: var(--ink);
      border: 1px solid rgba(27, 43, 52, 0.18);
    }
    button.danger {
      background: #8f2a2a;
    }
    button:disabled {
      cursor: not-allowed;
      opacity: 0.55;
    }
    .button-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 10px;
    }
    .stack {
      display: grid;
      gap: 8px;
    }
    .muted { color: var(--muted); font-size: 0.9rem; }
    .hidden { display: none; }
    ul { padding-left: 18px; margin: 8px 0 0; }
    .pill {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 0.8rem;
      background: rgba(27, 43, 52, 0.08);
      margin-right: 6px;
      margin-bottom: 6px;
    }
    .status-blue { color: var(--blue); }
    .status-red { color: var(--red); }
    .status-neutral { color: var(--neutral); }
    .session-links code, pre {
      display: block;
      margin-top: 6px;
      word-break: break-word;
      white-space: pre-wrap;
      font-size: 0.8rem;
      color: var(--muted);
    }
    .turn-banner {
      font-weight: bold;
      margin-bottom: 8px;
    }
    .order-item {
      padding: 8px 0;
      border-top: 1px solid rgba(27, 43, 52, 0.1);
    }
    .order-item:first-child { border-top: none; }
    .small { font-size: 0.82rem; color: var(--muted); }
    .mil-symbol {
      width: 44px;
      height: 44px;
      display: flex;
      align-items: center;
      justify-content: center;
      filter: drop-shadow(0 2px 10px rgba(27, 43, 52, 0.25));
      transform-origin: center;
    }
    .mil-symbol.selected {
      transform: scale(1.08);
    }
    .scenario-summary {
      padding: 10px;
      border-radius: 10px;
      background: rgba(27, 43, 52, 0.05);
    }
    dialog {
      width: min(760px, calc(100vw - 24px));
      border: 1px solid rgba(27, 43, 52, 0.12);
      border-radius: 16px;
      padding: 0;
      background: var(--panel);
      color: var(--ink);
      box-shadow: 0 24px 60px rgba(27, 43, 52, 0.22);
    }
    dialog::backdrop {
      background: rgba(27, 43, 52, 0.45);
    }
    .dialog-body {
      padding: 16px;
    }
    .dialog-actions {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 8px;
      margin-top: 12px;
    }
    .field-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 12px;
    }
    .field-grid.three {
      grid-template-columns: repeat(3, 1fr);
    }
    .fleet-list {
      display: grid;
      gap: 12px;
      margin-top: 10px;
    }
    .fleet-card {
      padding: 12px;
      border: 1px solid rgba(27, 43, 52, 0.12);
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.72);
    }
    .fleet-card h3 {
      margin: 0 0 8px;
      font-size: 0.95rem;
    }
    .dialog-divider {
      margin: 12px 0 8px;
      font-size: 0.86rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .side-strip {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 12px;
    }
    .side-box {
      padding: 12px;
      border-radius: 12px;
      background: rgba(27, 43, 52, 0.05);
    }
    .side-box.blue-side {
      border-left: 4px solid var(--blue);
    }
    .side-box.red-side {
      border-left: 4px solid var(--red);
    }
    .inline-actions {
      display: flex;
      gap: 8px;
      margin-top: 10px;
    }
    .inline-actions button {
      width: auto;
    }
    @media (max-width: 900px) {
      main {
        grid-template-columns: 1fr;
      }
      aside {
        border-right: none;
        border-bottom: 1px solid rgba(27, 43, 52, 0.15);
      }
      #map {
        min-height: 55vh;
      }
    }
  </style>
</head>
<body>
  <header>
    <h1>Sea Power Planner</h1>
  </header>
  <main>
    <aside>
      <section id="create-panel">
        <h2>Scenario Library</h2>
        <p class="muted">Select a saved scenario, create a session from it, or open the scenario creation dialog.</p>
        <label for="scenario-select">Saved Scenarios</label>
        <select id="scenario-select" size="8"></select>
        <div class="button-row">
          <button id="new-scenario">New Scenario</button>
          <button class="secondary" id="refresh-scenarios">Refresh List</button>
        </div>
        <div class="button-row">
          <button id="load-scenario">Load Selected</button>
          <button class="danger" id="delete-scenario">Delete Selected</button>
        </div>
        <div class="button-row">
          <button class="secondary" id="create-session">Create Session</button>
          <button class="secondary" id="load-example-scenario">Import Example</button>
        </div>
        <div id="scenario-details" class="scenario-summary small">No scenario selected.</div>
        <div id="create-result" class="session-links hidden"></div>
      </section>

      <section id="join-panel">
        <h2>Join Existing Session</h2>
        <label for="session-id-input">Session ID</label>
        <input id="session-id-input" placeholder="session id" />
        <label for="token-input">Side Token</label>
        <input id="token-input" placeholder="player token" />
        <div class="button-row">
          <button id="join-session">Open View</button>
          <button class="secondary" id="clear-session">Clear</button>
        </div>
      </section>

      <section id="play-panel" class="hidden">
        <div class="turn-banner" id="turn-banner">Turn</div>
        <div id="session-meta" class="muted"></div>
        <div style="margin-top: 10px;">
          <span class="pill" id="own-status-pill">Own turn open</span>
          <span class="pill" id="enemy-status-pill">Enemy pending</span>
        </div>
      </section>

      <section id="selected-panel" class="hidden">
        <h2>Selected Fleet</h2>
        <div id="selected-fleet">No fleet selected.</div>
        <div class="button-row">
          <button id="clear-selected-order" class="secondary">Clear Selected Order</button>
          <button id="submit-turn">Submit Turn</button>
        </div>
        <p class="small">Click a fleet, then click the map to add waypoint(s). Drag a fleet marker to create the first leg quickly.</p>
      </section>

      <section id="orders-panel" class="hidden">
        <h2>Current Orders</h2>
        <div id="orders-list" class="small">No drafted orders.</div>
      </section>

      <section id="contacts-panel" class="hidden">
        <h2>Contacts</h2>
        <div id="contacts-list" class="small">No enemy contacts.</div>
      </section>
    </aside>
    <div id="map"></div>
  </main>

  <dialog id="scenario-dialog">
    <div class="dialog-body">
      <h2 id="scenario-dialog-title">Create Scenario</h2>
      <p class="muted" id="scenario-dialog-text">Initialize a new scenario using structured setup fields and an editable fleet roster.</p>
      <div class="field-grid">
        <div>
          <label for="scenario-name">Scenario Name</label>
          <input id="scenario-name" />
        </div>
        <div>
          <label for="turn-duration">Turn Duration Minutes</label>
          <input id="turn-duration" type="number" min="1" step="1" />
        </div>
      </div>
      <div class="field-grid three">
        <div>
          <label for="map-center-lat">Map Center Lat</label>
          <input id="map-center-lat" type="number" step="0.0001" />
        </div>
        <div>
          <label for="map-center-lon">Map Center Lon</label>
          <input id="map-center-lon" type="number" step="0.0001" />
        </div>
        <div>
          <label for="sea-state">Sea State</label>
          <input id="sea-state" type="number" min="0" step="1" />
        </div>
      </div>
      <div class="field-grid">
        <div>
          <label for="scenario-date">Date</label>
          <input id="scenario-date" placeholder="1985,6,26" />
        </div>
        <div>
          <label for="scenario-time">Time</label>
          <input id="scenario-time" placeholder="10,0" />
        </div>
      </div>
      <div class="dialog-divider">Sides</div>
      <div class="side-strip">
        <div class="side-box blue-side">
          <label for="blue-faction">Blue Faction</label>
          <select id="blue-faction"></select>
          <label for="blue-funds" style="margin-top: 8px;">Blue Starting Funds</label>
          <input id="blue-funds" type="number" step="1" />
        </div>
        <div class="side-box red-side">
          <label for="red-faction">Red Faction</label>
          <select id="red-faction"></select>
          <label for="red-funds" style="margin-top: 8px;">Red Starting Funds</label>
          <input id="red-funds" type="number" step="1" />
        </div>
      </div>
      <div class="dialog-divider">Fleets</div>
      <div class="inline-actions">
        <button id="add-blue-fleet" type="button">Add Blue Fleet</button>
        <button id="add-red-fleet" type="button">Add Red Fleet</button>
      </div>
      <div id="fleet-editor" class="fleet-list"></div>
      <div class="dialog-actions">
        <button id="dialog-load-example" type="button">Load Example</button>
        <button id="save-scenario" type="button">Create Scenario</button>
        <button class="secondary" id="close-scenario-dialog" type="button">Cancel</button>
      </div>
    </div>
  </dialog>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <script>
    const query = new URLSearchParams(window.location.search);
    let sessionId = query.get("session") || "";
    let token = query.get("token") || "";
    let side = null;
    let currentView = null;
    let selectedFleetId = null;
    let selectedScenarioId = "";
    let editingScenarioId = "";
    let scenarioCache = new Map();
    let scenarioFormFleets = [];
    let draftOrders = {};
    let map = null;
    let mapInitializedForSession = null;
    let ownFleetMarkers = new Map();
    let contactMarkers = new Map();
    let orderPolylines = new Map();
    let pollHandle = null;
    let landPolygons = [];
    let terrainPromise = null;

    function $(id) { return document.getElementById(id); }

    function initializeMap() {
      if (map) return;
      map = L.map("map", { worldCopyJump: true, minZoom: 2 }).setView([20, 0], 3);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 18
      }).addTo(map);
      map.on("click", onMapClick);
      loadTerrain().then(() => {
        if (currentView) {
          updatePanels(currentView);
          renderView(currentView);
        }
      });
    }

    function colorForSide(value) {
      if (value === "Blue") return "#2b6bc4";
      if (value === "Red") return "#c43434";
      return "#6f7780";
    }

    function affiliationColor(affiliation) {
      if (affiliation === "friendly") return "#2b6bc4";
      if (affiliation === "hostile") return "#c43434";
      if (affiliation === "neutral") return "#3b7f4c";
      return "#b08b2d";
    }

    function symbolCategory(unitType) {
      const normalized = String(unitType || "").trim().toLowerCase();
      if (normalized.includes("subsurface") || normalized.includes("submarine")) return "subsurface";
      if (normalized.includes("air")) return "air";
      if (normalized.includes("land") || normalized.includes("ground") || normalized.includes("coastal") || normalized.includes("site")) return "land";
      if (normalized.includes("support") || normalized.includes("logistics")) return "support";
      return "surface";
    }

    function affiliationForFleet(view, fleet) {
      if (fleet.side === "Neutral") return "neutral";
      return fleet.side === view.side ? "friendly" : "hostile";
    }

    function symbolFrameSvg(affiliation, dashArray) {
      const stroke = affiliationColor(affiliation);
      const common = `fill="rgba(255,255,255,0.92)" stroke="${stroke}" stroke-width="3" ${dashArray ? `stroke-dasharray="${dashArray}"` : ""}`;
      if (affiliation === "hostile") {
        return `<polygon points="22,5 39,22 22,39 5,22" ${common} />`;
      }
      if (affiliation === "neutral") {
        return `<rect x="7" y="7" width="30" height="30" ${common} />`;
      }
      if (affiliation === "unknown") {
        return `<path d="M22 6 C29 6 35 12 35 19 C35 22 33 24 31 26 C33 28 35 30 35 34 C35 41 29 38 22 38 C15 38 9 41 9 34 C9 30 11 28 13 26 C11 24 9 22 9 19 C9 12 15 6 22 6 Z" ${common} />`;
      }
      return `<rect x="6" y="10" width="32" height="24" rx="2" ry="2" ${common} />`;
    }

    function symbolInteriorSvg(category, color) {
      if (category === "subsurface") {
        return `
          <path d="M12 22 C16 18, 20 26, 24 22 S32 18, 36 22" fill="none" stroke="${color}" stroke-width="2.4" stroke-linecap="round" />
          <path d="M14 29 L30 29" fill="none" stroke="${color}" stroke-width="2.4" stroke-linecap="round" />
        `;
      }
      if (category === "air") {
        return `
          <path d="M12 28 L22 16 L32 28" fill="none" stroke="${color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
          <path d="M22 17 L22 31" fill="none" stroke="${color}" stroke-width="2.2" stroke-linecap="round" />
        `;
      }
      if (category === "land") {
        return `
          <path d="M14 14 L30 30 M30 14 L14 30" fill="none" stroke="${color}" stroke-width="2.6" stroke-linecap="round" />
        `;
      }
      if (category === "support") {
        return `
          <path d="M22 13 L22 31 M13 22 L31 22" fill="none" stroke="${color}" stroke-width="2.6" stroke-linecap="round" />
        `;
      }
      return `
        <path d="M12 24 C16 20, 20 28, 24 24 S32 20, 36 24" fill="none" stroke="${color}" stroke-width="2.4" stroke-linecap="round" />
      `;
    }

    function headingVector(headingDeg, length) {
      const radians = ((Number(headingDeg || 0) - 90) * Math.PI) / 180;
      return {
        x: Math.cos(radians) * length,
        y: Math.sin(radians) * length
      };
    }

    function headingIndicatorSvg(headingDeg, color, moving) {
      const outer = headingVector(headingDeg, 16);
      const left = headingVector(Number(headingDeg || 0) + 150, 5);
      const right = headingVector(Number(headingDeg || 0) - 150, 5);
      const tipX = 22 + outer.x;
      const tipY = 22 + outer.y;
      const wingLeftX = tipX + left.x;
      const wingLeftY = tipY + left.y;
      const wingRightX = tipX + right.x;
      const wingRightY = tipY + right.y;
      const dash = moving ? "" : 'stroke-dasharray="2 2"';
      return `
        <path d="M22 22 L${tipX.toFixed(2)} ${tipY.toFixed(2)}" fill="none" stroke="${color}" stroke-width="2.2" stroke-linecap="round" ${dash} />
        <path d="M${wingLeftX.toFixed(2)} ${wingLeftY.toFixed(2)} L${tipX.toFixed(2)} ${tipY.toFixed(2)} L${wingRightX.toFixed(2)} ${wingRightY.toFixed(2)}" fill="none" stroke="${color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" ${dash} />
      `;
    }

    function topModifierSvg(label, color) {
      if (!label) return "";
      return `
        <text x="22" y="7.5" text-anchor="middle" font-size="8.5" font-weight="700" fill="${color}" style="font-family: Georgia, serif;">
          ${label}
        </text>
      `;
    }

    function natoSymbolHtml(unitType, affiliation, options = {}) {
      const color = affiliationColor(affiliation);
      const category = symbolCategory(unitType);
      const selected = options.selected ? " selected" : "";
      const dashArray = options.lastKnown ? "4 3" : "";
      const opacity = options.lastKnown ? 0.65 : 1.0;
      const topModifier = options.topModifier || "";
      const headingSvg = options.showHeading ? headingIndicatorSvg(options.headingDeg, color, options.moving) : "";
      const svg = `
        <svg width="44" height="44" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg" style="opacity:${opacity}">
          ${options.selected ? '<circle cx="22" cy="22" r="20" fill="rgba(196,139,43,0.16)" stroke="#c48b2b" stroke-width="2" />' : ""}
          ${topModifierSvg(topModifier, color)}
          ${symbolFrameSvg(affiliation, dashArray)}
          ${symbolInteriorSvg(category, color)}
          ${headingSvg}
        </svg>
      `;
      return `<div class="mil-symbol${selected}">${svg}</div>`;
    }

    function loadTerrain() {
      if (terrainPromise) return terrainPromise;
      terrainPromise = fetch("/terrain/land.geojson")
        .then((response) => response.json())
        .then((payload) => {
          landPolygons = flattenLandGeometry(payload);
          return landPolygons;
        })
        .catch((error) => {
          console.error("terrain load failed", error);
          landPolygons = [];
          return landPolygons;
        });
      return terrainPromise;
    }

    function flattenLandGeometry(geojson) {
      const polygons = [];
      for (const feature of (geojson.features || [])) {
        const geometry = feature.geometry || {};
        if (geometry.type === "Polygon") {
          polygons.push(buildPolygonRecord(geometry.coordinates || []));
        } else if (geometry.type === "MultiPolygon") {
          for (const polygon of (geometry.coordinates || [])) {
            polygons.push(buildPolygonRecord(polygon));
          }
        }
      }
      return polygons;
    }

    function buildPolygonRecord(rings) {
      const allPoints = rings.flat();
      const lons = allPoints.map((point) => point[0]);
      const lats = allPoints.map((point) => point[1]);
      return {
        rings,
        bbox: [Math.min(...lons), Math.min(...lats), Math.max(...lons), Math.max(...lats)]
      };
    }

    function unitDomain(unitType) {
      const normalized = String(unitType || "").trim().toLowerCase();
      if (!normalized) return null;
      const waterKeywords = ["surface", "subsurface", "naval", "sea", "ship", "submarine", "convoy"];
      const landKeywords = ["land", "ground", "shore", "coastal", "airbase", "sam", "site", "battery"];
      if (waterKeywords.some((keyword) => normalized.includes(keyword))) return "water";
      if (landKeywords.some((keyword) => normalized.includes(keyword))) return "land";
      return null;
    }

    function normalizeLongitude(lon) {
      return ((Number(lon) + 180) % 360 + 360) % 360 - 180;
    }

    function pointOnLand(lat, lon) {
      if (!landPolygons.length) return false;
      const normalizedLon = normalizeLongitude(lon);
      for (const polygon of landPolygons) {
        const [minLon, minLat, maxLon, maxLat] = polygon.bbox;
        if (normalizedLon < minLon || normalizedLon > maxLon || lat < minLat || lat > maxLat) continue;
        if (pointInPolygon(lat, normalizedLon, polygon.rings)) return true;
      }
      return false;
    }

    function pointInPolygon(lat, lon, rings) {
      if (!rings.length) return false;
      if (!pointInRing(lat, lon, rings[0])) return false;
      for (const hole of rings.slice(1)) {
        if (pointInRing(lat, lon, hole)) return false;
      }
      return true;
    }

    function pointInRing(lat, lon, ring) {
      let inside = false;
      let j = ring.length - 1;
      for (let i = 0; i < ring.length; i += 1) {
        const xi = ring[i][0];
        const yi = ring[i][1];
        const xj = ring[j][0];
        const yj = ring[j][1];
        const intersects = ((yi > lat) !== (yj > lat)) &&
          (lon < ((xj - xi) * (lat - yi)) / ((yj - yi) || 1e-12) + xi);
        if (intersects) inside = !inside;
        j = i;
      }
      return inside;
    }

    function validateUnitPosition(unitType, lat, lon) {
      const domain = unitDomain(unitType);
      if (!domain || !landPolygons.length) return { ok: true };
      const isLand = pointOnLand(lat, lon);
      if (domain === "water" && isLand) {
        return { ok: false, message: `${unitType} units must stay on water.` };
      }
      if (domain === "land" && !isLand) {
        return { ok: false, message: `${unitType} units must stay on land.` };
      }
      return { ok: true };
    }

    function validateMovementSegment(unitType, start, end) {
      const domain = unitDomain(unitType);
      if (!domain || !landPolygons.length) return { ok: true };
      const endpointCheck = validateUnitPosition(unitType, end.lat, end.lon);
      if (!endpointCheck.ok) return endpointCheck;
      for (let step = 1; step <= 16; step += 1) {
        const fraction = step / 16;
        const lat = start.lat + (end.lat - start.lat) * fraction;
        const lon = start.lon + (end.lon - start.lon) * fraction;
        const sampleCheck = validateUnitPosition(unitType, lat, lon);
        if (!sampleCheck.ok) return sampleCheck;
      }
      return { ok: true };
    }

    const FACTION_OPTIONS = ["NATO", "United States", "United Kingdom", "Iran", "Soviet Union", "Warsaw Pact", "Civilian"];

    function defaultScenarioSeed() {
      return {
        scenario_name: "New Scenario",
        turn_duration_minutes: 60,
        map_center: { lat: 0.0, lon: 1.0 },
        environment: {
          date: "1985,6,26",
          time: "10,0",
          convert_time_to_local: false,
          sea_state: 3,
          clouds: "Scattered_1",
          wind_direction: "E",
          load_background_data: false
        },
        side_metadata: {
          Blue: { faction: "NATO", starting_funds: 1000 },
          Red: { faction: "Warsaw Pact", starting_funds: 1000 }
        },
        fleets: [
          defaultFleet("Blue", 1),
          defaultFleet("Red", 1)
        ]
      };
    }

    function defaultFleet(side, index) {
      const isBlue = side === "Blue";
      return {
        id: `${side.toLowerCase()}_${index}`,
        sp_id: `${side.toUpperCase()}_${index}`,
        name: `${side} Fleet ${index}`,
        side,
        unit_type: "Surface",
        sea_power_type: isBlue ? "usn_dd_spruance" : "ir_ptg_combattante_II",
        variant_reference: "Variant1",
        station_role: "",
        crew_skill: "Trained",
        telegraph: 2,
        lat: 0.0,
        lon: isBlue ? 0.0 : 2.0,
        heading_deg: isBlue ? 90.0 : 270.0,
        speed_kts: 20.0,
        detection_radius_nm: 100.0,
        status: "Active"
      };
    }

    function totalCompositionCount(composition) {
      return (composition || []).reduce((total, item) => total + Number(item.count || 1), 0);
    }

    function echelonLabel(composition) {
      const total = totalCompositionCount(composition);
      if (total <= 1) return "I";
      if (total <= 3) return "II";
      if (total <= 6) return "III";
      if (total <= 9) return "X";
      return "XX";
    }

    async function fetchJson(url, options) {
      const response = await fetch(url, options);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Request failed");
      return data;
    }

    function formatScenarioDetails(scenario) {
      if (!scenario) {
        $("scenario-details").textContent = "No scenario selected.";
        return;
      }
      const fleets = Array.isArray(scenario.seed?.fleets) ? scenario.seed.fleets : [];
      const sideMetadata = scenario.seed?.side_metadata || {};
      const blueMeta = sideMetadata.Blue || {};
      const redMeta = sideMetadata.Red || {};
      $("scenario-details").innerHTML = `
        <strong>${scenario.scenario_name}</strong><br />
        ${fleets.length} fleet(s) • ${scenario.seed.turn_duration_minutes} minute turn<br />
        Blue: ${blueMeta.faction || "Unknown"} • funds ${blueMeta.starting_funds ?? 0}<br />
        Red: ${redMeta.faction || "Unknown"} • funds ${redMeta.starting_funds ?? 0}<br />
        Updated ${new Date(scenario.updated_at).toLocaleString()}
      `;
    }

    function populateFactionSelect(selectId) {
      const select = $(selectId);
      select.innerHTML = "";
      for (const faction of FACTION_OPTIONS) {
        const option = document.createElement("option");
        option.value = faction;
        option.textContent = faction;
        select.appendChild(option);
      }
    }

    function populateScenarioForm(seed) {
      const payload = seed || defaultScenarioSeed();
      $("scenario-name").value = payload.scenario_name || "";
      $("turn-duration").value = payload.turn_duration_minutes ?? 60;
      $("map-center-lat").value = payload.map_center?.lat ?? "";
      $("map-center-lon").value = payload.map_center?.lon ?? "";
      $("sea-state").value = payload.environment?.sea_state ?? 3;
      $("scenario-date").value = payload.environment?.date || "1985,6,26";
      $("scenario-time").value = payload.environment?.time || "10,0";
      $("blue-faction").value = payload.side_metadata?.Blue?.faction || "NATO";
      $("blue-funds").value = payload.side_metadata?.Blue?.starting_funds ?? 1000;
      $("red-faction").value = payload.side_metadata?.Red?.faction || "Warsaw Pact";
      $("red-funds").value = payload.side_metadata?.Red?.starting_funds ?? 1000;
      scenarioFormFleets = (payload.fleets || []).map((fleet) => ({ ...fleet }));
      renderFleetEditor();
    }

    function renderFleetEditor() {
      const container = $("fleet-editor");
      container.innerHTML = "";
      scenarioFormFleets.forEach((fleet, index) => {
        const card = document.createElement("div");
        card.className = "fleet-card";
        card.innerHTML = `
          <h3>${fleet.side} Fleet ${index + 1}</h3>
          <div class="field-grid">
            <div>
              <label>Fleet Name</label>
              <input data-field="name" data-index="${index}" value="${fleet.name || ""}" />
            </div>
            <div>
              <label>SP ID</label>
              <input data-field="sp_id" data-index="${index}" value="${fleet.sp_id || ""}" />
            </div>
          </div>
          <div class="field-grid three">
            <div>
              <label>Lat</label>
              <input data-field="lat" data-index="${index}" type="number" step="0.0001" value="${fleet.lat ?? 0}" />
            </div>
            <div>
              <label>Lon</label>
              <input data-field="lon" data-index="${index}" type="number" step="0.0001" value="${fleet.lon ?? 0}" />
            </div>
            <div>
              <label>Heading</label>
              <input data-field="heading_deg" data-index="${index}" type="number" step="0.1" value="${fleet.heading_deg ?? 0}" />
            </div>
          </div>
          <div class="field-grid three">
            <div>
              <label>Speed Kts</label>
              <input data-field="speed_kts" data-index="${index}" type="number" step="0.1" value="${fleet.speed_kts ?? 20}" />
            </div>
            <div>
              <label>Detection Radius</label>
              <input data-field="detection_radius_nm" data-index="${index}" type="number" step="0.1" value="${fleet.detection_radius_nm ?? 100}" />
            </div>
            <div>
              <label>Sea Power Type</label>
              <input data-field="sea_power_type" data-index="${index}" value="${fleet.sea_power_type || ""}" />
            </div>
          </div>
          <div class="field-grid three">
            <div>
              <label>Variant</label>
              <input data-field="variant_reference" data-index="${index}" value="${fleet.variant_reference || "Variant1"}" />
            </div>
            <div>
              <label>Role</label>
              <input data-field="station_role" data-index="${index}" value="${fleet.station_role || ""}" />
            </div>
            <div>
              <label>Skill</label>
              <input data-field="crew_skill" data-index="${index}" value="${fleet.crew_skill || "Trained"}" />
            </div>
          </div>
          <div class="inline-actions">
            <button type="button" class="danger" data-remove-fleet="${index}">Remove Fleet</button>
          </div>
        `;
        container.appendChild(card);
      });
      if (!scenarioFormFleets.length) {
        container.innerHTML = '<div class="small">No fleets configured yet.</div>';
      }
    }

    function updateFleetField(index, field, value) {
      const fleet = scenarioFormFleets[index];
      if (!fleet) return;
      const numericFields = new Set(["lat", "lon", "heading_deg", "speed_kts", "detection_radius_nm"]);
      fleet[field] = numericFields.has(field) ? Number(value) : value;
    }

    function addFleet(side) {
      const nextIndex = scenarioFormFleets.filter((fleet) => fleet.side === side).length + 1;
      scenarioFormFleets.push(defaultFleet(side, nextIndex));
      renderFleetEditor();
    }

    function collectScenarioFormData() {
      if (!scenarioFormFleets.length) {
        throw new Error("At least one fleet is required.");
      }
      return {
        scenario_name: $("scenario-name").value.trim(),
        turn_duration_minutes: Number($("turn-duration").value),
        map_center: {
          lat: Number($("map-center-lat").value),
          lon: Number($("map-center-lon").value),
        },
        environment: {
          date: $("scenario-date").value.trim(),
          time: $("scenario-time").value.trim(),
          convert_time_to_local: false,
          sea_state: Number($("sea-state").value),
          clouds: "Scattered_1",
          wind_direction: "E",
          load_background_data: false,
        },
        side_metadata: {
          Blue: {
            faction: $("blue-faction").value,
            starting_funds: Number($("blue-funds").value),
          },
          Red: {
            faction: $("red-faction").value,
            starting_funds: Number($("red-funds").value),
          }
        },
        fleets: scenarioFormFleets.map((fleet, index) => ({
          id: fleet.id || `${fleet.side.toLowerCase()}_${index + 1}`,
          sp_id: fleet.sp_id || `${fleet.side.toUpperCase()}_${index + 1}`,
          name: fleet.name || `${fleet.side} Fleet ${index + 1}`,
          side: fleet.side,
          unit_type: fleet.unit_type || "Surface",
          sea_power_type: fleet.sea_power_type || "usn_dd_spruance",
          variant_reference: fleet.variant_reference || "Variant1",
          station_role: fleet.station_role || "",
          crew_skill: fleet.crew_skill || "Trained",
          telegraph: 2,
          lat: Number(fleet.lat),
          lon: Number(fleet.lon),
          heading_deg: Number(fleet.heading_deg),
          speed_kts: Number(fleet.speed_kts),
          detection_radius_nm: Number(fleet.detection_radius_nm),
          status: fleet.status || "Active",
        }))
      };
    }

    function syncScenarioButtons() {
      const hasSelection = Boolean(selectedScenarioId);
      $("load-scenario").disabled = !hasSelection;
      $("delete-scenario").disabled = !hasSelection;
      $("create-session").disabled = !hasSelection;
    }

    async function refreshScenarioList(preferredScenarioId) {
      const data = await fetchJson("/scenarios");
      const select = $("scenario-select");
      scenarioCache = new Map();
      select.innerHTML = "";

      for (const scenario of data.scenarios) {
        scenarioCache.set(scenario.scenario_id, scenario);
        const option = document.createElement("option");
        option.value = scenario.scenario_id;
        option.textContent = scenario.scenario_name;
        select.appendChild(option);
      }

      const nextScenarioId = preferredScenarioId && scenarioCache.has(preferredScenarioId)
        ? preferredScenarioId
        : (data.scenarios[0]?.scenario_id || "");

      selectedScenarioId = nextScenarioId;
      select.value = nextScenarioId;
      syncScenarioButtons();

      if (nextScenarioId) {
        await loadScenario(nextScenarioId, false);
      } else {
        formatScenarioDetails(null);
      }
    }

    async function loadScenario(scenarioId, updateSelection = true) {
      if (!scenarioId) {
        selectedScenarioId = "";
        syncScenarioButtons();
        formatScenarioDetails(null);
        return;
      }
      const scenario = await fetchJson(`/scenarios/${encodeURIComponent(scenarioId)}`);
      scenarioCache.set(scenario.scenario_id, scenario);
      selectedScenarioId = scenario.scenario_id;
      if (updateSelection) $("scenario-select").value = scenario.scenario_id;
      syncScenarioButtons();
      formatScenarioDetails(scenario);
    }

    async function importExampleScenario() {
      const payload = await fetchJson("/example-seed.json");
      const created = await fetchJson("/scenarios", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      await refreshScenarioList(created.scenario_id);
    }

    function openScenarioDialog(seed, scenarioId) {
      editingScenarioId = scenarioId || "";
      $("scenario-dialog-title").textContent = editingScenarioId ? "Edit Scenario" : "Create Scenario";
      $("scenario-dialog-text").textContent = editingScenarioId
        ? "Update the selected scenario seed and save the changes back to the library."
        : "Initialize a new scenario using structured setup fields and an editable fleet roster.";
      $("save-scenario").textContent = editingScenarioId ? "Update Scenario" : "Create Scenario";
      populateScenarioForm(seed || defaultScenarioSeed());
      $("scenario-dialog").showModal();
    }

    function closeScenarioDialog() {
      editingScenarioId = "";
      $("scenario-dialog").close();
    }

    async function createSessionForScenario(scenarioId) {
      const created = await fetchJson("/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_id: scenarioId }),
      });
      $("create-result").classList.remove("hidden");
      $("create-result").innerHTML = `
        <div><strong>Session created.</strong></div>
        <div class="stack">
          <a href="${created.blue_url}">Open Blue team view</a>
          <a href="${created.red_url}">Open Red team view</a>
        </div>
        <code>Blue URL: ${created.blue_url}</code>
        <code>Red URL: ${created.red_url}</code>
        <code>Admin export token: ${created.admin_token}</code>
        <code>Export URL: ${created.export_url}</code>
      `;
      return created;
    }

    async function saveScenario() {
      try {
        const payload = collectScenarioFormData();
        const isEditing = Boolean(editingScenarioId);
        const method = editingScenarioId ? "PUT" : "POST";
        const url = editingScenarioId
          ? `/scenarios/${encodeURIComponent(editingScenarioId)}`
          : "/scenarios";
        const created = await fetchJson(url, {
          method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        closeScenarioDialog();
        await refreshScenarioList(created.scenario_id);
        if (!isEditing) {
          await createSessionForScenario(created.scenario_id);
        }
      } catch (error) {
        alert(error.message || "Scenario form is invalid.");
      }
    }

    async function startSelectedScenario() {
      if (!selectedScenarioId) return;
      await createSessionForScenario(selectedScenarioId);
    }

    async function deleteSelectedScenario() {
      if (!selectedScenarioId) return;
      const scenario = scenarioCache.get(selectedScenarioId);
      if (!window.confirm(`Delete scenario "${scenario?.scenario_name || selectedScenarioId}"?`)) return;
      await fetchJson(`/scenarios/${encodeURIComponent(selectedScenarioId)}`, { method: "DELETE" });
      $("create-result").classList.add("hidden");
      await refreshScenarioList("");
    }

    function createSession() {
      if (!selectedScenarioId) {
        alert("Select a saved scenario first.");
        return;
      }
      createSessionForScenario(selectedScenarioId).catch((error) => alert(error.message));
    }

    function openSessionFromInputs() {
      const nextSession = $("session-id-input").value.trim();
      const nextToken = $("token-input").value.trim();
      if (!nextSession || !nextToken) {
        alert("Session ID and token are required.");
        return;
      }
      const nextUrl = new URL(window.location.href);
      nextUrl.searchParams.set("session", nextSession);
      nextUrl.searchParams.set("token", nextToken);
      window.location.href = nextUrl.toString();
    }

    function clearSessionQuery() {
      const nextUrl = new URL(window.location.href);
      nextUrl.search = "";
      window.location.href = nextUrl.toString();
    }

    function updateScreenMode(hasActiveSession) {
      $("create-panel").classList.toggle("hidden", hasActiveSession);
      $("join-panel").classList.toggle("hidden", hasActiveSession);
      $("play-panel").classList.toggle("hidden", !hasActiveSession);
      $("selected-panel").classList.toggle("hidden", !hasActiveSession);
      $("orders-panel").classList.toggle("hidden", !hasActiveSession);
      $("contacts-panel").classList.toggle("hidden", !hasActiveSession);
    }

    function startPolling() {
      if (pollHandle) clearInterval(pollHandle);
      pollHandle = setInterval(loadView, 5000);
    }

    function loadView() {
      if (!sessionId || !token) return;
      fetch(`/sessions/${encodeURIComponent(sessionId)}/view?token=${encodeURIComponent(token)}`)
        .then(async (response) => {
          const data = await response.json();
          if (!response.ok) throw new Error(data.error || "Failed to load view");
          return data;
        })
        .then((view) => {
          currentView = view;
          side = view.side;
          initializeMap();
          updateScreenMode(true);
          syncDraftOrders(view);
          updatePanels(view);
          renderView(view);
        })
        .catch((error) => {
          console.error(error);
          updateScreenMode(false);
          $("play-panel").classList.remove("hidden");
          $("turn-banner").textContent = "Unable to load session";
          $("session-meta").textContent = error.message;
        });
    }

    function syncDraftOrders(view) {
      if (view.own_submitted) {
        draftOrders = {};
        for (const order of view.orders) {
          draftOrders[order.fleet_id] = order.waypoints.map((point) => ({ lat: point.lat, lon: point.lon }));
        }
        return;
      }
      const nextDraft = {};
      for (const order of view.orders) {
        nextDraft[order.fleet_id] = order.waypoints.map((point) => ({ lat: point.lat, lon: point.lon }));
      }
      for (const [fleetId, points] of Object.entries(draftOrders)) {
        if (!nextDraft[fleetId]) nextDraft[fleetId] = points;
      }
      draftOrders = nextDraft;
    }

    function updatePanels(view) {
      $("turn-banner").textContent = `${view.scenario_name} - Turn ${view.current_turn}`;
      $("session-meta").textContent = `${view.side} view • ${view.turn_duration_minutes} minute WEGO turn`;
      $("own-status-pill").textContent = view.own_submitted ? "Own turn submitted" : "Own turn open";
      $("enemy-status-pill").textContent = view.opponent_ready ? "Enemy ready" : "Enemy pending";

      const selectedFleet = view.fleets.find((fleet) => fleet.id === selectedFleetId);
      $("selected-fleet").innerHTML = selectedFleet
        ? `<strong>${selectedFleet.name}</strong><br /><span class="small">${selectedFleet.sp_id} • ${selectedFleet.speed_kts} kts • heading ${selectedFleet.heading_deg.toFixed(1)}°</span>`
        : "No fleet selected.";

      $("submit-turn").disabled = !view.can_submit;
      $("clear-selected-order").disabled = !selectedFleetId || !view.can_submit;

      const orderEntries = Object.entries(draftOrders);
      $("orders-list").innerHTML = orderEntries.length
        ? orderEntries.map(([fleetId, points]) => {
            const fleet = view.fleets.find((entry) => entry.id === fleetId);
            const fleetName = fleet ? fleet.name : fleetId;
            return `<div class="order-item"><strong>${fleetName}</strong><br />${points.length} waypoint(s)</div>`;
          }).join("")
        : "No drafted orders.";

      $("contacts-list").innerHTML = view.contacts.length
        ? view.contacts.map((contact) => {
            return `<div class="order-item"><strong>${contact.name}</strong><br />${contact.state} • last seen turn ${contact.last_seen_turn}</div>`;
          }).join("")
        : "No enemy contacts.";
    }

    function renderView(view) {
      if (!map) return;
      const center = [view.map_center.lat, view.map_center.lon];
      if (mapInitializedForSession !== view.session_id) {
        map.setView(center, 4);
        mapInitializedForSession = view.session_id;
      }

      for (const marker of ownFleetMarkers.values()) marker.remove();
      for (const marker of contactMarkers.values()) marker.remove();
      for (const polyline of orderPolylines.values()) polyline.remove();
      ownFleetMarkers.clear();
      contactMarkers.clear();
      orderPolylines.clear();

      for (const fleet of view.fleets) {
        const affiliation = affiliationForFleet(view, fleet);
        const points = draftOrders[fleet.id] || [];
        const marker = L.marker([fleet.lat, fleet.lon], {
          draggable: Boolean(view.can_submit),
          icon: L.divIcon({
            className: "",
            html: natoSymbolHtml(fleet.unit_type, affiliation, {
              selected: selectedFleetId === fleet.id,
              topModifier: echelonLabel(fleet.composition),
              showHeading: true,
              headingDeg: fleet.heading_deg,
              moving: points.length > 0
            }),
            iconSize: [44, 44],
            iconAnchor: [22, 22]
          })
        }).addTo(map);
        marker.bindTooltip(`${fleet.name} (${fleet.sp_id})`);
        marker.on("click", () => {
          selectedFleetId = fleet.id;
          renderView(currentView);
          updatePanels(view);
        });
        marker.on("dragstart", () => {
          selectedFleetId = fleet.id;
          updatePanels(view);
        });
        marker.on("dragend", (event) => {
          const latlng = event.target.getLatLng();
          const validation = validateMovementSegment(
            fleet.unit_type,
            { lat: fleet.lat, lon: fleet.lon },
            { lat: latlng.lat, lon: latlng.lng }
          );
          if (!validation.ok) {
            alert(validation.message);
            renderView(currentView);
            return;
          }
          draftOrders[fleet.id] = [{ lat: latlng.lat, lon: latlng.lng }];
          renderView(currentView);
          updatePanels(currentView);
        });
        ownFleetMarkers.set(fleet.id, marker);
        if (points.length) {
          const route = [[fleet.lat, fleet.lon], ...points.map((point) => [point.lat, point.lon])];
          const polyline = L.polyline(route, {
            color: colorForSide(fleet.side),
            weight: 2,
            dashArray: "6,6"
          }).addTo(map);
          orderPolylines.set(fleet.id, polyline);
        }
      }

      for (const contact of view.contacts) {
        const affiliation = contact.state === "last_known" ? "unknown" : "hostile";
        const marker = L.marker([contact.lat, contact.lon], {
          interactive: false,
          icon: L.divIcon({
            className: "",
            html: natoSymbolHtml(contact.unit_type, affiliation, {
              lastKnown: contact.state === "last_known",
              topModifier: "I",
              showHeading: contact.state !== "last_known",
              headingDeg: contact.heading_deg,
              moving: contact.state !== "last_known"
            }),
            iconSize: [40, 40],
            iconAnchor: [20, 20]
          })
        }).addTo(map);
        marker.bindTooltip(`${contact.name} (${contact.state})`);
        contactMarkers.set(contact.fleet_id, marker);
      }
    }

    function onMapClick(event) {
      if (!currentView || !currentView.can_submit || !selectedFleetId) return;
      const fleet = currentView.fleets.find((entry) => entry.id === selectedFleetId);
      if (!fleet) return;
      const points = draftOrders[selectedFleetId] || [];
      const startPoint = points.length
        ? points[points.length - 1]
        : { lat: fleet.lat, lon: fleet.lon };
      const nextPoint = { lat: event.latlng.lat, lon: event.latlng.lng };
      const validation = validateMovementSegment(fleet.unit_type, startPoint, nextPoint);
      if (!validation.ok) {
        alert(validation.message);
        return;
      }
      points.push(nextPoint);
      draftOrders[selectedFleetId] = points;
      renderView(currentView);
      updatePanels(currentView);
    }

    function clearSelectedOrder() {
      if (!selectedFleetId) return;
      delete draftOrders[selectedFleetId];
      renderView(currentView);
      updatePanels(currentView);
    }

    function submitTurn() {
      if (!currentView || !currentView.can_submit) return;
      const payload = {
        turn_number: currentView.current_turn,
        orders: Object.entries(draftOrders).map(([fleetId, waypoints]) => ({ fleet_id: fleetId, waypoints }))
      };
      fetch(`/sessions/${encodeURIComponent(sessionId)}/turns/${encodeURIComponent(side)}?token=${encodeURIComponent(token)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
        .then(async (response) => {
          const data = await response.json();
          if (!response.ok) throw new Error(data.error || "Submit failed");
          return data;
        })
        .then(() => loadView())
        .catch((error) => alert(error.message));
    }

    $("new-scenario").addEventListener("click", () => openScenarioDialog());
    $("refresh-scenarios").addEventListener("click", () => refreshScenarioList(selectedScenarioId).catch((error) => alert(error.message)));
    $("load-scenario").addEventListener("click", () => startSelectedScenario().catch((error) => alert(error.message)));
    $("delete-scenario").addEventListener("click", () => deleteSelectedScenario().catch((error) => alert(error.message)));
    $("create-session").addEventListener("click", createSession);
    $("load-example-scenario").addEventListener("click", () => importExampleScenario().catch((error) => alert(error.message)));
    $("join-session").addEventListener("click", openSessionFromInputs);
    $("clear-session").addEventListener("click", clearSessionQuery);
    $("submit-turn").addEventListener("click", submitTurn);
    $("clear-selected-order").addEventListener("click", clearSelectedOrder);
    $("dialog-load-example").addEventListener("click", async () => {
      const payload = await fetchJson("/example-seed.json");
      populateScenarioForm(payload);
    });
    $("save-scenario").addEventListener("click", () => saveScenario().catch((error) => alert(error.message)));
    $("close-scenario-dialog").addEventListener("click", closeScenarioDialog);
    $("add-blue-fleet").addEventListener("click", () => addFleet("Blue"));
    $("add-red-fleet").addEventListener("click", () => addFleet("Red"));
    $("fleet-editor").addEventListener("input", (event) => {
      const target = event.target;
      if (!target.dataset.index || !target.dataset.field) return;
      updateFleetField(Number(target.dataset.index), target.dataset.field, target.value);
    });
    $("fleet-editor").addEventListener("click", (event) => {
      const trigger = event.target.closest("[data-remove-fleet]");
      if (!trigger) return;
      scenarioFormFleets.splice(Number(trigger.dataset.removeFleet), 1);
      renderFleetEditor();
    });
    $("scenario-select").addEventListener("change", () => {
      loadScenario($("scenario-select").value).catch((error) => alert(error.message));
    });

    populateFactionSelect("blue-faction");
    populateFactionSelect("red-faction");
    syncScenarioButtons();
    updateScreenMode(false);
    refreshScenarioList().catch((error) => {
      $("scenario-details").textContent = error.message;
    });
    if (sessionId && token) {
      $("session-id-input").value = sessionId;
      $("token-input").value = token;
      loadView();
      startPolling();
    }
  </script>
</body>
</html>
"""

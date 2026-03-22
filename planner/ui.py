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
    textarea, input, button {
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
    .button-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 10px;
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
    .session-links code {
      display: block;
      margin-top: 6px;
      word-break: break-all;
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
    select {
      width: 100%;
      padding: 10px;
      border-radius: 10px;
      border: 1px solid rgba(27, 43, 52, 0.18);
      font: inherit;
      background: white;
    }
    .admin-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .stat-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 8px;
    }
    .stat-card {
      padding: 10px;
      border-radius: 10px;
      background: rgba(27, 43, 52, 0.06);
      font-size: 0.86rem;
    }
    .composition-list {
      margin-top: 10px;
      border-top: 1px solid rgba(27, 43, 52, 0.1);
      padding-top: 10px;
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
        <h2>Create Session</h2>
        <p class="muted">Paste or edit a scenario seed JSON, then create a hosted WEGO session.</p>
        <label for="seed-json">Scenario Seed</label>
        <textarea id="seed-json"></textarea>
        <div class="button-row">
          <button id="load-example">Load Example</button>
          <button class="secondary" id="create-session">Create Session</button>
        </div>
        <div id="create-result" class="session-links hidden"></div>
      </section>

      <section id="join-panel">
        <h2>Join Existing Session</h2>
        <label for="session-id-input">Session ID</label>
        <input id="session-id-input" placeholder="session id" />
        <label for="token-input">Access Token</label>
        <input id="token-input" placeholder="player or admin token" />
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

      <section id="economy-panel" class="hidden">
        <h2>Resources</h2>
        <div id="resource-summary" class="small">No economy data yet.</div>
      </section>

      <section id="build-panel" class="hidden">
        <h2>Build Fleets</h2>
        <div id="build-controls">
          <div id="build-side-row">
            <label for="build-side">Build For Side</label>
            <select id="build-side">
              <option value="Blue">Blue</option>
              <option value="Red">Red</option>
            </select>
          </div>
          <label for="build-template">Template</label>
          <select id="build-template"></select>
          <div id="build-template-details" class="small">No template selected.</div>
          <div class="button-row">
            <button id="build-fleet">Build Fleet</button>
            <button id="refresh-builds" class="secondary">Refresh Build Panel</button>
          </div>
        </div>
      </section>

      <section id="selected-panel" class="hidden">
        <h2>Selected Fleet</h2>
        <div id="selected-fleet">No fleet selected.</div>
        <div id="selected-composition" class="composition-list small">No fleet composition selected.</div>
        <div class="button-row">
          <button id="clear-selected-order" class="secondary">Clear Selected Order</button>
          <button id="submit-turn">Submit Turn</button>
        </div>
        <p class="small">Click a fleet, then click the map to add waypoint(s). Drag a fleet marker to create the first leg quickly.</p>
      </section>

      <section id="admin-panel" class="hidden">
        <h2>Admin Controls</h2>
        <div id="admin-summary" class="small">No session loaded.</div>
        <div id="admin-composition" class="composition-list small">Select a fleet to inspect full composition.</div>
        <div id="admin-fleet-editor" class="hidden" style="margin-top: 10px;">
          <label for="admin-name">Fleet Name</label>
          <input id="admin-name" />
          <div class="admin-grid">
            <div>
              <label for="admin-side">Side</label>
              <select id="admin-side">
                <option value="Blue">Blue</option>
                <option value="Red">Red</option>
              </select>
            </div>
            <div>
              <label for="admin-unit-type">Unit Type</label>
              <input id="admin-unit-type" />
            </div>
            <div>
              <label for="admin-lat">Latitude</label>
              <input id="admin-lat" type="number" step="0.0001" />
            </div>
            <div>
              <label for="admin-lon">Longitude</label>
              <input id="admin-lon" type="number" step="0.0001" />
            </div>
            <div>
              <label for="admin-heading">Heading</label>
              <input id="admin-heading" type="number" step="0.1" />
            </div>
            <div>
              <label for="admin-speed">Speed (kts)</label>
              <input id="admin-speed" type="number" step="0.1" min="0" />
            </div>
            <div>
              <label for="admin-detection">Detection Radius (nm)</label>
              <input id="admin-detection" type="number" step="0.1" min="0" />
            </div>
            <div>
              <label for="admin-status">Status</label>
              <input id="admin-status" />
            </div>
          </div>
          <div class="button-row">
            <button id="admin-save-fleet">Save Fleet</button>
            <button id="admin-resolve-turn" class="secondary">Resolve Turn</button>
          </div>
          <div class="button-row">
            <button id="admin-export-scenario">Open Export</button>
            <button id="admin-refresh-view" class="secondary">Refresh View</button>
          </div>
        </div>
        <p class="small">Admin drag edits save immediately. Hidden enemy movement is not revealed to players unless it becomes detectable.</p>
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

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <script>
    const query = new URLSearchParams(window.location.search);
    let sessionId = query.get("session") || "";
    let token = query.get("token") || "";
    let adminToken = query.get("admin_token") || "";
    let side = null;
    let currentRole = null;
    let currentView = null;
    let selectedFleetId = null;
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
      if (view.role === "admin") {
        return fleet.side === "Blue" ? "friendly" : "hostile";
      }
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

    function fleetCompositionHtml(composition) {
      if (!composition || !composition.length) return "No composition details.";
      return composition.map((item) => {
        const count = Number(item.count || 1);
        const prefix = count > 1 ? `${count}x ` : "";
        return `<div class="order-item"><strong>${prefix}${item.name}</strong><br />${item.sea_power_type} • ${item.variant_reference}</div>`;
      }).join("");
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

    function economyForSide(view, requestedSide) {
      if (view.role === "admin") {
        return view.side_state[requestedSide];
      }
      return view.economy;
    }

    function currentBuildSide(view) {
      if (view.role === "admin") {
        return $("build-side").value || "Blue";
      }
      return view.side;
    }

    function loadExample() {
      fetch("/example-seed.json")
        .then((response) => response.json())
        .then((payload) => {
          $("seed-json").value = JSON.stringify(payload, null, 2);
        });
    }

    function createSession() {
      let payload;
      try {
        payload = JSON.parse($("seed-json").value);
      } catch (error) {
        alert("Seed JSON is invalid.");
        return;
      }
      fetch("/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then(async (response) => {
          const data = await response.json();
          if (!response.ok) throw new Error(data.error || "Create failed");
          return data;
        })
        .then((data) => {
          $("create-result").classList.remove("hidden");
          $("create-result").innerHTML = `
            <div><strong>Session created.</strong></div>
            <code>Blue URL: ${data.blue_url}</code>
            <code>Red URL: ${data.red_url}</code>
            <code>Admin URL: ${data.admin_url}</code>
            <code>Export URL: ${data.export_url}</code>
          `;
        })
        .catch((error) => alert(error.message));
    }

    function openSessionFromInputs() {
      const nextSession = $("session-id-input").value.trim();
      const nextToken = $("token-input").value.trim();
      if (!nextSession || !nextToken) {
        alert("Session ID and token are required.");
        return;
      }
      const nextUrl = new URL(window.location.href);
      nextUrl.searchParams.delete("admin_token");
      nextUrl.searchParams.set("session", nextSession);
      nextUrl.searchParams.set("token", nextToken);
      window.location.href = nextUrl.toString();
    }

    function clearSessionQuery() {
      const nextUrl = new URL(window.location.href);
      nextUrl.search = "";
      window.location.href = nextUrl.toString();
    }

    function updateSessionPanels(hasActiveSession) {
      $("create-panel").classList.toggle("hidden", hasActiveSession);
      $("join-panel").classList.toggle("hidden", hasActiveSession);
    }

    function startPolling() {
      if (pollHandle) clearInterval(pollHandle);
      pollHandle = setInterval(loadView, 5000);
    }

    function rememberAdminToken(secret) {
      adminToken = secret;
      token = "";
      const nextUrl = new URL(window.location.href);
      nextUrl.searchParams.set("session", sessionId);
      nextUrl.searchParams.delete("token");
      nextUrl.searchParams.set("admin_token", secret);
      window.history.replaceState({}, "", nextUrl.toString());
    }

    function loadPlayerView() {
      return fetch(`/sessions/${encodeURIComponent(sessionId)}/view?token=${encodeURIComponent(token)}`)
        .then(async (response) => {
          const data = await response.json();
          if (!response.ok) throw { response, data };
          return data;
        });
    }

    function loadAdminView(secret) {
      return fetch(`/sessions/${encodeURIComponent(sessionId)}/admin/view?admin_token=${encodeURIComponent(secret)}`)
        .then(async (response) => {
          const data = await response.json();
          if (!response.ok) throw { response, data };
          return data;
        });
    }

    function loadView() {
      if (!sessionId || (!token && !adminToken)) return;
      const activeRequest = adminToken
        ? loadAdminView(adminToken)
        : loadPlayerView().catch((error) => {
            if (error.response && error.response.status === 403 && token) {
              return loadAdminView(token).then((view) => {
                rememberAdminToken(token);
                return view;
              });
            }
            throw error;
          });

      activeRequest
        .then((view) => {
          currentView = view;
          currentRole = view.role;
          side = view.side || null;
          initializeMap();
          updateSessionPanels(true);
          syncDraftOrders(view);
          updatePanels(view);
          renderView(view);
        })
        .catch((error) => {
          console.error(error);
          updateSessionPanels(false);
          $("play-panel").classList.remove("hidden");
          $("turn-banner").textContent = "Unable to load session";
          $("session-meta").textContent = (error.data && error.data.error) || error.message || "Failed to load session";
        });
    }

    function syncDraftOrders(view) {
      if (view.role === "admin") {
        draftOrders = {};
        return;
      }
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
      $("play-panel").classList.remove("hidden");
      $("economy-panel").classList.remove("hidden");
      $("build-panel").classList.remove("hidden");
      $("selected-panel").classList.remove("hidden");
      const adminMode = view.role === "admin";
      $("admin-panel").classList.toggle("hidden", !adminMode);
      $("orders-panel").classList.remove("hidden");
      $("contacts-panel").classList.toggle("hidden", adminMode);

      $("turn-banner").textContent = `${view.scenario_name} — Turn ${view.current_turn}`;
      $("session-meta").textContent = adminMode
        ? `Admin view • ${view.turn_duration_minutes} minute WEGO turn`
        : `${view.side} view • ${view.turn_duration_minutes} minute WEGO turn`;
      $("own-status-pill").textContent = adminMode
        ? `Blue ${view.current_turn_record.submissions.Blue ? "submitted" : "pending"}`
        : view.own_submitted ? "Own turn submitted" : "Own turn open";
      $("enemy-status-pill").textContent = adminMode
        ? `Red ${view.current_turn_record.submissions.Red ? "submitted" : "pending"}`
        : view.opponent_ready ? "Enemy ready" : "Enemy pending";

      const selectedFleet = view.fleets.find((fleet) => fleet.id === selectedFleetId);
      $("selected-fleet").innerHTML = selectedFleet
        ? `<strong>${selectedFleet.name}</strong><br /><span class="small">${selectedFleet.sp_id} • ${selectedFleet.speed_kts} kts • heading ${selectedFleet.heading_deg.toFixed(1)}°</span>`
        : "No fleet selected.";
      $("selected-composition").innerHTML = selectedFleet
        ? fleetCompositionHtml(selectedFleet.composition)
        : "No fleet composition selected.";

      $("selected-panel").classList.toggle("hidden", adminMode);
      $("submit-turn").disabled = adminMode || !view.can_submit;
      $("clear-selected-order").disabled = adminMode || !selectedFleetId || !view.can_submit;

      if (adminMode) {
        const submittedSides = Object.keys(view.current_turn_record.submissions);
        $("orders-list").innerHTML = `
          <div class="order-item"><strong>Current Turn Status</strong><br />${view.current_turn_record.status}</div>
          <div class="order-item"><strong>Submissions</strong><br />${submittedSides.length ? submittedSides.join(", ") : "None yet"}</div>
          <div class="order-item"><strong>Total Fleets</strong><br />${view.fleets.length}</div>
        `;
        const editorVisible = Boolean(selectedFleet);
        $("admin-fleet-editor").classList.toggle("hidden", !editorVisible);
        $("admin-summary").innerHTML = selectedFleet
          ? `Editing <strong>${selectedFleet.name}</strong> (${selectedFleet.side})`
          : "Select a fleet on the map to edit it, drag it to reposition, or build a new fleet for either side.";
        $("admin-composition").innerHTML = selectedFleet
          ? fleetCompositionHtml(selectedFleet.composition)
          : "Select a fleet to inspect full composition.";
        if (selectedFleet) populateAdminEditor(selectedFleet);
      } else {
        const orderEntries = Object.entries(draftOrders);
        $("orders-list").innerHTML = orderEntries.length
          ? orderEntries.map(([fleetId, points]) => {
              const fleet = view.fleets.find((entry) => entry.id === fleetId);
              const fleetName = fleet ? fleet.name : fleetId;
              return `<div class="order-item"><strong>${fleetName}</strong><br />${points.length} waypoint(s)</div>`;
            }).join("")
          : "No drafted orders.";
      }

      updateEconomyPanel(view);
      updateBuildPanel(view);

      if (!adminMode) {
        $("contacts-list").innerHTML = view.contacts.length
          ? view.contacts.map((contact) => {
              return `<div class="order-item"><strong>${contact.name}</strong><br />${contact.state} • last seen turn ${contact.last_seen_turn}</div>`;
            }).join("")
          : "No enemy contacts.";
      }
    }

    function updateEconomyPanel(view) {
      if (view.role === "admin") {
        $("resource-summary").innerHTML = ["Blue", "Red"].map((sideName) => {
          const economy = view.side_state[sideName];
          return `
            <div class="stat-card">
              <strong>${sideName}</strong><br />
              Resources: ${economy.resources}<br />
              Spent: ${economy.total_spent}<br />
              Income/turn: ${economy.income_per_turn}<br />
              Fleets: ${economy.fleet_count}<br />
              Spawn: ${economy.spawn_point.lat.toFixed(2)}, ${economy.spawn_point.lon.toFixed(2)}
            </div>
          `;
        }).join("");
        return;
      }

      const economy = view.economy;
      $("resource-summary").innerHTML = `
        <div class="stat-grid">
          <div class="stat-card"><strong>Available</strong><br />${economy.resources}</div>
          <div class="stat-card"><strong>Spent</strong><br />${economy.total_spent}</div>
          <div class="stat-card"><strong>Income / Turn</strong><br />${economy.income_per_turn}</div>
          <div class="stat-card"><strong>Fleet Count</strong><br />${economy.fleet_count}</div>
        </div>
        <div class="small" style="margin-top:10px;">Spawn point: ${economy.spawn_point.lat.toFixed(2)}, ${economy.spawn_point.lon.toFixed(2)}</div>
      `;
    }

    function updateBuildPanel(view) {
      const adminMode = view.role === "admin";
      $("build-side-row").classList.toggle("hidden", !adminMode);
      if (!adminMode) {
        $("build-side").value = view.side;
      }

      const sideName = currentBuildSide(view);
      const economy = economyForSide(view, sideName);
      const templates = economy.build_catalog || [];
      const previousValue = $("build-template").value;
      $("build-template").innerHTML = templates.length
        ? templates.map((entry) => `<option value="${entry.id}">${entry.name} (${entry.cost})</option>`).join("")
        : '<option value="">No builds available</option>';

      if (templates.some((entry) => entry.id === previousValue)) {
        $("build-template").value = previousValue;
      }
      renderBuildTemplateDetails(view);
    }

    function renderBuildTemplateDetails(view) {
      const sideName = currentBuildSide(view);
      const economy = economyForSide(view, sideName);
      const templateId = $("build-template").value;
      const template = (economy.build_catalog || []).find((entry) => entry.id === templateId);
      if (!template) {
        $("build-template-details").innerHTML = "No template selected.";
        $("build-fleet").disabled = true;
        return;
      }

      const canAfford = Number(economy.resources) >= Number(template.cost);
      const canIssueBuild = view.role === "admin" ? true : Boolean(view.can_build);
      const spawnCheck = validateUnitPosition(template.unit_type, economy.spawn_point.lat, economy.spawn_point.lon);
      $("build-fleet").disabled = !canAfford || !canIssueBuild || !spawnCheck.ok;

      $("build-template-details").innerHTML = `
        <div class="small" style="margin-top:10px;">
          Cost: ${template.cost} resources<br />
          Type: ${template.unit_type}<br />
          Speed: ${template.speed_kts} kts<br />
          Detection: ${template.detection_radius_nm} nm<br />
          Available: ${economy.resources}<br />
          Spawn: ${economy.spawn_point.lat.toFixed(2)}, ${economy.spawn_point.lon.toFixed(2)}${spawnCheck.ok ? "" : `<br /><strong>${spawnCheck.message}</strong>`}
        </div>
        <div class="composition-list small">${fleetCompositionHtml(template.composition)}</div>
      `;
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
        const points = view.role === "admin" ? [] : (draftOrders[fleet.id] || []);
        const marker = L.marker([fleet.lat, fleet.lon], {
          draggable: Boolean(view.role === "admin" || view.can_submit),
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
          if (view.role === "admin") {
            const validation = validateUnitPosition(fleet.unit_type, latlng.lat, latlng.lng);
            if (!validation.ok) {
              alert(validation.message);
              renderView(currentView);
              return;
            }
            saveAdminFleetUpdate(fleet.id, { lat: latlng.lat, lon: latlng.lng });
          } else {
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
          }
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

      if (view.role === "admin") return;

      for (const contact of (view.contacts || [])) {
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

    function populateAdminEditor(fleet) {
      $("admin-name").value = fleet.name || "";
      $("admin-side").value = fleet.side || "Blue";
      $("admin-unit-type").value = fleet.unit_type || "";
      $("admin-lat").value = fleet.lat;
      $("admin-lon").value = fleet.lon;
      $("admin-heading").value = fleet.heading_deg;
      $("admin-speed").value = fleet.speed_kts;
      $("admin-detection").value = fleet.detection_radius_nm;
      $("admin-status").value = fleet.status || "";
    }

    function saveAdminFleetUpdate(fleetId, payload) {
      if (!sessionId || !adminToken) return;
      fetch(`/sessions/${encodeURIComponent(sessionId)}/admin/fleets/${encodeURIComponent(fleetId)}?admin_token=${encodeURIComponent(adminToken)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
        .then(async (response) => {
          const data = await response.json();
          if (!response.ok) throw new Error(data.error || "Admin update failed");
          return data;
        })
        .then(() => loadView())
        .catch((error) => alert(error.message));
    }

    function saveAdminFleetFromForm() {
      if (!currentView || currentView.role !== "admin" || !selectedFleetId) return;
      const validation = validateUnitPosition(
        $("admin-unit-type").value,
        Number($("admin-lat").value),
        Number($("admin-lon").value)
      );
      if (!validation.ok) {
        alert(validation.message);
        return;
      }
      saveAdminFleetUpdate(selectedFleetId, {
        name: $("admin-name").value,
        side: $("admin-side").value,
        unit_type: $("admin-unit-type").value,
        lat: Number($("admin-lat").value),
        lon: Number($("admin-lon").value),
        heading_deg: Number($("admin-heading").value),
        speed_kts: Number($("admin-speed").value),
        detection_radius_nm: Number($("admin-detection").value),
        status: $("admin-status").value
      });
    }

    function buildFleet() {
      if (!currentView) return;
      const sideName = currentBuildSide(currentView);
      const templateId = $("build-template").value;
      if (!templateId) return;
      const queryString = currentView.role === "admin"
        ? `admin_token=${encodeURIComponent(adminToken)}`
        : `token=${encodeURIComponent(token)}`;

      fetch(`/sessions/${encodeURIComponent(sessionId)}/builds/${encodeURIComponent(sideName)}?${queryString}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ template_id: templateId })
      })
        .then(async (response) => {
          const data = await response.json();
          if (!response.ok) throw new Error(data.error || "Build failed");
          return data;
        })
        .then((data) => {
          selectedFleetId = data.fleet.id;
          loadView();
        })
        .catch((error) => alert(error.message));
    }

    function resolveTurnAsAdmin() {
      if (!sessionId || !adminToken) return;
      fetch(`/sessions/${encodeURIComponent(sessionId)}/resolve?admin_token=${encodeURIComponent(adminToken)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}"
      })
        .then(async (response) => {
          const data = await response.json();
          if (!response.ok) throw new Error(data.error || "Resolve failed");
          return data;
        })
        .then(() => loadView())
        .catch((error) => alert(error.message));
    }

    function openAdminExport() {
      if (!sessionId || !adminToken) return;
      window.open(`/sessions/${encodeURIComponent(sessionId)}/export/scenario.ini?admin_token=${encodeURIComponent(adminToken)}`, "_blank");
    }

    function onMapClick(event) {
      if (currentView && currentView.role === "admin") return;
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
      if (currentView && currentView.role === "admin") return;
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

    $("load-example").addEventListener("click", loadExample);
    $("create-session").addEventListener("click", createSession);
    $("join-session").addEventListener("click", openSessionFromInputs);
    $("clear-session").addEventListener("click", clearSessionQuery);
    $("submit-turn").addEventListener("click", submitTurn);
    $("clear-selected-order").addEventListener("click", clearSelectedOrder);
    $("build-fleet").addEventListener("click", buildFleet);
    $("refresh-builds").addEventListener("click", loadView);
    $("build-side").addEventListener("change", () => {
      if (currentView) updateBuildPanel(currentView);
    });
    $("build-template").addEventListener("change", () => {
      if (currentView) renderBuildTemplateDetails(currentView);
    });
    $("admin-save-fleet").addEventListener("click", saveAdminFleetFromForm);
    $("admin-resolve-turn").addEventListener("click", resolveTurnAsAdmin);
    $("admin-export-scenario").addEventListener("click", openAdminExport);
    $("admin-refresh-view").addEventListener("click", loadView);

    loadExample();
    if (sessionId && (token || adminToken)) {
      $("session-id-input").value = sessionId;
      $("token-input").value = token || adminToken;
      loadView();
      startPolling();
    } else {
      updateSessionPanels(false);
    }
  </script>
</body>
</html>
"""

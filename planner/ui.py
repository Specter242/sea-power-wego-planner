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
    .fleet-token {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      border: 2px solid rgba(255, 255, 255, 0.9);
      box-shadow: 0 2px 10px rgba(27, 43, 52, 0.28);
    }
    .fleet-token.selected {
      transform: scale(1.25);
      border-color: var(--accent);
    }
    .fleet-token.blue { background: var(--blue); }
    .fleet-token.red { background: var(--red); }
    .fleet-token.neutral { background: var(--neutral); }
    .contact-token {
      width: 14px;
      height: 14px;
      border-radius: 50%;
      border: 2px solid rgba(255, 255, 255, 0.85);
      box-shadow: 0 2px 8px rgba(27, 43, 52, 0.22);
    }
    .contact-token.last-known {
      background: #d9ba6a;
      border-style: dashed;
      border-color: #8b6b2f;
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

    function $(id) { return document.getElementById(id); }

    function initializeMap() {
      if (map) return;
      map = L.map("map", { worldCopyJump: true, minZoom: 2 }).setView([20, 0], 3);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 18
      }).addTo(map);
      map.on("click", onMapClick);
    }

    function colorForSide(value) {
      if (value === "Blue") return "#2b6bc4";
      if (value === "Red") return "#c43434";
      return "#6f7780";
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
        const marker = L.marker([fleet.lat, fleet.lon], {
          draggable: Boolean(view.can_submit),
          icon: L.divIcon({
            className: "",
            html: `<div class="fleet-token ${fleet.side.toLowerCase()} ${selectedFleetId === fleet.id ? "selected" : ""}"></div>`,
            iconSize: [18, 18],
            iconAnchor: [9, 9]
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
          draftOrders[fleet.id] = [{ lat: latlng.lat, lon: latlng.lng }];
          renderView(currentView);
          updatePanels(currentView);
        });
        ownFleetMarkers.set(fleet.id, marker);

        const points = draftOrders[fleet.id] || [];
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
        const marker = L.marker([contact.lat, contact.lon], {
          interactive: false,
          icon: L.divIcon({
            className: "",
            html: contact.state === "visible"
              ? `<div class="contact-token" style="background:${colorForSide(view.enemy_side)}"></div>`
              : `<div class="contact-token last-known"></div>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7]
          })
        }).addTo(map);
        marker.bindTooltip(`${contact.name} (${contact.state})`);
        contactMarkers.set(contact.fleet_id, marker);
      }
    }

    function onMapClick(event) {
      if (!currentView || !currentView.can_submit || !selectedFleetId) return;
      const points = draftOrders[selectedFleetId] || [];
      points.push({ lat: event.latlng.lat, lon: event.latlng.lng });
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

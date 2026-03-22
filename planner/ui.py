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

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <script>
    const query = new URLSearchParams(window.location.search);
    let sessionId = query.get("session") || "";
    let token = query.get("token") || "";
    let side = null;
    let currentView = null;
    let selectedFleetId = null;
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
            <code>Admin export token: ${data.admin_token}</code>
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
      nextUrl.searchParams.set("session", nextSession);
      nextUrl.searchParams.set("token", nextToken);
      window.location.href = nextUrl.toString();
    }

    function clearSessionQuery() {
      const nextUrl = new URL(window.location.href);
      nextUrl.search = "";
      window.location.href = nextUrl.toString();
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
          syncDraftOrders(view);
          updatePanels(view);
          renderView(view);
        })
        .catch((error) => {
          console.error(error);
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
      $("play-panel").classList.remove("hidden");
      $("selected-panel").classList.remove("hidden");
      $("orders-panel").classList.remove("hidden");
      $("contacts-panel").classList.remove("hidden");

      $("turn-banner").textContent = `${view.scenario_name} — Turn ${view.current_turn}`;
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

    $("load-example").addEventListener("click", loadExample);
    $("create-session").addEventListener("click", createSession);
    $("join-session").addEventListener("click", openSessionFromInputs);
    $("clear-session").addEventListener("click", clearSessionQuery);
    $("submit-turn").addEventListener("click", submitTurn);
    $("clear-selected-order").addEventListener("click", clearSelectedOrder);

    loadExample();
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

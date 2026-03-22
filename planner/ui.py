INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Sea Power Campaign Manager</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="" />
  <style>
    :root {
      --bg: #dfe7eb;
      --panel: #f7f3ea;
      --panel-2: rgba(255, 255, 255, 0.82);
      --ink: #1b2e39;
      --muted: #61737c;
      --line: rgba(27, 46, 57, 0.14);
      --blue: #295a9d;
      --red: #b44339;
      --gold: #927034;
      --shadow: 0 12px 32px rgba(27, 46, 57, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      font-family: Georgia, "Palatino Linotype", serif;
      background:
        radial-gradient(circle at top right, rgba(41, 90, 157, 0.12), transparent 25%),
        radial-gradient(circle at top left, rgba(180, 67, 57, 0.10), transparent 24%),
        linear-gradient(180deg, #cfd9df 0%, var(--bg) 100%);
    }
    button, input, select, textarea {
      font: inherit;
      color: inherit;
      width: 100%;
      border-radius: 12px;
      border: 1px solid var(--line);
      padding: 10px 12px;
      background: white;
    }
    button {
      cursor: pointer;
      background: var(--ink);
      color: white;
      border: none;
    }
    button:disabled, select:disabled, input:disabled, textarea:disabled {
      opacity: 0.58;
      cursor: not-allowed;
    }
    button.secondary {
      background: transparent;
      color: var(--ink);
      border: 1px solid var(--line);
    }
    button.ghost {
      background: rgba(255, 255, 255, 0.54);
      color: var(--ink);
      border: 1px solid var(--line);
    }
    textarea { min-height: 120px; resize: vertical; }
    header {
      padding: 14px 18px;
      border-bottom: 1px solid var(--line);
      background: rgba(247, 243, 234, 0.92);
      backdrop-filter: blur(10px);
    }
    header h1 {
      margin: 0;
      font-size: 1.2rem;
    }
    .app-shell {
      display: none;
      grid-template-columns: 320px minmax(480px, 1fr) 420px;
      min-height: calc(100vh - 61px);
    }
    .app-shell.ready {
      display: grid;
    }
    .gate {
      min-height: calc(100vh - 61px);
      display: grid;
      place-items: center;
      padding: 24px;
    }
    .gate.hidden {
      display: none;
    }
    .gate-card,
    .pane,
    .card {
      background: rgba(247, 243, 234, 0.84);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      border-radius: 18px;
    }
    .gate-card {
      width: min(560px, 100%);
      padding: 26px;
    }
    .gate-actions {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-top: 16px;
    }
    .pane {
      overflow: auto;
      padding: 16px;
      margin: 12px;
      background: rgba(247, 243, 234, 0.82);
    }
    .middle {
      display: grid;
      grid-template-rows: auto 1fr;
      gap: 12px;
      margin: 12px 0;
    }
    .toolbar {
      display: grid;
      gap: 12px;
      padding: 14px 16px;
    }
    .toolbar-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .role-switch {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .role-switch button.active {
      background: var(--ink);
      color: white;
    }
    .workspace {
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: 12px;
      margin-right: 12px;
    }
    .card {
      padding: 16px;
      background: var(--panel-2);
    }
    .card h2, .card h3, .card h4 {
      margin: 0 0 10px;
    }
    .tabs {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .tabs button.active {
      background: var(--ink);
      color: white;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .grid-3 {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }
    .stack {
      display: grid;
      gap: 8px;
    }
    .muted {
      color: var(--muted);
      font-size: 0.9rem;
    }
    .pill {
      display: inline-block;
      border-radius: 999px;
      padding: 4px 10px;
      background: rgba(27, 46, 57, 0.08);
      font-size: 0.78rem;
      margin-right: 6px;
      margin-bottom: 6px;
    }
    .summary-cards {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .summary-card {
      padding: 14px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.72);
    }
    .summary-metric {
      font-size: 1.4rem;
      font-weight: bold;
      margin: 4px 0;
    }
    .banner.success {
      background: rgba(41, 90, 157, 0.12);
      border-color: rgba(41, 90, 157, 0.28);
    }
    .banner.error {
      background: rgba(180, 67, 57, 0.12);
      border-color: rgba(180, 67, 57, 0.28);
    }
    .navigator-group {
      margin-bottom: 16px;
    }
    .navigator-group h3 {
      margin: 0 0 8px;
      font-size: 0.84rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .nav-item {
      display: block;
      width: 100%;
      text-align: left;
      margin-bottom: 6px;
      background: rgba(255, 255, 255, 0.74);
      color: var(--ink);
      border: 1px solid transparent;
    }
    .nav-item.active {
      border-color: rgba(146, 112, 52, 0.4);
      background: rgba(146, 112, 52, 0.16);
    }
    .list {
      display: grid;
      gap: 8px;
    }
    .list-item {
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.68);
    }
    .fleet-cards {
      display: grid;
      gap: 10px;
    }
    .fleet-card {
      padding: 12px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.78);
      cursor: pointer;
    }
    .fleet-card.active {
      border-color: rgba(146, 112, 52, 0.45);
      background: rgba(146, 112, 52, 0.16);
    }
    .fleet-card-title {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 10px;
      margin-bottom: 6px;
      flex-wrap: wrap;
    }
    .fleet-card-roster {
      font-size: 0.88rem;
      color: var(--muted);
    }
    .picker-toolbar {
      display: grid;
      gap: 8px;
    }
    .picker-results {
      display: grid;
      gap: 8px;
      max-height: 320px;
      overflow: auto;
      padding-right: 2px;
    }
    .picker-result {
      width: 100%;
      text-align: left;
      background: rgba(255, 255, 255, 0.82);
      color: var(--ink);
      border: 1px solid var(--line);
    }
    .picker-result.active {
      border-color: rgba(146, 112, 52, 0.45);
      background: rgba(146, 112, 52, 0.16);
    }
    .picker-result strong {
      display: block;
      margin-bottom: 4px;
    }
    .selected-ship-summary {
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.74);
      border: 1px solid var(--line);
    }
    .economy-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .highlight-item {
      border-color: rgba(41, 90, 157, 0.35);
      background: rgba(41, 90, 157, 0.12);
    }
    .inline-pills {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .roster-list {
      display: grid;
      gap: 8px;
    }
    .roster-item {
      border: 1px solid var(--line);
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.7);
      overflow: hidden;
    }
    .roster-toggle {
      width: 100%;
      text-align: left;
      background: transparent;
      color: var(--ink);
      border: none;
      padding: 12px;
    }
    .roster-toggle.active {
      background: rgba(146, 112, 52, 0.12);
    }
    .roster-summary {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 10px;
      flex-wrap: wrap;
    }
    .roster-expand {
      padding: 0 12px 12px;
      border-top: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.54);
    }
    .weapon-grid {
      display: grid;
      gap: 6px;
    }
    .weapon-row {
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 8px;
      align-items: baseline;
      padding: 8px 10px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.82);
      border: 1px solid var(--line);
      font-size: 0.9rem;
    }
    .detail-grid {
      display: grid;
      gap: 12px;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 0.84rem;
      font-family: Consolas, monospace;
    }
    #map-wrap {
      position: relative;
      min-height: 380px;
    }
    #map {
      width: 100%;
      min-height: 380px;
      height: 100%;
      border-radius: 16px;
      overflow: hidden;
      border: 1px solid var(--line);
    }
    .map-note {
      margin-top: 10px;
      font-size: 0.88rem;
      color: var(--muted);
    }
    .banner {
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.68);
      border: 1px solid var(--line);
    }
    .side-tag-blue { color: var(--blue); }
    .side-tag-red { color: var(--red); }
    .side-tag-admin { color: var(--gold); }
    @media (max-width: 1280px) {
      .app-shell.ready {
        grid-template-columns: 290px 1fr;
      }
      .workspace {
        margin-right: 12px;
      }
      .right-pane {
        grid-column: 1 / -1;
        margin-top: 0;
      }
    }
    @media (max-width: 900px) {
      .app-shell.ready {
        grid-template-columns: 1fr;
      }
      .pane, .middle {
        margin: 12px;
      }
      .workspace {
        margin-right: 0;
      }
      .gate-actions {
        grid-template-columns: 1fr;
      }
      .grid-2, .grid-3 {
        grid-template-columns: 1fr;
      }
      .summary-cards, .economy-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <header>
    <h1>Sea Power Campaign Manager</h1>
  </header>

  <section class="gate" id="role-gate">
    <div class="gate-card">
      <h2>Select Team</h2>
      <div class="muted">This local planner always opens one campaign. Choose the side you want to manage or open the full-truth admin view.</div>
      <div class="gate-actions">
        <button data-role-choice="Blue">Blue</button>
        <button data-role-choice="Red">Red</button>
        <button class="secondary" data-role-choice="Admin">ADMIN</button>
      </div>
    </div>
  </section>

  <main class="app-shell" id="app-shell">
    <aside class="pane">
      <div class="stack">
        <div class="banner" id="campaign-summary">Loading campaign...</div>
        <div id="admin-side-filter-wrap" class="stack" style="display:none;">
          <label for="focus-side">Admin Side Filter</label>
          <select id="focus-side">
            <option value="All">All</option>
            <option value="Blue">Blue</option>
            <option value="Red">Red</option>
          </select>
        </div>
        <div id="asset-navigator"></div>
      </div>
    </aside>

    <section class="middle">
      <div class="toolbar gate-card">
        <div class="toolbar-top">
          <div>
            <strong id="role-label">Role</strong>
            <div class="muted" id="turn-summary">Turn summary</div>
          </div>
          <div class="role-switch">
            <button class="ghost" data-switch-role="Blue">Blue</button>
            <button class="ghost" data-switch-role="Red">Red</button>
            <button class="ghost" data-switch-role="Admin">ADMIN</button>
          </div>
        </div>
      </div>

      <div class="workspace">
        <div class="card">
          <div class="tabs" id="workspace-tabs"></div>
        </div>
        <div class="card" id="workspace-overview"></div>
        <div class="card" id="workspace-detail"></div>
      </div>
    </section>

    <aside class="pane right-pane">
      <div class="stack">
        <div id="map-wrap">
          <div id="map"></div>
        </div>
        <div class="map-note" id="map-note">Select a fleet to view or draft orders.</div>
      </div>
    </aside>
  </main>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
  <script>
    const $ = (id) => document.getElementById(id);
    const SIDES = ["Blue", "Red"];
    const TABS = ["Overview", "Ports", "Fleets", "Ships", "Service", "Economy", "Turn"];

    let activeRole = "";
    let currentView = null;
    let selected = null;
    let activeTab = "Overview";
    let draftOrders = {};
    let map;
    let mapReady = false;
    let fleetMarkers = new Map();
    let portMarkers = new Map();
    let orderLines = new Map();
    let mapPreviewMarker = null;
    let shipPickerContext = null;
    let shipCreationFeedback = null;
    let shipCreationError = "";
    let economyFeedback = "";
    let portPlacementError = "";
    let importPreview = null;
    let importPreviewError = "";
    let importApplyFeedback = "";
    let importSelection = {};
    let importFormState = {
      savePath: "",
      ammoPath: "",
      costPath: ""
    };
    let mapMode = { kind: "idle" };
    let portPlacementDraft = {
      side: "",
      name: "",
      radiusNm: "5"
    };
    let portPlacementPreview = null;
    let shipPickerState = {
      nation: "All",
      classGroup: "All",
      search: "",
      shipId: "",
      quantity: "1",
      portId: "",
      variant: "Variant1",
      baseName: ""
    };
    let expandedRosterShipByFleet = {};

    function roleQuery() {
      return `role=${encodeURIComponent(activeRole)}`;
    }

    function isAdmin() {
      return activeRole === "Admin";
    }

    function focusSide() {
      if (!currentView) return activeRole;
      if (!isAdmin()) return activeRole;
      return $("focus-side").value || "All";
    }

    function visibleSides() {
      const value = focusSide();
      return value === "All" ? SIDES : [value];
    }

    function sideForCreates() {
      if (!isAdmin()) return activeRole;
      const value = focusSide();
      return value === "All" ? "Blue" : value;
    }

    function classOptions() {
      return currentView && currentView.catalogs ? (currentView.catalogs.ship_options || []) : [];
    }

    function clearMapMode(options = {}) {
      const preservePreview = !!options.preservePreview;
      mapMode = { kind: "idle" };
      if (!preservePreview) {
        portPlacementPreview = null;
      }
    }

    function setShipPickerContextForSide(side, selectedPortId = "") {
      const sidePorts = (currentView.ports || []).filter((port) => port.side === side);
      shipPickerContext = {
        side,
        selectedPortId,
        sidePortIds: sidePorts.map((port) => port.id)
      };
    }

    function asJson(response) {
      return response.json().then((data) => {
        if (!response.ok) throw data;
        return data;
      });
    }

    function setRole(role) {
      activeRole = role;
      localStorage.setItem("planner-role", role);
      const url = new URL(window.location.href);
      url.searchParams.set("role", role);
      window.history.replaceState({}, "", url);
      $("role-gate").classList.add("hidden");
      $("app-shell").classList.add("ready");
      document.querySelectorAll("[data-switch-role]").forEach((button) => {
        button.classList.toggle("active", button.dataset.switchRole === role);
      });
      $("admin-side-filter-wrap").style.display = isAdmin() ? "grid" : "none";
      if (!isAdmin()) $("focus-side").value = "All";
      selected = null;
      draftOrders = {};
      clearMapMode();
      shipCreationFeedback = null;
      shipCreationError = "";
      economyFeedback = "";
      portPlacementError = "";
      importPreview = null;
      importPreviewError = "";
      importApplyFeedback = "";
      importSelection = {};
      importFormState = { savePath: "", ammoPath: "", costPath: "" };
      loadView();
    }

    async function loadView() {
      if (!activeRole) return;
      try {
        currentView = await fetch(`/api/campaign/view?${roleQuery()}`).then(asJson);
        renderChrome();
        renderNavigator();
        renderWorkspace();
        renderMap();
      } catch (error) {
        $("workspace-overview").innerHTML = `<div class="muted">${error.error || error.message || "Failed to load campaign."}</div>`;
      }
    }

    function renderChrome() {
      const labelClass = activeRole === "Blue" ? "side-tag-blue" : activeRole === "Red" ? "side-tag-red" : "side-tag-admin";
      $("role-label").innerHTML = `<span class="${labelClass}">${activeRole}</span>`;
      const roleSummary = isAdmin() ? "ADMIN full truth" : `${activeRole} command view`;
      $("campaign-summary").innerHTML = `
        <strong>${currentView.scenario_name}</strong><br />
        <span class="muted">${roleSummary} | Turn ${currentView.current_turn} | ${currentView.turn_duration_minutes} min turns</span>
      `;
      const turnStatus = isAdmin()
        ? `Turn ${currentView.current_turn} | ${currentView.status}`
        : `Turn ${currentView.current_turn} | Submitted: ${currentView.own_submitted ? "yes" : "no"} | Opponent ready: ${currentView.opponent_ready ? "yes" : "no"}`;
      $("turn-summary").textContent = turnStatus;
    }

    function renderNavigator() {
      const selectedSides = visibleSides();
      const ships = currentView.ships || [];
      const fleets = currentView.fleets || [];
      const ports = currentView.ports || [];
      const rearmQueue = currentView.rearm_queue || [];
      const repairQueue = currentView.repair_queue || [];

      const sections = [];
      for (const side of selectedSides) {
        const sidePorts = ports.filter((port) => port.side === side);
        const dockedFleets = fleets.filter((fleet) => fleet.side === side && fleet.docked_port_id);
        const atSeaFleets = fleets.filter((fleet) => fleet.side === side && !fleet.docked_port_id);
        const reserveShips = ships.filter((ship) => ship.side === side && !ship.fleet_id);
        const serviceJobs = [...rearmQueue, ...repairQueue].filter((job) => job.side === side && job.state === "queued");
        sections.push(`
          <div class="navigator-group">
            <h3>${side}</h3>
            ${navigatorSection("Ports", sidePorts.map((port) => navButton("port", port.id, port.name)))}
            ${navigatorSection("Docked Fleets", dockedFleets.map((fleet) => navButton("fleet", fleet.id, `${fleet.name} (${fleet.ship_count})`)))}
            ${navigatorSection("At-Sea Fleets", atSeaFleets.map((fleet) => navButton("fleet", fleet.id, `${fleet.name} (${fleet.ship_count})`)))}
            ${navigatorSection("Reserve Ships", reserveShips.map((ship) => navButton("ship", ship.id, `${ship.name} [${ship.sea_power_type}]`)))}
            ${navigatorSection("Service Queue", serviceJobs.map((job) => `<div class="list-item">${job.id} <span class="muted">${job.ship_id} ready turn ${job.ready_turn}</span></div>`))}
          </div>
        `);
      }
      $("asset-navigator").innerHTML = sections.join("");
      document.querySelectorAll("[data-select-kind]").forEach((button) => {
        button.addEventListener("click", () => {
          clearMapMode();
          selected = { kind: button.dataset.selectKind, id: button.dataset.selectId };
          if (selected.kind === "port") activeTab = "Ports";
          if (selected.kind === "fleet") activeTab = "Fleets";
          if (selected.kind === "ship") activeTab = "Ships";
          renderNavigator();
          renderWorkspace();
          renderMap();
        });
      });
    }

    function navigatorSection(title, items) {
      return `
        <div class="stack" style="margin-bottom:10px;">
          <div class="muted">${title}</div>
          ${items.length ? items.join("") : `<div class="muted">None</div>`}
        </div>
      `;
    }

    function navButton(kind, id, label) {
      const active = selected && selected.kind === kind && selected.id === id ? "active" : "";
      return `<button class="nav-item ${active}" data-select-kind="${kind}" data-select-id="${id}">${label}</button>`;
    }

    function renderWorkspace() {
      $("workspace-tabs").innerHTML = TABS.map((tab) => `<button class="${activeTab === tab ? "active" : "secondary"}" data-tab="${tab}">${tab}</button>`).join("");
      document.querySelectorAll("[data-tab]").forEach((button) => {
        button.addEventListener("click", () => {
          if (button.dataset.tab !== "Ports" && button.dataset.tab !== "Fleets") clearMapMode();
          if (button.dataset.tab !== "Ports") portPlacementPreview = null;
          activeTab = button.dataset.tab;
          renderWorkspace();
          renderMap();
        });
      });
      renderOverviewCard();
      renderDetailCard();
    }

    function renderOverviewCard() {
      const sideSnapshots = SIDES.map((side) => economySummaryCard(currentView.side_state[side])).join("");
      const contactsHtml = isAdmin()
        ? `<div class="muted">ADMIN sees both sides, all fleets, and full queue state.</div>`
        : `<div class="muted">Contacts tracked: ${(currentView.contacts || []).length}</div>`;
      const filterNote = isAdmin() ? `<div class="muted">Side filter: ${focusSide()}</div>` : "";
      const catalogStatus = currentView.catalogs && currentView.catalogs.status
        ? `<div class="muted">Catalog: ${escapeHtml(currentView.catalogs.status.message || "Unavailable")}</div>`
        : "";
      $("workspace-overview").innerHTML = `
        <div class="stack">
          <div><strong>${currentView.scenario_name}</strong></div>
          <div class="summary-cards">${sideSnapshots}</div>
          ${contactsHtml}
          ${filterNote}
          ${catalogStatus}
        </div>
      `;
    }

    function selectedEntity() {
      if (!selected || !currentView) return null;
      if (selected.kind === "port") return (currentView.ports || []).find((entry) => entry.id === selected.id) || null;
      if (selected.kind === "fleet") return (currentView.fleets || []).find((entry) => entry.id === selected.id) || null;
      if (selected.kind === "ship") return (currentView.ships || []).find((entry) => entry.id === selected.id) || null;
      return null;
    }

    function renderDetailCard() {
      if (activeTab === "Overview") return renderOverviewTab();
      if (activeTab === "Ports") return renderPortsTab();
      if (activeTab === "Fleets") return renderFleetsTab();
      if (activeTab === "Ships") return renderShipsTab();
      if (activeTab === "Service") return renderServiceTab();
      if (activeTab === "Economy") return renderEconomyTab();
      return renderTurnTab();
    }

    function renderOverviewTab() {
      const side = sideForCreates();
      const adminControls = isAdmin() ? `
        <div class="detail-grid">
          <h3>Admin Campaign Controls</h3>
          ${importApplyFeedback ? `<div class="banner success">${escapeHtml(importApplyFeedback)}</div>` : ""}
          ${importPreviewError ? `<div class="banner error">${escapeHtml(importPreviewError)}</div>` : ""}
          <label for="import-save-path">Import Save Path</label>
          <input id="import-save-path" placeholder="C:\\\\path\\\\campaign.sav" value="${escapeAttr(importFormState.savePath)}" />
          <div class="grid-2">
            <input id="import-ammo-path" placeholder="Optional ammo_database.json path" value="${escapeAttr(importFormState.ammoPath)}" />
            <input id="import-cost-path" placeholder="Optional cost matrix HTML path" value="${escapeAttr(importFormState.costPath)}" />
          </div>
          <div class="grid-3">
            <button id="preview-import-btn">Preview Save Import</button>
            <button id="reset-campaign-btn" class="secondary">Reset Blank Campaign</button>
            <button id="export-campaign-btn" class="secondary">Export Scenario INI</button>
          </div>
          ${renderImportPreviewPanel()}
        </div>
      ` : "";
      $("workspace-detail").innerHTML = `
        <div class="detail-grid">
          <h3>Campaign Overview</h3>
          <div class="summary-cards">${SIDES.map((entry) => economySummaryCard(currentView.side_state[entry])).join("")}</div>
          <div class="list">
            <div class="list-item"><strong>Active command side:</strong> ${side}</div>
            <div class="list-item"><strong>Map center:</strong> ${currentView.map_center.lat.toFixed(3)}, ${currentView.map_center.lon.toFixed(3)}</div>
            <div class="list-item"><strong>Environment:</strong><pre>${JSON.stringify(currentView.environment, null, 2)}</pre></div>
            ${!isAdmin() ? `<div class="list-item"><strong>Contacts:</strong><pre>${JSON.stringify(currentView.contacts || [], null, 2)}</pre></div>` : ""}
          </div>
          ${adminControls}
        </div>
      `;
      if (isAdmin()) {
        $("preview-import-btn").addEventListener("click", previewImportSave);
        if ($("apply-import-btn")) $("apply-import-btn").addEventListener("click", applyImportSave);
        $("reset-campaign-btn").addEventListener("click", resetCampaign);
        $("export-campaign-btn").addEventListener("click", exportCampaign);
        ["import-save-path", "import-ammo-path", "import-cost-path"].forEach((id) => {
          const input = $(id);
          if (!input) return;
          input.addEventListener("input", () => {
            importFormState = {
              savePath: $("import-save-path") ? $("import-save-path").value : "",
              ammoPath: $("import-ammo-path") ? $("import-ammo-path").value : "",
              costPath: $("import-cost-path") ? $("import-cost-path").value : ""
            };
          });
        });
        bindImportPreviewControls();
      }
    }

    function renderImportPreviewPanel() {
      if (!importPreview) return "";
      const counts = importSelectionCounts();
      return `
        <div class="list-item">
          <strong>Import Preview</strong>
          <div class="stack" style="margin-top:8px;">
            <div class="muted">${escapeHtml(importPreview.save_path || "")}</div>
            <div class="inline-pills">
              <span class="pill">${counts.fleets} fleets selected</span>
              <span class="pill">${counts.ships} ships selected</span>
              ${counts.bySide.map((entry) => `<span class="pill">${entry.side}: ${entry.fleets} fleets / ${entry.ships} ships</span>`).join("")}
            </div>
            ${importPreview.sides.map((sideGroup) => importPreviewSideCard(sideGroup)).join("")}
            <button id="apply-import-btn" ${counts.ships ? "" : "disabled"}>Import Selected Fleets And Ships</button>
          </div>
        </div>
      `;
    }

    function importPreviewSideCard(sideGroup) {
      return `
        <div class="list-item">
          <label><input type="checkbox" data-import-side="${sideGroup.side}" /> <strong>${escapeHtml(sideGroup.side)}</strong></label>
          <div class="muted">${sideGroup.fleet_count} fleets | ${sideGroup.ship_count} ships in save</div>
          <div class="stack" style="margin-top:8px;">
            ${sideGroup.fleets.map((fleet) => importPreviewFleetCard(fleet)).join("")}
          </div>
        </div>
      `;
    }

    function importPreviewFleetCard(fleet) {
      return `
        <div class="list-item">
          <label><input type="checkbox" data-import-fleet="${fleet.candidate_id}" /> <strong>${escapeHtml(fleet.name)}</strong></label>
          <div class="muted">${escapeHtml(fleet.side)} | ${fleet.ship_count} ships | ${Number(fleet.lat || 0).toFixed(3)}, ${Number(fleet.lon || 0).toFixed(3)} | hdg ${Math.round(Number(fleet.heading_deg || 0))} | ${Math.round(Number(fleet.speed_kts || 0))} kts</div>
          <div class="stack" style="margin-top:8px; padding-left:12px;">
            ${fleet.ships.map((ship) => `
              <label>
                <input type="checkbox" data-import-ship="${ship.candidate_id}" data-import-parent="${fleet.candidate_id}" />
                ${escapeHtml(ship.name)} <span class="muted">(${escapeHtml(ship.class_display_name || ship.sea_power_type)} | ${escapeHtml(ship.variant_reference || "Variant1")})</span>
              </label>
            `).join("")}
          </div>
        </div>
      `;
    }

    function bindImportPreviewControls() {
      if (!importPreview) return;
      document.querySelectorAll("[data-import-ship]").forEach((input) => {
        input.checked = !!importSelection[input.dataset.importShip];
        input.addEventListener("change", () => {
          importSelection[input.dataset.importShip] = input.checked;
          renderWorkspace();
        });
      });
      document.querySelectorAll("[data-import-fleet]").forEach((input) => {
        const fleet = findImportFleet(input.dataset.importFleet);
        if (!fleet) return;
        const shipIds = fleet.ships.map((ship) => ship.candidate_id);
        const selectedShips = shipIds.filter((shipId) => !!importSelection[shipId]).length;
        input.checked = selectedShips === shipIds.length && shipIds.length > 0;
        input.indeterminate = selectedShips > 0 && selectedShips < shipIds.length;
        input.addEventListener("change", () => {
          shipIds.forEach((shipId) => {
            importSelection[shipId] = input.checked;
          });
          renderWorkspace();
        });
      });
      document.querySelectorAll("[data-import-side]").forEach((input) => {
        const sideGroup = (importPreview.sides || []).find((entry) => entry.side === input.dataset.importSide);
        if (!sideGroup) return;
        const shipIds = sideGroup.fleets.flatMap((fleet) => fleet.ships.map((ship) => ship.candidate_id));
        const selectedShips = shipIds.filter((shipId) => !!importSelection[shipId]).length;
        input.checked = selectedShips === shipIds.length && shipIds.length > 0;
        input.indeterminate = selectedShips > 0 && selectedShips < shipIds.length;
        input.addEventListener("change", () => {
          shipIds.forEach((shipId) => {
            importSelection[shipId] = input.checked;
          });
          renderWorkspace();
        });
      });
    }

    function findImportFleet(candidateId) {
      for (const sideGroup of (importPreview ? importPreview.sides || [] : [])) {
        const match = (sideGroup.fleets || []).find((fleet) => fleet.candidate_id === candidateId);
        if (match) return match;
      }
      return null;
    }

    function importSelectionCounts() {
      const bySide = [];
      let totalShips = 0;
      let totalFleets = 0;
      for (const sideGroup of (importPreview ? importPreview.sides || [] : [])) {
        let sideShipCount = 0;
        let sideFleetCount = 0;
        for (const fleet of sideGroup.fleets || []) {
          const selectedShips = fleet.ships.filter((ship) => !!importSelection[ship.candidate_id]).length;
          if (selectedShips > 0) {
            sideFleetCount += 1;
            sideShipCount += selectedShips;
          }
        }
        totalShips += sideShipCount;
        totalFleets += sideFleetCount;
        bySide.push({ side: sideGroup.side, fleets: sideFleetCount, ships: sideShipCount });
      }
      return { ships: totalShips, fleets: totalFleets, bySide };
    }

    function renderPortsTab() {
      const selectedPort = selected && selected.kind === "port" ? selectedEntity() : null;
      const side = selectedPort ? selectedPort.side : sideForCreates();
      const sidePorts = (currentView.ports || []).filter((port) => port.side === side);
      const dockedFleets = (currentView.fleets || []).filter((fleet) => fleet.side === side && fleet.docked_port_id === (selectedPort ? selectedPort.id : ""));
      const reserveShips = (currentView.ships || []).filter((ship) => ship.side === side && !ship.fleet_id && ship.port_id === (selectedPort ? selectedPort.id : ""));
      setShipPickerContextForSide(side, selectedPort ? selectedPort.id : "");
      const logisticsPortId = ensureLogisticsPortId(sidePorts, selectedPort);
      const placementSide = isAdmin() ? (portPlacementDraft.side || side) : side;
      if (!portPlacementDraft.side || !SIDES.includes(portPlacementDraft.side)) {
        portPlacementDraft.side = placementSide;
      }
      $("workspace-detail").innerHTML = `
        <div class="detail-grid">
          <h3>Ports</h3>
          <div class="grid-2">
            <div class="list-item">
              <strong>Selected port</strong>
              ${selectedPort ? `
                <div class="stack" style="margin-top:8px;">
                  <input id="edit-port-name" value="${escapeAttr(selectedPort.name)}" />
                  <div class="grid-3">
                    <input id="edit-port-lat" value="${selectedPort.lat}" />
                    <input id="edit-port-lon" value="${selectedPort.lon}" />
                    <input id="edit-port-radius" value="${selectedPort.radius_nm}" />
                  </div>
                  <button id="save-port-btn">Save Port</button>
                </div>
              ` : `<div class="muted" style="margin-top:8px;">Select a port from the navigator.</div>`}
            </div>
            <div class="list-item">
              <strong>Create port</strong>
              <div class="stack" style="margin-top:8px;">
                ${portPlacementError ? `<div class="banner error">${escapeHtml(portPlacementError)}</div>` : ""}
                ${isAdmin() ? adminSideSelector("create-port-side", placementSide) : `<div class="muted">${side}</div>`}
                <input id="create-port-name" placeholder="Port name" value="${escapeAttr(portPlacementDraft.name)}" />
                <div class="grid-2">
                  <input id="create-port-radius" placeholder="Radius nm" value="${escapeAttr(portPlacementDraft.radiusNm || "5")}" />
                  <button id="place-port-btn" class="${mapMode.kind === "place-port" ? "" : "secondary"}">${mapMode.kind === "place-port" ? "Awaiting Map Click" : "Place On Map"}</button>
                </div>
                ${portPlacementPreview ? `
                  <div class="banner">
                    <strong>Placement Preview</strong>
                    <div class="muted">Snapped to ${portPlacementPreview.lat.toFixed(4)}, ${portPlacementPreview.lon.toFixed(4)} (${Number(portPlacementPreview.distance_nm || 0).toFixed(2)} nm from click)</div>
                  </div>
                  <div class="grid-2">
                    <button id="create-port-btn">Create Port Here</button>
                    <button id="cancel-port-placement-btn" class="secondary">Cancel Placement</button>
                  </div>
                ` : `<div class="muted">${mapMode.kind === "place-port" ? "Click the map near shore to snap the new port onto the nearest valid coastline." : "Choose the side, name, and radius, then place the port on the map."}</div>`}
              </div>
            </div>
          </div>
          <div class="list-item">
            <strong>Side Logistics: Create Ships</strong>
            <div id="ship-picker-wrap" class="stack" style="margin-top:8px;"></div>
          </div>
          <div class="grid-2">
            <div class="list-item">
              <strong>Assemble fleet from reserve</strong>
              <div class="stack" style="margin-top:8px;">
                ${selectedPort ? `
                  <input id="create-fleet-name" placeholder="Fleet name" />
                  <select id="create-fleet-ships" multiple size="8">${reserveShips.map((ship) => `<option value="${ship.id}">${ship.name} (${ship.sea_power_type})</option>`).join("")}</select>
                  <button id="create-fleet-btn">Create Fleet</button>
                ` : `<div class="muted">Select a port to group reserve ships.</div>`}
              </div>
            </div>
            <div class="list-item">
              <strong>Selected port activity</strong>
              ${selectedPort ? portActivityDetail(selectedPort, dockedFleets, reserveShips) : `<div class="muted">Select a port to inspect docked fleets and reserve ships.</div>`}
            </div>
          </div>
          <div class="grid-2">
            <div class="list-item"><strong>${side} ports</strong><pre>${JSON.stringify(sidePorts, null, 2)}</pre></div>
            <div class="list-item"><strong>Logistics target</strong><pre>${JSON.stringify({ side, port_id: logisticsPortId, selected_ship_class: shipPickerState.shipId || null, quantity: shipPickerState.quantity, catalog_status: currentView.catalogs && currentView.catalogs.status ? currentView.catalogs.status.message : "" }, null, 2)}</pre></div>
          </div>
        </div>
      `;
      renderShipPickerPane();
      if (selectedPort) {
        $("save-port-btn").addEventListener("click", savePort);
        $("create-fleet-btn").addEventListener("click", createFleetAtPort);
      }
      $("place-port-btn").addEventListener("click", startPortPlacement);
      if ($("create-port-btn")) $("create-port-btn").addEventListener("click", createPort);
      if ($("cancel-port-placement-btn")) $("cancel-port-placement-btn").addEventListener("click", cancelPortPlacement);
      if ($("create-port-side")) {
        $("create-port-side").addEventListener("change", () => {
          portPlacementDraft.side = $("create-port-side").value;
        });
      }
      if ($("create-port-name")) {
        $("create-port-name").addEventListener("input", () => {
          portPlacementDraft.name = $("create-port-name").value;
          portPlacementError = "";
        });
      }
      if ($("create-port-radius")) {
        $("create-port-radius").addEventListener("input", () => {
          portPlacementDraft.radiusNm = $("create-port-radius").value;
          portPlacementError = "";
        });
      }
    }

    function renderFleetsTab() {
      const fleet = selected && selected.kind === "fleet" ? selectedEntity() : null;
      const fleetList = filteredFleets();
      const friendlyPorts = fleet ? (currentView.ports || []).filter((port) => port.side === fleet.side) : [];
      const mergeTargets = fleet ? (currentView.fleets || []).filter((entry) => entry.side === fleet.side && entry.id !== fleet.id) : [];
      const movementModeActive = mapMode.kind === "draft-fleet-move" && fleet && mapMode.fleetId === fleet.id;
      $("workspace-detail").innerHTML = `
        <div class="detail-grid">
          <h3>Fleets</h3>
          <div class="grid-2">
            <div class="list-item">
              <strong>Selected fleet</strong>
              ${fleet ? `
                <div class="stack" style="margin-top:8px;">
                  <input id="fleet-name" value="${escapeAttr(fleet.name)}" />
                  <div class="muted">Status ${fleet.status} | ${fleet.docked_port_id ? "Docked" : "At sea"} | ${fleet.ship_count} ships</div>
                  <div class="grid-2">
                    <button id="save-fleet-btn">Save Fleet Name</button>
                    <button id="dock-fleet-btn" class="secondary" ${fleet.docked_port_id || friendlyPorts.length ? "" : "disabled"}>${fleet.docked_port_id ? "Undock Fleet" : "Dock Fleet"}</button>
                  </div>
                  <div class="grid-2">
                    ${fleet.docked_port_id ? `<select id="dock-port-id" disabled><option>${escapeHtml(portNameForId(fleet.docked_port_id) || fleet.docked_port_id)}</option></select>` : `
                      ${friendlyPorts.length ? `
                        <select id="dock-port-id">
                          ${friendlyPorts.map((port) => `<option value="${port.id}">${escapeHtml(port.name)}</option>`).join("")}
                        </select>
                      ` : `<select id="dock-port-id" disabled><option>No friendly ports available</option></select>`}
                    `}
                    ${mergeTargets.length ? `
                      <select id="merge-target-id">${mergeTargets.map((target) => `<option value="${target.id}">${escapeHtml(target.name)} (${target.ship_count})</option>`).join("")}</select>
                    ` : `
                      <select id="merge-target-id" disabled><option>No friendly fleet targets</option></select>
                    `}
                  </div>
                  <button id="merge-fleet-btn" class="secondary" ${mergeTargets.length ? "" : "disabled"}>Merge Fleet</button>
                  <div class="muted">Drafted waypoints: ${(draftOrders[fleet.id] || []).length}</div>
                  <div class="grid-2">
                    <button id="fleet-draft-btn" class="${movementModeActive ? "" : "secondary"}" ${fleet.can_draft_movement ? "" : "disabled"}>${movementModeActive ? "Drafting On Map" : "Draft Movement"}</button>
                    <button id="fleet-clear-draft-btn" class="secondary" ${((draftOrders[fleet.id] || []).length > 0) ? "" : "disabled"}>Clear Draft</button>
                  </div>
                  ${fleet.movement_disabled_reason ? `<div class="muted">${escapeHtml(fleet.movement_disabled_reason)}</div>` : ""}
                </div>
              ` : `<div class="muted" style="margin-top:8px;">Select a fleet from the navigator or map.</div>`}
            </div>
            <div class="list-item">
              <strong>Fleet list</strong>
              ${fleetList.length ? `<div class="fleet-cards">${fleetList.map((item) => fleetCard(item)).join("")}</div>` : `<div class="muted">No fleets available for this view.</div>`}
            </div>
          </div>
          ${fleet ? `<div class="list-item"><strong>Roster</strong>${fleetRosterDetail(fleet)}</div>` : ""}
        </div>
      `;
      document.querySelectorAll("[data-fleet-card]").forEach((card) => {
        card.addEventListener("click", () => {
          selected = { kind: "fleet", id: card.dataset.fleetCard };
          activeTab = "Fleets";
          renderNavigator();
          renderWorkspace();
          renderMap();
        });
      });
      if (fleet) {
        $("save-fleet-btn").addEventListener("click", saveFleet);
        $("dock-fleet-btn").addEventListener("click", dockFleet);
        $("merge-fleet-btn").addEventListener("click", mergeFleet);
        $("fleet-draft-btn").addEventListener("click", toggleFleetDraftMode);
        $("fleet-clear-draft-btn").addEventListener("click", clearFleetDraft);
        document.querySelectorAll("[data-roster-ship]").forEach((button) => {
          button.addEventListener("click", () => {
            const shipId = button.dataset.rosterShip;
            if (expandedRosterShipByFleet[fleet.id] === shipId) {
              delete expandedRosterShipByFleet[fleet.id];
            } else {
              expandedRosterShipByFleet[fleet.id] = shipId;
            }
            renderWorkspace();
          });
        });
      }
    }

    function renderShipsTab() {
      const ship = selected && selected.kind === "ship" ? selectedEntity() : null;
      const builderSide = ship ? ship.side : sideForCreates();
      setShipPickerContextForSide(builderSide, ship && ship.port_id ? ship.port_id : "");
      $("workspace-detail").innerHTML = `
        <div class="detail-grid">
          <h3>Ships</h3>
          <div class="list-item">
            <strong>Build Ships</strong>
            <div id="ship-picker-wrap" class="stack" style="margin-top:8px;"></div>
          </div>
          ${ship ? `
            <div class="grid-2">
              <div class="list-item">
                <strong>Identity</strong>
                <div class="stack" style="margin-top:8px;">
                  <input id="ship-name" value="${escapeAttr(ship.name)}" />
                  <div class="muted">${ship.side} | ${ship.sea_power_type} | ${ship.variant_reference}</div>
                  <div class="muted">Fleet: ${ship.fleet_id || "Reserve"} | Port: ${ship.port_id || "At sea"} | Status: ${ship.status}</div>
                  <button id="save-ship-btn">Save Ship Name</button>
                </div>
              </div>
              <div class="list-item">
                <strong>Assignment</strong>
                <div class="stack" style="margin-top:8px;">
                  ${ship.can_transfer ? `
                    <select id="ship-target-fleet">
                      ${ship.eligible_transfer_fleets.map((fleet) => `<option value="${fleet.id}">${escapeHtml(fleet.name)} (${fleet.ship_count})${fleet.port_name ? ` | ${escapeHtml(fleet.port_name)}` : ""}</option>`).join("")}
                    </select>
                    <button id="ship-transfer-btn">Transfer To Fleet</button>
                  ` : `
                    <select id="ship-target-fleet" disabled><option>${escapeHtml(ship.transfer_reason || "No eligible friendly fleets available")}</option></select>
                    <button id="ship-transfer-btn" disabled>Transfer To Fleet</button>
                  `}
                  <div class="muted">${escapeHtml(ship.can_transfer ? "Select a friendly fleet to transfer this ship." : (ship.transfer_reason || "No eligible friendly fleets available"))}</div>
                  ${ship.can_dock ? `
                    <select id="ship-dock-port">
                      ${ship.eligible_dock_ports.map((port) => `<option value="${port.id}">${escapeHtml(port.name)} (${Number(port.distance_nm || 0).toFixed(2)} nm)</option>`).join("")}
                    </select>
                    <button id="ship-dock-btn" class="secondary">Dock At Nearby Port</button>
                  ` : `
                    <select id="ship-dock-port" disabled><option>${escapeHtml(ship.dock_reason || "No nearby friendly ports available")}</option></select>
                    <button id="ship-dock-btn" class="secondary" disabled>Dock At Nearby Port</button>
                  `}
                  <button id="ship-detach-btn" class="secondary" ${ship.can_detach ? "" : "disabled"}>Detach To New Fleet</button>
                  ${ship.detach_reason ? `<div class="muted">${escapeHtml(ship.detach_reason || "")}</div>` : ""}
                  <button id="ship-reserve-btn" class="secondary" ${ship.can_move_to_reserve ? "" : "disabled"}>Move To Reserve</button>
                  ${ship.move_to_reserve_reason ? `<div class="muted">${escapeHtml(ship.move_to_reserve_reason || "")}</div>` : ""}
                </div>
              </div>
            </div>
            <div class="grid-2">
              <div class="list-item">
                <strong>Loadout And Rearm</strong>
                <div class="stack" style="margin-top:8px;">
                  <textarea id="ship-rearm-json">${JSON.stringify(ship.max_loadout || {}, null, 2)}</textarea>
                  <div class="grid-2">
                    <button id="ship-rearm-full">Full Rearm</button>
                    <button id="ship-rearm-custom" class="secondary">Custom Rearm</button>
                  </div>
                </div>
              </div>
              <div class="list-item">
                <strong>Repairs</strong>
                <div class="stack" style="margin-top:8px;">
                  <select id="ship-repair-subsystem">${(ship.subsystems || []).map((subsystem) => `<option value="${subsystem.id}">${subsystem.name} (${subsystem.current_integrity}/${subsystem.nominal_integrity})</option>`).join("")}</select>
                  <button id="ship-repair-btn">Queue Repair</button>
                </div>
              </div>
            </div>
            <div class="grid-2">
              <div class="list-item"><strong>Current loadout</strong><pre>${JSON.stringify(ship.loadout || {}, null, 2)}</pre></div>
              <div class="list-item"><strong>Subsystem health</strong><pre>${JSON.stringify(ship.subsystems || [], null, 2)}</pre></div>
            </div>
            <div class="list-item"><strong>History</strong><pre>${(ship.history || []).join("\\n") || "No history yet."}</pre></div>
          ` : `<div class="muted">Select a ship to manage identity, assignment, loadout, and repairs. The ship builder stays available above.</div>`}
        </div>
      `;
      renderShipPickerPane();
      if (!ship) return;
      $("save-ship-btn").addEventListener("click", saveShip);
      $("ship-transfer-btn").addEventListener("click", transferShip);
      $("ship-dock-btn").addEventListener("click", dockShip);
      $("ship-detach-btn").addEventListener("click", detachShip);
      $("ship-reserve-btn").addEventListener("click", reserveShip);
      $("ship-rearm-full").addEventListener("click", rearmShipFull);
      $("ship-rearm-custom").addEventListener("click", rearmShipCustom);
      $("ship-repair-btn").addEventListener("click", repairShip);
    }

    function renderServiceTab() {
      const rearmQueue = filterByFocus(currentView.rearm_queue || []);
      const repairQueue = filterByFocus(currentView.repair_queue || []);
      $("workspace-detail").innerHTML = `
        <div class="detail-grid">
          <h3>Service Queue</h3>
          <div class="grid-2">
            <div class="list-item"><strong>Rearm Queue</strong><pre>${JSON.stringify(rearmQueue, null, 2)}</pre></div>
            <div class="list-item"><strong>Repair Queue</strong><pre>${JSON.stringify(repairQueue, null, 2)}</pre></div>
          </div>
        </div>
      `;
    }

    function renderEconomyTab() {
      const sides = isAdmin() ? SIDES : [activeRole];
      $("workspace-detail").innerHTML = `
        <div class="detail-grid">
          <h3>Economy</h3>
          ${economyFeedback ? `<div class="banner success">${escapeHtml(economyFeedback)}</div>` : ""}
          <div class="economy-grid">
            ${sides.map((side) => renderEconomyPanel(side)).join("")}
          </div>
        </div>
      `;
      if (isAdmin()) {
        SIDES.forEach((side) => {
          const button = $(`save-economy-${side}`);
          if (!button) return;
          button.addEventListener("click", () => saveEconomy(side));
        });
      }
    }

    function renderTurnTab() {
      const orders = !isAdmin() ? (currentView.orders || []) : [];
      $("workspace-detail").innerHTML = `
        <div class="detail-grid">
          <h3>Turn Control</h3>
          <div class="grid-2">
            <div class="list-item">
              <strong>Current turn</strong>
              <div class="stack" style="margin-top:8px;">
                <div class="muted">Turn ${currentView.current_turn} | Status ${currentView.status}</div>
                ${isAdmin() ? `<button id="resolve-turn-btn">Resolve Turn</button>` : `<button id="submit-turn-btn">Submit ${activeRole} Turn</button>`}
              </div>
            </div>
            <div class="list-item">
              <strong>Orders</strong>
              <pre>${JSON.stringify(isAdmin() ? currentView.current_turn_record || {} : { saved_orders: orders, drafted_orders: draftOrders }, null, 2)}</pre>
            </div>
          </div>
        </div>
      `;
      if (isAdmin()) {
        $("resolve-turn-btn").addEventListener("click", resolveTurn);
      } else {
        $("submit-turn-btn").addEventListener("click", submitTurn);
      }
    }

    function ensureMap() {
      if (mapReady) return;
      map = L.map("map").setView([0, 0], 4);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 13,
        attribution: "&copy; OpenStreetMap"
      }).addTo(map);
      map.on("click", (event) => {
        handleMapClick(event);
      });
      mapReady = true;
    }

    function renderMap() {
      ensureMap();
      map.setView([currentView.map_center.lat, currentView.map_center.lon], 5);
      for (const marker of fleetMarkers.values()) map.removeLayer(marker);
      for (const marker of portMarkers.values()) map.removeLayer(marker);
      for (const line of orderLines.values()) map.removeLayer(line);
      if (mapPreviewMarker) {
        map.removeLayer(mapPreviewMarker);
        mapPreviewMarker = null;
      }
      fleetMarkers.clear();
      portMarkers.clear();
      orderLines.clear();

      const sides = visibleSides();
      for (const port of (currentView.ports || []).filter((entry) => sides.includes(entry.side))) {
        const marker = L.circleMarker([port.lat, port.lon], {
          radius: 7,
          color: port.side === "Blue" ? "#295a9d" : "#b44339",
          weight: 2,
          fillOpacity: 0.84
        }).addTo(map);
        marker.bindTooltip(port.name);
        marker.on("click", () => {
          clearMapMode();
          selected = { kind: "port", id: port.id };
          activeTab = "Ports";
          renderNavigator();
          renderWorkspace();
          renderMap();
        });
        portMarkers.set(port.id, marker);
      }

      for (const fleet of (currentView.fleets || []).filter((entry) => sides.includes(entry.side))) {
        const marker = L.marker([fleet.lat, fleet.lon]).addTo(map);
        marker.bindTooltip(`${fleet.name} (${fleet.ship_count})`);
        marker.on("click", () => {
          clearMapMode();
          selected = { kind: "fleet", id: fleet.id };
          activeTab = "Fleets";
          renderNavigator();
          renderWorkspace();
          renderMap();
        });
        fleetMarkers.set(fleet.id, marker);
        const points = draftOrders[fleet.id] || [];
        if (points.length) {
          const route = [[fleet.lat, fleet.lon], ...points.map((point) => [point.lat, point.lon])];
          const line = L.polyline(route, {
            color: fleet.side === "Blue" ? "#295a9d" : "#b44339",
            dashArray: "6 4"
          }).addTo(map);
          orderLines.set(fleet.id, line);
        }
      }
      if (portPlacementPreview) {
        mapPreviewMarker = L.circleMarker([portPlacementPreview.lat, portPlacementPreview.lon], {
          radius: 9,
          color: "#927034",
          weight: 2,
          fillOpacity: 0.7
        }).addTo(map);
        mapPreviewMarker.bindTooltip("Pending port placement");
      }
      $("map-note").textContent = mapMode.kind === "place-port"
        ? "Port placement mode: click near shore to snap the new port onto the nearest valid coastline."
        : mapMode.kind === "draft-fleet-move"
          ? "Movement draft mode: click the map to append waypoints for the selected fleet."
          : isAdmin()
            ? "ADMIN map: inspect fleets and ports. Fleet movement drafting is disabled in admin view."
            : "Select a fleet, then use Draft Movement to enter waypoint mode on the map.";
    }

    function filterByFocus(items) {
      if (!isAdmin() || focusSide() === "All") return items;
      return items.filter((item) => item.side === focusSide());
    }

    function filteredFleets() {
      return filterByFocus(currentView.fleets || []);
    }

    function uniqueShipOptionValues(key) {
      const values = new Set();
      for (const option of classOptions()) {
        if (option && option[key]) values.add(option[key]);
      }
      return Array.from(values).sort();
    }

    function filteredShipOptions() {
      const search = (shipPickerState.search || "").trim().toLowerCase();
      return classOptions().filter((option) => {
        if (shipPickerState.nation !== "All" && option.nation_label !== shipPickerState.nation) return false;
        if (shipPickerState.classGroup !== "All" && option.class_group !== shipPickerState.classGroup) return false;
        if (!search) return true;
        const haystack = `${option.name || ""} ${option.ship_id || ""} ${option.search_text || ""}`.toLowerCase();
        return haystack.includes(search);
      });
    }

    function selectedShipOptionForPicker() {
      if (!shipPickerState.shipId) return null;
      return classOptions().find((option) => option.ship_id === shipPickerState.shipId) || null;
    }

    function ensureLogisticsPortId(sidePorts, selectedPort) {
      if (shipPickerState.portId && sidePorts.some((port) => port.id === shipPickerState.portId)) {
        return shipPickerState.portId;
      }
      if (selectedPort && sidePorts.some((port) => port.id === selectedPort.id)) {
        shipPickerState.portId = selectedPort.id;
        return selectedPort.id;
      }
      const fallback = sidePorts[0] ? sidePorts[0].id : "";
      shipPickerState.portId = fallback;
      return fallback;
    }

    function renderShipPickerPane() {
      const wrap = $("ship-picker-wrap");
      if (!wrap || !shipPickerContext) return;
      const sidePorts = (currentView.ports || []).filter((port) => shipPickerContext.sidePortIds.includes(port.id));
      const selectedPort = (currentView.ports || []).find((port) => port.id === shipPickerContext.selectedPortId) || null;
      const logisticsPortId = ensureLogisticsPortId(sidePorts, selectedPort);
      const logisticsPort = sidePorts.find((port) => port.id === logisticsPortId) || null;
      const catalogStatus = currentView.catalogs && currentView.catalogs.status ? currentView.catalogs.status : { available: false, message: "Catalog unavailable." };
      const catalogAvailable = !!catalogStatus.available && classOptions().length > 0;
      const filteredOptions = filteredShipOptions();
      const selectedShipOption = selectedShipOptionForPicker();
      if (shipPickerState.shipId && !selectedShipOption) {
        shipPickerState.shipId = "";
      }
      const nationOptions = ["All", ...uniqueShipOptionValues("nation_label")];
      const roleOptions = ["All", ...uniqueShipOptionValues("class_group")];
      const selectedHidden = !!selectedShipOption && !filteredOptions.some((option) => option.ship_id === selectedShipOption.ship_id);
      const visibleResults = filteredOptions.slice(0, 40);
      wrap.innerHTML = sidePorts.length ? `
        ${shipCreationFeedback && shipCreationFeedback.portId === logisticsPortId ? `<div class="banner success">${escapeHtml(shipCreationFeedback.message)}</div>` : ""}
        ${shipCreationError ? `<div class="banner error">${escapeHtml(shipCreationError)}</div>` : ""}
        ${catalogAvailable ? "" : `<div class="muted">${escapeHtml(catalogStatus.message || "Catalog unavailable.")}</div>`}
        <div class="grid-2">
          ${portSelect("create-ship-port", sidePorts, logisticsPortId)}
          <input id="create-ship-variant" placeholder="Variant" value="${escapeAttr(shipPickerState.variant)}" />
        </div>
        <div class="picker-toolbar">
          <div class="grid-3">
            ${optionSelect("create-ship-nation", nationOptions, shipPickerState.nation)}
            ${optionSelect("create-ship-role", roleOptions, shipPickerState.classGroup)}
            <input id="create-ship-search" placeholder="Search by ship name, class id, note, or sensors" value="${escapeAttr(shipPickerState.search)}" />
          </div>
          <div class="muted">${filteredOptions.length} matching ship classes${filteredOptions.length > visibleResults.length ? `, showing first ${visibleResults.length}` : ""}</div>
          <div class="picker-results">
            ${catalogAvailable && visibleResults.length ? visibleResults.map((option) => shipPickerResult(option, selectedShipOption && selectedShipOption.ship_id === option.ship_id)).join("") : `<div class="muted">${catalogAvailable ? "No ships match the current filters." : "Ship creation is disabled until a catalog is available."}</div>`}
          </div>
          ${selectedShipOption ? selectedShipSummary(selectedShipOption, logisticsPort, selectedHidden) : `<div class="muted">Choose a ship class from the results list to enable creation.</div>`}
        </div>
        <div class="grid-2">
          ${optionSelect("create-ship-quantity", quantityOptions(), shipPickerState.quantity)}
          <input id="create-ship-name" placeholder="Optional base name override" value="${escapeAttr(shipPickerState.baseName)}" />
        </div>
        <button id="create-ship-btn" ${(!catalogAvailable || !selectedShipOption || !logisticsPort) ? "disabled" : ""}>Create Ship${shipPickerState.quantity !== "1" ? "s" : ""} For ${logisticsPort ? logisticsPort.name : shipPickerContext.side}</button>
      ` : `<div class="muted">No friendly ports available for ${shipPickerContext.side}.</div>`;
      bindShipPickerControls();
    }

    function bindShipPickerControls() {
      const port = $("create-ship-port");
      const nation = $("create-ship-nation");
      const role = $("create-ship-role");
      const search = $("create-ship-search");
      const quantity = $("create-ship-quantity");
      const variant = $("create-ship-variant");
      const baseName = $("create-ship-name");
      if (port) {
        port.addEventListener("change", () => {
          shipPickerState.portId = port.value;
          shipCreationFeedback = null;
          shipCreationError = "";
          renderShipPickerPane();
        });
      }
      if (nation) {
        nation.addEventListener("change", () => {
          shipPickerState.nation = nation.value;
          renderShipPickerPane();
        });
      }
      if (role) {
        role.addEventListener("change", () => {
          shipPickerState.classGroup = role.value;
          renderShipPickerPane();
        });
      }
      if (search) {
        search.addEventListener("input", () => {
          shipPickerState.search = search.value;
          renderShipPickerPane();
        });
        search.addEventListener("keydown", (event) => {
          if (event.key !== "Enter") return;
          const firstMatch = filteredShipOptions()[0];
          if (!firstMatch) return;
          event.preventDefault();
          shipPickerState.shipId = firstMatch.ship_id;
          renderShipPickerPane();
        });
      }
      if (quantity) {
        quantity.addEventListener("change", () => {
          shipPickerState.quantity = quantity.value;
        });
      }
      if (variant) {
        variant.addEventListener("input", () => {
          shipPickerState.variant = variant.value;
        });
      }
      if (baseName) {
        baseName.addEventListener("input", () => {
          shipPickerState.baseName = baseName.value;
        });
      }
      document.querySelectorAll("[data-pick-ship]").forEach((button) => {
        button.addEventListener("click", () => {
          shipPickerState.shipId = button.dataset.pickShip;
          shipCreationError = "";
          renderShipPickerPane();
        });
      });
      if ($("create-ship-btn")) $("create-ship-btn").addEventListener("click", createShipAtPort);
    }

    function quantityOptions() {
      return Array.from({ length: 12 }, (_, index) => String(index + 1));
    }

    function optionSelect(id, options, selectedValue) {
      return `<select id="${id}">${options.map((option) => `<option value="${escapeAttr(option)}" ${option === selectedValue ? "selected" : ""}>${option}</option>`).join("")}</select>`;
    }

    function portSelect(id, ports, selectedValue) {
      return `<select id="${id}">${ports.map((port) => `<option value="${port.id}" ${port.id === selectedValue ? "selected" : ""}>${escapeHtml(port.name)} (${port.id})</option>`).join("")}</select>`;
    }

    function shipPickerResult(option, active) {
      return `
        <button class="picker-result ${active ? "active" : ""}" data-pick-ship="${option.ship_id}">
          <strong>${escapeHtml(option.name)}</strong>
          <div class="muted">${escapeHtml(option.ship_id)} | ${escapeHtml(option.nation_label)} | ${escapeHtml(option.class_group || "Other")} | ${escapeHtml(option.role)}</div>
          <div class="muted">${escapeHtml(option.summary_note || option.sensors || "No summary available.")}</div>
        </button>
      `;
    }

    function selectedShipSummary(option, logisticsPort, selectedHidden) {
      return `
        <div class="selected-ship-summary">
          <div class="inline-pills">
            <span class="pill">${escapeHtml(option.name)}</span>
            <span class="pill">${escapeHtml(option.nation_label)}</span>
            <span class="pill">${escapeHtml(option.class_group || "Other")}</span>
            <span class="pill">${escapeHtml(option.role)}</span>
            <span class="pill">Loadout: ${escapeHtml(option.loadout_reference || "unavailable")}</span>
            ${logisticsPort ? `<span class="pill">${escapeHtml(logisticsPort.name)}</span>` : ""}
          </div>
          <div><strong>${escapeHtml(option.ship_id)}</strong></div>
          ${option.sensors ? `<div class="muted">Sensors: ${escapeHtml(option.sensors)}</div>` : ""}
          ${option.summary_note ? `<div class="muted">${escapeHtml(option.summary_note)}</div>` : ""}
          <div class="muted">Class value ${formatNumber(option.class_total_value)} | Hull ${formatNumber(option.class_base_hull)} | Weapons ${formatNumber(option.class_weapons_value)}</div>
          ${selectedHidden ? `<div class="muted">This selection is currently hidden by the active filters, but it remains selected.</div>` : ""}
        </div>
      `;
    }

    function fleetCard(fleet) {
      const active = selected && selected.kind === "fleet" && selected.id === fleet.id ? "active" : "";
      const portName = portNameForId(fleet.docked_port_id);
      const locationSummary = fleet.docked_port_id
        ? `Docked at ${portName || fleet.docked_port_id}`
        : `At sea ${fleet.lat.toFixed(2)}, ${fleet.lon.toFixed(2)}`;
      const rosterPreview = (fleet.ships || [])
        .slice(0, 3)
        .map((ship) => `${ship.name} (${ship.sea_power_type})`)
        .join(", ");
      const extraCount = Math.max(0, (fleet.ships || []).length - 3);
      return `
        <div class="fleet-card ${active}" data-fleet-card="${fleet.id}">
          <div class="fleet-card-title">
            <strong>${escapeHtml(fleet.name)}</strong>
            <span class="muted">${fleet.ship_count} ships</span>
          </div>
          <div class="inline-pills">
            <span class="pill">${fleet.side}</span>
            <span class="pill">${fleet.status}</span>
            ${fleet.station_role ? `<span class="pill">${escapeHtml(fleet.station_role)}</span>` : ""}
          </div>
          <div class="muted">${locationSummary}</div>
          <div class="fleet-card-roster">${rosterPreview || "No ships assigned"}${extraCount > 0 ? ` +${extraCount} more` : ""}</div>
        </div>
      `;
    }

    function fleetRosterDetail(fleet) {
      const ships = fleet.ships || [];
      if (!ships.length) return `<div class="muted">No ships assigned.</div>`;
      const expandedShipId = expandedRosterShipByFleet[fleet.id] || "";
      return `<div class="roster-list">${ships.map((ship) => {
        const active = ship.id === expandedShipId;
        return `
          <div class="roster-item">
            <button class="roster-toggle ${active ? "active" : ""}" data-roster-ship="${ship.id}">
              <div class="roster-summary">
                <strong>${escapeHtml(ship.name)}</strong>
                <span class="muted">${escapeHtml(ship.class_display_name || ship.sea_power_type)}</span>
              </div>
              <div class="muted">${ship.status} | ${ship.nation_label || ""} ${ship.class_role ? `| ${escapeHtml(ship.class_role)}` : ""} | ${ship.port_id || "At sea"}</div>
            </button>
            ${active ? rosterShipExpand(ship) : ""}
          </div>
        `;
      }).join("")}</div>`;
    }

    function rosterShipExpand(ship) {
      return `
        <div class="roster-expand">
          <div class="inline-pills" style="margin:10px 0 8px;">
            <span class="pill">${escapeHtml(ship.class_display_name || ship.sea_power_type)}</span>
            ${ship.class_role ? `<span class="pill">${escapeHtml(ship.class_role)}</span>` : ""}
            ${ship.nation_label ? `<span class="pill">${escapeHtml(ship.nation_label)}</span>` : ""}
            <span class="pill">${escapeHtml(ship.variant_reference || "")}</span>
            ${ship.loadout_source ? `<span class="pill">Loadout ${escapeHtml(ship.loadout_source)}</span>` : ""}
          </div>
          <div class="grid-2" style="margin-bottom:8px;">
            <div class="muted">Assignment: ${ship.fleet_id || "Reserve"} | ${ship.port_id || "At sea"}</div>
            <div class="muted">Class value: ${formatNumber(ship.class_total_value)} | Hull ${formatNumber(ship.class_base_hull)}</div>
          </div>
          ${ship.class_sensors ? `<div class="muted" style="margin-bottom:8px;">Sensors: ${escapeHtml(ship.class_sensors)}</div>` : ""}
          ${ship.class_summary_note ? `<div class="muted" style="margin-bottom:8px;">${escapeHtml(ship.class_summary_note)}</div>` : ""}
          <div class="weapon-grid">
            ${ship.weapon_entries && ship.weapon_entries.length ? ship.weapon_entries.map((weapon) => `
              <div class="weapon-row">
                <div><strong>${escapeHtml(weapon.name)}</strong><div class="muted">${escapeHtml(weapon.weapon_id)}</div></div>
                <div>${weapon.current}/${weapon.max}</div>
                <div class="muted">${weapon.basis || ""}</div>
              </div>
            `).join("") : `<div class="muted">No weapon data available.</div>`}
          </div>
        </div>
      `;
    }

    function portNameForId(portId) {
      if (!portId) return "";
      const port = (currentView.ports || []).find((entry) => entry.id === portId);
      return port ? port.name : "";
    }

    function economySummaryCard(snapshot) {
      const tone = snapshot.side === "Blue" ? "side-tag-blue" : "side-tag-red";
      return `
        <div class="summary-card">
          <div class="${tone}"><strong>${escapeHtml(snapshot.side)}</strong></div>
          <div class="summary-metric">${formatNumber(snapshot.resources)} RP</div>
          <div class="muted">Income ${formatNumber(snapshot.income_per_turn)} / turn</div>
          <div class="muted">Spent ${formatNumber(snapshot.total_spent)} | Ships ${snapshot.ship_count} | Fleets ${snapshot.fleet_count} | Ports ${snapshot.port_count}</div>
        </div>
      `;
    }

    function renderEconomyPanel(side) {
      const snapshot = currentView.side_state[side];
      const projected = Number(snapshot.resources || 0) + Number(snapshot.income_per_turn || 0);
      return `
        <div class="list-item">
          <strong>${escapeHtml(side)} Economy</strong>
          <div class="stack" style="margin-top:8px;">
            <div class="summary-metric">${formatNumber(snapshot.resources)} RP</div>
            <div class="muted">Projected next turn: ${formatNumber(projected)} RP</div>
            <div class="muted">Income ${formatNumber(snapshot.income_per_turn)} | Total spent ${formatNumber(snapshot.total_spent)}</div>
            <div class="muted">Ships ${snapshot.ship_count} | Fleets ${snapshot.fleet_count} | Ports ${snapshot.port_count}</div>
            ${isAdmin() ? `
              <div class="grid-2">
                <input id="economy-resources-${side}" value="${escapeAttr(snapshot.resources)}" />
                <input id="economy-income-${side}" value="${escapeAttr(snapshot.income_per_turn)}" />
              </div>
              <button id="save-economy-${side}">Save ${escapeHtml(side)} Economy</button>
            ` : ""}
          </div>
        </div>
      `;
    }

    function portActivityDetail(selectedPort, dockedFleets, reserveShips) {
      return `
        <div class="stack" style="margin-top:8px;">
          <div class="muted">Docked fleets</div>
          ${dockedFleets.length ? `<div class="list">${dockedFleets.map((fleet) => `<div class="list-item"><strong>${escapeHtml(fleet.name)}</strong><div class="muted">${fleet.ship_count} ships</div></div>`).join("")}</div>` : `<div class="muted">No fleets docked at ${escapeHtml(selectedPort.name)}.</div>`}
          <div class="muted">Reserve ships</div>
          ${reserveShips.length ? `<div class="list">${reserveShips.map((ship) => `<div class="list-item ${shipCreationFeedback && shipCreationFeedback.shipIds && shipCreationFeedback.shipIds.includes(ship.id) ? "highlight-item" : ""}"><strong>${escapeHtml(ship.name)}</strong><div class="muted">${escapeHtml(ship.class_display_name || ship.sea_power_type)}</div></div>`).join("")}</div>` : `<div class="muted">No reserve ships at this port.</div>`}
        </div>
      `;
    }

    function handleMapClick(event) {
      if (mapMode.kind === "draft-fleet-move") {
        const fleet = (currentView.fleets || []).find((entry) => entry.id === mapMode.fleetId);
        if (!fleet || !fleet.can_draft_movement) return;
        draftOrders[fleet.id] = draftOrders[fleet.id] || [];
        draftOrders[fleet.id].push({ lat: event.latlng.lat, lon: event.latlng.lng });
        renderMap();
        if (activeTab === "Fleets" || activeTab === "Turn") renderWorkspace();
        return;
      }
      if (mapMode.kind === "place-port") {
        previewPortPlacement(event.latlng.lat, event.latlng.lng);
      }
    }

    function selectedFleetForDraft() {
      return selected && selected.kind === "fleet" ? selectedEntity() : null;
    }

    function toggleFleetDraftMode() {
      const fleet = selectedFleetForDraft();
      if (!fleet || !fleet.can_draft_movement) return;
      if (mapMode.kind === "draft-fleet-move" && mapMode.fleetId === fleet.id) {
        clearMapMode({ preservePreview: true });
      } else {
        portPlacementPreview = null;
        mapMode = { kind: "draft-fleet-move", fleetId: fleet.id };
      }
      renderWorkspace();
      renderMap();
    }

    function clearFleetDraft() {
      const fleet = selectedFleetForDraft();
      if (!fleet) return;
      delete draftOrders[fleet.id];
      if (mapMode.kind === "draft-fleet-move" && mapMode.fleetId === fleet.id) {
        clearMapMode({ preservePreview: true });
      }
      renderWorkspace();
      renderMap();
    }

    function nauticalMilesBetween(a, b) {
      const lat1 = degreesToRadians(Number(a.lat || 0));
      const lat2 = degreesToRadians(Number(b.lat || 0));
      const dlat = lat2 - lat1;
      const dlon = degreesToRadians(Number(b.lon || 0) - Number(a.lon || 0));
      const hav = Math.sin(dlat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dlon / 2) ** 2;
      return 3440.065 * 2 * Math.asin(Math.min(1, Math.sqrt(hav)));
    }

    function degreesToRadians(value) {
      return (value * Math.PI) / 180;
    }

    async function postJson(path, payload) {
      return fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload || {})
      }).then(asJson);
    }

    async function mutate(path, payload, after) {
      try {
        await postJson(path, payload);
        await loadView();
        if (after) after();
      } catch (error) {
        alert(error.error || error.message || "Action failed");
      }
    }

    function buildImportPayload() {
      const payload = {
        save_path: (importFormState.savePath || ($("import-save-path") ? $("import-save-path").value : "")).trim(),
        scenario_name: "Imported Campaign",
        turn_duration_minutes: 60,
        catalog_paths: {}
      };
      const ammoPath = (importFormState.ammoPath || ($("import-ammo-path") ? $("import-ammo-path").value : "")).trim();
      const costPath = (importFormState.costPath || ($("import-cost-path") ? $("import-cost-path").value : "")).trim();
      if (ammoPath) payload.catalog_paths.ammo_database = ammoPath;
      if (costPath) payload.catalog_paths.cost_matrix_html = costPath;
      if (!Object.keys(payload.catalog_paths).length) delete payload.catalog_paths;
      return payload;
    }

    function initializeImportSelection(preview) {
      importSelection = {};
      for (const sideGroup of (preview.sides || [])) {
        for (const fleet of (sideGroup.fleets || [])) {
          for (const ship of (fleet.ships || [])) {
            importSelection[ship.candidate_id] = true;
          }
        }
      }
    }

    async function previewImportSave() {
      try {
        const result = await postJson(`/api/campaign/import-save/preview?${roleQuery()}`, buildImportPayload());
        importPreview = result.preview;
        initializeImportSelection(importPreview);
        importPreviewError = "";
        importApplyFeedback = "";
        renderWorkspace();
      } catch (error) {
        importPreview = null;
        importSelection = {};
        importPreviewError = error.error || error.message || "Save import preview failed.";
        renderWorkspace();
      }
    }

    async function applyImportSave() {
      if (!importPreview) return;
      const selectedShipIds = Object.entries(importSelection)
        .filter(([, selected]) => !!selected)
        .map(([shipId]) => shipId);
      if (!selectedShipIds.length) {
        importPreviewError = "Select at least one ship to import.";
        renderWorkspace();
        return;
      }
      try {
        const result = await postJson(`/api/campaign/import-save?${roleQuery()}`, {
          ...buildImportPayload(),
          selected_ship_ids: selectedShipIds
        });
        importApplyFeedback = `${result.imported.ship_count} ship${result.imported.ship_count === 1 ? "" : "s"} imported into ${result.imported.fleet_count} fleet${result.imported.fleet_count === 1 ? "" : "s"}.`;
        importPreviewError = "";
        importPreview = null;
        importSelection = {};
        selected = null;
        activeTab = "Overview";
        await loadView();
      } catch (error) {
        importPreviewError = error.error || error.message || "Save import failed.";
        renderWorkspace();
      }
    }

    async function resetCampaign() {
      await mutate(`/api/campaign/reset?${roleQuery()}`, {}, () => {
        selected = null;
        activeTab = "Overview";
      });
    }

    function exportCampaign() {
      window.location.href = `/api/campaign/export/scenario.ini?${roleQuery()}`;
    }

    function startPortPlacement() {
      const side = isAdmin() ? $("create-port-side").value : activeRole;
      const name = $("create-port-name").value.trim();
      const radius = $("create-port-radius").value.trim() || "5";
      if (!name) {
        portPlacementError = "Port name is required before placement.";
        renderWorkspace();
        return;
      }
      portPlacementDraft = { side, name, radiusNm: radius };
      portPlacementPreview = null;
      portPlacementError = "";
      mapMode = { kind: "place-port", side };
      renderWorkspace();
      renderMap();
    }

    function cancelPortPlacement() {
      clearMapMode();
      portPlacementError = "";
      renderWorkspace();
      renderMap();
    }

    async function previewPortPlacement(lat, lon) {
      try {
        const side = portPlacementDraft.side || sideForCreates();
        const result = await postJson(`/api/ports/preview?${roleQuery()}`, { side, lat, lon });
        portPlacementPreview = result.placement;
        portPlacementError = "";
        renderWorkspace();
        renderMap();
      } catch (error) {
        portPlacementError = error.error || error.message || "Port placement preview failed.";
        renderWorkspace();
      }
    }

    async function createPort() {
      if (!portPlacementPreview) {
        portPlacementError = "Place the port on the map first.";
        renderWorkspace();
        return;
      }
      await mutate(`/api/ports?${roleQuery()}`, {
        side: portPlacementDraft.side || sideForCreates(),
        name: (portPlacementDraft.name || "").trim(),
        lat: portPlacementPreview.lat,
        lon: portPlacementPreview.lon,
        radius_nm: parseFloat(portPlacementDraft.radiusNm || "5")
      }, () => {
        clearMapMode();
        portPlacementError = "";
        selected = null;
        activeTab = "Ports";
      });
    }

    async function savePort() {
      const port = selectedEntity();
      await mutate(`/api/ports/${encodeURIComponent(port.id)}?${roleQuery()}`, {
        name: $("edit-port-name").value.trim(),
        lat: parseFloat($("edit-port-lat").value),
        lon: parseFloat($("edit-port-lon").value),
        radius_nm: parseFloat($("edit-port-radius").value)
      });
    }

    async function createShipAtPort() {
      const portId = shipPickerState.portId || ($("create-ship-port") ? $("create-ship-port").value : "");
      if (!portId) {
        shipCreationError = "Select a destination port first.";
        renderShipPickerPane();
        return;
      }
      const port = (currentView.ports || []).find((entry) => entry.id === portId);
      if (!port) {
        shipCreationError = "Select a valid friendly port first.";
        renderShipPickerPane();
        return;
      }
      if (!shipPickerState.shipId) {
        shipCreationError = "Select a ship class first.";
        renderShipPickerPane();
        return;
      }
      const payload = {
        side: port.side,
        sea_power_type: shipPickerState.shipId,
        variant_reference: (($("create-ship-variant") && $("create-ship-variant").value) || shipPickerState.variant || "Variant1").trim() || "Variant1",
        port_id: port.id,
        quantity: parseInt((($("create-ship-quantity") && $("create-ship-quantity").value) || shipPickerState.quantity || "1"), 10)
      };
      const providedName = (($("create-ship-name") && $("create-ship-name").value) || shipPickerState.baseName || "").trim();
      if (providedName) payload.name = providedName;
      try {
        const created = await postJson(`/api/ships?${roleQuery()}`, { ...payload });
        shipCreationError = "";
        shipPickerState.baseName = "";
        shipCreationFeedback = {
          portId: port.id,
          shipIds: (created.ships || []).map((ship) => ship.id),
          message: `${(created.ships || []).length} ship${(created.ships || []).length === 1 ? "" : "s"} created at ${port.name}: ${(created.ships || []).map((ship) => ship.name).join(", ")}`
        };
        selected = { kind: "port", id: port.id };
        await loadView();
      } catch (error) {
        shipCreationError = error.error || error.message || "Ship creation failed.";
        renderShipPickerPane();
      }
    }

    async function createFleetAtPort() {
      const port = selectedEntity();
      await mutate(`/api/fleets?${roleQuery()}`, {
        side: port.side,
        name: $("create-fleet-name").value.trim(),
        port_id: port.id,
        ship_ids: Array.from($("create-fleet-ships").selectedOptions).map((option) => option.value)
      });
    }

    async function saveFleet() {
      const fleet = selectedEntity();
      await mutate(`/api/fleets/${encodeURIComponent(fleet.id)}?${roleQuery()}`, {
        name: $("fleet-name").value.trim()
      });
    }

    async function dockFleet() {
      const fleet = selectedEntity();
      const payload = fleet.docked_port_id ? { action: "undock" } : { port_id: $("dock-port-id").value.trim() };
      await mutate(`/api/fleets/${encodeURIComponent(fleet.id)}/dock?${roleQuery()}`, payload);
    }

    async function mergeFleet() {
      const fleet = selectedEntity();
      await mutate(`/api/fleets/${encodeURIComponent(fleet.id)}/merge?${roleQuery()}`, {
        target_fleet_id: $("merge-target-id").value.trim()
      });
    }

    async function saveShip() {
      const ship = selectedEntity();
      await mutate(`/api/ships/${encodeURIComponent(ship.id)}?${roleQuery()}`, {
        name: $("ship-name").value.trim()
      });
    }

    async function transferShip() {
      const ship = selectedEntity();
      const fleetSelect = $("ship-target-fleet");
      if (!fleetSelect || !fleetSelect.value) return;
      await mutate(`/api/ships/${encodeURIComponent(ship.id)}/transfer?${roleQuery()}`, {
        target_fleet_id: fleetSelect.value.trim()
      });
    }

    async function dockShip() {
      const ship = selectedEntity();
      const portSelect = $("ship-dock-port");
      if (!ship || !portSelect || !portSelect.value) return;
      await mutate(`/api/ships/${encodeURIComponent(ship.id)}/transfer?${roleQuery()}`, {
        dock_port_id: portSelect.value.trim(),
        new_fleet_name: `${ship.name} Dock Group`
      });
    }

    async function saveEconomy(side) {
      try {
        const resources = parseInt($(`economy-resources-${side}`).value, 10);
        const income = parseInt($(`economy-income-${side}`).value, 10);
        await postJson(`/api/sides/${encodeURIComponent(side)}?${roleQuery()}`, {
          resources,
          income_per_turn: income
        });
        economyFeedback = `${side} economy updated.`;
        await loadView();
      } catch (error) {
        alert(error.error || error.message || "Economy update failed");
      }
    }

    async function detachShip() {
      const ship = selectedEntity();
      await mutate(`/api/ships/${encodeURIComponent(ship.id)}/transfer?${roleQuery()}`, {
        new_fleet_name: `${ship.name} Group`
      });
    }

    async function reserveShip() {
      const ship = selectedEntity();
      await mutate(`/api/ships/${encodeURIComponent(ship.id)}/transfer?${roleQuery()}`, {
        to_reserve: true
      });
    }

    async function rearmShipFull() {
      const ship = selectedEntity();
      await mutate(`/api/ships/${encodeURIComponent(ship.id)}/rearm?${roleQuery()}`, { mode: "full" });
    }

    async function rearmShipCustom() {
      const ship = selectedEntity();
      await mutate(`/api/ships/${encodeURIComponent(ship.id)}/rearm?${roleQuery()}`, {
        mode: "custom",
        desired_loadout: JSON.parse($("ship-rearm-json").value || "{}")
      });
    }

    async function repairShip() {
      const ship = selectedEntity();
      await mutate(`/api/ships/${encodeURIComponent(ship.id)}/repair?${roleQuery()}`, {
        subsystem_id: $("ship-repair-subsystem").value
      });
    }

    async function submitTurn() {
      const payload = {
        turn_number: currentView.current_turn,
        orders: Object.entries(draftOrders).map(([fleet_id, waypoints]) => ({ fleet_id, waypoints }))
      };
      await mutate(`/api/turns/${encodeURIComponent(activeRole)}?${roleQuery()}`, payload, () => {
        draftOrders = {};
      });
    }

    async function resolveTurn() {
      await mutate(`/api/campaign/resolve?${roleQuery()}`, {}, () => {
        draftOrders = {};
      });
    }

    function classSelect(id, options) {
      return `<select id="${id}">${options.map((entry) => `<option value="${entry}">${entry}</option>`).join("")}</select>`;
    }

    function adminSideSelector(id, selectedSide) {
      return `
        <select id="${id}">
          ${SIDES.map((side) => `<option value="${side}" ${side === selectedSide ? "selected" : ""}>${side}</option>`).join("")}
        </select>
      `;
    }

    function escapeAttr(value) {
      return String(value || "").replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");
    }

    function escapeHtml(value) {
      return String(value || "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
    }

    function formatNumber(value) {
      const numeric = Number(value || 0);
      if (!numeric) return "0";
      return numeric.toLocaleString(undefined, { maximumFractionDigits: 0 });
    }

    document.querySelectorAll("[data-role-choice]").forEach((button) => {
      button.addEventListener("click", () => setRole(button.dataset.roleChoice));
    });
    document.querySelectorAll("[data-switch-role]").forEach((button) => {
      button.addEventListener("click", () => setRole(button.dataset.switchRole));
    });
    $("focus-side").addEventListener("change", () => {
      selected = null;
      renderNavigator();
      renderWorkspace();
      renderMap();
    });

    const params = new URLSearchParams(window.location.search);
    const initialRole = params.get("role") || localStorage.getItem("planner-role") || "";
    if (["Blue", "Red", "Admin"].includes(initialRole)) {
      setRole(initialRole);
    }
  </script>
</body>
</html>
"""

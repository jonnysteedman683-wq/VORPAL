# Unified Hive UI Reference

## File
- `C:\Users\jonny\OneDrive\Desktop\AQB\OMNIBUS\hive-unified-ui.html`

## Purpose
Single-page Hive Command Center that consolidates chat, swarm status, phase groups, memory, learning, tools, ML brainstorm, and ARISE into one tabbed UI.

## Panels
- `panel-chat` — unified chat input/output with send button
- `panel-status` — health, peers, last intent/provider, queue, Hermes availability
- `panel-phase` — phase group summary from `GET /api/neurocore/phase-groups`
- `panel-memory` — recent intent memory table with id, intent, provider, confidence, status, latency, timestamp
- `panel-learning` — provider stats table and threshold suggestion
- `panel-tools` — tool list selector, run echo/system_status via `POST /api/neurocore/tools/call`
- `panel-brainstorm` — synthesize and send-to-chat actions
- `panel-arise` — start/pause/inspect controls with status output

## Routing
- Tabs are buttons with `data-panel` matching panel IDs.
- `switchTab(panelId)` toggles `.active` on the target panel and tab button.

## Connect flow
- `window.connectNeurocore()` POSTs to `/api/neurocore/connect` with `baseUrl` and `enableHermes`.
- Updates global status pill to `connected`/`error`.

## Polling/refresh
- Status, phase, memory, and learning panels expose refresh buttons that fetch their respective endpoints.
- Tools panel has `Load Tools` and `Run Echo` buttons.

## Pitfalls
- Keep panel content defensive: table bodies may be empty; render empty-state rows instead of failing.
- `GET /api/neurocore/status` may return HTML if the server is not running or the route is missing; handle non-JSON responses gracefully.
- ARISE controls are currently mocked; real control requires `/api/neurocore/arise/*` routes or direct simulation binding.

## Verification
- Serve OMNIBUS and open `http://localhost:3000/hive-unified-ui.html`
- Confirm tab switching works without console errors
- Confirm `Connect Neurocore` updates the global status pill
- Confirm tool load lists `echo` and `system_status`

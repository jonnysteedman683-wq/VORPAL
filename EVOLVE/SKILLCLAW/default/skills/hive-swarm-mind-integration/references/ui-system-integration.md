---
name: ui-system-integration
title: UI System Integration & API Bridging
description: Mount external UIs and wire cross-system API bridges.
created: 2026-08-05
---

# UI System Integration & API Bridging

**Use when** mounting external/sophisticated UIs into a running backend service, or wiring cross-system API calls (one UI/service talks to another's endpoints via translation layers).

## Core Pattern

1. **Mount the external UI** as static assets under a route prefix
   - Serve assets from external build dist/ directory
   - Rewrite relative asset paths if serving from a subdirectory (e.g., `/sentinel/assets/`)
   - Add Express static route + fallback to index.html for SPA routing
   - For unified root UI, also serve the same external shell at `/` if desired

2. **Create API bridge endpoints** that translate UI calls into backend calls
   - UI calls `/api/bridge/initiate` → backend calls `/api/neurocore/intent` (or equivalent)
   - Store poll state in memory Map (swarmPolls, sessionCache, etc.)
   - Return state shape expected by UI

3. **Handle cross-module friction** (CommonJS/ESM, Windows paths)
   - Use `path.resolve(__dirname, '...')` for relative requires instead of hardcoded Windows paths
   - `.cjs` extension forces CommonJS in ESM packages
   - Verify syntax with `node --check` before backgrounding

4. **Inject unified overlays without rebuilding the external UI**
   - If the external build is not modifiable, inject HTML/JS into the served `index.html` response
   - Inject before `</head>` or at the top of `<body>` depending on layout constraints
   - Keep injected CSS/JS self-contained and feature-detecting so the underlying app still works if injection fails
   - Use existing backend JSON endpoints instead of duplicating data paths

5. **Validate end-to-end**
   - GET `/` returns the unified external UI shell when intended
   - GET `/mounted-ui-route` returns valid HTML shell
   - GET `/mounted-ui-route/assets/*` serves JS/CSS without 404
   - POST `/api/bridge/*` calls translate cleanly to backend calls
   - Run full test suite to catch silent integration breaks

## Pitfalls

- **Hardcoded paths break on new machines.** Always use `path.resolve()` relative to `__dirname`.
- **Windows path separators in require().** Use forward-slash paths or `path.resolve()`, never backslash strings.
- **Asset paths in mounted SPA.** If serving from `/sentinel`, HTML `src="/assets/..."` breaks. Rewrite to `src="./assets/..."` at serve time.
- **CORS missing.** External applets (AI Studio, iframe embeds) need `app.use(cors())`. Add at top.
- **Poll state never cleaned.** Memory Maps grow unbounded. Implement TTL or explicit cleanup for poll IDs.
- **Silent failures on ESM/CJS mismatch.** Error is cryptic ('module is not defined in ES module scope'). Check package.json `"type": "module"` and use `.cjs` for CommonJS entry points.

## See Also

- `references/arc-sentinel-integration.md` — session-specific paths and endpoint mappings for OMNIBUS + Sentinel bridge
- `references/windows-node-cjs-esm-notes.md` — CommonJS/ESM friction patterns on Windows

## Success Criteria

- ✅ External UI loads from `http://localhost:PORT/route`
- ✅ External UI assets resolve and app initializes (no 404s, no CORS errors)
- ✅ Bridge endpoints accept and translate calls without errors
- ✅ Existing test suite still passes (no silent integration breaks)
- ✅ Code runs on fresh checkout (no hardcoded user paths)

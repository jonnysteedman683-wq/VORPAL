# ARC Sentinel Mount Pattern

## Problem

Mounting a built frontend dist from an external repo under an OMNIBUS subpath so it can be served as a control UI without rewriting the app.

## Verified Pattern

- Static assets: `app.use('/sentinel/assets', express.static(path.join(arcDistPath, 'assets')))`
- Served app shell: rewrite built absolute `/assets/...` references to relative `./assets/...` before sending `index.html`
- Fallback route: `app.get('/sentinel/*', ...)` serves files from the dist root, falling back to `index.html`

## Why Not Plain Static Mount

A plain `express.static('/sentinel')` can return the built app's redirect/html instead of the real shell if the dist contains redirect pages or root-relative asset links. The rewrite + explicit asset mount avoids that.

## Reuse Note

- Path: `C:\Users\jonny\OneDrive\Documents\AEGIS\ARCANE QUANTUM BRAIN\dist`
- Local route: `http://localhost:3001/sentinel`
- Bridge API: `/api/swarm/initiate`, `/api/swarm/poll`

## Neurocore Bridge Wiring Notes

- In OMNIBUS `server.cjs`, require the bridge via `path.resolve(__dirname, '../../../Documents/AEGIS/neurocore/neurocore-bridge.cjs')` rather than a hardcoded Windows path.
- Neurocore declares `"type": "module"`; any loaded adapter/bridge file under it must use `.cjs` for CommonJS, or Node will fail with `module is not defined in ES module scope`.
- If adding or renaming such files, update the corresponding import path in `neurocore-bridge.cjs` and keep the file extension aligned with the module system.
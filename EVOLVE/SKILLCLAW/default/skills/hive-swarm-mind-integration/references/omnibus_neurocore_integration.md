# OMNIBUS + Neurocore Hive Swarm Mind — Session Reference

## Exact Paths

- OMNIBUS backend: `C:\Users\jonny\OneDrive\Desktop\AQB\OMNIBUS\server.cjs`
- Neurocore bridge: `C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore\neurocore-bridge.cjs`
- Frontend dispatch: `C:\Users\jonny\OneDrive\Desktop\AQB\OMNIBUS\agent_system.js`
- Frontend init: `C:\Users\jonny\OneDrive\Desktop\AQB\OMNIBUS\app.js`
- UI entry: `C:\Users\jonny\OneDrive\Desktop\AQB\OMNIBUS\index.html`
- Tests: `C:\Users\jonny\OneDrive\Desktop\AQB\OMNIBUS\tests\*.test.ts`

## Repo Remotes

- OMNIBUS: `https://github.com/jonnysteedman683-wq/OMNIBUS.git`
- Neurocore: `https://github.com/jonnysteedman683-wq/neurocore.git`

## Pushed Commits

- OMNIBUS: `aa09166` — Hive Swarm Mind integration, auto-triage routing, frontend dispatch, tests
- Neurocore: `12bf974` — ESM/CJS bridge and neural-decoder scaffolding

## Endpoint Contracts

- `GET /api/neurocore/health`
- `POST /api/neurocore/connect`
- `POST /api/neurocore/intent`
- `GET /api/neurocore/peers`
- `POST /api/neurocore/emergency-stop`
- `GET /api/neurocore/status`

## Debug Notes

- `titans_memory_store.js` has a pre-existing ESM/CJS mismatch; use `server.cjs` directly.
- Health endpoint should use `capabilities()` or explicit state fields, not missing `getHealthMetrics()`.
- OneDrive Windows paths need absolute require strings for cross-repo imports.
- Tests are stable at `41/41` with `npx tsx --test tests/*.test.ts`.

## Pending

- AI Studio decoder update in `neurocore/adapters/neural-decoder/decoder.py`
- Optional `/api/neurocore/intent` confidence preview via `?confidence=` in status
- Optional ARISE status bridge after decoder stabilizes

# Hive Swarm Mind — pitfalls

Load this file when a hive/swarm integration step fails or behaves
unexpectedly. The workflow stays in `SKILL.md`.

## Known Pitfalls

- On Windows/OneDrive, absolute paths are safer than relative cross-repo requires.
- Do not call missing adapter methods like `getHealthMetrics()` unless the adapter actually provides them.
- Keep backend entrypoint `.cjs` if the repo mixes ESM and CJS files.
- If old background logs show stale module-resolution errors, inspect the live `server.cjs` require path before retrying.
- Use dynamic `import('file://' + path)` only from the ESM/CJS bridge; don't use `require('file://...')`.
- When adding bridge modules, also add accessor functions (`getMemoryStore`, `getLearningLogger`) instead of exporting singletons directly.
- `tests/*.test.ts` can fail when `package.json` points at a directory without `index.ts`; fix the test script to the actual file path.
- `/api/neurocore/intent` rejects `phase: null`; omit the field when the caller has no phase.
- `/api/chat` bridge must compute triage provider before calling `/api/neurocore/intent`; otherwise intent handler sees `source: undefined` and may route incorrectly.
- `/api/neurocore/intent` returns `{ success, triage: { confidence, routedTo }, actionId, status }`, not `{ response, provider, confidence, swarmId }`. The `/api/chat` bridge must translate `actionId` into a user-facing `response` and read routing from `triage.routedTo`.

## Cloudflare Tunnel Notes

- Quick tunnel URLs are ephemeral; they rotate when the tunnel process restarts or after timeouts.
- On this host/network, Cloudflare DNS can time out during tunnel startup even when `cloudflared` is running. In that case the tunnel is effectively unreachable from outside.
- Fallback: verify public access by fetching the tunnel URL from the same network path users will use. If it returns non-2xx or times out, stop advertising the public URL until the tunnel is healthy again.

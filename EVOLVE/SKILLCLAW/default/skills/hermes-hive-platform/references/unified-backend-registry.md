# Unified Backend Registry Verified State

This reference documents the adapter/registry pattern added so Hermes Hive can manage multiple swarm backends through one control plane.

## Files

- `src/server/backends/backendRegistry.ts`
- `src/server/backends/omnibusAdapter.ts`
- `src/server/apiMiddleware.ts`
- `src/client/components/backends/BackendsView.tsx`
- `src/App.tsx`
- `src/client/components/layout/Sidebar.tsx`

## Registry pattern

```ts
backendRegistry.register({
  name: 'suprime',
  adapter: {
    name: 'suprime',
    async health() { return suprimeBridge.health(); },
    async start() { return suprimeBridge.startSwarm(); },
    async stop() { return suprimeBridge.stopSwarm(); },
    async status() { return suprimeBridge.status(); },
    async submitTask(payload) { return suprimeBridge.submitTask(payload.kind, payload.args, payload.taskId); },
    async listTasks() { return suprimeBridge.listTasks(); },
    async registerWorker(kind) { return suprimeBridge.registerWorker(kind); },
  },
});

backendRegistry.register({
  name: 'omnibus',
  adapter: new OmnibusBackendAdapter(),
});
```

## Unified proxy routes

- `GET /api/backends`
- `GET /api/backends/:name`
- `POST /api/backends/:name/start`
- `POST /api/backends/:name/stop`
- `POST /api/backends/:name/status`
- `POST /api/backends/:name/tasks`
- `POST /api/backends/:name/tasks/submit`
- `POST /api/backends/:name/workers/:kind`

## Frontend

- Added `BackendsView` under `src/client/components/backends/BackendsView.tsx`
- Added `SuprimeSwarmView` import/tab wiring in `src/App.tsx`
- Added sidebar tab type and menu entry for `backends` in `Sidebar.tsx`

## Edit reliability notes

- `src/App.tsx` is sensitive to repeated patch/read cycles in this environment. If `patch` or `read_file` appears to revert imports/tab cases, prefer:
  - one full-file `write_file`, or
  - one narrow `execute_code` replacement, or
  - one targeted `sed` command, then verify with `grep`
- Verify with `grep -n "BackendsView\|SuprimeSwarmView\|backends" src/App.tsx`

## Runtime verification

- `GET /api/backends` -> `["suprime","omnibus"]`
- `GET /api/backends/suprime` -> real SUPRIME health when bridge is running
- `GET /api/backends/omnibus` -> expected `fetch failed` when OMNIBUS is not running locally

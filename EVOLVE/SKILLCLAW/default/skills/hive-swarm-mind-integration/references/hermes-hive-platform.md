---
name: hermes-hive-platform
description: "Operate Hermes Hive and integrate it with SUPRIME."
---

# Hermes Hive Platform

Class-level guidance for Hermes Hive as a control-plane/UI layer backed by a real swarm execution engine.

## Architecture Direction

Treat Hermes Hive as the **control plane and operator UI**.
Treat SUPRIME as the **real decentralized swarm execution backend**.

Hive responsibilities:
- REST/SSE control surface
- Mission/agent/task orchestration API
- Observability: diagnostics, events, memory, decisions
- Operator-facing quick actions and demos

SUPRIME responsibilities:
- Actual peer-to-peer gossip membership
- CRDT replicated state
- Distributed task claiming/execution
- Leader election, failover, persistence, chaos testing

## Persistence Layer

Use `better-sqlite3` with WAL mode in `.hive/hive.sqlite`.

### Database bootstrap

```ts
import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

const DB_PATH = path.resolve(process.cwd(), '.hive', 'hive.sqlite');
const DB_DIR = path.dirname(DB_PATH);
if (!fs.existsSync(DB_DIR)) fs.mkdirSync(DB_DIR, { recursive: true });
const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');
db.pragma('synchronous = NORMAL');
```

**Pitfall:** Missing `.hive` directory causes Vite to fail restarting with `Cannot open database because the directory does not exist`. Always ensure the directory exists before constructing the database.

### Repository pattern

For each domain entity, create a repository with `upsert`, `getAll`, `get`, and `delete` methods. Keep SQL in the repository; keep domain logic in the registry/engine.

Load from database on startup, seed defaults only when empty:

```ts
constructor() {
  this.loadFromDatabase();
  if (this.agents.size === 0) {
    this.seedDefaultAgents();
  }
}
```

## TypeScript + better-sqlite3 typing fix

`better-sqlite3` returns `unknown[]` from `.all()` in strict TypeScript. Cast query results before mapping:

```ts
const rows = this.db.prepare('SELECT * FROM decisions').all(limit) as any[];
return rows.map((row) => ({
  ...row,
  actions: JSON.parse(row.actions || '[]'),
}));
```

Without this cast, `tsc --noEmit` emits:
- `TS2698: Spread types may only be created from object types`
- `TS2339: Property 'actions' does not exist on type 'unknown'`

## Runtime Verification

After wiring persistence:
1. `POST /api/memory` with a test record
2. `GET /api/memory?search=<key>` to confirm round-trip
3. `GET /api/health` to confirm server still boots

## SUPRIME Integration

SUPRIME is the real swarm execution backend. Hermes Hive proxies control-plane requests to SUPRIME through a small FastAPI bridge.

### SUPRIME bridge

Install the optional bridge dependencies:

```bash
cd C:/Users/jonny/SUPRIME
pip install -e ".[bridge]"
```

Start the bridge:

```bash
python -m suprime bridge --port 8123
```

The bridge exposes:
- `/health`
- `/swarm/start`
- `/swarm/stop`
- `/swarm/status`
- `/tasks`
- `/tasks/submit`
- `/worker/{kind}`

**Pitfall:** On Windows, do not launch the bridge with `python -m suprime bridge` from a shell where `python` resolves unexpectedly. Use the full venv/python path if needed. If startup fails with `NameError: name 'os' is not defined`, the CLI module is missing an `import os`; patch `suprime/cli.py` before retrying.

### Hermes Hive proxy routes

Add `/api/suprime/*` routes in `src/server/apiMiddleware.ts` that call the SUPRIME bridge client in `src/server/suprime/suprimeBridge.ts`.

**Pattern:** import `suprimeBridge` and wrap each bridge call in `try/catch`, returning `502` on failure so Hermes remains authoritative even if SUPRIME is down:

```ts
if (url === '/api/suprime/health' && method === 'GET') {
  try {
    const result = await suprimeBridge.health();
    return jsonResponse(result);
  } catch (err) {
    return jsonResponse({ error: 'SUPRIME bridge unreachable', message: err instanceof Error ? err.message : String(err) }, 502);
  }
}
```

Apply the same wrapper to `startSwarm`, `stopSwarm`, `status`, `listTasks`, `submitTask`, and `registerWorker`.

Mirror SUPRIME task creation from Hermes missions so both systems track the same work. The exact route block already proved operational:
- `POST /api/suprime/tasks/submit` → submits a mirrored SUPRIME task
- `GET /api/suprime/tasks` → lists swarm tasks
- `POST /api/suprime/worker/:kind` → registers a handler kind
- `GET /api/suprime/status` → peers, leader, metrics, store keys
- `GET /api/suprime/health` → bridge health
- `POST /api/suprime/swarm/start` → start swarm
- `POST /api/suprime/swarm/stop` → stop swarm

## Runtime Verification

After wiring persistence and SUPRIME:
1. `POST /api/memory` with a test record
2. `GET /api/memory?search=<key>` to confirm round-trip
3. `GET /api/health` to confirm server still boots
4. `GET /api/suprime/health` and `POST /api/suprime/tasks/submit` to confirm bridge integration

## Build Verification Strategy

**Do not loop on `npx tsc --noEmit`** when the reported errors are confined to unrelated modules and runtime endpoints already pass. In that case, prefer:
- `npm run build`
- targeted runtime checks for the changed surface area
- searching the repo to confirm changed routes/files are actually wired

Repeated identical full-project type-check runs are a loop signal. Inspect error locality first, then choose a cheaper verification path.

**Pitfall:** Pre-existing TypeScript errors in `src/server/world/*` and `src/test/*` are common in this codebase. Filter `tsc` output by the changed file path before concluding the edit broke compilation.

## Unified Backend Registry

Use a backend registry when Hermes Hive must manage multiple swarm runtimes through one control plane.

### Backend adapter interface

```ts
export interface BackendAdapter {
  name: string;
  health(): Promise<{ status: string; detail?: string }>;
  start?(): Promise<{ status: string }>;
  stop?(): Promise<{ status: string }>;
  status?(): Promise<unknown>;
  submitTask?(payload: { kind: string; args?: Record<string, unknown>; taskId?: string }): Promise<{ status: string; taskId?: string }>;
  listTasks?(): Promise<{ status: string; tasks: Array<Record<string, unknown>> }>;
  registerWorker?(kind: string): Promise<{ status: string }>;
}
```

### Registry bootstrap in `apiMiddleware.ts`

```ts
import { backendRegistry } from './backends/backendRegistry';
import { OmnibusBackendAdapter } from './backends/omnibusAdapter';

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

**Pitfall:** Do not pass `suprimeBridge` directly if its method signatures differ from `BackendAdapter`. Register an adapter wrapper object instead; otherwise `tsc --noEmit` will report `submitTask` / `status` type mismatches.

### Unified proxy routes

```ts
if (url === '/api/backends' && method === 'GET') {
  return jsonResponse({ backends: backendRegistry.list() });
}

if (url.startsWith('/api/backends/') && method === 'GET') {
  const name = url.split('/')[3];
  const adapter = backendRegistry.get(name);
  if (!adapter) return jsonResponse({ error: 'Backend not found', name }, 404);
  return jsonResponse({ backend: name, health: await adapter.health() });
}

if (url.startsWith('/api/backends/') && method === 'POST') {
  const name = url.split('/')[3];
  const adapter = backendRegistry.get(name);
  if (!adapter) return jsonResponse({ error: 'Backend not found', name }, 404);
  const body = await getBody();
  if (url.includes('/start')) return jsonResponse(await (adapter.start?.() ?? { status: 'unsupported' }));
  if (url.includes('/stop')) return jsonResponse(await (adapter.stop?.() ?? { status: 'unsupported' }));
  if (url.includes('/status')) return jsonResponse(await (adapter.status?.() ?? { status: 'unknown' }));
  if (url.includes('/tasks/submit')) return jsonResponse(await (adapter.submitTask?.(body || {}) ?? { status: 'unsupported' }));
  if (url.includes('/tasks')) return jsonResponse(await (adapter.listTasks?.() ?? { status: 'unsupported', tasks: [] }));
  if (url.includes('/workers/')) {
    const kind = url.split('/').pop() || 'generic';
    return jsonResponse(await (adapter.registerWorker?.(kind) ?? { status: 'unsupported' }));
  }
  return jsonResponse({ error: 'Unsupported backend action', url }, 400);
}
```

### Frontend wiring note

When `patch`/`read_file` on `src/App.tsx` appears to revert or loop, use one deterministic full-file write or a narrow `sed` insertion instead of repeated fuzzy patches. Re-reading after every edit wastes turns on this file.

## Build Verification Strategy

**Do not loop on `npx tsc --noEmit`** when the reported errors are confined to unrelated modules and runtime endpoints already pass. In that case, prefer:
- `npm run build`
- targeted runtime checks for the changed surface area
- searching the repo to confirm changed routes/files are actually wired

Repeated identical full-project type-check runs are a loop signal. Inspect error locality first, then choose a cheaper verification path.

**Pitfall:** Pre-existing TypeScript errors in `src/server/world/*` and `src/test/*` are common in this codebase. Filter `tsc` output by the changed file path before concluding the edit broke compilation.

**Pitfall:** Missing ambient typings for `vite` or `@google/genai` can surface in `tsc --noEmit` even when the app builds and runs. Treat those as environment/typing-declaration issues, not evidence that the new runtime path is broken.

## SUPRIME Reference

See `references/suprime-bridge-verified.md` for the exact verified endpoints, startup commands, the Windows CLI pitfall encountered during integration, and the confirmed proxy route pattern.

# SUPRIME Bridge Plan

Goal: make Hermes Hive the operator UI/control plane while SUPRIME becomes the real swarm execution backend.

## Integration Approach

1. Add a bridge module in Hermes Hive: `src/server/suprimeBridge/`
2. Expose SUPRIME lifecycle through Hive APIs or direct process management
3. Translate Hive missions/tasks into SUPRIME task-board claims
4. Stream SUPRIME events back into Hive's message bus

## SUPRIME Entrypoints

- Library: `from suprime import SwarmNode`
- CLI: `python -m suprime run --port 7001 --id alpha --worker sum`
- In-process demo: `python examples/local_swarm.py`

## Key SUPRIME Modules

- `suprime/node.py` — SwarmNode composition
- `suprime/tasks.py` — Decentralised task submission, claiming, execution
- `suprime/gossip.py` — Epidemic dissemination
- `suprime/peers.py` — Membership + heartbeat failure detection
- `suprime/store.py` — LWW CRDT key/value store
- `suprime/persistence.py` — WAL + snapshot crash recovery
- `suprime/metrics.py` — Observability
- `suprime/cli.py` — `run` and `dashboard` commands

## API Surface Proposal

Hive-side additions:
- `POST /api/suprime/start` — start local swarm node
- `POST /api/suprime/stop` — stop node
- `GET /api/suprime/status` — node status
- `POST /api/suprime/tasks` — submit task to SUPRIME swarm
- `GET /api/suprime/tasks` — list SUPRIME tasks

Event mapping:
- SUPRIME task claimed → Hive `TASK_ASSIGNMENT`
- SUPRIME task completed → Hive `TASK_RESULT`
- SUPRIME peer joined/left → Hive `AGENT_CREATED`/`AGENT_STOPPED`
- SUPRIME leader change → Hive `HERMES_DECISION`

## Transport Options

- In-process Python bridge via child process/stdio
- REST bridge wrapping SUPRIME node
- Direct TCP if SUPRIME exposes an API endpoint

## Persistence Bridge

SUPRIME already has WAL+snapshot persistence. Hive should:
1. Record SUPRIME state snapshots in SQLite
2. Replay SUPRIME events through Hive event bus on startup
3. Keep Hive as source of truth for mission metadata; SUPRIME as source of truth for swarm state

## Testing Plan

1. Start a 3-node SUPRIME swarm via Docker or local process
2. Create a Hive mission
3. Bridge mission tasks to SUPRIME task board
4. Verify task completion events flow back into Hive
5. Kill a node, verify failover events appear in Hive

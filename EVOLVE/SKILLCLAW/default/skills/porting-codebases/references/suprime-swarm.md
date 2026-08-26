# SUPRIME — Gossip-Based Swarm Network

Repo: https://github.com/jonnysteedman683-wq/SUPRIME
Stack: Pure Python (no dependencies), async
Stars: 2

## Core Architecture
A decentralised, gossip-based mesh of autonomous nodes. No central coordinator.
Membership, replicated state, distributed task execution, and leader election all
emerge from a single epidemic gossip channel.

## Key Modules

### gossip.py — Epidemic Dissemination
- Each round: pick random subset of peers, send state digest
- Push-based: send full state to random peer
- Pull-based: send digest, receive missing entries
- Anti-entropy: periodic full state reconciliation

### crdt.py — Convergent Replicated Data Types
- GCounter: grow-only counter (per-node increments, merge = max)
- PNCounter: positive/negative counter (two GCounters)
- LWWRegister: last-writer-wins register (timestamp-based)
- GSet: grow-only set (union merge)
- ORSet: observed-remove set (add with unique tags)
- Merge is commutative, associative, idempotent

### tasks.py — Distributed Task Execution
- Any node can submit work
- Swarm decides deterministically which node runs it (no scheduler)
- Uses consistent hashing on task ID

### agent.py — Collective AI Layer
- Pluggable brain per node
- Shared memory via CRDT KV store
- Work distribution via task system
- Quorum voting for collective decisions

### stigmergy.py — Indirect Coordination
- Agents coordinate through environment traces (like ant pheromones)
- Load balancing via stigmergic signals

### simulation.py — Deterministic Simulation Tester
- In-memory transport for testing entire swarm in one process
- Deterministic tick-based simulation

## Porting to ARISE
- Gossip → agents share task solutions / food locations with nearby agents
- CRDT → shared world state that converges even with agent movement
- Stigmergy → pheromone-like trails on the terrain
- Collective AI → agent groups that vote on collective actions

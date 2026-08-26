---
name: emergent-simulation
description: "Use when building agent-based emergent simulations."
---
# Emergent Simulation Design Patterns

## Core Loop
```
for each tick:
    for each agent:
        sense(world, other_agents) → state
        brain.think(state) → action
        execute(action) → effects
        learn(state, action, reward, next_state)
    world.tick()  # resources regrow, signals decay, etc.
    stats.record()
```

## Agent Brain Architecture
Two proven approaches (use both, let evolution decide):

**QNetwork (gradient-based)**
- 3-layer feedforward: fc1(ReLU) → fc2(ReLU) → out(linear)
- Epsilon-greedy exploration (start 0.3, decay to 0.05)
- ICM curiosity bonus: intrinsic_reward = prediction_error of forward model
- Replay buffer for experience storage
- Target network synced every 50 train steps

**HebbNet (local learning)**
- Competitive hidden layer with lateral inhibition + conscience bias
- Delta-rule readout (locally observable error)
- 4 plasticity rules: Hebbian (unstable), Oja (PCA), Instar (k-means), BCM (self-stabilizing)
- No backpropagation — updates during forward sweep
- Optional global modulation gate (3-factor rule)

## System Layering Pattern
Build emergent systems in layers, each enabling the next:

**Layer 1: Foundation** — lineage, resources, memory
**Layer 2: Social** — territory, signals, culture
**Layer 3: Dynamics** — conflict, trade routes
**Layer 4: Complexity** — technology, architecture, language

Each layer depends on previous layers. Wire all into simulation.tick().

## Economy Balance Rules
- hunger_per_tick: 0.03 (agents must survive long enough to earn currency)
- Food cost: 3 (affordable after 1 task solve)
- Task success: 0.5 (not too easy, not too hard)
- Reproduce cost: 5 currency + 15 hunger + 20 energy
- Auto-reseed: <5 alive → spawn 8 new agents (gentle, not 15+)

## Rendering Pattern
- Pre-render terrain to cached surface (expensive, draw once)
- Draw layers in order: terrain → grid → connections → objects → agents → UI
- Stats bar at bottom with clickable buttons (Pause/Save/Load)
- Agent inspector panel on click
- Flash messages for save/load feedback

## Pitfalls
- **Biome assignment**: go highest-to-lowest threshold, NOT lowest-to-highest
- **Population crashes**: test 500 ticks before shipping. Population should hold steady or grow
- **Reseed oscillation**: if reseed > 10 agents, population oscillates (die → reseed → die)
- **HebbNet action count**: must match Brain.N_ACTIONS exactly — update both when adding actions
- **Float precision in save/load**: JSON converts float32→float64→float32, drift < 1e-4 is acceptable
- **Terrain generation**: scipy zoom + gaussian_filter for smooth noise. Don't hand-roll Perlin noise — it's buggy at small scales

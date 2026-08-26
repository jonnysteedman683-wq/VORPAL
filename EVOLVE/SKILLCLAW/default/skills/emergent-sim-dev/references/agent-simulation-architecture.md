---
name: agent-simulation
description: "Use when building agent-based sims with evolution or RL."
---
# Agent-Based Simulation Development

Build simulations where AI agents evolve, learn, and exhibit emergent behavior.

## Architecture Pattern
```
config.py       — All tuning constants in one place
brain.py        — Neural network(s) for agent decision-making
world.py        — Spatial environment (grid, toroidal, graph)
agent.py        — Agent class: sense → think → act → learn
tasks.py        — Challenges agents solve for rewards
simulation.py   — Tick loop wiring all systems together
renderer.py     — Visualization (Pygame, matplotlib, web)
save.py         — Serialization for persistence
```

## Brain Architecture Patterns

### Genetic + Learned (dual inheritance)
Agents inherit brain weights (mutation across generations) AND learn within their lifetime (Q-learning, Hebbian). This creates two timescales of adaptation.

### Multiple Brain Types
Give different agents different learning algorithms. Let evolution decide which wins:
- Q-learning with replay buffer (strategic, slow)
- Hebbian local learning (reactive, fast)
- Hybrid blending both systems

### Action Count Migration (CRITICAL PITFALL)
When adding new actions to the brain, old saves break because weight matrices have wrong dimensions. In the deserializer:
1. Check `q_network.out.out_dim != NEW_N_ACTIONS` → reinitialize output layer
2. Check `icm.n_actions != NEW_N_ACTIONS` → reinitialize ICM
3. Check `readout.n_outputs != NEW_N_ACTIONS` → reinitialize readout weights

Never assume saved action count matches current. Always compare and resize.

### Simulation.__new__ Pitfall
When loading saves, using `__new__()` bypasses `__init__`. Every subsystem must be manually initialized in the load function. Create a checklist of all subsystems and verify each is initialized.

## Emergent Civilization Systems
Layer systems from simple to complex:
1. **Foundation**: lineage tracking, resource scarcity, agent memory
2. **Social**: territory, communication signals, cultural memes
3. **Economic**: conflict, trade routes, technology discovery
4. **Biological**: aging, disease, parasites, symbiosis, migration
5. **Architectural**: buildings with effects, upgrades, synergy bonuses

## Procedural Terrain
- Multi-octave noise (coarse + medium + fine) for natural-looking landscapes
- Biome assignment: iterate thresholds HIGH-to-LOW (not low-to-high, which overwrites everything)
- Cache terrain as a surface for rendering performance
- Terrain affects agent movement speed

## Save/Load System
- JSON for metadata + agent state, numpy arrays serialized as lists
- Save all subsystem state (lineage, culture, technology, etc.)
- Handle version migration gracefully (new fields get defaults)
- CLI: `python main.py --load [save_name]` for quick resume

## Economy Tuning
- Start generous (low hunger, cheap food) and tighten as agents evolve
- Auto-reseed threshold prevents population death spirals
- Task success rate should be high enough that agents can sustain themselves
- Multiple income sources (tasks, foraging, trading) prevents single-point failure

## Pygame Rendering Tips
- Cache static terrain as a Surface, blit once per frame
- Draw structures larger than agents (1.5x) with labels for visibility
- Use color tinting for status (sick=green, parasitized=red, aging=dim)
- Stats bar at bottom with clickable buttons
- Mini-graphs for population/fitness history

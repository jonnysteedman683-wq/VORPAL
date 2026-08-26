---
name: arise-sim
description: "Use when developing ARISE — AI swarm survival simulation."
version: 0.1.0
---
# ARISE Simulation Development

## Project: ARISE
- **What**: 2D aerial-view ant-farm simulation where AI agents evolve, solve coding tasks, and survive
- **Location**: `~/OneDrive/Documents/AEGIS/ARISE/`
- **Stack**: Python, Pygame, NumPy (no ML frameworks)
- **Run**: `cd ARISE && python main.py`

## Architecture
```
arise/
  config.py       — All tuning constants
  brain.py        — QNetwork + ICM curiosity (ported from AQB's rl-core.ts)
  hebbian.py      — HebbNet: 4 plasticity rules (Hebbian, Oja, Instar, BCM) from NYX
  terrain.py      — Procedural biome generation (6 biomes via multi-octave noise)
  world.py        — Toroidal 800x800 world, terrain, tasks, markets
  agent.py        — Agent lifecycle, sensing, social learning (Hebbian edges)
  tasks.py        — 4 task types (Logic, Pattern, Math, Creative) with specializations
  simulation.py   — Tick loop, stats, auto-reseed
  renderer.py     — Pygame aerial view, terrain, social connections, agent inspector
  save.py         — Save/load (F5/F9), JSON serialization of both brain types
main.py           — Entry point
```

## Key Design Decisions
- **Dual inheritance**: Genetic (brain weights mutate across generations) + Learned (Q-learning + curiosity within lifetime)
- **Curiosity**: ICM module from AQB — agents explore novel states, not just food
- **Social learning**: Hebbian-inspired edges between agents; nearby agents get currency bonus when one solves a task
- **Specializations**: 4 task types (Logic/Pattern/Math/Creative) with agent affinities that mutate
- **Toroidal world**: Wraps on all edges — no corners to camp
- **Two brain types** (NYX): QNet (Q-learning + ICM) and HebbNet (local learning, no backprop). HebbNet has 4 plasticity rules: Hebbian, Oja, Instar, BCM. Evolution decides which survives.

## Ported from ARCANE QUANTUM BRAIN
- `rl-core.ts` Dense/QNetwork → `brain.py` Dense/QNetwork with numpy backprop
- `rl-core.ts` Encoder/ForwardModel/InverseModel → `brain.py` ICM curiosity
- `swarm-engine.ts` roles → `tasks.py` task types with specializations
- `hebbian.ts` traces → `agent.py` social_edges with decay

## Ported from NYX
- `hebb/layers.py` CompetitiveHebbianLayer → `hebbian.py` CompetitiveLayer (lateral inhibition + conscience)
- `hebb/layers.py` DeltaReadout → `hebbian.py` DeltaReadout (local error learning)
- `hebb/rules.py` 4 plasticity rules → `hebbian.py` (Hebbian, Oja, Instar, BCM)
- `hebb/model.py` HebbNet → `hebbian.py` HebbNet (no-backprop brain)

## Save/Load System
- `arise/save.py` — full serialization of agents, brains (QNetwork + ICM weights), world state
- Saves to `ARISE/saves/<timestamp>/` as JSON (metadata + agent state)
- F5: quick save, F9: quick load (most recent)
- CLI: `python main.py --load` to resume last save
- Weight drift < 1e-4 on round-trip (float32→JSON→float64→float32)
- `save.save(sim)`, `save.load(path)`, `save.list_saves()`

## Controls
- Space: pause/resume
- Up/Down: speed (or torus camera tilt when 3D view active)
- G: grid, T: trails, S: social connections, V: 3D torus view
- Click: inspect agent
- F5: save, F9: load
- Esc: quit

## Pitfalls
- Use `python` not `python3` — numpy installed for Python 3.11
- pygame requires display — can't run headless
- Agents auto-reseed if population crashes below 3

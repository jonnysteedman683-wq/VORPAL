---
name: alife-simulation
description: "Evolving AI agent simulations with neural nets and pygame."
triggers:
  - user wants to build a simulation, ant farm, fish tank, or ecosystem
  - user wants agents that evolve, learn, or exhibit emergent behavior
  - user wants neural network agents in a visual environment
  - user mentions artificial life, alife, swarm, or evolutionary simulation
---

# Artificial Life Simulation

Build agent-based simulations where entities live, learn, evolve, and die — observed from the outside.

## Critical User Preference: Design First

**The user wants to nail down the concept BEFORE writing code.** When they say "let's get the concept proper first" or "stop" during implementation, halt coding and return to design. Present the concept as a structured document (world, agents, loop, controls) and get explicit sign-off before building.

Do NOT jump into code when the user says they want to "develop" something. Ask what they mean first — it might be design, not implementation.

## Workflow

1. **Concept phase** — Nail down:
   - What is the world? (2D/3D, grid/continuous, topology)
   - What do agents DO? (sense → think → act loop)
   - What's the survival mechanic? (food, energy, currency)
   - What drives evolution? (genetic mutation, learning, both)
   - What does the observer SEE? (aerial view, dashboards, overlays)
   - What's the tech? (pygame, matplotlib, web, terminal)

2. **Prototype phase** — Build a working simulation with:
   - Minimal viable agent behavior
   - Basic world with resources
   - Simple renderer
   - Verify it runs before adding complexity

3. **Enrichment phase** — Layer on:
   - Neural network brains (Q-learning, curiosity)
   - Social learning between agents
   - Task specialization / role differentiation
   - Advanced visualization (social connections, brain viz)

4. **Tuning phase** — Adjust constants until emergent behavior appears:
   - Hunger/survival pressure (too high = extinction, too low = no evolution)
   - Mutation rate (too high = random, too low = stagnation)
   - Population caps
   - Reward shaping

## Architecture Pattern

```
project/
  config.py          — ALL tuning constants in one place
  brain.py           — Neural network (numpy, no frameworks)
  world.py           — Environment, topology, resources
  agent.py           — Agent class (sense → think → act)
  tasks.py           — Challenge/reward system
  evolution.py       — Reproduction, mutation, selection
  simulation.py      — Tick loop, stats tracking
  renderer.py        — Visual output
  main.py            — Entry point
```

## Key Design Decisions

### Neural Network Brains
- Use numpy-only feedforward networks (no pytorch/tensorflow for prototypes)
- Architecture: Dense(input, hidden, ReLU) → Dense(hidden, hidden, ReLU) → Dense(hidden, output)
- Include ICM (Intrinsic Curiosity Module) for exploration: encoder + forward model + inverse model
- Curiosity reward = prediction error of forward model (agents explore novel states)

### Hebbian Brains (No Backprop)
- Port from NYX `hebb/` module — 4 plasticity rules: Hebbian, Oja, Instar, BCM
- `CompetitiveLayer`: lateral inhibition + conscience bias (prevents brain collapse)
- `DeltaReadout`: supervised output with locally observable error
- Each layer updates during forward sweep — no backward pass, no stored activations
- More biologically plausible, creates different evolutionary dynamics than Q-learning

### Hybrid Brains
- Combine QNet (strategic) + HebbNet (fast reactions) in one agent
- Blend factor controls influence: fast actions favor HebbNet, strategic favor QNet
- Created when QNet and HebbNet agents reproduce near each other (40% chance)
- Most interesting evolutionary outcome — survives better than either parent type

### Dual Inheritance
- **Genetic**: brain weights mutate across generations (parent → child with noise)
- **Learned**: Q-learning within each agent's lifetime (experience replay, target network)
- This creates interesting dynamics: genetically gifted agents learn faster

### Toroidal World
- Wraps at edges (no corners to camp)
- Distance/angle must use shortest toroidal path:
  ```python
  def toroidal_dx(dx, width):
      if dx > width / 2: dx -= width
      elif dx < -width / 2: dx += width
      return dx
  ```

### Social Learning (Hebbian-inspired)
- Agents that are near each other strengthen "social edges"
- When one agent solves a task, nearby agents get small currency bonus
- Edges decay over time if agents don't interact
- Creates emergent clustering and knowledge transfer

### Task Specialization
- Multiple task types (logic, pattern, math, string, sorting, creative)
- Each agent has innate affinities (Dirichlet-distributed)
- Creates niche partitioning — agents naturally specialize

### Species System
- Define 2-3 species with distinct trait modifiers (speed, task success, hunger rate, reproduce cost)
- Each species gets a capital city (equally spaced on map)
- Capitals offer 100% protection to new agents
- Protection lost when agent reproduces — forces exploration
- Creates tribal dynamics: species cluster at capitals, expand outward

### Biology Systems (Layer on Top)
- **Aging**: agents weaken over time (speed/energy decay), max lifespan
- **Disease**: infections spread on contact, weaken hosts, hospitals heal
- **Parasites**: drain host currency, spread between nearby agents
- **Symbiosis**: mutually beneficial partnerships form through interaction
- **Migration**: seasonal biome preferences drive movement patterns
- Start with low severity — too much disease kills the population

### Civilization Systems (12+ Interacting)
- Territory, signals, culture (memes), conflict, trade routes
- Technology (task-based discoveries), architecture (buildings)
- Language (emergent signal-response patterns)
- Memory (agent relationships, event history)
- Each system should be simple alone but create complexity together

### Agent Skills (XP-Based Leveling)
- Skills level up from actions, not evolution (complements genetic inheritance)
- 6 types: farming, medic, combat, crafting, diplomacy, scouting
- Each has level (0-10), experience, xp_to_next (grows 1.5x per level)
- Farming: +5% harvest per level. Medic: +5% disease resistance per level
- Combat: +5% conflict strength. Scouting: +3% speed per level
- Skills affect agent stats in real-time, creating visible specialization

### Leader System
- Agents gain reputation from task completion and building
- At threshold (e.g., 50 rep), agents become leaders
- Leaders provide speed/power/resistance bonuses to nearby same-species agents
- Leaders can coordinate followers: direct hungry→food, tired→shelter, healthy→tasks
- Leader coordination overrides agent brain decisions temporarily

## Pygame Renderer Checklist
- Aerial/top-down view as the primary perspective
- Agents colored by species (primary) with specialization tint
- Task nodes shaped/colored by type (diamonds for tasks, squares for markets)
- Buildings: 1.5x size, white border, abbreviated labels (SH, GR, HP, RD)
- Stats bar at bottom with population, fitness, generation, brain type, season
- Click-to-inspect agent panel (brain type, species, skills, stats)
- Politics sidebar (280px right): species counts, leaders, avg skills
- Toggle overlays: grid (G), trails (T), social connections (S), 3D torus (V)
- Speed controls (↑/↓), pause (space), save (F5), load (F9), exit button
- Capital zones: translucent colored circles with species labels
- Leader coordination lines: yellow lines from agent to target
- Flash messages for save/load feedback

## Pitfalls

### Population Collapse
- Auto-reseed when population drops below threshold (e.g., 3 agents)
- Without this, a bad generation can cause permanent extinction
- Reseed with slightly lower generation number so it feels natural
- Disease/parasite rates are the #1 cause of unexpected crashes — tune conservatively

### Save/Load Schema Migration
- When adding new actions to the brain (e.g., ACT_BUILD), old saves break
- Fix: check `brain.q_online.out.out_dim != current_actions` on load → reinitialize output layers
- Same for ICM `n_actions` and HebbNet `readout.n_outputs`
- Old brain weights are lost for resized layers, but hidden layers survive

### Architecture System Design
- Buildings should be VISUAL — larger than agents, labeled, bordered
- Use abbreviations (SH, GR, HP, RD) for labels on small buildings
- Upgrade paths create engagement (dirt_path → road at level 2)
- Synergy bonuses (housing + nearby friendly structures) encourage settlement

### Python Version Mismatch
- `python3` may point to a different version than where packages are installed
- Use `python` (not `python3`) on Windows if packages were installed via pip for a specific version
- Verify with: `python -c "import pygame; import numpy; print('OK')"`

### Simulation Speed
- Q-learning with replay buffer is CPU-intensive per tick
- Start with small agent count (30) and scale up
- Batch neural network operations (forward pass on all agents, then all learn)

### Reward Shaping
- Too little reward → agents wander randomly forever
- Too much reward → agents exploit one strategy, no diversity
- Include small living reward (+0.01/tick) to encourage survival
- Include curiosity bonus to encourage exploration
- Balance: external reward (tasks) + intrinsic reward (curiosity)

## Porting Neural Network Code Between Languages

See `references/ts-to-python-nn-porting.md` for a full conversion reference from TypeScript/rl-core.ts to Python/numpy.

When the user has existing neural network code in another language (TypeScript, etc.):
1. Read the original architecture carefully — note layer sizes, activations, training loop
2. Port the MATHEMATICS, not the syntax — same shapes, same operations
3. Key mappings:
   - TypeScript `Array.from({length: n}, () => Array(m).fill(0))` → Python `np.zeros((n, m))`
   - TypeScript class methods → Python class methods (same structure)
   - Manual matrix multiply → numpy `@` operator
   - `relu(x)` → `np.maximum(0, x)`
4. Keep the same hyperparameter names so you can compare behavior
5. Test layer-by-layer before integrating into the full system

## Verification Script Pattern

Always verify core systems before running the full renderer:
```python
# Test each layer independently
assert Dense(10, 5).forward(x).shape == (4, 5)
assert QNetwork(10, 7).forward(s).shape == (8, 7)
assert ICM(10, 7).compute_curiosity(s, 3, ns) >= 0
# Then test integration
sim = Simulation()
for _ in range(300): sim.tick()
assert len(sim.alive_agents) > 0
```

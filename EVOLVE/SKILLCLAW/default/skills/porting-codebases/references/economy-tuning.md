# Agent Simulation Economy Tuning

## The Problem
Initial economy params caused population crash-reseed cycles:
- Hunger rate too fast (0.08/tick = dead in 1250 ticks)
- Task success too low (0.3 base) for agents to earn enough
- Tasks too scarce (12) with slow respawn (60 ticks)
- Reproduction too expensive (10 currency + 30 energy)
- Reseed too aggressive (jumps from 3 → 17 agents)

## The Fix (tuned values)
```python
HUNGER_PER_TICK    = 0.03    # was 0.08 — 2.7x slower starvation
ENERGY_REGEN       = 0.08    # was 0.05 — faster recovery
FOOD_HUNGER_RESTORE = 50.0   # was 40 — more bang per meal
FOOD_COST          = 3       # was 5 — cheaper food
REPRODUCE_HUNGER   = 15.0    # was 20 — cheaper reproduction
REPRODUCE_ENERGY   = 20.0    # was 30
REPRODUCE_CURRENCY = 5.0     # was 10
NUM_TASKS          = 20      # was 12 — more opportunities
TASK_RESPAWN_DELAY = 30      # was 60 — faster recycling
TASK_BASE_SUCCESS  = 0.5     # was 0.3 — easier tasks
```

## Tuning Principles
1. **Agents should survive ~3000+ ticks** on a full stomach (100/0.03 = 3333 ticks)
2. **One successful task solve should buy ~1.5 meals** (reward/food_cost ≈ 1.5)
3. **Population should grow through reproduction, not reseed** — reseed is emergency-only
4. **Reseed should be gentle** (5-8 agents, not 15) to avoid artificial population spikes
5. **Start generous, tighten later** — it's easier to make survival harder than to debug starvation

## Verification Pattern
```python
sim = Simulation()
pops = []
for tick in range(500):
    sim.tick()
    if tick % 50 == 0:
        pops.append(len(sim.alive_agents))
assert min(pops) >= 10, f'population dipped to {min(pops)}'
assert pops[-1] >= pops[0] - 5, f'population crashed'
```

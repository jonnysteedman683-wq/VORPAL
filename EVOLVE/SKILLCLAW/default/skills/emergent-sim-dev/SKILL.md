---
name: emergent-sim-dev
description: "Agent-based & emergent simulation dev (ARISE, alife, evolution/RL): genetics, communication, personality, weather, rendering, performance, pygame."
version: 0.4.0
author: Hermes
metadata:
  hermes.tags:
    - simulation
    - genetics
    - communication
    - personality
    - performance
    - pygame
---

# ARISE Simulation Development — Umbrella Skill

This skill covers the full ARISE (Artificial Rising Intelligence Swarm Ecosystem) development workflow: 30+ subsystems, 16-gene genetics, emergent communication, personality/emotions, weather events, building strategy, and performance optimization.

**Key references** (load with `skill_view(name, file_path)`):
- `references/genetics-system.md` — 16 genes, mutation, crossover, species diversity
- `references/communication-system.md` — 6 signal types, vocabularies, ripples, deception
- `references/personality-emotions.md` — Big Five personality, 5 emotions, behavior modifiers
- `references/performance-optimization.md` — spatial grid, throttling, squared distance
- `references/agent-intelligence.md` — goal persistence, social learning, state vector, curiosity
- `references/save-subsystem-sync.md` — every new system needs save.py load() entry
- `references/building-strategy.md` — resource chains, weather defense, settlements
- `references/weather-events.md` — 5 event types, building resistance
- `references/predator-prey-design.md` — camouflage, combat, fleeing
- `references/migration-roles-pattern.md` — seasonal migration, 6 agent roles
- `references/local-import-pitfall.md` — never re-import inside functions
- `references/agent-memory-argus.md` — time-series memory, drives with decay, anomaly detection
- `references/time-warp.md` — number keys 1-5 for accelerated evolution
- `references/reproduction-incentives.md` — biological clock, social pressure, energy bonus
- `references/pygame-verification-avoidance.md` — source-only checks, no pygame in verify scripts
- `references/agent-simulation-architecture.md` — generic agent-sim architecture (config/brain/agent/world layout, evolution + RL loops)
- `references/emergent-simulation-overview.md` — emergent-simulation design principles (absorbed skill)
- `references/arise-architecture.md` — ARISE repo architecture map
- `references/arise-personality-genetics.md` — personality/emotion/genetics deep dive (absorbed skill)
- `references/alife-simulation-pygame.md` — alife/pygame evolving-NN sim workflow (absorbed skill)
- `references/economy-tuning-history.md` — economy/resource tuning history
- `references/hebbian-nyx-porting.md`, `references/ts-to-python-nn-porting.md` — porting NN code into sims
- `references/sentinel-repo-analysis.md` — private repo with Options Framework, QuadTree, World Model, Active Inference, Debate Machine, Triangulation Engine

## Architecture

ARISE is a 2D aerial-view "ant farm" Pygame simulation. 120 agents (configurable), 3 species (red/green/blue), 11 biomes, toroidal world. Dual brain types (QNet vs HebbNet) compete. 30+ integrated subsystems.

## Critical Pitfalls

1. **Save.py subsystem sync**: Every new system in `Simulation.__init__()` MUST also be in `save.py load()`. Missing this causes `AttributeError` on load. Pattern: add import + init in load().

2. **No local re-imports**: If `toroidal_distance` is imported at module level, NEVER add `from .world import toroidal_distance` inside functions. Python treats it as a local variable, causing `UnboundLocalError`.

3. **SocialEdge field names**: Uses `target_id` (not `other_id`) and `trace` (not `weight`). Always check dataclass definition.

4. **disease.infect() requires tick arg**: `self.disease.infect(agent.id, self.stats.tick)` — tick is mandatory.

5. **Probabilistic assertions**: `is_old_age_death()` is random. Never assert it returns True. Use: `assert sum(1 for _ in range(100) if fn()) > 0`

6. **Never auto-launch**: User said "stop sending me into the app". NEVER run `python main.py` unless asked.

7. **Config changes**: INITIAL_AGENTS=40, BRAIN_INPUTS=14, AGENT_MAX_SPEED=4.0 (was 2.0 — agents are fast). MAX_LIFESPAN=7500, AGING_START=3000. REPRODUCE costs: hunger=5, energy=10, currency=2 (very cheap). Reproduction fitness reward=20× (was 10×). Reproduce threshold: hunger < 70 (not MAX_HUNGER - cost). User wants wide genetic diversity — use randomized species traits, rare mutations, transgressive segregation. User explicitly wants reproduction as a primary goal — keep costs low, rewards high.

8. **Brain resize on state dim change**: When BRAIN_INPUTS changes (e.g. 10→14), old saves have wrong-sized weights. Add `_resize_dense`, `_resize_qnet`, `_resize_icm` helpers to save.py. Apply in ALL brain deserialization paths (hybrid AND standalone). Pattern:
   ```python
   def _resize_dense(dense, old_in, new_in):
       new_dense = Dense(new_in, dense.out_dim, dense.lr)
       copy_cols = min(old_in, new_in)
       new_dense.weight[:, :copy_cols] = dense.weight[:, :copy_cols]
       if new_in > old_in:
           new_dense.weight[:, old_in:] = np.random.randn(dense.out_dim, new_in - old_in) * 0.01
       new_dense.bias = dense.bias.copy()
       return new_dense
   ```
   Also resize HebbNet hidden weights (competitive layer input dim).

9. **HebbNet MUST have epsilon-greedy**: HebbNet's `think()` had NO exploration — always `np.argmax(logits)`. Also had `@property epsilon` returning 0.0 that blocked assignment. CRITICAL FIX: remove the property, add epsilon-greedy to `think()`:
    ```python
    def think(self, state):
        if not hasattr(self, 'epsilon'):
            self.epsilon = 0.3
        if np.random.random() < self.epsilon:
            return np.random.randint(logits.shape[1])
        self.epsilon = max(0.05, self.epsilon * 0.9999)
        return int(np.argmax(logits[0]))
    ```
    Without this, agents NEVER explore new actions (like ACT_REPRODUCE). This caused 0 reproduction across 500 ticks.

10. **Never force behavior — use rewards**: User said "dont force just make it worth it". Never use action overrides (`action = Brain.ACT_REPRODUCE`). Instead use reward shaping: add intrinsic reward when agents attempt desired actions, scaled by drive strength. The brain learns naturally.

11. **newborn referenced before creation**: In `_try_reproduce()`, code that references `newborn.id` MUST come AFTER `newborn = Agent(...)`. Common bug pattern: adding post-birth logic above the Agent constructor call. Always put `self.children_ids.append(newborn.id)` etc. AFTER the return becomes `newborn = Agent(...); ...; return newborn`.

12. **Goal persistence**: Agents stick with working actions for 3-8 ticks. Prevents thrashing.
   ```python
   if action == self._prev_action:
       self._goal_persistence = min(self._goal_persistence + 1, 8)
   elif self._goal_persistence > 3:
       action = self._goal_action  # stick with goal
       self._goal_persistence -= 1
   ```

10. **Social learning**: Every 10 ticks, agents scan nearby agents within ~63px. If a fitter agent exists, 20% chance to copy their last action. Only triggers when `_social_mod > 0.5`.

11. **Cached nearest-agent**: The O(n²) nearest-agent scan in `sense()` is expensive. Cache result every 5 ticks:
    ```python
    if self.age - self._cached_nearest_tick > 5:
        # full scan
        self._cached_nearest_tick = self.age
    else:
        a_dist_norm = self._cached_a_dist  # use cached
    ```

12. **Profiling results** (40 agents): sense=0.52ms, think=0.47ms, learn=1.63ms (bottleneck), social_tick=0.47ms. learn() is 3× slower than anything else — throttle to every other tick.

13. **Reward shaping for desired behavior**: User said "dont force just make it worth it". NEVER override actions. Instead shape rewards:
    ```python
    # In _compute_reward():
    if self.stats.children_born > 0:
        r += self.stats.children_born * 0.5  # huge ongoing reward
    r += self.currency * 0.005  # currency feels good
    if self.hunger < 30: r += 0.05  # satisfaction
    if self._cached_a_dist < 0.3: r += 0.02  # social proximity
    # In action handler, reward attempts:
    elif action == Brain.ACT_REPRODUCE:
        newborn = self._try_reproduce(agents)
        rep_drive = self._agent_memory.get_drive_strength(self.id, "reproduction_drive", self.age)
        if rep_drive > 0.3:
            self.stats.intrinsic_reward_total += rep_drive * 0.3
    ```

13. **Method signature changes break saves**: When changing method signatures (adding args), grep ALL call sites.

14. **Genetic diversity**: User wants wide diversity. Use randomized species traits (uniform ranges, not fixed multipliers), rare large mutations (3% chance of ±0.3 jump), transgressive segregation in crossover (5% chance of completely random gene), wider initial range (60-95% of gene range instead of 80-80%).

15. **User preferences**: "you tell me" = wants proactive recommendations. "upgrade more" = build everything offered. Creative naming preferred. "stop sending me into the app" = NEVER auto-launch. Frustrated by population crashes — prioritize survivability.

16. **Pygame verification avoidance**: Importing `arise.agent` triggers pygame transitively. For verification scripts that don't need pygame, use source-only checks (read file, grep for keywords) instead of importing modules. Or check `with open(path) as f: src = f.read()`. See `references/pygame-verification-avoidance.md` for safe/unsafe module lists.

17. **INITIAL_AGENTS = 40**: User set to 40 for better performance (was 120). Don't change back without asking.

18. **Reproduction as primary goal**: User explicitly wants reproduction to be the main evolutionary driver. Config: REPRODUCE costs minimal (hunger=5, energy=10, currency=2), fitness reward=20×, reproduce threshold hunger < 70. Biological clock + social pressure + energy bonus + leadership rep. See `references/reproduction-incentives.md` for full pattern.

19. **Fast agents**: AGENT_MAX_SPEED=4.0 (was 2.0). Agents zoom around. Adjust movement-related constants accordingly.

17. **INITIAL_AGENTS = 40**: User set to 40 for better performance (was 120). Don't change back without asking.

18. **Reproduction as primary goal**: User explicitly wants reproduction to be the main evolutionary driver. Config: REPRODUCE costs minimal (hunger=5, energy=10, currency=2), fitness reward=20×, reproduce threshold hunger < 70. Reproduction drive initialized at 0.8× fertility (strong). Reproduction drive half-life=200 ticks (slow decay). This creates strong selection pressure for agents that reproduce early and often.

19. **Fast agents**: AGENT_MAX_SPEED=4.0 (was 2.0). Agents zoom around. Adjust movement-related constants accordingly.

9. **Hybrid brains**: Import all brain types at top of `_deserialize_agent`, not inside if/elif.

10. **Terrain gen is slow (~3s)**: Cache it. Use file reads for verification, not re-generation.

## Time Warp Workflow

When developing new systems that need evolution time (genetics, communication, etc.), use time warp to accelerate:
1. Make changes, verify with source-only checks
2. Launch game with `python main.py`  
3. User presses **1-5** to warp ahead (10→5000 ticks)
4. Check console output for alive count, generation, gene diversity
5. Auto-save triggers after warps ≥200 ticks

This lets mutations accumulate across generations without waiting in real-time.

## Verification Pattern

Write temp verify script, run it, clean up:
```python
# hermes-verify-arise-*.py
import sys; sys.path.insert(0, 'C:/Users/jonny/OneDrive/Documents/AEGIS/ARISE')
# test imports, check source for keywords, verify data structures
print('ALL VERIFIED')
```

Run with: `python 'C:\Users\jonny\AppData\Local\Temp\hermes-verify-arise-*.py'`
Clean up: `rm -f 'C:\Users\jonny\AppData\Local\Temp\hermes-verify-arise-*.py'`

**Pygame avoidance**: Importing `arise.agent` or `arise.renderer` triggers pygame transitively (via `from .brain import Brain` which initializes pygame). For verification scripts that only need to check source code, use source-only checks instead of importing modules:

```python
# WRONG — triggers pygame, may hang or timeout
from arise.simulation import Simulation

# CORRECT — source-only check, no pygame
with open('C:/Users/jonny/OneDrive/Documents/AEGIS/ARISE/arise/simulation.py') as f:
    src = f.read()
assert 'self.weather' in src
assert 'self.communication' in src
print('OK simulation.py')
```

Use this pattern for any verification that only needs to check file contents, method signatures, or class definitions. Only import modules when you need to actually run code (e.g. testing a function output).

## Communication System

## Architecture

Species develop independent vocabularies through signal-response reinforcement. 8 features: visual ripples, signal chains/gossip, dialect divergence, call & response bonding, teaching, deception, signal memory (trust), and communication cost.

### Signal types

```python
SIGNAL_FOOD = 0      # "food here" — emitted when hungry agent finds food
SIGNAL_DANGER = 1    # "danger" — emitted when sick
SIGNAL_SOCIAL = 2    # "come here" — emitted occasionally
SIGNAL_TERRITORY = 3 # "my area" — emitted during territory claims
SIGNAL_CALL = 4      # general call — for call & response bonding
SIGNAL_WARNING = 5   # "predator nearby" — emitted when fleeing

SIGNAL_TYPE_COLORS = {
    SIGNAL_FOOD: (80, 255, 80),
    SIGNAL_DANGER: (255, 60, 60),
    SIGNAL_SOCIAL: (100, 180, 255),
    SIGNAL_TERRITORY: (255, 200, 60),
    SIGNAL_CALL: (200, 150, 255),
    SIGNAL_WARNING: (255, 100, 100),
}
```

### Vocabulary convergence

Each species has vocabulary centers that drift toward successful signals:

```python
species_vocab = {
    "red": {"food_center": 0.15, "danger_center": 0.45, "social_center": 0.7,
            "territory_center": 0.9, "call_center": 0.5, "warning_center": 0.35},
    "green": {...}, "blue": {...},
}
```

Reinforcement: `vocab_center += lr * (signal_value - vocab_center)`
- Success: lr = 0.03 (fast learning)
- Failure: lr = -0.008 (slow unlearning)

### 8 Features

**1. Visual ripples** — each emission creates `[x, y, color, age, max_age]`. Renderer draws expanding translucent circles that fade:
```python
self.ripples.append([x, y, color, 0, max_age])
# in tick(): age += 1, remove when age >= max_age
# renderer: radius = 5 + progress*40, alpha = 150*(1-progress)
```

**2. Signal chains/gossip** — relay heard signals to nearby agents:
```python
def relay_signal(self, signal, relay_agent_id, x, y, tick, species):
    relayed_value = signal.signal_value + np.random.normal(0, 0.02)
    self.emit(relay_agent_id, signal.signal_type, relayed_value,
              x, y, signal.intensity * 0.7, tick, species, reliable=signal.reliable)
```
Relay rates: food 15%, danger 30%, warning 40%.

**3. Dialect divergence** — species vocabularies diverge:
```python
def get_dialect_divergence(self):
    all_food = [v["food_center"] for v in self.species_vocab.values()]
    avg_food = np.mean(all_food)
    return {sp: abs(v["food_center"] - avg_food) for sp, v in self.species_vocab.items()}
```

**4. Call & response** — agents bond through signal matching:
```python
def check_call_response(self, agent_id, partner_id, signal_value, species):
    vocab = self.species_vocab[species]
    call_center = vocab["call_center"]
    if abs(signal_value - call_center) < 0.15:
        self.call_response_pairs[agent_id] = partner_id
        return True
    return False
```
On response, increase `social_edges` weight by 0.1.

**5. Teaching** — old agents (age > 500) emit food signals near young:
```python
if self.age > 500 and np.random.random() < 0.03:
    comm.emit_food_signal(self.id, self.x, self.y, self.age, sp)
    self.energy -= 0.2
```

**6. Deception** — aggressive agents emit false food signals:
```python
def should_deceive(self, agent_genome):
    aggression = agent_genome.get('aggression')
    return aggression > 0.7 and np.random.random() < 0.05
```
False signals have `reliable=False`. Trust drops when deception is discovered.

**7. Signal memory/trust** — per-emitter reliability tracking:
```python
self.agent_trust: dict[int, dict[int, float]] = defaultdict(lambda: defaultdict(lambda: 0.5))

def reinforce(self, species, signal_value, actual_type, success, emitter_id, perceiver_id):
    # ... vocabulary reinforcement ...
    if emitter_id and perceiver_id:
        old_trust = self.agent_trust[perceiver_id][emitter_id]
        new_trust = old_trust + (0.1 if success else -0.15)
        self.agent_trust[perceiver_id][emitter_id] = max(0.0, min(1.0, new_trust))

def interpret_signal(self, signal, perceiver_species, perceiver_id):
    trust = self.agent_trust[perceiver_id][signal.emitter_id]
    if trust < 0.2:
        return None  # don't trust this emitter
```

**8. Communication cost** — signaling takes energy:
```python
can_signal = self.energy > 15  # need energy to communicate
if can_signal:
    # emit signals
    self.energy -= 0.3  # cost per signal
```

### Agent integration

In `_social_tick()`:
1. Check `can_signal` (energy > 15)
2. Emit appropriate signals based on state (food, danger, warning, social, call, teaching)
3. Deception check for aggressive agents
4. Perceive nearby signals (range = 80 × sense_gene)
5. Interpret with trust filter
6. React: food→approach, danger→flee, social→approach, call→bond, warning→flee
7. Relay gossip (food 15%, danger 30%, warning 40%)
8. Reinforce vocabulary + update emitter trust

### 3-file wiring

1. `communication.py`: CommunicationSystem class
2. `simulation.py`: `self.communication = CommunicationSystem()` in `__init__`, `self.communication.tick()` in `_single_tick`, pass to agents via `agent._communication = self.communication`
3. `agent.py`: emit/perceive/interpret/reinforce/relay in `_social_tick()`, import `SIGNAL_RANGE_BASE`

### Renderer

- Active signal count in stats bar: `Signals: {self.sim.communication.active_count}`
- Ripple count: `Ripples: {self.sim.communication.ripple_count}`
- Visual: expanding translucent circles per signal emission, color-coded by type

### Performance optimization

ARISE with 120+ agents and 30+ subsystems hits ~989ms/tick without optimization. Target: <200ms/tick (~5 FPS). Key techniques:

1. **Spatial grid for O(n²) loops**: Communication perceive was 4239ms for 76 agents. With spatial grid (100px cells) + inline squared distance: 22ms (193× speedup). Pattern:
   ```python
   self._grid: dict[tuple, list] = {}
   def _grid_key(self, x, y): return (int(x/CELL_SIZE) % grid_w, int(y/CELL_SIZE) % grid_h)
   def _rebuild_grid(self): self._grid.clear(); [add each item to grid]
   def _get_nearby(self, x, y, radius): # check 3×3 grid cells around (x,y)
   ```

2. **Inline toroidal distance squared**: Avoid function call overhead + sqrt in hot loops:
   ```python
   dx = x2 - x1; dy = y2 - y1
   if dx > WORLD_WIDTH*0.5: dx -= WORLD_WIDTH
   elif dx < -WORLD_WIDTH*0.5: dx += WORLD_WIDTH
   # same for dy with WORLD_HEIGHT
   dist_sq = dx*dx + dy*dy  # compare with range², no sqrt needed
   ```

3. **Throttle expensive operations**: Weather every 3 ticks, migration every 5, flee every 2, brain learn every other tick. These don't need per-tick precision.

4. **Ring buffer instead of append/pop(0)**: `pop(0)` is O(n). Use ring buffer:
   ```python
   if len(trail) < max_trail: trail.append(item)
   else: trail[age % max_trail] = item  # O(1) overwrite
   ```

5. **No per-element Surface creation in renderer**: Creating `pygame.Surface((r*2, r*2), pygame.SRCALPHA)` per ripple/event is expensive. Draw directly on screen with dimmed color instead:
   ```python
   dim = alpha / 100
   dim_color = (int(color[0]*dim), int(color[1]*dim), int(color[2]*dim))
   pygame.draw.circle(self.screen, dim_color, (int(x), int(y)), radius, 2)
   ```

6. **Cap collection sizes**: Max 200 active signals, 50 ripples, 30 rendered ripples. Uncapped collections grow without bound.

7. **Module-level imports**: Never use `from .world import toroidal_distance` inside functions — Python treats it as a local variable, shadowing the module-level import and causing `UnboundLocalError` in other code paths.

### Pitfalls

1. **No local re-imports**: If `toroidal_distance` is imported at module level in `agent.py`, do NOT add `from .world import toroidal_distance` inside functions. Python treats the local import as a local variable, causing `UnboundLocalError` in other code paths. Same for `SocialEdge` — already defined in agent.py, don't self-import.

2. **Communication cost guard**: Always check `self.energy > 15` before emitting signals. Without this guard, signaling drains agents to death.

3. **Trust threshold**: `interpret_signal()` returns `None` for emitters with trust < 0.2. This means agents learn to ignore liars — but also means initial signals from unknown agents go through (trust defaults to 0.5).

4. **Relay intensity decay**: Relayed signals have `intensity * 0.7`, limiting chain length. Without this decay, signals would propagate infinitely.

5. **SocialEdge field names**: `SocialEdge` uses `target_id` (not `other_id`) and `trace` (not `weight`). Using wrong field names causes `TypeError` or `AttributeError`. Always check the dataclass definition before using:
   ```python
   SocialEdge(target_id=sig.emitter_id, trace=0.3)  # CORRECT
   SocialEdge(other_id=sig.emitter_id, weight=0.3)  # WRONG
   ```

6. **Probabilistic functions**: `is_old_age_death(age, modifier)` returns `True` ~50% of the time after max lifespan. Never `assert is_old_age_death(age, 1.0)` — it's random. Instead:
   ```python
   deaths = sum(1 for _ in range(100) if is_old_age_death(11000, 2.0))
   assert deaths > 0  # correct — probabilistic over many trials
   ```

7. **disease.infect() requires tick arg**: `self.disease.infect(agent.id, self.stats.tick)` — the `tick` parameter is mandatory. Forgetting it causes `TypeError: missing 1 required positional argument`.

8. **Never auto-launch the game**: User explicitly said "stop sending me into the app". NEVER run `python main.py` unless the user asks. Build/verify changes, then report results — don't launch.

### Save/load

CommunicationSystem is stateless (vocabularies reset on load). Just init in `save.py load()`:
```python
from .communication import CommunicationSystem
sim.communication = CommunicationSystem()
```

Must also add `from .weather import WeatherSystem` and `sim.weather = WeatherSystem()` if not already present — they're often added together.

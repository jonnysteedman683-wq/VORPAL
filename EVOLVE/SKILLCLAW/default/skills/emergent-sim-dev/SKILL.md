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

The full emergent-communication design — 6 signal types, vocabulary
convergence, all 8 features (ripples, gossip, dialect divergence, call
& response, teaching, deception, trust, cost), agent integration,
3-file wiring, renderer, communication pitfalls, and save/load — lives
in `references/communication-system.md`. Load it with
`skill_view(name, file_path)` when you work on communication,
`communication.py`, or `_social_tick()`.


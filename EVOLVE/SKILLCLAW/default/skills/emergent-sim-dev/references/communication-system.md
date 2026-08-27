# Emergent Communication System (full detail)

Species develop independent vocabularies through signal-response
reinforcement. 8 features: visual ripples, signal chains/gossip,
dialect divergence, call & response bonding, teaching, deception,
signal memory (trust), and communication cost.

## Architecture

## Signal types

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

## Vocabulary convergence

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

## 8 Features

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

## Agent integration

In `_social_tick()`:
1. Check `can_signal` (energy > 15)
2. Emit appropriate signals based on state (food, danger, warning, social, call, teaching)
3. Deception check for aggressive agents
4. Perceive nearby signals (range = 80 × sense_gene)
5. Interpret with trust filter
6. React: food→approach, danger→flee, social→approach, call→bond, warning→flee
7. Relay gossip (food 15%, danger 30%, warning 40%)
8. Reinforce vocabulary + update emitter trust

## 3-file wiring

1. `communication.py`: CommunicationSystem class
2. `simulation.py`: `self.communication = CommunicationSystem()` in `__init__`, `self.communication.tick()` in `_single_tick`, pass to agents via `agent._communication = self.communication`
3. `agent.py`: emit/perceive/interpret/reinforce/relay in `_social_tick()`, import `SIGNAL_RANGE_BASE`

## Renderer

- Active signal count in stats bar: `Signals: {self.sim.communication.active_count}`
- Ripple count: `Ripples: {self.sim.communication.ripple_count}`
- Visual: expanding translucent circles per signal emission, color-coded by type

## Performance optimization (communication-specific)

The O(n²) perceive loop is the classic bottleneck. See
`references/performance-optimization.md` for the spatial-grid pattern
(4239ms → 22ms, 193× speedup), inline toroidal distance squared,
throttling, and the ring buffer — the same patterns apply here.

## Pitfalls (communication-specific)

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

## Save/load

CommunicationSystem is stateless (vocabularies reset on load). Just init in `save.py load()`:
```python
from .communication import CommunicationSystem
sim.communication = CommunicationSystem()
```

Must also add `from .weather import WeatherSystem` and `sim.weather = WeatherSystem()` if not already present — they're often added together.

# Save/Subsystem Sync Checklist

Every time you add a new system to `Simulation.__init__`, you MUST update ALL of these locations. Missing any one causes a crash on load.

## Locations to update

1. **`simulation.py` `__init__`** — where the system is created
2. **`save.py` `load()`** — must initialize the same system (even if empty)
   - **CRITICAL**: Also add the import line! `from .module import ClassName` at the top of `load()`.
   - Missing the import causes `NameError: name 'WeatherSystem' is not defined`
   - The init line `sim.weather = WeatherSystem()` is useless without the import above it
3. **`save.py` `_serialize_agent`** — if the system has per-agent state
4. **`save.py` `_deserialize_agent`** — restore per-agent state
5. **`simulation.py` `_single_tick`** — pass system reference to agents (`agent._system = self.system`)
6. **`simulation.py` `_single_tick`** — call `self.system.tick(alive_ids)` in the tick loop
7. **`simulation.py` newborn handling** — record births if needed
8. **`simulation.py` death handling** — record deaths if needed

## Complete subsystem inventory (as of 2026-07-30, 22 systems)

```python
# In save.py load(), ALL of these must be initialized:
sim.lineage = LineageTree()
sim.resources = ResourceWorld(C.WORLD_WIDTH, C.WORLD_HEIGHT, terrain=sim.world.terrain)
sim.territory = TerritoryMap(C.WORLD_WIDTH, C.WORLD_HEIGHT)
sim.signals = SignalField()
sim.culture = CultureSystem()
sim.conflict = ConflictSystem()
sim.trade_routes = TradeRouteSystem()
sim.technology = TechnologySystem()
sim.architecture = ArchitectureSystem()
sim.language = LanguageSystem()
sim.species = SpeciesSystem()
sim.species.initialize(C.WORLD_WIDTH, C.WORLD_HEIGHT)
sim.leadership = LeadershipSystem()
sim.disease = DiseaseSystem()
sim.parasites = ParasiteSystem()
sim.symbiosis = SymbiosisSystem()
sim.predator_prey = PredatorPreySystem()
sim.evolution = EvolutionSystem()
sim.weather = WeatherSystem()        # must import: from .weather import WeatherSystem
sim.communication = CommunicationSystem()  # must import: from .communication import CommunicationSystem
sim.personality = PersonalitySystem()  # must import: from .personality import PersonalitySystem
```

## Per-agent state to persist

```python
# In _serialize_agent, add:
"genome": agent.genome.genes if hasattr(agent, 'genome') else {},

# In _deserialize_agent, add:
genome=Genome(genes=data.get("genome", {})) if data.get("genome") else Genome(),
```

## Imports in save.py load()

Always check that load() has ALL needed imports. Common pattern: adding `sim.weather = WeatherSystem()` without `from .weather import WeatherSystem` causes `NameError`. The init line is useless without the import above it.

```python
# These imports go INSIDE load() (local imports to avoid circular deps):
from .biology import DiseaseSystem, ParasiteSystem, SymbiosisSystem
from .predator import PredatorPreySystem
from .evolution import EvolutionSystem
from .communication import CommunicationSystem
from .weather import WeatherSystem
from .personality import PersonalitySystem
from .genetics import Genome
```

## Quick grep to verify sync

```bash
# Find all systems in simulation.py __init__
grep "self\.[a-z_]* = " simulation.py | grep -v "self\.agents\|self\.world\|self\.stats\|self\.paused\|self\.speed"

# Find all systems in save.py load()
grep "sim\.[a-z_]* = " save.py

# Compare — anything in sim.py but not save.py will crash on load
```

## Common error pattern

```
AttributeError: 'Simulation' object has no attribute 'disease'
```

This means you added `self.disease = DiseaseSystem()` to simulation.py but forgot to add `sim.disease = DiseaseSystem()` to save.py's `load()` function.

## Additional pitfall: method signatures

When changing method signatures (e.g. adding `tick` arg to `disease.infect()`),
grep ALL call sites:
```bash
grep -rn "disease.infect(" arise/
```
Missing argument changes break saves AND runtime.

## Brain resize on state dim change

When BRAIN_INPUTS changes (e.g. 10→14), old saves have wrong-sized brain weights.
Add resize helpers and apply in all deserialization paths:

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

Apply in 3 places:
1. Hybrid brain: `_resize_qnet()` for QNetwork.fc1, `_resize_icm()` for encoder
2. Standalone brain: same resize on q_online.fc1 and icm.encoder
3. HebbNet: resize hidden.weight (input dim = state_dim)

Check: `if saved_dim != C.BRAIN_INPUTS: q_online = _resize_qnet(q_online, saved_dim, C.BRAIN_INPUTS)`

## HebbNet @property epsilon bug

HebbNet had `@property epsilon` returning 0.0 that blocked `self.epsilon = 0.3` assignment.
This caused `AttributeError: property 'epsilon' of 'HebbNet' object has no setter`.

Fix: Remove the `@property epsilon` method AND add epsilon-greedy to `think()`:
```python
# REMOVE this:
@property
def epsilon(self):
    return 0.0

# ADD this to think():
if not hasattr(self, 'epsilon'):
    self.epsilon = 0.3
if np.random.random() < self.epsilon:
    return np.random.randint(logits.shape[1])
self.epsilon = max(0.05, self.epsilon * 0.9999)
```

Without this fix, HebbNet agents NEVER explore — always pick argmax. This caused 0 reproduction across 500 ticks because ACT_REPRODUCE was never selected.

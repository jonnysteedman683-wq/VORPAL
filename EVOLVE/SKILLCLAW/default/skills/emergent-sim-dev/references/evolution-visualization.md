# Evolution Visualization Pattern

When adding evolution tracking, create `evolution.py` with three components:

## 1. FamilyTree
Tracks ancestry across all generations.

```python
@dataclass
class TreeNode:
    agent_id: int
    parent_id: int = None
    species: str = "unknown"
    brain_type: str = "qnet"
    generation: int = 0
    birth_tick: int = 0
    death_tick: int = None
    fitness: float = 0.0
    children: list = field(default_factory=list)

class FamilyTree:
    def add_agent(self, agent_id, parent_id=None, species="unknown", ...)
    def record_death(self, agent_id, death_tick, fitness=0.0)
    def get_ancestry(self, agent_id, depth=5) -> list[TreeNode]
    def get_descendants(self, agent_id, depth=3) -> list[TreeNode]
```

## 2. SpeciationTracker
Detects population divergence by monitoring trait variance within species.

```python
class SpeciationTracker:
    def snapshot_traits(self, agents, species_system, tick, interval=100)
    def detect_speciation(self, agents, species_system, tick) -> list[SpeciationEvent]
```

Detection: if combat skill std > 2.5 within a species, flag speciation.

## 3. GeneticDriftTracker
Records trait averages per generation for drift visualization.

```python
class GeneticDriftTracker:
    def record_generation(self, agents, generation)
    def get_drift_data(self, trait_name) -> list[tuple[int, float]]
```

Tracked traits: speed, power, hunger, energy, combat, farming, scouting.

## Integration
- Record births in `simulation.py` when agents spawn
- Record deaths when agents die
- Call `evolution.tick()` every tick for speciation/drift updates
- Add evolution stats to renderer sidebar (family tree size, max gen, speciation events)
- Draw genetic drift mini-chart (combat skill over generations)

## UI Panel
```python
# In renderer _draw_politics_panel:
evo = self.sim.evolution
lines = [
    f"Family tree: {evo.family_tree.total_agents} total",
    f"Max gen: {evo.family_tree.max_generation}",
    f"Speciation events: {evo.speciation.total_events}",
    f"Drift tracked: {evo.genetic_drift.tracked_generations} gens",
]
# Draw drift mini-chart
drift_data = evo.genetic_drift.get_drift_data("combat")
# plot as line chart in 200x40 pixel area
```

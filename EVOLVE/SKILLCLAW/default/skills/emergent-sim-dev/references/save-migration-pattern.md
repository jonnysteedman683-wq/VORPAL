# Save Migration Pattern for Evolving Action Spaces

When a simulation adds new agent actions (e.g., going from 7 to 10 actions), old saves break because neural network output layers have fixed dimensions.

## The Problem
- `QNetwork.out` has shape `(hidden_dim, old_n_actions)` — mismatch with new `N_ACTIONS`
- `ICM` uses one-hot encoding sized to `old_n_actions` — index out of bounds
- `HebbNet.DeltaReadout` has weight matrix `(old_n_actions, hidden_dim)` — shape mismatch

## The Fix (in `save.py` `_deserialize_agent`)

### For QNet brains:
```python
brain = Brain(state_dim=..., q_net=q_online, icm=icm, ...)
# Check output layer dimension
if brain.q_online.out.out_dim != Brain.N_ACTIONS:
    # Reinitialize with current action count (loses trained weights)
    brain = Brain(state_dim=..., epsilon=..., lr=..., gamma=...)
# Check ICM separately (it has its own n_actions)
if brain.icm.n_actions != Brain.N_ACTIONS:
    brain.icm = ICM(state_dim, Brain.N_ACTIONS, lr)
```

### For HebbNet brains:
```python
# On deserialization, always use current N_ACTIONS
brain.n_actions = Brain.N_ACTIONS  # not brain_data["n_actions"]

# Check readout dimension
saved_n = len(brain_data["readout_bias"])
if saved_n != Brain.N_ACTIONS:
    brain.readout.weight = np.zeros((Brain.N_ACTIONS, hidden_dim), dtype=np.float32)
    brain.readout.bias = np.zeros(Brain.N_ACTIONS, dtype=np.float32)
else:
    brain.readout.weight = np.array(brain_data["readout_weight"])
    brain.readout.bias = np.array(brain_data["readout_bias"])
```

### For Hybrid brains:
```python
# Hybrid has both qnet and hebbnet sub-components
# Deserialize qnet part with same migration logic as QNet brains
# Deserialize hebbnet part with same migration logic as HebbNet brains
# Then combine:
brain = HybridBrain(qnet=qnet_brain, hebbnet=hebbnet, blend=brain_data.get("blend", 0.5))
```

### Key insight:
- Hidden layers (fc1, fc2, encoder) transfer fine across action count changes
- Only output-facing layers need reinitialization
- The agent loses some learned behavior but keeps its internal representations
- Evolution will re-learn the new actions quickly

## Prevention
When designing the save format, always include `n_actions` in the brain metadata so you can detect mismatches on load.

## New Brain Type Serialization
When adding a new brain type (e.g., HybridBrain), add a `"type"` field to the brain serialization:
```python
data["brain"] = {"type": "hybrid", "blend": 0.5, "qnet": {...}, "hebbnet": {...}}
```
On deserialization, check `brain_data.get("type")` first to dispatch to the right handler.

## New Subsystem Migration
When adding new subsystems (species, leadership, etc.), the `load()` function must:
1. Init ALL subsystems with defaults (even if save predates them)
2. Restore per-agent data from saved JSON (species, protection status, skills)
3. Rebuild lineage from loaded agents

```python
def load(path):
    sim = Simulation.__new__(Simulation)
    # ALWAYS init all subsystems — missing ANY ONE causes AttributeError on load
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

    # Then load agents and restore their per-agent state
    for agent in sim.agents:
        # Restore species (read from saved agent JSON)
        sim.species.agent_species[agent.id] = saved_species
        sim.species.species_counts[saved_species] += 1
```

**IMPORTANT**: When removing a field from a system (e.g. `agent_protected` from SpeciesSystem), grep ALL files for references before committing. `save.py` is the #1 culprit — both `_serialize_agent` and `load()` may reference it. Pattern: `grep -rn "field_name" arise/`

## New Agent Fields
When adding fields to Agent dataclass (core_stats, skills, trail, leader_target):
- Use `data.get("field", default)` for backward compat
- Use `field(default_factory=...)` in dataclass for new instances
- Test: load an old save, verify no crashes, verify new fields have defaults

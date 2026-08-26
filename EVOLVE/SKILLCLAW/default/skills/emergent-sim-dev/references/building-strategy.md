# Building Strategy: Resource Chains, Weather Defense, Settlements

## Resource Chain Design

Buildings amplify nearby complementary buildings. The key insight: buildings should NEED each other for maximum effect, creating strategic depth.

### Chain pairs and bonuses

| Pair | Bonus | Range | Logic |
|------|-------|-------|-------|
| farm + granary | farm 2.0x, granary 1.5x | 60px | Food production + storage |
| farm + workshop | workshop 1.5x | 60px | Raw materials + crafting |
| shelter + housing | shelter 1.5x, housing 1.3x | 50px | Rest + living quarters |
| hospital + housing | hospital 1.5x | 50px | Healing + safe recovery |
| temple + housing | temple 1.5x | 55px | Culture + community |
| wall + tower | wall 1.5x, tower 1.3x | 50px | Defense + detection |

### Implementation pattern

```python
def _get_chain_multiplier(self, structure: Structure) -> float:
    mult = 1.0
    for s in self.structures.values():
        if not s.active or s.id == structure.id:
            continue
        d = toroidal_distance(structure.x, structure.y, s.x, s.y)
        pair = tuple(sorted([structure.structure_type, s.structure_type]))
        if pair in RESOURCE_CHAINS:
            chain = RESOURCE_CHAINS[pair]
            if d < chain.get("range", 50):
                key = f"{structure.structure_type}_bonus"
                if key in chain:
                    mult *= chain[key]
    return mult
```

Each `get_*_bonus()` method multiplies by chain multiplier:
```python
def get_food_gen_bonus(self, x, y) -> float:
    bonus = 0
    for s in self.structures.values():
        if s.active and s.structure_type == "farm":
            chain_mult = self._get_chain_multiplier(s)
            bonus += s.effect_at(x, y) * STRUCTURE_TYPES["farm"]["value"] * chain_mult
    return bonus
```

## Weather Defense

Buildings counter weather events. Without this, weather is just random punishment.

| Building | Weather Countered | Effect |
|----------|------------------|--------|
| Shelter | Storm | Blocks 80% damage |
| Granary | Drought | Buffers 50% food loss |
| Hospital | Plague | Resists 60% spread |

### Simulation integration

```python
# In _single_tick, after weather effects:
storm_dmg = self.weather.get_storm_damage(agent.x, agent.y)
if storm_dmg > 0:
    storm_protection = self.architecture.get_storm_protection(agent.x, agent.y)
    storm_dmg *= (1.0 - storm_protection)
    agent.hunger = min(100, agent.hunger + storm_dmg)
```

## Settlement System

Settlements auto-form from building clusters. No manual creation needed.

### Detection algorithm
1. Find all structures not yet in a settlement
2. BFS from each unassigned structure to find connected clusters within 80px
3. Require 3+ buildings of 2+ types
4. Merge into existing settlements if within 120px
5. Track center position (mean of structure positions)

### Settlement tiers
- Village: 3+ structures
- Town: 5+ structures  
- City: 8+ structures

### Agent building AI

Agents build chains based on what they already own:
```python
my_types = set(s.structure_type for s in my_buildings)
if "farm" in my_types and "granary" not in my_types:
    return "granary"
if "shelter" in my_types and "housing" not in my_types:
    return "housing"
```

Role-based fallback when no chain opportunity:
- Farmer → farm, Warrior → wall, Scout → beacon
- Builder → workshop, Medic → hospital, Diplomat → temple

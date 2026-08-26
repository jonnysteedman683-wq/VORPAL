# Migration + Roles Integration Pattern

## Migration System

Migration makes agents drift toward seasonally preferred biomes. Three files must agree:

### biology.py
```python
SEASON_LENGTH = 400
SPECIES_BIOME_PREFS = {
    "red":   {0: [5, 2],    1: [5, 7, 2],  2: [5, 2],    3: [2, 5]},    # highlands/desert
    "green": {0: [3, 4, 2], 1: [3, 4, 5],  2: [3, 4, 2], 3: [2, 3]},    # forest/jungle
    "blue":  {0: [1, 2, 3], 1: [2, 3, 1],  2: [1, 2],    3: [1, 2]},    # shallows/plains
}

def migration_bias(x, y, terrain, tick, species=None):
    preferred = get_preferred_biomes(tick, species)
    if terrain.biome_at(x, y) in preferred:
        return 0.0, 0.0  # already in preferred biome
    # sample 12 nearby points, bias toward preferred + passable
    ...
```

### simulation.py (_single_tick)
```python
# after speed/power bonuses, before leader bonuses:
if self.world.terrain:
    sp = self.species.get_species(agent.id)
    mx, my = migration_bias(agent.x, agent.y, self.world.terrain, self.stats.tick, sp)
    agent._migration_mx = mx
    agent._migration_my = my
    current_biome = self.world.terrain.biome_at(agent.x, agent.y)
    preferred = get_preferred_biomes(self.stats.tick, sp)
    if current_biome in preferred:
        agent._speed_mult = min(2.0, agent._speed_mult + 0.15)
```

### agent.py (ACT_MOVE_RANDOM handler)
```python
elif action == Brain.ACT_MOVE_RANDOM:
    angle = np.random.uniform(0, 2 * math.pi)
    mx = getattr(self, '_migration_mx', 0.0)
    my = getattr(self, '_migration_my', 0.0)
    dx = math.cos(angle) * C.AGENT_MAX_SPEED + mx
    dy = math.sin(angle) * C.AGENT_MAX_SPEED + my
    self.x = wrap_x(self.x + dx)
    self.y = wrap_y(self.y + dy)
```

## Agent Roles System

Roles auto-assigned from dominant skill every 100 ticks.

### roles.py
- `Role` enum: FARMER, WARRIOR, SCOUT, BUILDER, MEDIC, DIPLOMAT
- `ROLE_SKILL_MAP`: maps Role → skill name
- `ROLE_BONUSES`: maps Role → dict of bonus_name → value
- `assign_role(skills)`: returns Role based on highest skill level
- `get_role_bonus(role, bonus_name)`: returns float bonus

### Integration
- Add `role: int = 0` field to Agent dataclass
- In simulation tick: `agent.role = assign_role(agent.skills).value`
- Apply bonuses: speed (scout), power (warrior), hunger (farmer), build cost (builder)
- In agent actions: farmer bonus to foraging, builder bonus to build cost
- Stats bar: `role_str = " ".join(f"{k[:3]}:{v}" for k, v in sorted(role_counts.items()))`

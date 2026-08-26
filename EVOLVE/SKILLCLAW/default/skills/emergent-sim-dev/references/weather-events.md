# Weather & Map Events — Integration Pattern

## Module structure (`weather.py`)

```python
class EventType(IntEnum):
    STORM = 0       # local: damages + slows movement
    DROUGHT = 1     # global: food regrows 50% slower
    PLAGUE = 2      # global: extra disease spread chance
    RESOURCE_BOOM = 3  # local: double food in region
    FLOOD = 4       # local: shallow water expands

@dataclass
class ActiveEvent:
    event_type: EventType
    start_tick: int
    duration: int
    center_x: float = 0.0   # for localized events
    center_y: float = 0.0
    radius: float = 0.0     # 0 = global event
    intensity: float = 1.0
```

## Integration into simulation.py

```python
# In __init__:
self.weather = WeatherSystem()

# In _single_tick (after evolution.tick):
self.weather.tick(self.stats.tick, self.world.terrain)

# Per-agent effects (in the aging/role bonuses block):
storm_dmg = self.weather.get_storm_damage(agent.x, agent.y)
if storm_dmg > 0:
    agent.hunger = min(100, agent.hunger + storm_dmg)
    agent._speed_mult = max(0.3, agent._speed_mult - 0.3)

flood_depth = self.weather.get_flood_depth(agent.x, agent.y, self.world.terrain)
if flood_depth > 0.3:
    agent._speed_mult = max(0.2, agent._speed_mult - flood_depth * 0.5)
    if flood_depth > 0.7:
        agent.hunger = min(100, agent.hunger + 0.05)

plague_chance = self.weather.get_plague_chance()
if plague_chance > 0 and np.random.random() < plague_chance:
    if not self.disease.is_sick(agent.id):
        self.disease.infect(agent.id)
```

## Integration into renderer.py

Stats bar:
```python
f"Weather: {self._weather_str()}",

def _weather_str(self) -> str:
    events = self.sim.weather.active_events
    if not events:
        return "Clear"
    parts = []
    for e in events:
        progress = int(e.progress(self.sim.stats.tick) * 100)
        parts.append(f"{e.name}({progress}%)")
    return " ".join(parts)
```

Map overlay — draw DIRECTLY on screen (no per-event Surface creation for perf):
```python
for event in self.sim.weather.active_events:
    if event.radius > 0:
        color = EVENT_COLORS.get(event.event_type, (100, 100, 100))
        ex, ey = int(event.center_x), int(event.center_y)
        r = int(event.radius)
        alpha = int(30 * event.intensity)
        dim = alpha / 100
        dim_color = (int(color[0]*dim), int(color[1]*dim), int(color[2]*dim))
        pygame.draw.circle(self.screen, dim_color, (ex, ey), r)
        pygame.draw.circle(self.screen, color, (ex, ey), r, 2)
        lbl = self.font_big.render(event.name, True, color)
        self.screen.blit(lbl, (ex - lbl.get_width()//2, ey - r - 14))
```

## Building defense integration

Weather effects should be reduced by nearby buildings:
```python
storm_dmg = self.weather.get_storm_damage(agent.x, agent.y)
if storm_dmg > 0:
    storm_protection = self.architecture.get_storm_protection(agent.x, agent.y)
    storm_dmg *= (1.0 - storm_protection)
    agent.hunger = min(100, agent.hunger + storm_dmg)

plague_chance = self.weather.get_plague_chance()
if plague_chance > 0:
    plague_resist = self.architecture.get_plague_resistance(agent.x, agent.y)
    gene_resist = getattr(agent, '_resistance', 0.5)  # from genetics
    if np.random.random() < plague_chance * (1.0 - plague_resist) * (1.0 - gene_resist):
        if not self.disease.is_sick(agent.id):
            self.disease.infect(agent.id, self.stats.tick)  # tick arg required!
```

## Performance: throttle weather checks

Weather checks every tick for 120 agents is expensive. Throttle to every 3 ticks:
```python
if self.stats.tick % 3 == 0:
    storm_dmg = self.weather.get_storm_damage(agent.x, agent.y)
    # ... flood, plague, drought checks
```

## Save/load

Weather state is ephemeral — no need to save. Events re-trigger naturally.

## Season-based probability tuning

- Spring: storms 8%, resource boom 10%, flood 6%
- Summer: drought 10%, resource boom 8%
- Autumn: storms 12%, plague 6%, flood 8%
- Winter: storms 15%, plague 8%, flood 10%

Drought and plague are GLOBAL (affect entire map). Storm, boom, flood are LOCAL (specific region).

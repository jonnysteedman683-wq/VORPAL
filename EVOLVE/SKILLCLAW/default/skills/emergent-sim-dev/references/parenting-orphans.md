# Parenting & Orphan System

## Parent behavior

When an agent reproduces, it registers the child and directs it:

```python
# In _try_reproduce(), AFTER newborn = Agent(...):
self.children_ids.append(newborn.id)
newborn.leader_id = self.id
newborn.hunger = max(0, newborn.hunger - 20)  # share food at birth
```

### Feed children (in _social_tick)
Parents feed hungry children every 3 ticks:
```python
if self.children_ids and self.hunger < 40 and self.age % 3 == 0:
    for other in agents:
        if other.id in self.children_ids and other.alive:
            d = toroidal_distance(self.x, self.y, other.x, other.y)
            if d < 40 and other.hunger > 30:
                transfer = min(15, self.hunger)
                self.hunger += transfer
                other.hunger = max(0, other.hunger - transfer)
                # direct child toward tasks
                task, t_dist, _ = world.nearest_task(other.x, other.y)
                if task and t_dist < 100:
                    other.leader_target = (task.x, task.y)
                    other.leader_id = self.id
                break
```

### Orphan behavior
When a parent dies, children seek cross-species partners:
```python
# In simulation.py, when agent dies:
if is_old_age_death(agent.age, ...):
    agent.alive = False
    for other in self.alive_agents:
        if other.parent_id == agent.id:
            other._parent_alive = False

# In agent._social_tick(), every 50 ticks:
if (self.parent_id is not None and self.age % 50 == 0
    and not getattr(self, '_parent_alive', True)):
    for other in agents:
        if other.id == self.id or not other.alive:
            continue
        other_sp = other._species.get_species(other.id) or "unknown"
        if other_sp != sp and other_sp != "unknown":
            d = dx*dx + dy*dy
            if d < 3600:  # within 60px
                self.leader_id = other.id
                self.leader_target = (other.x, other.y)
                break
```

## Save/load

`children_ids` must be persisted:
```python
# In save.py serialize:
"children_ids": agent.children_ids,
# In save.py deserialize:
children_ids=data.get("children_ids", []),
```

## Pitfalls

1. **Never reference `newborn` before `newborn = Agent(...)`**: Common bug — adding `self.children_ids.append(newborn.id)` above the Agent constructor call. Put ALL post-birth logic AFTER creating the newborn.

2. **Performance**: The orphan check `not any(a.id == self.parent_id and a.alive for a in agents)` is O(n). Use `_parent_alive` flag instead, set in simulation tick when parent dies.

3. **children_ids is a list, not a set**: Use `other.id in self.children_ids` for lookup. With small agent counts this is fine; convert to set if counts grow large.

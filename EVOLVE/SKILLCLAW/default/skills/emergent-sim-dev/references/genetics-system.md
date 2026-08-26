# Genetics System Pattern

Heritable traits with mutation, crossover, and species-specific initialization. 16 genes total.

## Genome Structure (16 genes)

```python
GENE_NAMES = [
    "speed", "size", "sense", "metabolism",
    "fertility", "longevity", "aggression", "sociability",
    "camouflage", "resistance", "fat_storage", "curiosity",
    "cooperation", "stress_tolerance", "regeneration", "color_vivid"
]
```

Gene ranges: physical (0.5-2.0), behavioral (0.0-1.0). Mutation rates: 0.07-0.15 per gene.

## Mutation

Gaussian noise + rare large mutations (3% chance of ±0.3 jump). Rate decreases with generation:

```python
gen_factor = max(0.6, 1.0 - generation * 0.001)
delta = np.random.normal(0, rate * gen_factor)
if np.random.random() < 0.03:
    delta += np.random.uniform(-0.3, 0.3)  # rare large mutation
```

## Crossover (sexual reproduction)

50/50 pick + blending (0-30%) + 5% transgressive segregation:

```python
blend = np.random.uniform(0.0, 0.3)
child = value * (1 - blend) + parent_avg * blend
if np.random.random() < 0.05:  # transgressive — beyond parent range
    lo, hi = GENE_RANGES.get(gene_name, (0.0, 2.0))
    child = np.random.uniform(lo, hi)
```

## Species Initialization (randomized within species)

Species traits use `np.random.uniform()` for diversity within species:

```python
def create_initial_genome(species):
    genome = Genome.random()  # wide range: 60-95% of gene range
    if species == "red":
        genome.set("speed", genome.get("speed") * np.random.uniform(1.0, 1.4))
        genome.set("aggression", min(1.0, genome.get("aggression") + np.random.uniform(0.0, 0.3)))
    elif species == "green":
        genome.set("metabolism", genome.get("metabolism") * np.random.uniform(0.7, 1.0))
        genome.set("resistance", min(1.0, genome.get("resistance") + np.random.uniform(0.0, 0.25)))
    elif species == "blue":
        genome.set("cooperation", min(1.0, genome.get("cooperation") + np.random.uniform(0.0, 0.3)))
        genome.set("regeneration", genome.get("regeneration") * np.random.uniform(1.0, 1.4))
    return genome
```

## Gene Effects on Behavior

Applied in simulation tick — each gene affects specific mechanics:

```python
# Physical
agent._speed_mult *= genome.get("speed")
agent._power_mult *= (0.5 + genome.get("size") * 0.5)
agent._hunger_mult *= genome.get("metabolism") * genome.get("size")
agent._hunger_mult *= (0.8 + genome.get("fat_storage") * 0.2)

# Survival
agent._speed_mult *= (0.8 + genome.get("stress_tolerance") * 0.2)
agent.energy = min(MAX_ENERGY, agent.energy + genome.get("regeneration") * 0.01)
agent._camouflage = genome.get("camouflage")  # predator detection resistance
agent._resistance = genome.get("resistance")  # disease/parasite resistance

# Social
agent._curiosity_bonus = genome.get("curiosity") * 0.5  # ICM bonus
agent._cooperation = genome.get("cooperation")  # food sharing
agent._vivid = genome.get("color_vivid")  # visual brightness
```

## Color Visualization

11 gene color shifts for visual diversity:

```python
GENE_COLOR_SHIFT = {
    "speed": (0.2, 0.0, 0.0),      "size": (0.0, 0.2, 0.0),
    "sense": (0.0, 0.0, 0.2),      "aggression": (0.3, 0.0, 0.0),
    "sociability": (0.0, 0.0, 0.3), "camouflage": (0.0, 0.15, 0.15),
    "resistance": (0.0, 0.25, 0.0), "curiosity": (0.15, 0.0, 0.15),
    "cooperation": (0.0, 0.1, 0.2), "color_vivid": (0.15, 0.15, 0.0),
}
```

## 3-File Integration

1. `genetics.py` — Genome class, create_initial_genome(), crossover_and_mutate()
2. `simulation.py` — give initial agents species genomes, apply gene effects in tick
3. `agent.py` — genome field, inherit in _try_reproduce(), pass to Agent constructor

## Hybrid Genome Improvements

When creating hybrid offspring (QNet × HebbNet):
- Use `crossover_and_mutate(parent1_genome, parent2_genome, generation)` instead of just mutating one parent
- Apply 2× longevity bonus: `child_genome.set("longevity", child_genome.get("longevity") * 2.0)`
- This creates hybrid vigor — long-lived agents spread mixed genes further into the pool
- Hybrids also get random genome between both ancestors (crossover), not just one parent mutated

## Longevity Gene → Aging

The longevity gene directly affects max lifespan via `is_old_age_death()`:

```python
# biology.py
def is_old_age_death(age: int, longevity_modifier: float = 1.0) -> bool:
    effective_max = MAX_LIFESPAN * longevity_modifier  # 5000 * modifier
    if age < effective_max:
        return False
    return np.random.random() < 0.5

# simulation.py
if is_old_age_death(agent.age, agent.genome.get("longevity")):
    agent.alive = False
```

With longevity=2.0 (hybrids), agents live to ~15000 ticks instead of ~7500 (MAX_LIFESPAN=7500, AGING_START=3000).

## Save/Load

```python
# serialize
"genome": agent.genome.genes

# deserialize
genome=Genome(genes=data.get("genome", {})) if data.get("genome") else Genome()
```

## Renderer Integration

- Agent inspection: show gene values (spd, sz, met, agr)
- Population overview: average gene values across alive agents
- Agent colors: genome shifts species base color

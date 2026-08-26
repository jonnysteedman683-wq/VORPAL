# Economy Tuning History — ARISE

Real iteration history showing what broke and what worked.

## Iteration 1: Too Harsh
```
HUNGER_PER_TICK = 0.08
FOOD_COST = 5
REPRODUCE_CURRENCY = 10
TASK_BASE_SUCCESS = 0.3
```
**Result**: Population crashed to 3, then jumped to 17 (auto-reseed). Repeated cycle.

## Iteration 2: Gentler
```
HUNGER_PER_TICK = 0.03
FOOD_COST = 3
REPRODUCE_CURRENCY = 5
TASK_BASE_SUCCESS = 0.5
```
**Result**: Population held at 30-50. Stable but no growth.

## Iteration 3: Comfortable (Final)
```
HUNGER_PER_TICK = 0.015
FOOD_COST = 2
REPRODUCE_CURRENCY = 3
TASK_BASE_SUCCESS = 0.65
REPRODUCE_HUNGER = 10
REPRODUCE_ENERGY = 15
ENERGY_REGEN = 0.12
FOOD_HUNGER_RESTORE = 60
```
**Result**: Population grows from 80 to 120+. Stable growth, no crashes.

## Biology Tuning
- Disease spread: 0.05 → 0.02 (too many sick agents crashed population)
- Disease damage: 0.15 → 0.08
- Parasite drain: 0.1 → 0.05
- Parasite spread: 0.03 → 0.01

## Reseed Threshold
- Started at 3 agents → too aggressive (jumped to 17)
- Moved to 5 → still jumpy
- Moved to 15 → better
- Settled on 20 with 20 reseed count → smooth recovery

## Key Lesson
**Start generous, dial back.** It's much easier to make the game harder than to debug population crashes. The user will notice starvation immediately but won't notice if agents are "too comfortable" for a while.

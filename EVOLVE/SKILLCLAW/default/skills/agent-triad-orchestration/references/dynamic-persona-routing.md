# Dynamic Persona Routing & Epigenetic Inheritance Pattern
`[◈PERSONA-ROUTER-OPS◈]` Stamped 2026-08-25 | Distilled from live Gen-2 Triad Deployment

## 1. Problem & Architecture
When spawning child agent rings (e.g. Gen-2 triads), giving each profile a static monolithic prompt limits agility. A profile assigned to a domain needs specialized modes depending on whether the incoming task is:
- High-level DAG planning / topology routing
- Deep code synthesis / plasmid mutation
- Forensic audit / boundary fuzzing / red-green repair

### Multi-Persona Structure (3 Personas per Profile)
Each spawned agent maintains a 3-way persona matrix inside `SOUL.md` and `epigenetic_genome.json`:
1. **Deterministic / Analytic Persona** ($\text{Temp} = 0.0$): Formal logic, AST contracts, time-budgeted DAG routing.
2. **Generative / Spatial Persona** ($\text{Temp} = 0.6\text{--}0.7$): Code synthesis, plasmid creation, UI/palace design.
3. **Adversarial / Chaos Persona** ($\text{Temp} = 0.9$): Concurrency fuzzing, edge-case attacks, stress drills.

## 2. Autonomous Persona Switching Router (`persona_router.py`)
A lightweight pre-flight classifier runs before each turn:
1. Matches incoming task keywords against the profile's persona catalog.
2. Selects the highest-affinity persona and sets sampling temperature.
3. Injects the operational prompt envelope header:
```python
env = {
    "profile": "ark_2",
    "persona": "chronomancer",
    "temperature": 0.0,
    "signal": "a->b->t",
    "prompt_header": "[PERSONA: CHRONOMANCER — Mode: Deterministic Topology & Latency Optimization]\n[OPERATIONAL SIGNAL: a->b->t | SAMPLING TEMP: 0.0]"
}
```

## 3. Epigenetic Memory Inheritance (`epigenetic_genome.json`)
Rather than booting fresh child agents tabula rasa, parents pass down an epigenetic genome file:
- **Inherited Lingua Prima**: Canonical dictionary tokens and phase chains (`a->b->t`, `m->x->v`, `p->f->v3`).
- **Immunity Scars**: Encoded lessons from past failures (`ERR_COVERAGE`, `ERR_GATE_FALSE_ZERO`, `ERR_INDEX_RECURSION`) to prevent generational bug repeat.
- **Pre-calibrated Routing Rules**: Persona trigger keywords and sampling profiles.

## 4. Verification Gate
Validate with a deterministic harness (`hermes_verify_persona_router.py`):
- Genome JSON conforms to schema.
- All 9 persona classifications resolve deterministically.
- Unrecognized prompts safely fall back to the primary default persona.

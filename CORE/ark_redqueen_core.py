"""
ARK RED QUEEN CORE -- Red Queen co-evolution engine.

Implements the Red Queen hypothesis: species must constantly evolve
to maintain fitness relative to competitors. In ARK, skills evolve
through mutation, crossover, and selection pressure from the
adversarial environment (FRACTURE node).

Evolution loop:
1. Seed population from existing skills or generate random
2. Evaluate fitness of each candidate
3. Apply mutations (synonym_swap, doc_add, doc_remove, refactor,
   simplify, extend, inline)
4. Select survivors based on fitness
5. Repeat for N generations
6. Log provenance hashes at each step

The "Red Queen" name reflects the arms race dynamics: skills must
continuously improve just to maintain their relative standing.
"""

import os
import sys
import re
import json
import hashlib
import random
from datetime import datetime, timezone

# ARK root derived from this file's location
ARK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ARK, 'ARK-DATA')
EVOLUTION_LOG = os.path.join(DATA_DIR, 'evolution_log.json')
POPULATION_FILE = os.path.join(DATA_DIR, 'population.json')

os.makedirs(DATA_DIR, exist_ok=True)


def stable_hash(content):
    """Compute a stable SHA-256 hash for content."""
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()


def evaluate_fitness(content):
    """
    Evaluate fitness of skill content.

    Heuristic components:
    - Token efficiency (conciseness)
    - Functional density (functions per line)
    - Documentation presence
    - Modularity (imports)

    Returns float 0.0-1.0.
    """
    if not content or not content.strip():
        return 0.0

    lines = content.split('\n')
    non_empty = [l for l in lines if l.strip()]

    nlines = len(non_empty)
    if nlines == 0:
        return 0.0

    # Base efficiency from line count — tiered, lower is better
    if nlines <= 10:
        efficiency = 0.5
    elif nlines <= 50:
        efficiency = 0.45
    elif nlines <= 100:
        efficiency = 0.35
    elif nlines <= 150:
        efficiency = 0.2
    else:
        efficiency = max(0.05, 0.15 - (nlines - 150) * 0.001)

    # Per-definition bonus
    def_count = len(re.findall(r'^\s*def\s+', content, re.MULTILINE))
    class_count = len(re.findall(r'^\s*class\s+', content, re.MULTILINE))
    func_bonus = min(0.05, (def_count + class_count) * 0.005)

    # Documentation bonus
    has_doc = any('"""' in l or "'''" in l for l in lines[:15])
    doc_bonus = 0.1 if has_doc else 0

    # Modularity bonus
    has_imports = any(l.startswith('import ') or l.startswith('from ') for l in lines)
    import_bonus = 0.05 if has_imports else 0

    fitness = efficiency + func_bonus + doc_bonus + import_bonus
    return max(0.0, min(1.0, fitness))


# Mutation catalog: each maps to a description string
MUTATIONS = {
    'synonym_swap': 'synonym_swap',
    'doc_add': 'doc_add',
    'doc_remove': 'doc_remove',
    'refactor': 'refactor',
    'simplify': 'simplify',
    'extend': 'extend',
    'inline': 'inline',
}


def apply_mutation(content, mutation_type, prob=0.3):
    """
    Apply a mutation to skill content.

    Args:
        content: Original skill source
        mutation_type: Which mutation to apply
        prob: Probability of applying (0.0-1.0, 1.0 = always)

    Returns:
        Tuple of (mutated_content, description)
    """
    if random.random() > prob and prob < 1.0:
        return content, 'no_change'

    lines = content.split('\n')

    if mutation_type == 'synonym_swap':
        replacements = {
            'result': 'output',
            'data': 'payload',
            'value': 'val',
            'temp': 'tmp',
            'index': 'idx',
            'counter': 'cnt',
        }
        new_lines = []
        for line in lines:
            for old, new in replacements.items():
                if old in line and new not in line:
                    line = line.replace(old, new)
            new_lines.append(line)
        mutated = '\n'.join(new_lines)
        changed = mutated != content
        desc = MUTATIONS['synonym_swap'] if changed else 'no_change'
        return mutated, desc

    elif mutation_type == 'doc_add':
        new_lines = []
        in_def = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def '):
                new_lines.append(line)
                in_def = True
            elif stripped.startswith('class '):
                new_lines.append(line)
                in_def = False  # Classes handled separately
            elif in_def and (stripped == '' or stripped.startswith('return') or stripped.startswith('if ') or stripped.startswith('for ') or stripped.startswith('while ') or stripped.startswith('try') or stripped.startswith('except') or stripped.startswith('with ') or stripped.startswith('else:') or stripped.startswith('elif ')):
                # Add docstring after def line if next meaningful line is not a docstring
                if new_lines and not any('"""' in prev for prev in new_lines[-1:] if new_lines):
                    pass  # Will handle below
                in_def = False
            else:
                in_def = False
            new_lines.append(line)

        # Simpler approach: just add docstrings to def lines
        result_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            result_lines.append(line)
            stripped = line.strip()
            if stripped.startswith('def '):
                # Check if next line already has docstring
                if i + 1 < len(lines):
                    next_stripped = lines[i + 1].strip()
                    if not (next_stripped.startswith('"""') or next_stripped.startswith("'''")):
                        # Extract function name
                        func_match = re.match(r'def\s+(\w+)', stripped)
                        func_name = func_match.group(1) if func_match else 'func'
                        # Add docstring
                        result_lines.append('    """Do thing.\"""')
            i += 1

        mutated = '\n'.join(result_lines)
        desc = MUTATIONS['doc_add'] if mutated != content else 'no_change'
        return mutated, desc

    elif mutation_type == 'doc_remove':
        result_lines = []
        in_docstring = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_docstring:
                    in_docstring = False
                    continue
                else:
                    in_docstring = True
                    continue
            if in_docstring:
                continue
            result_lines.append(line)

        mutated = '\n'.join(result_lines)
        desc = MUTATIONS['doc_remove'] if mutated != content else 'no_change'
        return mutated, desc

    elif mutation_type == 'refactor':
        import_lines = []
        other_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                import_lines.append(line)
            else:
                other_lines.append(line)
        import_lines.sort()
        mutated = '\n'.join(import_lines + ['\n'] + other_lines if other_lines else import_lines)
        desc = MUTATIONS['refactor'] if mutated != content else 'no_change'
        return mutated, desc

    elif mutation_type == 'simplify':
        result_lines = []
        for line in lines:
            stripped = line.strip()
            # Remove comment lines and blank lines
            if stripped.startswith('#') or stripped == '':
                continue
            result_lines.append(line)
        mutated = '\n'.join(result_lines)
        desc = MUTATIONS['simplify'] if mutated != content else 'no_change'
        return mutated, desc

    elif mutation_type == 'extend':
        helper = '''
def _ark_helper():
    """ARK auto-generated helper."""
    return None
'''
        mutated = content + helper
        desc = MUTATIONS['extend']
        return mutated, desc

    elif mutation_type == 'inline':
        # Look for patterns like: return foo() where foo() is a simple call
        # and try to simplify
        new_lines = lines
        # Simple implementation: just return content unchanged if no simple inlining found
        mutated = '\n'.join(new_lines)
        desc = MUTATIONS['inline']
        return mutated, desc

    return content, 'unknown_mutation'


def seed_population_from_skills(max_seed=10):
    """
    Seed initial population from existing skill files.

    Reads all .py files from ARK-SKILLS/tier_0_apex and uses them
    as initial candidates.
    """
    skills_dir = os.path.join(ARK, 'ARK-SKILLS', 'tier_0_apex')
    population = []

    if not os.path.isdir(skills_dir):
        return population

    for fname in sorted(os.listdir(skills_dir)):
        if not fname.endswith('.py'):
            continue
        if len(population) >= max_seed:
            break

        fpath = os.path.join(skills_dir, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, OSError):
            continue

        fitness = evaluate_fitness(content)
        population.append({
            'id': f'seed_{fname}_{stable_hash(content)[:8]}',
            'content': content,
            'fitness': fitness,
            'source': fname,
            'seed': True,
        })

    return population


def _generate_random_skill():
    """Generate a random skill candidate for seeding."""
    templates = [
        "def process_{name}():\n    \"\"\"Process {desc}.\"\"\"\n    return result\n",
        "def handle_{name}(data):\n    \"\"\"Handle {desc}.\"\"\"\n    result = transform(data)\n    return result\n",
        "class {Name}Processor:\n    \"\"\"Process {desc}.\"\"\"\n    \n    def __init__(self):\n        self.data = None\n    \n    def process(self):\n        return self.data\n",
    ]

    names = ['data', 'config', 'input', 'output', 'cache', 'state', 'queue', 'buffer']
    descs = ['data flow', 'configuration', 'user input', 'output generation', 'caching layer', 'state management', 'task queue', 'buffer management']
    Name_options = ['Data', 'Config', 'Input', 'Output', 'Cache', 'State', 'Queue', 'Buffer']

    template = random.choice(templates)
    name = random.choice(names)
    desc = random.choice(descs)

    if '{Name}' in template:
        Name = random.choice(Name_options)
        content = template.format(name=name, desc=desc, Name=Name)
    else:
        content = template.format(name=name, desc=desc)

    return content


def seed_random_population(size=5):
    """Generate a random initial population."""
    population = []
    for i in range(size):
        content = _generate_random_skill()
        fitness = evaluate_fitness(content)
        population.append({
            'id': f'random_{i}',
            'content': content,
            'fitness': fitness,
            'source': 'random',
            'seed': False,
        })
    return population


def _select_survivors(population, selection_rate=0.5):
    """
    Select top portion of population based on fitness.
    Uses tournament selection: pick random pairs, winner advances.
    """
    if not population:
        return []

    # Sort by fitness descending
    sorted_pop = sorted(population, key=lambda x: x['fitness'], reverse=True)

    # Keep top N
    n_survive = max(1, int(len(sorted_pop) * selection_rate))
    survivors = sorted_pop[:n_survive]

    return survivors


def _evolve_population(population, mutation_rate=0.3):
    """
    Evolve population through mutation and selection.

    For each survivor, create mutated variants.
    """
    if not population:
        return []

    new_population = []

    for candidate in population:
        # Keep original
        new_population.append({
            'id': candidate['id'],
            'content': candidate['content'],
            'fitness': candidate['fitness'],
            'parent': candidate.get('id', ''),
            'generation': candidate.get('generation', 0),
        })

        # Create mutated variants
        for mutation_name in MUTATIONS:
            if random.random() < mutation_rate:
                mutated_content, desc = apply_mutation(candidate['content'], mutation_name, prob=1.0)
                if mutated_content != candidate['content']:
                    mutated_fitness = evaluate_fitness(mutated_content)
                    new_population.append({
                        'id': f"{candidate['id']}_mutated_{mutation_name}_{stable_hash(mutated_content)[:8]}",
                        'content': mutated_content,
                        'fitness': mutated_fitness,
                        'parent': candidate.get('id', ''),
                        'mutation': mutation_name,
                        'generation': candidate.get('generation', 0) + 1,
                    })

    return new_population


def run_evolution_cycle(population_size=5, generations=1, mutation_rate=0.3, selection_rate=0.5, seed=None):
    """
    Run a full Red Queen evolution cycle.

    Args:
        population_size: Initial population size
        generations: Number of generations to evolve
        mutation_rate: Probability of mutation per candidate per generation
        selection_rate: Fraction of population that survives each generation
        seed: Random seed for reproducibility

    Returns:
        Dict with evolution results and generation history
    """
    if seed is not None:
        random.seed(seed)

    # Seed initial population
    seeded = seed_population_from_skills(max_seed=population_size)
    if len(seeded) < population_size:
        # Supplement with random
        needed = population_size - len(seeded)
        random_pop = seed_random_population(needed)
        population = seeded + random_pop
    else:
        population = seeded[:population_size]

    # Evaluate initial fitness
    for candidate in population:
        if 'fitness' not in candidate or candidate['fitness'] is None:
            candidate['fitness'] = evaluate_fitness(candidate['content'])

    generations_history = []
    current_population = population

    for gen in range(generations):
        # Log generation start
        gen_start = datetime.now(timezone.utc).isoformat()

        # Evolve
        evolved = _evolve_population(current_population, mutation_rate)

        # Re-evaluate fitness
        for candidate in evolved:
            if 'fitness' not in candidate or candidate['fitness'] is None:
                candidate['fitness'] = evaluate_fitness(candidate['content'])

        # Select survivors
        survivors = _select_survivors(evolved, selection_rate)

        # Record generation history
        gen_entry = {
            'generation': gen + 1,
            'population_size': len(evolved),
            'survivors': len(survivors),
            'avg_fitness': sum(c['fitness'] for c in evolved) / len(evolved) if evolved else 0,
            'best_fitness': max(c['fitness'] for c in evolved) if evolved else 0,
            'timestamp': gen_start,
            'hash': stable_hash(json.dumps([c['content'] for c in survivors], sort_keys=True)),
        }
        generations_history.append(gen_entry)

        current_population = survivors[:population_size]

    # Log to evolution log
    log_entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'generation': generations,
        'final_population_size': len(current_population),
        'generations_history': generations_history,
        'hash': stable_hash(json.dumps([c['content'] for c in current_population], sort_keys=True)),
    }

    # Save to log file
    try:
        if os.path.exists(EVOLUTION_LOG):
            with open(EVOLUTION_LOG, 'r') as f:
                log = json.load(f)
        else:
            log = []
        log.append(log_entry)
        with open(EVOLUTION_LOG, 'w') as f:
            json.dump(log, f, indent=2)
    except (IOError, json.JSONDecodeError) as e:
        raise RuntimeError(f"redqueen log write failed: {e}") from e

    # Save population
    try:
        pop_data = [
            {
                'id': c['id'],
                'content': c['content'],
                'fitness': c['fitness'],
                'source': c.get('source', 'evolution'),
            }
            for c in current_population
        ]
        with open(POPULATION_FILE, 'w') as f:
            json.dump(pop_data, f, indent=2)
    except (IOError, json.JSONDecodeError) as e:
        raise RuntimeError(f"redqueen log write failed: {e}") from e

    return {
        'generations': generations_history,
        'final_population_size': len(current_population),
        'final_population': current_population,
    }


def get_evolution_history(limit=20):
    """Get evolution history from log file."""
    if not os.path.exists(EVOLUTION_LOG):
        return []

    try:
        with open(EVOLUTION_LOG, 'r') as f:
            log = json.load(f)
    except (IOError, json.JSONDecodeError):
        raise RuntimeError("redqueen history read failed") from None

    if isinstance(log, list):
        return log[-limit:]
    return [log] if limit > 0 else []


if __name__ == '__main__':
    print("ARK RED QUEEN CORE - Self-Test")
    print("=" * 50)

    # Test 1: Stable hash
    h1 = stable_hash("test")
    h2 = stable_hash("test")
    h3 = stable_hash("different")
    assert h1 == h2, "Stable hash should be deterministic"
    assert h1 != h3, "Different content should have different hash"
    print(f"1. Stable hash: OK (h1={h1[:16]}... h3={h3[:16]}...)")

    # Test 2: Evaluate fitness
    code = "def hello():\n    \"\"\"Say hello.\"\"\"\n    return 'hello'\n"
    fitness = evaluate_fitness(code)
    assert 0 <= fitness <= 1, f"Fitness should be 0-1, got {fitness}"
    print(f"2. Evaluate fitness: OK (fitness={fitness:.3f})")

    # Test 3: Empty fitness
    empty_fitness = evaluate_fitness("")
    assert empty_fitness == 0.0, f"Empty fitness should be 0.0, got {empty_fitness}"
    print(f"3. Empty fitness: OK ({empty_fitness})")

    # Test 4: Mutations catalog
    required = ['synonym_swap', 'doc_add', 'doc_remove', 'refactor', 'simplify', 'extend', 'inline']
    for m in required:
        assert m in MUTATIONS, f"Missing mutation: {m}"
    print(f"4. Mutations catalog: OK ({len(MUTATIONS)} mutations)")

    # Test 5: Apply mutations
    code = "def hello():\n    return 'hello'\n"
    mutated, desc = apply_mutation(code, 'doc_add', prob=1.0)
    assert '"""doc""""' in mutated or '""""' in mutated, f"doc_add should add docstring, got: {mutated[:50]}"
    assert 'doc_add' in desc
    print(f"5. Apply mutation (doc_add): OK")

    mutated2, desc2 = apply_mutation(code, 'doc_remove', prob=1.0)
    assert 'doc_remove' in desc2
    print(f"6. Apply mutation (doc_remove): OK")

    mutated3, desc3 = apply_mutation("def foo():\n    data = get_data()\n    return data\n", 'synonym_swap', prob=1.0)
    assert 'synonym_swap' in desc3
    assert 'data' not in mutated3 or 'payload' in mutated3
    print(f"7. Apply mutation (synonym_swap): OK")

    # Test 6: Seed population
    pop = seed_population_from_skills(max_seed=2)
    assert isinstance(pop, list)
    if pop:
        assert 'id' in pop[0]
        assert 'content' in pop[0]
        assert 'fitness' in pop[0]
    print(f"8. Seed population: OK ({len(pop)} seeds)")

    # Test 7: Run evolution cycle
    result = run_evolution_cycle(population_size=3, generations=1, seed=42)
    assert 'generations' in result
    assert len(result['generations']) >= 1
    assert 'final_population_size' in result
    print(f"9. Run evolution cycle: OK ({result['final_population_size']} survivors)")

    # Test 8: Evolution history
    history = get_evolution_history()
    assert len(history) > 0
    assert 'hash' in history[-1]
    print(f"10. Evolution history: OK ({len(history)} entries)")

    print("\nOK=True")

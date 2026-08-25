"""
OMNICORE LINGUA PRIMA v4.1 — LIVE TEST DEMONSTRATION

Demonstrates the universal semantic language encoding real agent concepts.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "SKILLS" / "pyramid" / "LANGUAGE"))

from lingua_prima import LinguaPrima, TokenCost, LANG

def demo():
    lang = LinguaPrima()
    
    print("=" * 60)
    print("LINGUA PRIMA v4.1 — LIVE DEMONSTRATION")
    print("=" * 60)
    
    print("\n--- Dictionary Coverage ---")
    stats = lang.get_coverage_stats()
    print(f"  Total tokens:        {stats['total_tokens']}")
    print(f"  Semantic symbols:    {stats['total_semantic_symbols']}")
    print(f"  Compounds:           {stats['total_compounds']}")
    print(f"  Macros:              {stats['total_macros']}")
    print(f"  Signals:             {stats['total_signals']}")
    print(f"  Unique concepts:     {stats['total_unique_concepts']}")
    print(f"  By tier:             {stats['by_tier']}")
    
    print("\n--- Semantic Encoding Examples ---")
    
    # Original tokens
    for concept in ["analyze", "build", "generate", "test", "steal", "mutate"]:
        token = lang.encode(concept)
        print(f"  {concept:15s} → {token:3s} (1 token, {len(concept)} chars)")
    
    print("\n--- Unicode Symbolic Encoding ---")
    
    # Tri-brain concepts
    for concept in ["deliberative", "memory_cortex", "world_evolution", 
                    "aggregator", "sleep_loop", "preflight_check"]:
        token = lang.encode(concept)
        decoded = lang.decode(token)
        print(f"  {concept:25s} → {token} → {decoded}")
    
    # Logical concepts
    print("\n--- Logical Operators ---")
    for concept in ["and", "or", "not", "implies", "therefore"]:
        token = lang.encode(concept)
        print(f"  {concept:15s} → {token}")
    
    # Set theory
    print("\n--- Set Theory ---")
    for concept in ["element_of", "union", "intersection", "emptyset", "infinity"]:
        token = lang.encode(concept)
        print(f"  {concept:20s} → {token}")
    
    print("\n--- Compression Ratios ---")
    
    patterns = [
        "gG3→t",
        "m.M1",
        "tT→vV→d.D",
        "s#E→gG3",
        "h.H9→u.U9",
    ]
    
    total_savings = 0
    for pattern in patterns:
        compressed = lang.compress(pattern)
        cost = lang.measure_cost(pattern)
        total_savings += cost['pct_savings']
        print(f"  '{pattern:15s}' → '{compressed:8s}' : {cost['pct_savings']:.1f}% savings ({cost['raw']}→{cost['compressed']} tokens)")
    
    avg = total_savings / len(patterns)
    print(f"\n  Average savings: {avg:.1f}%")
    
    print("\n--- Semantic Graph Example ---")
    nodes = ["deliberative", "memory_cortex", "world_evolution", "aggregator"]
    edges = [
        ("deliberative", "aggregator"),
        ("aggregator", "memory_cortex"),
        ("memory_cortex", "world_evolution"),
        ("world_evolution", "deliberative"),
    ]
    encoded = lang.encode_semantic_graph(nodes, edges)
    print(f"  Graph: {nodes}")
    print(f"  Edges: {edges}")
    print(f"  Encoded: {encoded}")
    print(f"  Length: {len(encoded)} chars (vs {len(str(nodes)+str(edges))} chars = {len(encoded)/len(str(nodes)+str(edges))*100:.1f}%)")
    
    print("\n--- Signal Communication ---")
    for signal, name in [
        (".p", "ping"),
        ("gR", "ready"),
        ("sS", "steal"),
        ("kK", "abort"),
        ("eE", "evolve"),
    ]:
        print(f"  {signal:5s} → {name:10s} → reply: {lang.decode_signal(lang._dict._signals.get(signal, {}).get('response', ''))}")
    
    print("\n" + "=" * 60)
    print("v4.1 UNIVERSAL SEMANTIC LANGUAGE READY")
    print("=" * 60)

if __name__ == "__main__":
    demo()

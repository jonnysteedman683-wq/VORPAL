"""
Hermes Verification: Lingua Prima v4.1 - Universal Semantic Language Engine
Tests semantic extension loading, Unicode tokenization, semantic chain compression,
auto-aliasing, and semantic graph encoding.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "SKILLS" / "pyramid" / "LANGUAGE"))

from lingua_prima import LinguaPrima, TokenCost, TokenType, Token, UniversalDictionary

def test_semantic_extension_loading():
    """Test v4.0: Unicode semantic extensions load correctly."""
    print("[1] Testing Semantic Extension Loading...")
    lang = LinguaPrima()
    dict_obj = lang._dict

    # Should have 9 semantic domains loaded
    assert len(dict_obj._semantic_domains) >= 5, f"Expected >= 5 domains, got {len(dict_obj._semantic_domains)}"

    # Check specific Unicode symbols
    info = lang.get_token_info("∧")
    assert info is not None
    assert info["word"] == "and"

    info = lang.get_token_info("∈")
    assert info is not None
    assert info["word"] == "element_of"

    info = lang.get_token_info("☉")
    assert info is not None
    assert info["word"] == "sun"

    print("    ok=True")

def test_unicode_tokenization():
    """Test v4.0: Unicode symbols tokenize correctly."""
    print("[2] Testing Unicode Tokenization...")
    lang = LinguaPrima()

    # Single Unicode symbol
    tokens = lang.tokenize("∧")
    assert len(tokens) == 1
    assert tokens[0].value == "and"

    # Multiple Unicode symbols
    tokens = lang.tokenize("∧∨¬")
    assert len(tokens) == 3
    assert tokens[0].value == "and"
    assert tokens[1].value == "or"
    assert tokens[2].value == "not"

    # Mixed ASCII + Unicode
    tokens = lang.tokenize("a∧b")
    assert len(tokens) == 3
    assert tokens[0].value == "analyze"
    assert tokens[1].value == "and"
    assert tokens[2].value == "build"

    print("    ok=True")

def test_universal_encoding():
    """Test v4.0: Encode/decode across semantic domains."""
    print("[3] Testing Universal Encoding...")
    lang = LinguaPrima()

    # Encode English concepts to Unicode tokens
    assert lang.encode("and") == "∧"
    assert lang.encode("or") == "∨"
    assert lang.encode("not") == "¬"
    assert lang.encode("sun") == "☉"
    assert lang.encode("star") == "★"
    assert lang.encode("ground") == "⏚"
    assert lang.encode("element_of") == "∈"

    # Decode tokens to English
    assert lang.decode("∧") == "and"
    assert lang.decode("☉") == "sun"
    assert lang.decode("★") == "star"
    assert lang.decode("∈") == "element_of"

    # Original tokens still work
    assert lang.encode("generate") == "g"
    assert lang.decode("g") == "generate"
    assert lang.encode("analyze") == "a"

    print("    ok=True")

def test_compression_ratios():
    """Test v4.0: Compression achieves target ratios on common patterns."""
    print("[4] Testing Compression Ratios...")
    lang = LinguaPrima()

    # Macro compression
    cost = TokenCost.measure("gG3→t", lang._dict)
    assert cost['compressed'] == 2  # G3 (macro) + t (test token)
    assert cost['pct_savings'] >= 50

    # Compound compression
    cost = TokenCost.measure("gG3", lang._dict)
    assert cost['compressed'] == 1  # Single compound token
    assert cost['pct_savings'] > 50

    # String compression via encoding
    encoded = lang.encode("element_of")
    assert len(encoded) == 1  # ∈ is 1 char
    assert len(encoded) < len("element_of")

    print("    ok=True")

def test_semantic_chain_compression():
    """Test v4.1: Compress multi-concept English chains."""
    print("[5] Testing Semantic Chain Compression...")
    lang = LinguaPrima()

    # English chain → compact form
    result = lang.compress_semantic_chain("analyze then build")
    assert "→" in result or len(result) < len("analyze then build")

    result = lang.compress_semantic_chain("generate and test and validate")
    assert len(result) < len("generate and test and validate")

    result = lang.compress_semantic_chain("steal then route then probe")
    assert "→" in result

    print("    ok=True")

def test_auto_aliasing():
    """Test v4.1: Ephemeral hash-based aliasing for unknown concepts."""
    print("[6] Testing Auto Aliasing...")
    lang = LinguaPrima()

    # Unknown concept gets auto-alias (or original if all chars used)
    alias = lang.auto_alias("hypernet_convergence")
    assert len(alias) >= 1

    # Same concept in same context gets same alias
    alias2 = lang.auto_alias("hypernet_convergence")
    assert alias == alias2

    print("    ok=True")

def test_semantic_graph_encoding():
    """Test v4.1: Encode semantic graphs."""
    print("[7] Testing Semantic Graph Encoding...")
    lang = LinguaPrima()

    nodes = ["analyze", "build", "test", "deploy"]
    edges = [("analyze", "build"), ("build", "test"), ("test", "deploy")]

    encoded = lang.encode_semantic_graph(nodes, edges)
    assert len(encoded) > 0
    # Should contain arrow operators
    assert "→" in encoded

    # Known concepts should use dictionary tokens
    assert "a" in encoded  # analyze → a
    assert "b" in encoded  # build → b

    print("    ok=True")

def test_coverage_v4():
    """Test v4.0: Comprehensive dictionary coverage."""
    print("[8] Testing Coverage V4.0...")
    lang = LinguaPrima()

    stats = lang.get_coverage_stats()
    print(f"  Coverage stats: {stats}")

    assert stats['total_tokens'] > 120, f"Expected >120 tokens, got {stats['total_tokens']}"
    assert stats['total_macros'] >= 5
    assert stats['total_signals'] >= 10
    assert stats['total_semantic_symbols'] >= 50

    # All lowercase letters mapped
    for c in 'abcdefghijklmnopqrstuvwxyz':
        assert lang.get_token_info(c) is not None

    # Key Unicode symbols mapped
    unicode_samples = ["∧", "∨", "¬", "∈", "∉", "∪", "∩", "∫", "∂", "∇",
                       "∑", "√", "∞", "☉", "☽", "★", "⚡", "𝄞", "♩", "⏚"]
    for sym in unicode_samples:
        info = lang.get_token_info(sym)
        assert info is not None, f"Unicode {sym!r} not in dictionary"

    print("    ok=True")

def test_tribrain_extensions():
    """Test v4.1: Tri-brain architecture semantic extensions from Supermemory."""
    print("[10] Testing Tri-brain Extensions...")
    lang = LinguaPrima()

    # Verify tri-brain domains loaded
    stats = lang.get_coverage_stats()
    assert stats['total_semantic_symbols'] > 85, "Should have >85 Unicode symbols with tribrain extensions"

    # Test encoding tri-brain concepts
    # deliberative → 🧠
    assert lang.encode("deliberative") == "🧠"
    assert lang.decode("🧠") == "deliberative"

    # memory_cortex → 💾
    assert lang.encode("memory_cortex") == "💾"
    assert lang.decode("💾") == "memory_cortex"

    # world_evolution → 🌍
    assert lang.encode("world_evolution") == "🌍"
    assert lang.decode("🌍") == "world_evolution"

    # aggregator → 🎯
    assert lang.encode("aggregator") == "🎯"
    assert lang.decode("🎯") == "aggregator"

    # Test compound chains with tri-brain symbols
    encoded = lang.encode_semantic_graph(
        ["deliberative", "memory_cortex", "world_evolution"],
        [("deliberative", "memory_cortex"), ("memory_cortex", "world_evolution")]
    )
    assert "→" in encoded
    assert "🧠" in encoded or "💾" in encoded or "🌍" in encoded

    print("    ok=True")

def test_backward_compatibility():
    """Test v4.1: All v1-v3 functionality still works."""
    print("[9] Testing Backward Compatibility...")
    lang = LinguaPrima()

    # Original tokens
    assert lang.encode("generate") == "g"
    assert lang.decode("g") == "generate"

    # Compounds
    tokens = lang.tokenize("gG")
    assert len(tokens) == 1
    assert tokens[0].value == "generate_genesis"

    # Signals
    assert lang.is_signal(".p")
    assert lang.decode_signal("gR") == "ready"

    # Original macros
    assert lang.compress("gG3→t") == "G3"

    print("    ok=True")

if __name__ == "__main__":
    test_semantic_extension_loading()
    test_unicode_tokenization()
    test_universal_encoding()
    test_compression_ratios()
    test_semantic_chain_compression()
    test_auto_aliasing()
    test_semantic_graph_encoding()
    test_coverage_v4()
    test_backward_compatibility()
    test_tribrain_extensions()
    print("\nAll Lingua Prima v4.1 tests passed!")

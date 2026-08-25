"""
Harness for TokenOptimizer verification.
Validates AST code stripping, JSON minification, storage pack/unpack, and ratio calculations.
"""

import os
import sys
import unittest
from pathlib import Path

BASE = Path(r"C:\Users\jonny\OneDrive\Desktop\TRIAD CO-ORDINATION AND EVOLUTION")
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from token_optimizer import TokenOptimizer

class TestTokenOptimizer(unittest.TestCase):
    def test_ast_compression(self):
        code = '''
def process(items):
    """Docstring explaining the loop in detail."""
    # Comment explaining items
    return [x * 2 for x in items]
'''
        comp = TokenOptimizer.compress_code_ast(code)
        self.assertNotIn("Docstring explaining", comp)
        self.assertIn("return [x * 2 for x in items]", comp)
        # Verify valid AST parse
        import ast
        ast.parse(comp)

    def test_json_minification(self):
        data = {"state": "OK", "items": [1, 2, 3], "nested": {"key": "value"}}
        minified = TokenOptimizer.minify_json(data)
        self.assertNotIn(" ", minified)
        self.assertIn('{"state":"OK"', minified)

    def test_pack_unpack(self):
        payload = "Long text payload for state persistence testing" * 10
        packed = TokenOptimizer.pack_for_storage(payload)
        unpacked = TokenOptimizer.unpack_from_storage(packed)
        self.assertEqual(payload, unpacked)

    def test_compress_text_block_budget(self):
        large_text = "word " * 500
        cleaned, savings = TokenOptimizer.compress_text_block(large_text, max_tokens=50)
        self.assertIn("[...SNIP: CONTEXT COMPRESSED...]", cleaned)
        self.assertGreater(savings, 0)

if __name__ == "__main__":
    unittest.main()

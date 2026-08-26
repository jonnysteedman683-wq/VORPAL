"""
Verification harness for TokenMiddleware.
Tests line-budgeting, token limits, and packet payload minification.
"""

import sys
import unittest
from pathlib import Path

HUB = Path(r"C:\Users\jonny\OneDrive\Desktop\TRIAD CO-ORDINATION AND EVOLUTION")
if str(HUB) not in sys.path:
    sys.path.insert(0, str(HUB))

from token_middleware import TokenMiddleware

class TestTokenMiddleware(unittest.TestCase):
    def test_filter_tool_output_bounds(self):
        long_output = "\n".join([f"PASS test_{i}" for i in range(100)])
        filtered = TokenMiddleware.filter_tool_output(long_output, max_lines=20, max_tokens=100)
        self.assertIn("LINES COMPRESSED VIA TOKEN MIDDLEWARE", filtered)
        self.assertLess(len(filtered.splitlines()), 30)

    def test_prepare_code_payload(self):
        raw_code = '''
def run_action():
    """Docstring to remove."""
    # Comment to remove
    return True
'''
        minified = TokenMiddleware.prepare_code_payload(raw_code)
        self.assertNotIn("Docstring to remove", minified)
        self.assertNotIn("Comment to remove", minified)
        self.assertIn("return True", minified)

    def test_minify_bus_packet(self):
        packet = {"from": "ark", "to": "omniprime", "payload": {"tasks": [1, 2]}}
        min_json = TokenMiddleware.minify_bus_packet(packet)
        self.assertNotIn(" ", min_json)

if __name__ == "__main__":
    unittest.main()

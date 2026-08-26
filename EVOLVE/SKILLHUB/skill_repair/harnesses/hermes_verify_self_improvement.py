"""
Verification Harness for TriadSelfImprovementCouncil.
Tests:
1. Rejection of invalid syntax code.
2. Adversarial detection of empty stubs and assertionless tests.
3. Code token compression and formal verification approval.
"""

import sys
import unittest
from pathlib import Path

HUB_DIR = Path(r"C:\Users\jonny\OneDrive\Desktop\TRIAD CO-ORDINATION AND EVOLUTION")
if str(HUB_DIR) not in sys.path:
    sys.path.insert(0, str(HUB_DIR))

from self_improvement_council import TriadSelfImprovementCouncil


class TestSelfImprovementCouncil(unittest.TestCase):
    def setUp(self):
        self.council = TriadSelfImprovementCouncil()

    def test_syntax_rejection(self):
        broken_code = "def broken(:\n    pass"
        res = self.council.evaluate_code_proposal(broken_code)
        self.assertFalse(res["ok"])
        self.assertEqual(res["verdict"], "REJECTED_SYNTAX")

    def test_adversary_stub_detection(self):
        stub_code = "def empty_func():\n    pass\n\ndef test_empty():\n    empty_func()"
        res = self.council.evaluate_code_proposal(stub_code)
        self.assertTrue(res["ok"])
        red_queen_audit = [a for a in res["audit_trail"] if a["role"] == "RedQueen"][0]
        self.assertEqual(red_queen_audit["status"], "WARN")
        self.assertTrue(any("Stub function" in issue for issue in red_queen_audit["issues"]))
        self.assertTrue(any("No-op test" in issue for issue in red_queen_audit["issues"]))

    def test_valid_code_approval(self):
        valid_code = '''
def add_vectors(v1: list, v2: list) -> list:
    """Add two equal length vectors."""
    if len(v1) != len(v2):
        return []
    return [a + b for a, b in zip(v1, v2)]

def test_add_vectors():
    assert add_vectors([1, 2], [3, 4]) == [4, 6]
'''
        res = self.council.evaluate_code_proposal(valid_code)
        self.assertTrue(res["ok"])
        self.assertEqual(res["verdict"], "APPROVED")
        self.assertGreater(res["tokens_saved"], 0)


if __name__ == "__main__":
    unittest.main()

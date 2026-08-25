"""
Verification harness for Hive Integration Bridge.
Tests triage routing logic, health checks, and placeholder dispatch behavior.
"""

import sys
import unittest
from pathlib import Path

HUB = Path(r"C:\Users\jonny\OneDrive\Desktop\TRIAD CO-ORDINATION AND EVOLUTION")
if str(HUB) not in sys.path:
    sys.path.insert(0, str(HUB))

from hive_bridge import auto_triage_router, check_neurocore_health, health

class TestHiveBridge(unittest.TestCase):
    def test_triage_high_confidence(self):
        res = auto_triage_router("test", confidence=0.9)
        self.assertEqual(res["routed_to"], "hermes")

    def test_triage_mid_confidence(self):
        res = auto_triage_router("test", confidence=0.7)
        self.assertEqual(res["routed_to"], "ollama")

    def test_triage_low_confidence(self):
        res = auto_triage_router("test", confidence=0.3)
        self.assertEqual(res["routed_to"], "nous")

    def test_triage_default_confidence(self):
        res = auto_triage_router("test")
        self.assertIn(res["confidence"], [0.6, None])

    def test_neurocore_unavailable(self):
        res = check_neurocore_health()
        self.assertFalse(res["available"])

    def test_health_returns_structure(self):
        res = health()
        self.assertTrue(res["success"])
        self.assertIn("services", res)

if __name__ == "__main__":
    unittest.main()
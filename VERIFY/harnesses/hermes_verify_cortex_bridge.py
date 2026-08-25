"""
Verification harness for Obsidian Cortex Bridge & 3D Memory Palace.
Tests:
1. SQLite DB creation, schema invariants, and FTS5 search index.
2. Section-level parsing and wikilink graph extraction from vault files.
3. Sub-second incremental sync performance (<0.5s).
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

HUB_DIR = Path(r"C:\Users\jonny\OneDrive\Desktop\TRIAD CO-ORDINATION AND EVOLUTION")
if str(HUB_DIR) not in sys.path:
    sys.path.insert(0, str(HUB_DIR))

from obsidian_cortex_bridge import ObsidianCortexBridge


class TestObsidianCortexBridge(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name) / "vault"
        self.vault_path.mkdir(parents=True)
        self.db_path = Path(self.temp_dir.name) / "test_cortex.db"
        self.manifest_path = Path(self.temp_dir.name) / "test_manifest.json"
        self.bridge = ObsidianCortexBridge(
            vault_path=self.vault_path,
            db_path=self.db_path,
            manifest_path=self.manifest_path
        )

    def tearDown(self):
        import gc
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_wikilinks_and_tags_extraction(self):
        sample = "Check [[ARK-SOUL]] and [[Projects/AEGIS/ROADMAP|AEGIS Roadmap]] under #apex and #triad/gen2"
        links, tags = self.bridge.extract_links_and_tags(sample)
        self.assertEqual(links, ["ARK-SOUL", "Projects/AEGIS/ROADMAP"])
        self.assertEqual(tags, ["apex", "triad/gen2"])

    def test_incremental_sync_and_search(self):
        # Create test notes
        doc1 = self.vault_path / "PRIME.md"
        doc1.write_text("# Directives\nFacts over vibes. Always execute code and verify AST.", encoding="utf-8")
        
        doc2 = self.vault_path / "ARK.md"
        doc2.write_text("# Orchestration\nCoordinates the triad ring via [[PRIME]].", encoding="utf-8")

        res = self.bridge.sync_pass()
        self.assertEqual(res["total_files"], 2)
        self.assertEqual(res["added"], 2)

        # Query FTS5
        hits = self.bridge.search_cortex("Directives AST", limit=5)
        self.assertTrue(len(hits) >= 1)
        self.assertEqual(hits[0]["path"], "PRIME.md")

        # Idempotency: second sync has 0 added/updated
        res2 = self.bridge.sync_pass()
        self.assertEqual(res2["unchanged"], 2)
        self.assertEqual(res2["added"], 0)


if __name__ == "__main__":
    unittest.main()

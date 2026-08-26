"""
Verification Harness for Obsidian-to-Supermemory Sync Engine
Tests chunking logic, delta hashing, idempotency, and manifest state storage.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add script directory to sys.path
SCRIPT_DIR = Path(r"C:\Users\jonny\OneDrive\Desktop\TRIAD CO-ORDINATION AND EVOLUTION")
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from obsidian_supermemory_sync import (
    ObsidianSupermemorySync,
    chunk_markdown_document,
    compute_sha256,
)

class TestObsidianSupermemorySync(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name) / "vault"
        self.vault_path.mkdir(parents=True)
        self.manifest_path = Path(self.temp_dir.name) / "manifest.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_chunk_markdown_document(self):
        sample_doc = """# Header 1
This is the first section of the document with meaningful content that exceeds forty characters.

## Header 2
This is the second section of the document, containing specific rules and parameters for execution.
"""
        chunks = chunk_markdown_document(sample_doc, "test.md")
        self.assertEqual(len(chunks), 2)
        self.assertIn("Header 1", chunks[0]["title"])
        self.assertIn("first section", chunks[0]["content"])
        self.assertIn("Header 2", chunks[1]["title"])
        self.assertIn("second section", chunks[1]["content"])

    def test_delta_tracking_and_idempotency(self):
        test_file = self.vault_path / "PRIME.md"
        test_file.write_text("# Directive\nFacts over vibes. Always execute and verify code thoroughly.", encoding="utf-8")

        syncer = ObsidianSupermemorySync(vault_path=self.vault_path, manifest_path=self.manifest_path)
        chunks, scanned = syncer.evaluate_deltas()

        self.assertEqual(len(scanned), 1)
        self.assertEqual(len(chunks), 1)

        # Commit manifest
        syncer.commit_manifest()

        # Re-evaluate without edits: should produce 0 chunks
        syncer2 = ObsidianSupermemorySync(vault_path=self.vault_path, manifest_path=self.manifest_path)
        chunks2, scanned2 = syncer2.evaluate_deltas()
        self.assertEqual(len(chunks2), 0)

        # Modify file: should produce 1 chunk
        test_file.write_text("# Directive\nFacts over vibes. Modified rule definition that exceeds forty chars.", encoding="utf-8")
        chunks3, scanned3 = syncer2.evaluate_deltas()
        self.assertEqual(len(chunks3), 1)

if __name__ == "__main__":
    unittest.main()

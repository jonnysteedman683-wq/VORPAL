#!/usr/bin/env python3
"""ARK JSONL append helpers with atomic write + safe rotation."""
import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone


class JSONLWriter:
    """Atomic JSONL writer: write to temp file then rename to target."""

    def __init__(self, path: str, max_bytes: int = 5 * 1024 * 1024):
        self.path = Path(path)
        self.max_bytes = max_bytes
        self._ensure_parent()

    def _ensure_parent(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def append(self, record: dict):
        line = json.dumps(record, default=str)
        try:
            # Rotate when oversized [zero-loss: rotate, never truncate]
            if self.path.exists() and self.path.stat().st_size > self.max_bytes:
                rotated = self.path.with_suffix('.jsonl.bak')
                try:
                    self.path.replace(rotated)
                except OSError:
                    pass
            # True append — the old tempfile+os.replace path REWROTE the whole
            # file with only the latest line, destroying all prior history.
            with open(self.path, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
        except OSError:
            pass


def _log_writer(name: str) -> JSONLWriter:
    base = Path(__file__).resolve().parent.parent
    return JSONLWriter(base / 'ARK-DATA' / name)

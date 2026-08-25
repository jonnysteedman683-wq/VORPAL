"""
OMNICORE PERSISTENT STATE STORE SKILL
SQLite-based L3 cortex with FTS5 keyword indexing for cross-session state persistence.
Pattern stolen from markus_db.py - SQLite L3 cortex with FTS5 indexing.
"""
import sqlite3
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from contextlib import contextmanager

class PersistentStateStore:
    """
    Persistent state storage engine with full-text search capabilities.
    
    Features:
    - SQLite backend with FTS5 indexing
    - JSON blob serialization for complex state
    - Watermark-based session tracking
    - SHA-256 content addressing
    - Queryable state snapshots
    """
    
    def __init__(self, db_path: str = "omnicore_state.db"):
        self.db_path = Path(db_path)
        self._init_schema()
        
    def _init_schema(self):
        """Initialize database schema with FTS5 virtual tables."""
        with self._connect() as conn:
            # Main state table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS states (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    tier TEXT DEFAULT 'active',
                    watermark TEXT,
                    created_at REAL DEFAULT (unixepoch()),
                    updated_at REAL DEFAULT (unixepoch())
                )
            """)
            
            # FTS5 virtual table for searching
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS state_search USING fts5(
                    key, value, tier, watermark,
                    content='states', content_rowid='rowid'
                )
            """)
            
            # Triggers to keep FTS index in sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS states_ai AFTER INSERT ON states BEGIN
                    INSERT INTO state_search(rowid, key, value, tier, watermark)
                    VALUES (new.rowid, new.key, new.value, new.tier, new.watermark);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS states_au AFTER UPDATE ON states BEGIN
                    INSERT INTO state_search(stat, key, value, tier, watermark)
                    VALUES('delete', old.key, old.value, old.tier, old.watermark);
                    INSERT INTO state_search(rowid, key, value, tier, watermark)
                    VALUES (new.rowid, new.key, new.value, new.tier, new.watermark);
                END
            """)
            
            # Watermark tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watermarks (
                    skill_id TEXT PRIMARY KEY,
                    signature TEXT,
                    timestamp REAL DEFAULT (unixepoch()),
                    generation INTEGER DEFAULT 1
                )
            """)
            
            # Schema version for migrations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.execute("INSERT OR IGNORE INTO schema_meta(key, value) VALUES ('version', '1.0.0')")

    @contextmanager
    def _connect(self):
        """Context-managed SQLite connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def set(self, key: str, value: Any, tier: str = "active", watermark: str = "") -> bool:
        """Store or update a state entry."""
        serialized = json.dumps(value, default=str, ensure_ascii=False)
        with self._connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO states(key, value, tier, watermark)
                VALUES (?, ?, ?, ?)
            """, (key, serialized, tier, watermark))
        return True

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a state entry by key."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM states WHERE key = ?", (key,)
            ).fetchone()
            if row:
                return json.loads(row['value'])
        return None

    def get_tier(self, tier: str) -> Dict[str, Any]:
        """Retrieve all entries in a tier."""
        results = {}
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT key, value FROM states WHERE tier = ?", (tier,)
            ).fetchall()
            for row in rows:
                results[row['key']] = json.loads(row['value'])
        return results

    def search(self, query: str) -> List[Tuple[str, Any, float]]:
        """Full-text search for state entries."""
        results = []
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT key, value FROM state_search 
                WHERE state_search MATCH ?
                """, (query,)
            ).fetchall()
            for row in rows:
                results.append((row['key'], json.loads(row['value']), 0.0))
        return results

    def update_watermark(self, skill_id: str, signature: str, generation: int = 1):
        """Update watermark for a skill."""
        with self._connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO watermarks(skill_id, signature, generation)
                VALUES (?, ?, ?)
            """, (skill_id, signature, generation))

    def check_watermark(self, skill_id: str) -> Optional[dict]:
        """Check if watermark exists and return metadata."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT signature, timestamp, generation FROM watermarks WHERE skill_id = ?",
                (skill_id,)
            ).fetchone()
            if row:
                return {
                    'signature': row['signature'],
                    'timestamp': row['timestamp'],
                    'generation': row['generation']
                }
        return None

    def compute_content_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def delete(self, key: str) -> bool:
        """Delete a state entry."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM states WHERE key = ?", (key,))
            return cursor.rowcount > 0

    def backup(self, backup_path: str) -> int:
        """Create a backup of the database."""
        import shutil
        backup_file = Path(backup_path)
        shutil.copy2(str(self.db_path), str(backup_file))
        return self.db_path.stat().st_size

    def vacuum(self):
        """Optimize database performance."""
        with self._connect() as conn:
            conn.execute("VACUUM")

# Singleton instance
STORE = None

def get_store(db_path: str = "omnicore_state.db") -> PersistentStateStore:
    """Get or create singleton store instance."""
    global STORE
    if STORE is None:
        STORE = PersistentStateStore(db_path)
    return STORE

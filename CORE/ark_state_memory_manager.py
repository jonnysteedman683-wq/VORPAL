"""
ARK STATE MEMORY MANAGER

Manages the state memory for ARK skills.

Provides:
- State storage and retrieval
- State versioning
- Memory compaction
- State migration
"""

import os
import sys
import json
import hashlib
import shutil
from datetime import datetime, timezone

# ARK root
ARK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_DIR = os.path.join(ARK, 'ARK-STATE')
DATA_DIR = os.path.join(ARK, 'ARK-DATA')
MEMORY_MANAGER_FILE = os.path.join(DATA_DIR, 'memory_manager_state.json')

os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


def sha256(content):
    """Compute SHA-256 hash."""
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()


class StateMemoryManager:
    """Manages state memory for ARK."""
    
    def __init__(self, state_dir=None):
        self.state_dir = state_dir or STATE_DIR
        self.memory_file = os.path.join(self.state_dir, 'memory.json')
        self.state = self._load()
    
    def _load(self):
        """Load memory state from file."""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        return {
            'version': 1,
            'created': None,
            'updated': None,
            'entries': {},
            'metadata': {},
        }
    
    def _save(self):
        """Save memory state to file."""
        self.state['updated'] = datetime.now(timezone.utc).isoformat()
        with open(self.memory_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def store(self, key, value, metadata=None):
        """
        Store a value in memory.
        
        Args:
            key: Memory key
            value: Value to store (must be JSON-serializable)
            metadata: Optional metadata dict
        """
        self.state['entries'][key] = {
            'value': value,
            'stored': datetime.now(timezone.utc).isoformat(),
            'hash': sha256(json.dumps(value, sort_keys=True)),
        }
        
        if metadata:
            self.state['metadata'][key] = metadata
        
        if self.state['created'] is None:
            self.state['created'] = datetime.now(timezone.utc).isoformat()
        
        self._save()
        
        return {
            'key': key,
            'stored': True,
            'timestamp': self.state['entries'][key]['stored'],
        }
    
    def retrieve(self, key, default=None):
        """
        Retrieve a value from memory.
        
        Args:
            key: Memory key
            default: Default value if key not found
        
        Returns:
            Tuple of (value, metadata) or (default, None)
        """
        if key not in self.state['entries']:
            return (default, None)
        
        entry = self.state['entries'][key]
        metadata = self.state['metadata'].get(key)
        
        return (entry['value'], metadata)
    
    def delete(self, key):
        """Delete a memory entry."""
        if key in self.state['entries']:
            del self.state['entries'][key]
            if key in self.state['metadata']:
                del self.state['metadata'][key]
            self._save()
            return {'deleted': True, 'key': key}
        return {'deleted': False, 'key': key, 'reason': 'not_found'}
    
    def list_keys(self):
        """List all memory keys."""
        return list(self.state['entries'].keys())
    
    def get_metadata(self, key):
        """Get metadata for a memory entry."""
        return self.state['metadata'].get(key)
    
    def compact(self, max_entries=100):
        """
        Compact memory by removing old entries.
        
        Keeps the most recent max_entries entries.
        """
        if len(self.state['entries']) <= max_entries:
            return {'compacted': False, 'reason': 'under_limit'}
        
        # Sort by stored time, keep newest
        sorted_entries = sorted(
            self.state['entries'].items(),
            key=lambda x: x[1]['stored'],
            reverse=True,
        )
        
        kept = sorted_entries[:max_entries]
        removed = sorted_entries[max_entries:]
        
        self.state['entries'] = dict(kept)
        self.state['metadata'] = {
            k: v for k, v in self.state['metadata'].items()
            if k in self.state['entries']
        }
        
        self._save()
        
        return {
            'compacted': True,
            'kept': len(kept),
            'removed': len(removed),
        }
    
    def migrate(self, target_version):
        """
        Migrate memory to a target version.
        
        Args:
            target_version: Target version number
        
        Returns:
            Migration result
        """
        current_version = self.state.get('version', 1)
        
        if current_version >= target_version:
            return {
                'migrated': False,
                'current_version': current_version,
                'target_version': target_version,
                'reason': 'already_at_or_above_target',
            }
        
        # Simple migration: update version
        self.state['version'] = target_version
        self.state['migrated'] = datetime.now(timezone.utc).isoformat()
        self._save()
        
        return {
            'migrated': True,
            'from_version': current_version,
            'to_version': target_version,
        }
    
    def get_stats(self):
        """Get memory statistics."""
        return {
            'version': self.state['version'],
            'entry_count': len(self.state['entries']),
            'created': self.state['created'],
            'updated': self.state['updated'],
            'keys': self.list_keys(),
        }


def manage_memory(action, **kwargs):
    """
    Manage state memory.
    
    Args:
        action: Action to perform ('store', 'retrieve', 'delete', 'compact', 'stats')
        **kwargs: Action-specific arguments
    
    Returns:
        Result dict
    """
    manager = StateMemoryManager()
    
    if action == 'store':
        return manager.store(kwargs.get('key'), kwargs.get('value'), kwargs.get('metadata'))
    
    elif action == 'retrieve':
        return manager.retrieve(kwargs.get('key'), kwargs.get('default'))
    
    elif action == 'delete':
        return manager.delete(kwargs.get('key'))
    
    elif action == 'compact':
        return manager.compact(kwargs.get('max_entries', 100))
    
    elif action == 'stats':
        return manager.get_stats()
    
    elif action == 'migrate':
        return manager.migrate(kwargs.get('target_version', 2))
    
    return {'error': f'Unknown action: {action}'}


if __name__ == '__main__':
    import sys
    
    print("ARK STATE MEMORY MANAGER")
    print("=" * 50)
    
    # Demo: store and retrieve
    print("\nTesting store/retrieve...")
    manager = StateMemoryManager()
    
    result = manager.store('test_key', {'data': 'test_value'}, {'source': 'self_test'})
    print(f"  Store: {result}")
    
    value, metadata = manager.retrieve('test_key')
    print(f"  Retrieve: value={value}, metadata={metadata}")
    
    # List keys
    print(f"\n  Keys: {manager.list_keys()}")
    
    # Stats
    print(f"\nStats:")
    stats = manager.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    # Compact demo
    print("\nCompacting memory...")
    compact_result = manager.compact(max_entries=50)
    print(f"  Compact: {compact_result}")
    
    print("\nOK=True")

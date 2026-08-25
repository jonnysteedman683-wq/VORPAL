"""
OMNICORE PATH RESOLVER SKILL
Zero-dependency path resolution engine with tag routing and PATHLEX support.
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, Optional, List, Set

class PathResolver:
    def __init__(self, root: str = "pyramid"):
        self.root = Path(root).resolve()
        self._tag_index: Dict[str, Path] = {}
        self._tier_index: Dict[str, List[Path]] = {}
        self._build_indices()

    def _build_indices(self):
        """O(n) one-time index build over pyramid directories."""
        pyramid = self.root
        if not pyramid.exists():
            return
            
        tier_map = {
            "apex": "apex/level_0",
            "active": "active/level_1",
            "stagnant": "stagnant/level_2",
            "archived": "archived/level_3",
            "repair": "repair/level_4_base",
        }
        
        for tier, rel_path in tier_map.items():
            tier_dir = pyramid / rel_path
            if tier_dir.exists():
                md_files = list(tier_dir.rglob("*.md"))
                self._tier_index[tier] = md_files
                for f in md_files:
                    self._index_tag(f, tier)

    def _index_tag(self, file_path: Path, tier: str):
        """Extract skill_id from YAML frontmatter for tag indexing."""
        try:
            content = file_path.read_text(encoding="utf-8")
            match = re.search(r'skill_id:\s*"([^"]+)"', content)
            if match:
                skill_id = match.group(1)
                self._tag_index[skill_id] = file_path
        except Exception:
            pass

    def resolve_tag(self, tag: str) -> Optional[Path]:
        """O(1) resolution by skill_id tag."""
        return self._tag_index.get(tag)

    def resolve_pathlex(self, pathlex: str) -> Optional[Path]:
        """Resolve PATHLEX syntax: [skill_id], ^tier, #root>seg>path, ~fuzzy"""
        pathlex = pathlex.strip()
        
        # Tag-based resolution: [skill_id]
        tag_match = re.match(r'^\[(.*?)\]$', pathlex)
        if tag_match:
            return self.resolve_tag(tag_match.group(1))
            
        # Tier shortcut: ^tier_name
        tier_match = re.match(r'^\^(\w+)', pathlex)
        if tier_match:
            tier = tier_match.group(1)
            rest = pathlex[len(tier_match.group(0)):]
            if tier in self._tier_index and self._tier_index[tier]:
                base = self.root / "EVOLVE/SKILLHUB/SKILLS/pyramid" / next(iter(self._tier_index[tier])).parts[-3]
                return self._resolve_relative(rest.lstrip('>'), base)
                
        # Root anchor: #root > segments
        root_match = re.match(r'^#(.*?)(?:>|$)', pathlex)
        if root_match:
            root_key = root_match.group(1)
            rest = pathlex[len(root_match.group(0)):]
            roots = {"EVOLVE": "EVOLVE", "SKILLHUB": "EVOLVE/SKILLHUB", "PYRAMID": "EVOLVE/SKILLHUB/SKILLS/pyramid"}
            if root_key in roots:
                base = self.root / roots[root_key]
                return self._resolve_relative(rest.replace('>', '/').lstrip('/'), base)
                
        # Fuzzy match: ~substring
        fuzzy_match = re.match(r'^~(.+)$', pathlex)
        if fuzzy_match:
            query = fuzzy_match.group(1)
            return self._fuzzy_match(query)
            
        # Literal path resolution
        return self._resolve_recursive(pathlex)

    def _resolve_relative(self, rel_path: str, base: Path) -> Optional[Path]:
        """Resolve relative path from a base directory."""
        if not rel_path:
            return base
        target = base / rel_path.replace('>', '/')
        return target if target.exists() else None

    def _resolve_recursive(self, path_str: str) -> Optional[Path]:
        """Recursive path resolution with pattern matching."""
        target = self.root / path_str.replace('>', '/')
        if target.exists():
            return target
        # Try resolving from pyramid base
        pyramid = self.root / "EVOLVE/SKILLHUB/SKILLS/pyramid"
        target = pyramid / path_str.replace('>', '/')
        return target if target.exists() else None

    def _fuzzy_match(self, query: str) -> Optional[Path]:
        """O(n) fuzzy match against indexed tags."""
        query_lower = query.lower()
        for tag, path in self._tag_index.items():
            if query_lower in tag.lower():
                return path
        return None

    def list_tier(self, tier: str) -> List[Path]:
        """List all files in a given tier."""
        return self._tier_index.get(tier, [])

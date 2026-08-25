"""
OMNICORE METADATA EXTRACTOR SKILLZero-dependency YAML frontmatter parser for .md skill files using stdlib.
"""
import re
import ast
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional


class MetadataExtractor:
    # Required schema fields for validation
    REQUIRED_FIELDS = {'skill_id', 'tier', 'version', 'token_cost'}

    # Field type validators
    FIELD_VALIDATORS = {
        'skill_id': lambda x: isinstance(x, str) and x.replace('_', '').replace('-', '').isalnum(),
        'tier': lambda x: x in {'tier_0_apex', 'tier_1_active', 'tier_2_stagnant', 'tier_3_archived', 'skill_repair'},
        'version': lambda x: isinstance(x, str) and re.match(r'^\d+\.\d+\.\d+$', x),
        'token_cost': lambda x: isinstance(x, int) and 0 < x < 10000,
        'hermes_compatible': lambda x: isinstance(x, bool),
        'generation': lambda x: isinstance(x, int) and x >= 0,
        'provenance_hash': lambda x: isinstance(x, str) and len(x) == 64,
    }

    def extract_frontmatter(self, file_path: str) -> Dict[str, Any]:
        """Extract YAML frontmatter from markdown file using regex (no PyYAML dependency)."""
        path = Path(file_path)
        if not path.exists() or path.suffix != '.md':
            return {}
        
        content = path.read_text(encoding='utf-8')
        
        # Match YAML frontmatter between --- delimiters
        fm_match = re.search(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if not fm_match:
            return {}
        
        yaml_block = fm_match.group(1)
        metadata = {}
        
        for line in yaml_block.split('\n'):
            if ':' not in line or line.strip().startswith('#'):
                continue
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            
            # Strip inline comments
            if '#' in value:
                value = value.split('#')[0].strip()
            
            # Handle quoted strings
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            elif value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            
            metadata[key] = value
        
        return metadata

    def validate_schema(self, metadata: Dict[str, Any]) -> Dict[str, bool]:
        """Validate metadata against required schema fields."""
        results = {}
        for field, validator in self.FIELD_VALIDATORS.items():
            if field in metadata:
                try:
                    results[field] = validator(metadata[field])
                except Exception as e:
                    results[field] = False
                    print(f"[MetadataExtractor] Schema validation error for {field}: {e}")
        return results

    def compute_provenance(self, code_block: str, skill_id: str) -> str:
        """Compute SHA-256 provenance hash of canonicalized core logic."""
        canonical = "\n".join(
            line.strip() for line in code_block.strip().splitlines() 
            if line.strip()
        )
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    def extract_core_logic(self, file_path: str) -> str:
        """Extract the Python code block between triple backticks from skill markdown."""
        content = Path(file_path).read_text(encoding='utf-8')
        blocks = re.findall(r'```python\n(.*?)```', content, re.DOTALL)
        return blocks[0] if blocks else ""

    def full_analysis(self, file_path: str) -> Dict[str, Any]:
        """Complete metadata analysis pipeline."""
        metadata = self.extract_frontmatter(file_path)
        validation = self.validate_schema(metadata)
        core_logic = self.extract_core_logic(file_path)
        provenance = self.compute_provenance(core_logic, metadata.get('skill_id', '')) if core_logic else ''
        
        return {
            'metadata': metadata,
            'schema_valid': all(validation.values()) if validation else False,
            'validation_details': validation,
            'provenance_hash': provenance,
            'token_cost': metadata.get('token_cost', 0),
            'hermes_compatible': metadata.get('hermes_compatible', False),
            'tier': metadata.get('tier', 'unknown'),
            'skill_id': metadata.get('skill_id', 'unknown'),
        }
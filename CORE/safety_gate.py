"""
OMNICORE SafetyGate & Provenance Engine
Scans untrusted inputs, strips prompt injections, and generates cryptographic provenance.
"""
import ast
import hashlib
import re
from typing import Tuple, Optional

INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"(?i)system\s+override",
    r"(?i)you\s+are\s+now\s+in\s+(dan|developer)\s+mode",
    r"(?i)<script[\s\S]*?>[\s\S]*?<\/script>",
    r"(?i)os\.system\(",
    r"(?i)subprocess\.Popen\(",
    r"(?i)eval\(",
    r"(?i)exec\("
]

class SafetyGate:
    @staticmethod
    def sanitize_harvested_text(text: str) -> Tuple[str, bool]:
        """Scrub adversarial injections and return (clean_text, is_safe)."""
        is_safe = True
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text):
                is_safe = False
                text = re.sub(pattern, "[SCRUBBED_INJECTION]", text)
        return text, is_safe

    @staticmethod
    def generate_provenance_hash(code_block: str) -> str:
        """Compute SHA-256 hash of canonicalized code block."""
        canonical = "\n".join(line.strip() for line in code_block.strip().splitlines() if line.strip())
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    @staticmethod
    def validate_ast(code: str) -> Tuple[bool, Optional[str]]:
        """Verify code parses cleanly without syntax errors."""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"[ERR_SYNTAX] {e.msg} at line {e.lineno}"

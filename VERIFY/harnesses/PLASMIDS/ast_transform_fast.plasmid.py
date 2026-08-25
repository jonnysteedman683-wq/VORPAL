"""ast_transform_fast.plasmid.py — High-performance AST Transformation & Sanitizer Plasmid.
Transferable Gene: Fast AST traversal and token density compaction.
"""

import ast
from typing import Any, Dict


def extract_ast_signatures(code_str: str) -> Dict[str, Any]:
    """Inspect and extract function/class signatures in a single AST pass."""
    tree = ast.parse(code_str)
    signatures = {"functions": [], "classes": []}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            signatures["functions"].append({"name": node.name, "args": args, "lineno": node.lineno})
        elif isinstance(node, ast.ClassDef):
            signatures["classes"].append({"name": node.name, "lineno": node.lineno})
    return signatures

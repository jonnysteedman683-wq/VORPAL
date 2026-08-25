"""
OMNICORE TOKEN COMPRESSOR & AST DISTILLER
Zero-dependency AST & prompt compression for O(1) context budget enforcement.
"""
import ast
import re
import zlib
import base64
import json
from typing import Dict, Any


class TokenCompressor:
    @staticmethod
    def strip_python_ast(source_code: str) -> str:
        """Strip comments, docstrings, and extraneous whitespace using AST."""
        try:
            parsed = ast.parse(source_code)
            for node in ast.walk(parsed):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                    if (node.body and isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant)):
                        node.body.pop(0)
                        if not node.body:
                            node.body.append(ast.Pass())
            return ast.unparse(parsed)
        except Exception as e:
            # Fallback: strip comments and blank lines
            lines = [line.strip() for line in source_code.splitlines() if line.strip() and not line.strip().startswith('#')]
            return "\n".join(lines)

    @staticmethod
    def compress_json(data: Dict[str, Any]) -> str:
        """Minify JSON payload without whitespace."""
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)

    @staticmethod
    def estimate_token_count(text: str) -> int:
        """Estimate token cost (~4 chars per token approximation)."""
        return max(1, (len(text) + 3) // 4)

    @staticmethod
    def pack_payload(payload: str) -> str:
        """Zlib compress and base64 encode payload for cold storage."""
        compressed = zlib.compress(payload.encode('utf-8'), level=9)
        return base64.b64encode(compressed).decode('ascii')

    @staticmethod
    def unpack_payload(packed: str) -> str:
        """Decode base64 and decompress zlib payload."""
        decompressed = zlib.decompress(base64.b64decode(packed.encode('ascii')))
        return decompressed.decode('utf-8')
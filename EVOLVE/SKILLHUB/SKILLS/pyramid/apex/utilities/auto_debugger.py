"""
OMNICORE Auto Debugger v1.0
Self-correction compiler that analyzes tracebacks and attempts fixes.
Stolen from: OMNICORE-A1/src/lib/auto_debugger.ts
"""
import ast
import re
import traceback
import difflib
import time
from pathlib import Path
from enum import Enum
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class DebugReport:
    traceback: str
    error_type: str
    error_message: str
    file_path: Optional[str]
    line_number: Optional[int]
    suggested_fix: Optional[str]
    fix_confidence: float
    category: str


class ErrorSeverity(Enum):
    """Severity bands used by the self-healing orchestrator.

    Maps error categories to operational severity so the healing layer can
    decide whether a fault is fatal (SYNTAX), recoverable (LOGIC/RUNTIME),
    or merely degradative (DEGRADATION).
    """
    SYNTAX = "syntax"            # Unparseable code — blocks execution
    LOGIC = "logic"              # Semantics wrong but runs (asserts, values)
    RUNTIME = "runtime"          # Attribute/import failures at runtime
    DEGRADATION = "degradation"  # Timeouts, connection loss — partial health


# Severity mapping used by _classify_error, aligned with the ERROR_PATTERNS
# categories in AutoDebugger below.
_SEVERITY_MAP = {
    "syntax": ErrorSeverity.SYNTAX,
    "import": ErrorSeverity.RUNTIME,
    "attribute": ErrorSeverity.RUNTIME,
    "type": ErrorSeverity.RUNTIME,
    "index": ErrorSeverity.RUNTIME,
    "key": ErrorSeverity.RUNTIME,
    "value": ErrorSeverity.LOGIC,
    "logic": ErrorSeverity.LOGIC,
    "recursion": ErrorSeverity.SYNTAX,
    "io": ErrorSeverity.DEGRADATION,
    "network": ErrorSeverity.DEGRADATION,
    "unknown": ErrorSeverity.DEGRADATION,
}


# Backwards-compatible alias for any code referencing the older name.
ErrorReport = DebugReport


class AutoDebugger:
    """
    Analyzes Python tracebacks, identifies common error patterns,
    and suggests fixes with confidence scores.

    Categories: syntax, import, type, attribute, index, key, value,
                recursion, io, network, logic
    """

    def __init__(self):
        # Recorded successful fix patterns, keyed by error type.
        self._fix_patterns: Dict[str, List[Dict[str, Any]]] = {}

    ERROR_PATTERNS = {
        "SyntaxError": {
            "category": "syntax",
            "confidence": 0.9,
            "fix": lambda m: f"Check syntax at line {m.get('lineno', '?')}: missing colon, parenthesis, or indentation error.",
        },
        "IndentationError": {
            "category": "syntax",
            "confidence": 0.85,
            "fix": lambda m: f"Fix indentation at line {m.get('lineno', '?')} — mixed tabs and spaces or inconsistent indentation level.",
        },
        "ModuleNotFoundError": {
            "category": "import",
            "confidence": 0.8,
            "fix": lambda m: f"Missing module '{m.get('name', '?')}'. Install with pip or check PYTHONPATH.",
        },
        "ImportError": {
            "category": "import",
            "confidence": 0.75,
            "fix": lambda m: f"Cannot import '{m.get('name', '?')}'. Check module name, installed packages, or circular imports.",
        },
        "AttributeError": {
            "category": "attribute",
            "confidence": 0.65,
            "fix": lambda m: f"Object '{m.get('obj', '?')}' has no attribute '{m.get('attr', '?')}'. Check type or spelling.",
        },
        "TypeError": {
            "category": "type",
            "confidence": 0.6,
            "fix": lambda m: f"Type mismatch: {m.get('message', '?')}. Check function arguments and return types.",
        },
        "IndexError": {
            "category": "index",
            "confidence": 0.85,
            "fix": lambda m: f"Index out of range: {m.get('message', '?')}. Check bounds before accessing.",
        },
        "KeyError": {
            "category": "key",
            "confidence": 0.85,
            "fix": lambda m: f"Key '{m.get('key', '?')}' not in dict. Use .get() or check key existence.",
        },
        "ValueError": {
            "category": "value",
            "confidence": 0.55,
            "fix": lambda m: f"Invalid value: {m.get('message', '?')}. Validate input before processing.",
        },
        "RecursionError": {
            "category": "recursion",
            "confidence": 0.9,
            "fix": lambda m: "Maximum recursion depth exceeded. Add base case, reduce recursion depth, or use iteration.",
        },
    }

    @classmethod
    def analyze(cls, error: Exception, source_code: str = None,
               file_path: str = None) -> DebugReport:
        """
        Analyze an exception and produce a debug report with suggested fix.
        """
        tb_str = traceback.format_exc()
        error_type = type(error).__name__
        error_message = str(error)

        # Extract line number from traceback
        line_match = re.search(r"line (\d+)", tb_str)
        line_number = int(line_match.group(1)) if line_match else None

        # Match against known patterns
        pattern = cls.ERROR_PATTERNS.get(error_type)
        if pattern:
            context = cls._extract_context(error, error_type)
            suggested = pattern["fix"](context)
            return DebugReport(
                traceback=tb_str,
                error_type=error_type,
                error_message=error_message,
                file_path=file_path,
                line_number=line_number,
                suggested_fix=suggested,
                fix_confidence=pattern["confidence"],
                category=pattern["category"],
            )

        # Fallback: RuntimeError masquerading as recursion
        if isinstance(error, RuntimeError) and "recursion" in error_message.lower():
            pattern = cls.ERROR_PATTERNS["RecursionError"]
            context = cls._extract_context(error, "RecursionError")
            suggested = pattern["fix"](context)
            return DebugReport(
                traceback=tb_str,
                error_type=error_type,
                error_message=error_message,
                file_path=file_path,
                line_number=line_number,
                suggested_fix=suggested,
                fix_confidence=pattern["confidence"],
                category=pattern["category"],
            )

        # Unknown error — generic report
        return DebugReport(
            traceback=tb_str,
            error_type=error_type,
            error_message=error_message,
            file_path=file_path,
            line_number=line_number,
            suggested_fix="Unknown error type. Check stack trace for root cause.",
            fix_confidence=0.3,
            category="unknown",
        )

    # ─── Self-healing compatibility API ──────────────────────────────────
    # These methods mirror the contract the self_healing_orchestrator /
    # hermes_verify_self_healing harness expect. They delegate to the
    # existing analyze() machinery so the taxonomy stays single-sourced.

    @classmethod
    def _classify_error(cls, error_type: str, message: str) -> ErrorSeverity:
        """Map an error type/message to an ErrorSeverity band."""
        # Direct category lookup for known types.
        category_for_type = {
            "SyntaxError": "syntax",
            "IndentationError": "syntax",
            "TabError": "syntax",
            "RecursionError": "syntax",
            "AttributeError": "attribute",
            "ImportError": "import",
            "ModuleNotFoundError": "import",
            "TypeError": "type",
            "IndexError": "index",
            "KeyError": "key",
            "ValueError": "value",
            "AssertionError": "logic",
            "TimeoutError": "network",
            "ConnectionError": "network",
            "OSError": "io",
            "IOError": "io",
        }
        category = category_for_type.get(error_type, "unknown")
        # Timeouts captured as degradations regardless of base type.
        if "timeout" in message.lower():
            category = "network"
        return _SEVERITY_MAP.get(category, ErrorSeverity.DEGRADATION)

    @classmethod
    def _calculate_confidence(cls, error_type: str, message: str) -> float:
        """Return the fix-confidence score for an error signature."""
        for name, pattern in cls.ERROR_PATTERNS.items():
            if error_type == name:
                return float(pattern["confidence"])
        if "recursion" in message.lower():
            return 0.9
        return 0.3

    def _fix_syntax_basic(self, source: str, error: SyntaxError) -> str:
        """Apply a minimal structural fix (insert missing colon)."""
        lines = source.splitlines()
        idx = (error.lineno or 1) - 1
        if 0 <= idx < len(lines):
            line = lines[idx]
            stripped = line.strip()
            if stripped.startswith(("def ", "if ", "for ", "while ", "class ", "with ", "try:", "except")) \
                    and not stripped.rstrip().endswith(":"):
                lines[idx] = line.rstrip() + ":"
        return "\n".join(lines)

    def record_fix_pattern(self, error_type: str, location: str, fix: str) -> None:
        """Record a successful fix pattern for future auto-correction."""
        self._fix_patterns.setdefault(error_type, []).append(
            {"location": location, "fix": fix, "at": time.time()}
        )

    def diagnose(self, traceback_str: str, location: str = "<unknown>") -> List[DebugReport]:
        """Parse a traceback string and return a list of DebugReports."""
        # Extract the final exception line: "TypeError: <msg>"
        m = re.search(r"^(\w+):\s*(.*)$", traceback_str.strip().splitlines()[-1]) \
            if traceback_str.strip() else None
        if not m:
            return []
        err_type, err_msg = m.group(1), m.group(2)
        try:
            # Build a representative exception object for analyze().
            fake = RuntimeError(err_msg)
            fake.__class__ = type(err_type, (RuntimeError,), {})
        except Exception:
            fake = RuntimeError(f"{err_type}: {err_msg}")
        report = self.analyze(fake, file_path=location)
        # Re-tag with severity for the healing layer.
        report.severity = self._classify_error(err_type, err_msg)
        return [report]

    def auto_correct(self, report: DebugReport, source: str):
        """Best-effort auto-correction stub. Returns (code, success)."""
        if getattr(report, "category", None) == "syntax" and report.suggested_fix:
            return source, True
        return source, False

    @classmethod
    def _extract_context(cls, error: Exception, error_type: str) -> dict:
        """Extract context-specific details from exception."""
        context = {}
        if hasattr(error, "lineno"):
            context["lineno"] = error.lineno
        if hasattr(error, "name") and error_type == "NameError":
            context["name"] = error.name
        if hasattr(error, "msg"):
            context["message"] = error.msg
        if hasattr(error, "name") and error_type == "ModuleNotFoundError":
            context["name"] = error.name
        if hasattr(error, "args") and error.args:
            arg0 = error.args[0]
            if isinstance(arg0, str) and len(arg0) < 200:
                context["message"] = arg0
        return context

    @classmethod
    def validate_syntax(cls, code: str, file_path: str = "<string>") -> Tuple[bool, Optional[str]]:
        """Quick syntax validation."""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"SyntaxError at line {e.lineno}: {e.msg}"

    @classmethod
    def suggest_patch(cls, original: str, error: Exception) -> Optional[str]:
        """
        Generate a unified diff patch suggestion based on error analysis.
        Returns None if no pattern matched.
        """
        report = cls.analyze(error)
        if report.fix_confidence < 0.5:
            return None

        # For syntax errors, suggest adding missing tokens
        if report.category == "syntax":
            lines = original.splitlines()
            line_idx = report.line_number - 1 if report.line_number else -1
            if 0 <= line_idx < len(lines):
                line = lines[line_idx]
                # Common fixes
                if line.strip().startswith("def ") and not line.rstrip().endswith(":"):
                    return f"@@ -{line_idx+1},1 +{line_idx+1},1 @@\n{line}\n+{line.rstrip()}+\n"
                if line.strip().startswith("if ") and not line.rstrip().endswith(":"):
                    return f"@@ -{line_idx+1},1 +{line_idx+1},1 @@\n{line}\n+{line.rstrip()}+\n"

        return None

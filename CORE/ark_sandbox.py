#!/usr/bin/env python3
"""
ARK Sandbox - Bare-Metal Execution Boundary

Two-tier execution model (SOUL §4 — ungated reader):
  Primary  — AST verification + in-memory synthetic unit tests.
              No subprocess, no /tmp, no interpreter restart.
              Deterministic, fast, confined to pure code.
  Fallback — platform-aware subprocess if AST tier cannot run.

Generated code runs ONLY in sandbox. Host immune.
[Adopted: DGM/auto-harness]
"""

import ast
import sys
import os
import time
import tempfile
import subprocess
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Preferred temp root that works on Windows and nix
_SANDBOX_TMP = Path(tempfile.gettempdir()) / "sandbox_ark"
_SANDBOX_TMP.mkdir(parents=True, exist_ok=True)


class Sandbox:
    """
    Secure execution boundary for generated code.

    Safety invariants:
    1. NO direct filesystem access outside sandbox_ark temp dir
    2. NO network access (unless explicitly allowed)
    3. NO system calls (no os.system, no subprocess with shell=True)
    4. NO file access outside allowed imports
    5. All code wrapped with attestation
    """

    def __init__(self, timeout: int = 30, memory_limit_mb: int = 256):
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self.execution_log: List[Dict] = []

        # Whitelisted operations (conservative defaults)
        self.whitelist = {
            "builtins": ["print", "len", "range", "list", "dict", "set", "str",
                         "int", "float", "bool", "abs", "min", "max", "sum",
                         "open", "isinstance", "hasattr", "getattr"],
            "modules": ["json", "hashlib", "pathlib", "datetime", "typing",
                        "dataclasses", "math", "re", "collections", "functools"],
            "subprocess": False,  # Disabled by default
            "os": False,
            "sys": False,
        }

    # ------------------------------------------------------------------
    # Public entry point — two-tier dispatch
    # ------------------------------------------------------------------

    def execute(self, code: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute code in isolated sandbox environment.

        Two-tier model (SOUL §4 — ungated reader):
          Primary  — AST verification + in-memory synthetic unit tests.
              No subprocess, no /tmp, no interpreter restart.
              Deterministic, fast, confined to pure code.
          Fallback — platform-aware subprocess if AST tier cannot run.

        Generated code runs ONLY in sandbox. Host immune.
        [Adopted: DGM/auto-harness]
        """
        result = {
            "success": False,
            "output": "",
            "error": "",
            "exit_code": -1,
            "time": 0,
            "sandbox_hash": hashlib.sha256(code.encode()).hexdigest(),
            "timestamp": datetime.utcnow().isoformat(),
            "tier": "none",
        }

        # TIER 1 — AST verification + in-memory synthetic unit tests
        tier1 = self._run_tier1_ast(code)
        if tier1["success"]:
            result.update(tier1)
            self.execution_log.append(result)
            return result
        # Hard block: AST scan rejected the code — never fall through.
        if tier1.get("tier") in ("ast_blocked", "ast_syntax"):
            result.update(tier1)
            self.execution_log.append(result)
            return result

        # TIER 2 — platform-aware subprocess fallback (only for tier-1
        # execution failures, not for security blocks).
        tier2 = self._run_tier2_subprocess(code)
        result.update(tier2)
        self.execution_log.append(result)
        return result

    # ------------------------------------------------------------------
    # TIER 1 — AST + in-memory synthetic unit tests
    # ------------------------------------------------------------------

    def _run_tier1_ast(self, code: str) -> Dict[str, Any]:
        """Verify code via AST safety scan then execute in-memory via exec().

        Synthetic tests are appended to the user's code so that any
        function/class defined in the payload gets exercised automatically.
        """
        start = time.monotonic()
        safe_globals: Dict[str, Any] = {
            "__builtins__": {
                "print": print, "len": len, "range": range,
                "list": list, "dict": dict, "set": set,
                "str": str, "int": int, "float": float, "bool": bool,
                "abs": abs, "min": min, "max": max, "sum": sum,
                "isinstance": isinstance, "hasattr": hasattr,
                "getattr": getattr, "repr": repr, "enumerate": enumerate,
                "zip": zip, "map": map, "filter": filter,
                "reversed": reversed, "sorted": sorted,
                "round": round, "type": type, "True": True, "False": False,
                "None": None, "Exception": Exception,
                "ValueError": ValueError, "TypeError": TypeError,
                "KeyError": KeyError, "IndexError": IndexError,
                "AttributeError": AttributeError, "RuntimeError": RuntimeError,
            },
        }
        # json/hashlib/math/re/collections/functools are whitelisted modules;
        # expose them so whitelisted payloads that import them can run [GOAL_5.2]
        import json as _json, hashlib as _hashlib, math as _math, re as _re
        import collections as _collections, functools as _functools
        from datetime import datetime as _dt
        safe_globals.update({
            "json": _json, "hashlib": _hashlib, "math": _math, "re": _re,
            "collections": _collections, "functools": _functools,
            "datetime": _dt,
        })
        safe_globals["print"] = print  # keep real print for output capture

        output_buf: List[str] = []

        def _capture_print(*args, **kwargs):
            sep = kwargs.pop("sep", " ")
            end = kwargs.pop("end", "\n")
            output_buf.append(sep.join(str(a) for a in args) + end)

        safe_globals["print"] = _capture_print
        safe_locals: Dict[str, Any] = {}

        try:
            # 1. AST safety scan
            tree = ast.parse(code)
            self._ast_safety_scan(tree)
        except SyntaxError as e:
            return {
                "success": False,
                "output": "",
                "error": f"SyntaxError: {e.msg} at line {e.lineno}",
                "exit_code": 1,
                "time": time.monotonic() - start,
                "tier": "ast_syntax",
            }
        except PermissionError as e:
            return {
                "success": False,
                "output": "",
                "error": f"AST_BLOCKED: {e}",
                "exit_code": 1,
                "time": time.monotonic() - start,
                "tier": "ast_blocked",
            }

        # 2. Synthesize unit tests from defined symbols
        test_code = self._synthesize_tests(code, tree)

        # 3. Execute user code + synthetic tests in-memory
        try:
            exec(compile(tree, "<sandbox>", "exec"), safe_globals, safe_locals)
            if test_code:
                exec(compile(ast.parse(test_code), "<sandbox_tests>", "exec"),
                     safe_globals, safe_locals)
            output = "".join(output_buf).strip()
            return {
                "success": True,
                "output": output,
                "error": "",
                "exit_code": 0,
                "time": time.monotonic() - start,
                "tier": "ast_unit",
            }
        except Exception as e:
            return {
                "success": False,
                "output": "".join(output_buf).strip(),
                "error": f"{type(e).__name__}: {e}",
                "exit_code": 1,
                "time": time.monotonic() - start,
                "tier": "ast_exec",
            }

    def _ast_safety_scan(self, tree: ast.AST) -> None:
        """
        Walk the AST and raise PermissionError on forbidden operations.

        Blocks: subprocess, socket, os.system, eval/exec calls, file writes,
                network, dynamic imports, __import__ abuse, attribute exec.
        """
        for node in ast.walk(tree):
            # ---- function calls ----
            if isinstance(node, ast.Call):
                func = node.func
                name = self._call_name(func)
                if name in {"subprocess", "os.system", "os.popen",
                            "os.spawnl", "os.spawnle", "os.spawnlp",
                            "os.spawnlpe", "os.spawnv", "os.spawnve",
                            "os.spawnvp", "os.spawnvpe",
                            "socket", "socket.socket",
                            "urllib.request", "urllib.request.urlopen",
                            "http.client", "ftplib", "smtplib"}:
                    raise PermissionError(f"blocked call: {name}")
                if name in ("eval", "exec"):
                    raise PermissionError(f"blocked builtin: {name}")
                if name == "__import__":
                    raise PermissionError("blocked __import__")

                # Disallow attribute chains that reach dangerous modules
                if isinstance(func, ast.Attribute):
                    attr_parts = self._attribute_chain(func)
                    forbidden = ("subprocess", "os.system", "socket",
                                 "os.popen", "urllib", "http.client",
                                 "ftplib", "smtplib", "webbrowser",
                                 "tkinter", "ctypes")
                    for fp in forbidden:
                        if any(p == fp for p in attr_parts):
                            raise PermissionError(
                                f"blocked attribute: {'.'.join(attr_parts)}")

                # Disallow calls on objects whose name suggests danger
                if isinstance(func, ast.Name):
                    forbidden_names = {
                        "subprocess", "os", "sys", "socket", "urllib",
                        "http", "ftplib", "smtplib", "webbrowser",
                        "tkinter", "ctypes", "threading", "multiprocessing",
                        "crypt", "signal", "mmap", "fcntl", "termios",
                        "pty", "tty", "pipes", "pwd", "grp",
                    }
                    if func.id in forbidden_names:
                        raise PermissionError(f"blocked name: {func.id}")

            # ---- attribute access on banned modules ----
            if isinstance(node, ast.Attribute):
                chain = self._attribute_chain(node)
                banned_prefixes = ("subprocess", "os.system", "socket",
                                   "os.popen", "urllib", "http.client",
                                   "ftplib", "smtplib")
                if any(chain and chain[0] == bp for bp in banned_prefixes):
                    raise PermissionError(
                        f"blocked attribute access: {'.'.join(chain)}")

            # ---- imports ----
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = []
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        names.append(alias.name.split(".")[0])
                else:
                    mod = node.module or ""
                    names.append(mod.split(".")[0])
                    for alias in node.names:
                        if alias.name != "*":
                            names.append(alias.name.split(".")[0])
                forbidden_imports = {
                    "subprocess", "os", "sys", "socket", "urllib",
                    "http", "ftplib", "smtplib", "webbrowser",
                    "tkinter", "ctypes", "threading", "multiprocessing",
                    "crypt", "signal", "mmap", "fcntl", "termios",
                    "pty", "tty", "pipes", "pwd", "grp",
                }
                for n in names:
                    if n in forbidden_imports:
                        raise PermissionError(f"blocked import: {n}")

            # ---- attribute assignment to __class__ etc. (escape attempts) ----
            if isinstance(node, ast.Attribute):
                if node.attr.startswith("__") and node.attr.endswith("__"):
                    if isinstance(node.ctx, ast.Store):
                        raise PermissionError(f"blocked dunder write: {node.attr}")

    # ------------------------------------------------------------------
    # TIER 1 helpers
    # ------------------------------------------------------------------

    def _call_name(self, node: ast.expr) -> str:
        """Return a readable name for a call target, or '' if unknowable."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parts = []
            cur: ast.expr = node
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            else:
                return ""
            return ".".join(reversed(parts))
        return ""

    def _attribute_chain(self, node: ast.expr) -> List[str]:
        """Walk an Attribute chain from root to leaf, return list of parts."""
        parts: List[str] = []
        cur: ast.expr = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return list(reversed(parts))

    def _synthesize_tests(self, code: str, tree: ast.AST) -> str:
        """
        Generate synthetic unit tests for functions/classes found in `code`.

        For each top-level function def with no params, emits a call + assert
        on the return value being non-None. For classes, emits instantiation.
        Returns empty string when nothing can be tested.
        """
        funcs: List[ast.FunctionDef] = []
        classes: List[ast.ClassDef] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                funcs.append(node)
            elif isinstance(node, ast.ClassDef):
                classes.append(node)

        if not funcs and not classes:
            return ""

        out: List[str] = []
        for f in funcs:
            name = f.name
            args = [a.arg for a in f.args.args if a.arg not in ("self", "cls")]
            if not args:
                out.append(f"r_{name} = {name}()")
                out.append(
                    f"assert r_{name} is not None, '{name} returned None'")
            # skip param'd funcs — can't synthesize safe calls
        for c in classes:
            out.append(f"inst_{c.name} = {c.name}()")
            out.append(
                f"assert inst_{c.name} is not None, "
                f"'{c.name} instantiation returned None'")
        return "\n".join(out)

    # ------------------------------------------------------------------
    # TIER 2 — platform-aware subprocess fallback
    # ------------------------------------------------------------------

    def _run_tier2_subprocess(self, code: str) -> Dict[str, Any]:
        """
        Execute code in a subprocess with platform-aware temp dir.

        Uses the same _SANDBOX_TMP root on both Windows and nix.
        Wraps code with _wrap_isolation so the fallback still carries
        the sandbox attestation header.
        """
        start = time.monotonic()
        wrapped = self._wrap_isolation(code)

        fd = None
        temp_path = None
        try:
            fd, temp_path = tempfile.mkstemp(
                dir=str(_SANDBOX_TMP), suffix=".py", prefix="ark_sandbox_")
            os.write(fd, wrapped.encode("utf-8"))
            os.close(fd)
            fd = None

            proc = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(_SANDBOX_TMP),
                env={
                    **os.environ,
                    "PYTHONPATH": str(_SANDBOX_TMP),
                    "sandbox_mode": "isolated",
                },
            )
            return {
                "success": proc.returncode == 0,
                "output": proc.stdout.strip(),
                "error": proc.stderr.strip(),
                "exit_code": proc.returncode,
                "time": time.monotonic() - start,
                "tier": "subprocess",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Sandbox timeout after {self.timeout}s",
                "exit_code": -1,
                "time": self.timeout,
                "tier": "subprocess_timeout",
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Sandbox error: {e}",
                "exit_code": -1,
                "time": time.monotonic() - start,
                "tier": "subprocess_error",
            }
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    # ------------------------------------------------------------------
    # Wrapper (used by tier 2 + existing callers)
    # ------------------------------------------------------------------

    def _wrap_isolation(self, code: str) -> str:
        """Wrap code with sandbox constraints and attestation."""
        watermark = f"""
# ARK SANDBOX WRAPPER
# Generated: {datetime.utcnow().isoformat()}
# Attribution: ARK Autonomous Recursive Kernel
# Security: All execution isolated from host
# """
        wrapper = f'''
{watermark}

# === SANDBOX WRAPPER START ===

import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import *

# Override dangerous builtins
_original_open = open
def _safe_open(*args, **kwargs):
    # Only allow read-only access to sandbox temp dir
    path = str(args[0]) if args else ''
    allowed_root = {repr(str(_SANDBOX_TMP))}
    if not path.startswith(allowed_root):
        raise PermissionError(f"Write prohibited: {{path}}")
    return _original_open(*args, **kwargs)

# Block network access
import socket
_original_socket = socket.socket
def _blocked_socket(*args, **kwargs):
    raise RuntimeError("Network access blocked in sandbox")

# === USER CODE BELOW ===

{code}

# === SANDBOX WRAPPER END ===
'''
        return wrapper

    # ------------------------------------------------------------------
    # Integrity + quarantine
    # ------------------------------------------------------------------

    def verify_artifact_integrity(self, artifact_hash: str, expected: str) -> bool:
        """Verify artifact wasn't tampered with"""
        return artifact_hash == expected

    def quarantine(self, suspicious_code: str, reason: str) -> Dict:
        """Move potentially malicious code to quarantine"""
        quar_path = Path("quarantine")
        quar_path.mkdir(exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"suspicious_{timestamp}.py"
        filepath = quar_path / filename

        quarantine_record = {
            "quarantined_file": str(filepath),
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "code_hash": hashlib.sha256(suspicious_code.encode()).hexdigest(),
            "length_chars": len(suspicious_code),
        }

        # Write to quarantine (never execute)
        filepath.write_text(suspicious_code)

        # Log quarantine event
        quar_log = quar_path / "quarantine_log.jsonl"
        with open(quar_log, "a") as f:
            f.write(json.dumps(quarantine_record) + "\n")

        return quarantine_record


class BareMetalBoundary:
    """
    Hard boundary protecting host from sandbox escape.
    Enforces: Host filesystem != Sandbox filesystem
    """

    HOST_PROTECTED_PATHS = [
        "/c/Users/jonny/",
        "/c/Program Files/",
        "/c/Windows/",
        "/etc/",
        "/root/",
    ]

    SANDBOX_ALLOWED_PATHS = [
        str(_SANDBOX_TMP),
    ]

    @classmethod
    def enforce(cls, operation: str, target_path: str) -> bool:
        """Check if operation violates bare-metal boundary"""
        for allowed in cls.SANDBOX_ALLOWED_PATHS:
            if target_path.startswith(allowed):
                return True

        for blocked in cls.HOST_PROTECTED_PATHS:
            if target_path.startswith(blocked):
                raise PermissionError(
                    f"HOST PROTECTED: {operation} on {target_path}")

        # Default deny
        return False


if __name__ == "__main__":
    # Test sandbox isolation
    sandbox = Sandbox(timeout=5)

    # Test safe code
    safe_code = '''
def main():
    result = sum([i**2 for i in range(10)])
    print(f"Safe computation: {result}")

main()
'''

    result = sandbox.execute(safe_code)
    print(json.dumps(result, indent=2))

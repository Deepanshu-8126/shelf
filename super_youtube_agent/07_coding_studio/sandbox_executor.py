"""
Python Sandbox Execution Engine for Channel 7.
Safely executes student/teacher snippets, records runtime in ms,
captures stdout, and formats terminal trace output.
"""
from __future__ import annotations
import subprocess
import sys
import time
from typing import Dict, Any, List


def run_code_in_sandbox(code_str: str, timeout_sec: float = 3.0) -> Dict[str, Any]:
    """
    Executes Python code in an isolated subprocess.
    Returns:
    {
        "success": bool,
        "runtime_ms": float,
        "output_lines": list[str],
        "stdout": str,
        "error": str
    }
    """
    if not code_str.strip():
        return {
            "success": True,
            "runtime_ms": 0.0,
            "output_lines": ["[+] No executable payload provided."],
            "stdout": "",
            "error": ""
        }

    t0 = time.perf_counter()
    try:
        res = subprocess.run(
            [sys.executable, "-c", code_str],
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        raw_stdout = res.stdout.strip()
        raw_stderr = res.stderr.strip()
        lines = [line.strip() for line in raw_stdout.split("\n") if line.strip()] if raw_stdout else []

        if res.returncode != 0:
            lines.append(f"❌ Error (code {res.returncode}): {raw_stderr[:80]}")
            return {
                "success": False,
                "runtime_ms": round(elapsed_ms, 2),
                "output_lines": lines,
                "stdout": raw_stdout,
                "error": raw_stderr
            }

        return {
            "success": True,
            "runtime_ms": round(elapsed_ms, 2),
            "output_lines": lines,
            "stdout": raw_stdout,
            "error": ""
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "runtime_ms": timeout_sec * 1000.0,
            "output_lines": [f"⚠️ Execution timed out after {timeout_sec}s"],
            "stdout": "",
            "error": "TimeoutExpired"
        }
    except Exception as e:
        return {
            "success": False,
            "runtime_ms": 0.0,
            "output_lines": [f"⚠️ Execution failure: {str(e)[:80]}"],
            "stdout": "",
            "error": str(e)
        }

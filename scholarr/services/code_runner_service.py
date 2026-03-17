"""Sandboxed code execution service for note editor code blocks."""

import asyncio
import logging
import tempfile
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Safety limits
MAX_EXEC_TIME = 10  # seconds
MAX_OUTPUT_SIZE = 50_000  # characters
ALLOWED_LANGUAGES = {"python", "javascript", "bash"}


async def run_code(language: str, code: str) -> dict:
    """Execute code in a sandboxed subprocess and return output."""
    if language not in ALLOWED_LANGUAGES:
        return {"success": False, "output": f"Unsupported language: {language}", "error": True}

    if not code.strip():
        return {"success": True, "output": "", "error": False}

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=_ext(language), delete=False, dir=tempfile.gettempdir()
        ) as f:
            f.write(code)
            tmp_path = f.name

        cmd = _command(language, tmp_path)
        if not cmd:
            return {"success": False, "output": "Could not determine runner", "error": True}

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=_safe_env(),
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=MAX_EXEC_TIME
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {"success": False, "output": f"Execution timed out ({MAX_EXEC_TIME}s limit)", "error": True}

        output = stdout.decode("utf-8", errors="replace")
        err_output = stderr.decode("utf-8", errors="replace")

        combined = output
        if err_output:
            combined = output + ("\n" if output else "") + err_output

        # Truncate if too long
        if len(combined) > MAX_OUTPUT_SIZE:
            combined = combined[:MAX_OUTPUT_SIZE] + f"\n... (truncated at {MAX_OUTPUT_SIZE} chars)"

        return {
            "success": proc.returncode == 0,
            "output": combined,
            "error": proc.returncode != 0,
            "exit_code": proc.returncode,
        }

    except Exception as e:
        logger.error(f"Code execution error: {e}")
        return {"success": False, "output": str(e), "error": True}
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _ext(lang: str) -> str:
    return {
        "python": ".py",
        "javascript": ".js",
        "bash": ".sh",
    }.get(lang, ".txt")


def _command(lang: str, path: str) -> list[str] | None:
    if lang == "python":
        return ["python3", "-u", path]
    elif lang == "javascript":
        return ["node", path]
    elif lang == "bash":
        return ["bash", path]
    return None


def _safe_env() -> dict:
    """Minimal environment for sandboxed execution."""
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": tempfile.gettempdir(),
        "LANG": "en_US.UTF-8",
    }
    # Inherit Python path for imports
    if "PYTHONPATH" in os.environ:
        env["PYTHONPATH"] = os.environ["PYTHONPATH"]
    return env

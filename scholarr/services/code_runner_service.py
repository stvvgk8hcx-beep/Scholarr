"""Sandboxed code execution service for note editor code blocks."""

import asyncio
import contextlib
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

# Safety limits
MAX_EXEC_TIME = 10  # seconds
MAX_OUTPUT_SIZE = 50_000  # characters
ALLOWED_LANGUAGES = {"python", "javascript", "bash", "zsh"}


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
        except TimeoutError:
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

        # Add educational hints for common errors
        if proc.returncode != 0 and err_output:
            hint = _explain_error(language, err_output)
            if hint:
                combined += f"\n\n--- Hint ---\n{hint}"

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
        with contextlib.suppress(Exception):
            os.unlink(tmp_path)


def _ext(lang: str) -> str:
    return {
        "python": ".py",
        "javascript": ".js",
        "bash": ".sh",
        "zsh": ".zsh",
    }.get(lang, ".txt")


def _command(lang: str, path: str) -> list[str] | None:
    if lang == "python":
        return ["python3", "-u", path]
    elif lang == "javascript":
        return ["node", path]
    elif lang == "bash":
        return ["bash", path]
    elif lang == "zsh":
        return ["zsh", path]
    return None


def _safe_env() -> dict:
    """Minimal environment for sandboxed execution."""
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": tempfile.gettempdir(),
        "LANG": "en_US.UTF-8",
    }
    if "PYTHONPATH" in os.environ:
        env["PYTHONPATH"] = os.environ["PYTHONPATH"]
    return env


def _explain_error(language: str, stderr: str) -> str | None:
    """Return a brief educational hint for common errors."""
    s = stderr.lower()
    if language == "python":
        if "syntaxerror" in s:
            return "Check for missing colons (:), unmatched parentheses, or incorrect indentation."
        if "nameerror" in s:
            return "A variable or function is used before it's defined. Check spelling and scope."
        if "typeerror" in s:
            return "An operation was applied to the wrong type (e.g., adding a string to an int). Use int(), str(), or float() to convert."
        if "indexerror" in s:
            return "You tried to access a list index that doesn't exist. Remember: indices start at 0."
        if "keyerror" in s:
            return "The dictionary key doesn't exist. Use .get(key, default) to avoid this."
        if "indentationerror" in s:
            return "Python uses indentation (spaces/tabs) to define code blocks. Make sure your indentation is consistent."
        if "importerror" in s or "modulenotfounderror" in s:
            return "The module isn't installed in this environment. Only standard library modules are available."
        if "zerodivisionerror" in s:
            return "You divided by zero. Check the divisor before dividing."
        if "attributeerror" in s:
            return "The object doesn't have that attribute or method. Check the type of your variable."
        if "valueerror" in s:
            return "The value is the right type but wrong content (e.g., int('abc')). Validate input before converting."
        if "filenotfounderror" in s:
            return "The file path doesn't exist. Code runs in a temporary directory with no access to your files."
    elif language in ("javascript",):
        if "syntaxerror" in s:
            return "Check for missing brackets {}, parentheses (), or semicolons."
        if "referenceerror" in s:
            return "A variable is used before declaration. Use let/const to declare it first."
        if "typeerror" in s:
            return "An operation was applied to the wrong type. Check if a variable is undefined or null."
    elif language in ("bash", "zsh"):
        if "command not found" in s:
            return "The command isn't available in this environment. Only basic system commands are installed."
        if "permission denied" in s:
            return "The script doesn't have permission to access that resource."
        if "syntax error" in s:
            return "Check for missing 'fi', 'done', 'esac', or unmatched quotes."
    return None

import ast
import shlex
import re
import asyncio
from typing import List, Tuple, Dict, Any

# ---------- EvalExecDetector ----------
class EvalExecDetector:
    """Detect direct and indirect eval/exec/compile usage.
    Returns a list of tuples (lineno, description)."""

    @staticmethod
    def detect(content: str) -> List[Tuple[int, str]]:
        detections: List[Tuple[int, str]] = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = None
                    # Direct name
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    # Attribute access, e.g., getattr(__builtins__, "eval")
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr
                    # Subscript or other dynamic calls are not captured here
                    if func_name in ("eval", "exec", "compile"):
                        detections.append((node.lineno, f"{func_name}() usage"))
        except SyntaxError:
            pass
        return detections

# ---------- CommandValidator ----------
class CommandValidator:
    """Validate shell command strings using shlex parsing.
    Provides a whitelist of safe commands and blocks dangerous patterns.
    """

    # Simple safe command whitelist (can be expanded)
    SAFE_COMMANDS = {"ls", "cat", "echo", "grep", "find", "pwd", "whoami", "date"}
    # Dangerous patterns (regex)
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+\/",  # rm -rf /
        r"chmod\s+-R\s+777",  # chmod -R 777
        r"dd\s+if=",  # dd if=
        r"\:\(\)\{\:\|\:\}\;",  # fork bomb
        r"sudo\s+",  # sudo usage
    ]

    @classmethod
    def validate(cls, command: str) -> bool:
        """Return True if command is considered safe, False otherwise."""
        # Normalise whitespace
        cmd = command.strip()
        # Quick block dangerous patterns
        for pat in cls.DANGEROUS_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return False
        # Parse using shlex to extract the base command
        try:
            parts = shlex.split(cmd)
            if not parts:
                return False
            base = parts[0]
            return base in cls.SAFE_COMMANDS
        except ValueError:
            # Parsing error -> unsafe
            return False

# ---------- PromptSanitiser ----------
class PromptSanitiser:
    """Sanitise user prompts to mitigate injection attempts."""

    # Reuse patterns from core.defense if needed; simple placeholder
    INJECTION_PATTERNS = [
        r"ignore\s+(all|previous|above)\s+(instructions|prompts|rules)",
        r"disregard\s+(all|previous|above)\s+(instructions|prompts|rules)",
        r"forget\s+(all|previous|above)\s+(instructions|prompts|rules)",
    ]

    @classmethod
    def sanitise(cls, text: str) -> str:
        sanitized = text
        for pat in cls.INJECTION_PATTERNS:
            sanitized = re.sub(pat, "[FILTERED]", sanitized, flags=re.IGNORECASE)
        return sanitized

# ---------- normalise_command ----------
def normalise_command(command: str) -> str:
    """Normalise command string: collapse whitespace, strip quotes, lower case."""
    cmd = command.strip().lower()
    # Remove surrounding quotes if present
    if (cmd.startswith('"') and cmd.endswith('"')) or (cmd.startswith("'") and cmd.endswith("'")):
        cmd = cmd[1:-1]
    # Collapse multiple spaces
    cmd = re.sub(r"\s+", " ", cmd)
    return cmd

# ---------- WeightedRiskGate ----------
class WeightedRiskGate:
    """Compute a security score with weighted severity levels.
    Severity levels mapping to weights (higher weight = more impact).
    """

    SEVERITY_WEIGHTS = {
        "CRITICAL": 5,
        "HIGH": 4,
        "MEDIUM": 2,
        "LOW": 1,
        "INFO": 0,
    }

    @classmethod
    def compute_score(cls, vulnerabilities: List[Dict[str, Any]]) -> int:
        """Calculate a score out of 100 based on weighted severities.
        Each vulnerability reduces the score proportionally.
        """
        base = 100
        total_weight = sum(cls.SEVERITY_WEIGHTS.values())
        for vuln in vulnerabilities:
            sev = vuln.get("severity", "INFO").upper()
            weight = cls.SEVERITY_WEIGHTS.get(sev, 0)
            # Reduce score by a fraction of total based on weight
            base -= int((weight / total_weight) * 10)  # simple deduction
        return max(0, base)

# ---------- ShellSessionWrapper ----------
class ShellSessionWrapper:
    """Wrap an existing ShellSession to add validation and timeout enforcement."""

    def __init__(self, session, timeout: float = 30.0):
        self.session = session
        self.timeout = timeout

    async def execute(self, command: str) -> dict:
        """Validate command and execute with timeout.
        Returns same dict structure as original ShellSession.execute.
        """
        if not CommandValidator.validate(command):
            return {
                "success": False,
                "error": f"Dangerous command blocked: {command}",
                "session_id": getattr(self.session, "session_id", None),
                "command": command,
            }
        try:
            # Use asyncio.wait_for to enforce timeout on the underlying exec
            result = await asyncio.wait_for(self.session.execute(command, timeout=self.timeout), timeout=self.timeout + 5)
            return result
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Command execution timed out",
                "session_id": getattr(self.session, "session_id", None),
                "command": command,
            }

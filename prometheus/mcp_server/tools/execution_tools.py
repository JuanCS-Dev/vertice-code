"""
Execution Tools for MCP Server
Secure command execution and background task management

This module provides 3 critical execution tools with
strong security validation, resource limits, and process management.
"""

import asyncio
import logging
import os
import re
import shlex
import signal
import subprocess
import threading
from typing import Dict, Optional
from .validated import create_validated_tool

logger = logging.getLogger(__name__)


# Security validator (simplified from exec_hardened.py)
class CommandSecurityValidator:
    """Validates bash commands for security."""

    BLACKLIST = {
        "rm -rf /",
        "rm -rf /*",
        "rm -rf ~",
        "rm -rf ~/*",
        "chmod -R 777",
        "chmod 777 /",
        "dd if=/dev/zero",
        "dd if=/dev/random",
        "mkfs",
        "mkfs.ext4",
        ":(){ :|:& };:",  # Fork bomb
        "curl | sh",
        "wget | sh",
        "curl | bash",
        "wget | bash",
        "sudo ",
        "su ",
    }

    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",  # Any rm -rf on root
        r"chmod\s+-R\s+777",  # Recursive 777
        r"dd\s+if=/dev/(zero|random|urandom)",  # Disk destroyers
        r">\s*/dev/sd[a-z]",  # Writing to raw disk
        r"mkfs\.",  # Filesystem creation
        r":\(\)\{.*\|.*&\s*\}",  # Fork bombs
        r"eval.*\$\(",  # Code injection via eval
        r"\$\(.*curl",  # Remote code execution
        r"\$\(.*wget",  # Remote code execution
        r"(curl|wget).*\|\s*(sh|bash)",  # Piping curl/wget to shell
    ]

    @classmethod
    def validate(cls, command: str) -> tuple[bool, Optional[str]]:
        """Validate command is safe."""
        if not command or not command.strip():
            return False, "Empty command"

        cmd_lower = command.lower().strip()

        # Check blacklist
        for blocked in cls.BLACKLIST:
            if blocked in cmd_lower:
                return False, f"BLOCKED: Dangerous command '{blocked}'"

        # Check dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"BLOCKED: Dangerous pattern '{pattern}'"

        # Check excessive piping
        if command.count("|") > 10:
            return False, "Too many pipes (max 10)"

        # Check command length
        if len(command) > 4096:
            return False, "Command too long (max 4096 chars)"

        return True, None


# Simple task tracker (simplified from _parity_utils.py)
class TaskTracker:
    """Track background tasks."""

    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self._counter = 0

    def create_task(self, command: str, process: subprocess.Popen, status: str) -> str:
        """Create a new task."""
        self._counter += 1
        task_id = f"task_{self._counter}"
        self.tasks[task_id] = {
            "id": task_id,
            "command": command,
            "process": process,
            "status": status,
            "stdout": [],
            "stderr": [],
            "started_at": None,
            "completed_at": None,
            "return_code": None,
        }
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID."""
        return self.tasks.get(task_id)

    def find_task(self, task_id: str) -> Optional[Dict]:
        """Find task by ID."""
        return self.get_task(task_id)

    def list_tasks(self) -> list:
        """List all tasks."""
        return list(self.tasks.values())

    def update_status(self, task_id: str, status: str, return_code: Optional[int] = None):
        """Update task status."""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status
            self.tasks[task_id]["return_code"] = return_code
            if status in ("completed", "failed", "killed"):
                self.tasks[task_id]["completed_at"] = None  # Would set timestamp

    def append_output(self, task_id: str, stdout: str = "", stderr: str = ""):
        """Append output to task."""
        if task_id in self.tasks:
            if stdout:
                self.tasks[task_id]["stdout"].append(stdout)
            if stderr:
                self.tasks[task_id]["stderr"].append(stderr)


# Global task tracker
_task_tracker = TaskTracker()


# Tool 1: Bash Command
async def bash_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 30,
    env: Optional[Dict[str, str]] = None,
) -> dict:
    """Execute shell command with security validation."""
    # Validate command
    is_valid, error_msg = CommandSecurityValidator.validate(command)
    if not is_valid:
        return {"success": False, "error": error_msg}

    # Validate timeout
    if timeout > 300:  # Max 5 minutes
        timeout = 300

    try:
        # Setup environment
        exec_env = os.environ.copy()
        exec_env["PATH"] = "/usr/local/bin:/usr/bin:/bin"  # Restricted PATH

        if env:
            # Filter dangerous env vars
            safe_env = {
                k: v
                for k, v in env.items()
                if k not in ["LD_PRELOAD", "LD_LIBRARY_PATH", "BASH_ENV"]
            }
            exec_env.update(safe_env)

        # Execute command
        logger.info(f"EXECUTING: {command[:100]}... (timeout={timeout}s)")

        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=exec_env,
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

            # Truncate if too large (1MB limit)
            max_size = 1024 * 1024
            if len(stdout_str) > max_size:
                stdout_str = stdout_str[:max_size] + "\n\n[OUTPUT TRUNCATED]"
            if len(stderr_str) > max_size:
                stderr_str = stderr_str[:max_size] + "\n\n[OUTPUT TRUNCATED]"

            return {
                "success": proc.returncode == 0,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "exit_code": proc.returncode,
                "command": command[:200],
            }

        except asyncio.TimeoutError:
            try:
                proc.kill()
                await proc.wait()
            except:
                pass
            return {"success": False, "error": f"Command timeout after {timeout}s"}

    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return {"success": False, "error": str(e)}


# Tool 2: Background Task
async def background_task(
    action: str,
    command: Optional[str] = None,
    task_id: Optional[str] = None,
) -> dict:
    """Manage background tasks."""
    if action == "start":
        if not command:
            return {"success": False, "error": "command required for start"}

        # Validate command
        is_valid, error_msg = CommandSecurityValidator.validate(command)
        if not is_valid:
            return {"success": False, "error": error_msg}

        try:
            # Parse command safely
            args = shlex.split(command)
            if not args:
                return {"success": False, "error": "Empty command"}

            # Start process
            process = subprocess.Popen(
                args,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Create task
            task_id = _task_tracker.create_task(command, process, "running")

            # Start output collector
            collector = threading.Thread(target=_collect_output, args=(task_id,), daemon=True)
            collector.start()

            return {
                "success": True,
                "task_id": task_id,
                "command": command[:100],
                "status": "started",
                "pid": process.pid,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    elif action == "list":
        tasks = _task_tracker.list_tasks()

        # Update statuses
        for task in tasks:
            if task.get("status") == "running":
                proc = task.get("process")
                if proc and proc.poll() is not None:
                    _task_tracker.update_status(
                        task["id"],
                        "completed" if proc.returncode == 0 else "failed",
                        proc.returncode,
                    )

        tasks = _task_tracker.list_tasks()
        tasks_info = [
            {
                "id": t["id"],
                "command": t["command"][:50],
                "status": t["status"],
                "start_time": t.get("started_at"),
            }
            for t in tasks
        ]

        return {"success": True, "tasks": tasks_info, "count": len(tasks_info)}

    elif action == "status":
        if not task_id:
            return {"success": False, "error": "task_id required for status"}

        task = _task_tracker.find_task(task_id)
        if not task:
            return {"success": False, "error": f"Task not found: {task_id}"}

        # Update status if process finished
        proc = task.get("process")
        if proc and task["status"] == "running" and proc.poll() is not None:
            _task_tracker.update_status(
                task["id"], "completed" if proc.returncode == 0 else "failed", proc.returncode
            )
            task = _task_tracker.get_task(task["id"])

        return {
            "success": True,
            "task": {
                "id": task["id"],
                "command": task["command"],
                "status": task["status"],
                "return_code": task.get("return_code"),
                "started_at": task.get("started_at"),
                "completed_at": task.get("completed_at"),
            },
        }

    elif action == "output":
        if not task_id:
            return {"success": False, "error": "task_id required for output"}

        task = _task_tracker.find_task(task_id)
        if not task:
            return {"success": False, "error": f"Task not found: {task_id}"}

        return {
            "success": True,
            "stdout": "\n".join(task.get("stdout", [])),
            "stderr": "\n".join(task.get("stderr", [])),
            "status": task["status"],
        }

    elif action == "kill":
        if not task_id:
            return {"success": False, "error": "task_id required for kill"}

        task = _task_tracker.find_task(task_id)
        if not task:
            return {"success": False, "error": f"Task not found: {task_id}"}

        if task["status"] in ("completed", "failed", "killed"):
            return {
                "success": True,
                "message": f"Task already {task['status']}",
                "status": task["status"],
            }

        proc = task.get("process")
        if proc:
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=1)

                _task_tracker.update_status(task_id, "killed", -signal.SIGTERM)
                return {
                    "success": True,
                    "message": "Task terminated",
                    "status": "killed",
                }
            except Exception as e:
                return {"success": False, "error": f"Failed to kill task: {e}"}

        return {"success": False, "error": "No process associated with task"}

    else:
        return {"success": False, "error": f"Unknown action: {action}"}


def _collect_output(task_id: str):
    """Collect output from background process."""
    task = _task_tracker.get_task(task_id)
    if not task:
        return

    proc = task.get("process")
    if not proc:
        return

    try:
        stdout, stderr = proc.communicate()

        if stdout:
            _task_tracker.append_output(task_id, stdout=stdout)

        if stderr:
            _task_tracker.append_output(task_id, stderr=stderr)

        return_code = proc.returncode
        status = "completed" if return_code == 0 else "failed"
        _task_tracker.update_status(task_id, status, return_code)

    except Exception as e:
        logger.error(f"Output collection error for {task_id}: {e}")
        _task_tracker.update_status(task_id, "failed", -1)


# Tool 3: Kill Shell
async def kill_shell(shell_id: str) -> dict:
    """Kill a background shell."""
    if not shell_id:
        return {"success": False, "error": "shell_id required"}

    task = _task_tracker.find_task(shell_id)
    if not task:
        return {"success": False, "error": f"Shell not found: {shell_id}"}

    if task["status"] in ("completed", "failed", "killed"):
        return {
            "success": True,
            "message": f"Shell already {task['status']}",
            "status": task["status"],
        }

    proc = task.get("process")
    if proc:
        try:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=1)

            _task_tracker.update_status(shell_id, "killed", -signal.SIGTERM)
            return {
                "success": True,
                "message": "Shell terminated",
                "status": "killed",
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to kill shell: {e}"}

    return {"success": False, "error": "No process associated with shell"}


# Create and register all execution tools
execution_tools = [
    create_validated_tool(
        name="bash_command",
        description="Execute shell command with security validation and resource limits",
        category="execution",
        parameters={
            "command": {
                "type": "string",
                "description": "Shell command to execute",
                "required": True,
            },
            "cwd": {"type": "string", "description": "Working directory"},
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (max 300)",
                "default": 30,
                "minimum": 1,
                "maximum": 300,
            },
            "env": {"type": "object", "description": "Environment variables"},
        },
        required_params=["command"],
        execute_func=bash_command,
    ),
    create_validated_tool(
        name="background_task",
        description="Manage background shell tasks (start, list, status, output, kill)",
        category="execution",
        parameters={
            "action": {
                "type": "string",
                "description": "Action: start, list, status, output, kill",
                "required": True,
                "enum": ["start", "list", "status", "output", "kill"],
            },
            "command": {"type": "string", "description": "Command to run (for start action)"},
            "task_id": {
                "type": "string",
                "description": "Task ID (for status/output/kill actions)",
            },
        },
        required_params=["action"],
        execute_func=background_task,
    ),
    create_validated_tool(
        name="kill_shell",
        description="Kill a running background shell",
        category="execution",
        parameters={
            "shell_id": {
                "type": "string",
                "description": "ID of the shell to kill",
                "required": True,
            }
        },
        required_params=["shell_id"],
        execute_func=kill_shell,
    ),
]

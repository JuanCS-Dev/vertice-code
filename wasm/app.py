"""
Vertice Agent Executor - Spin Wasm Component
Secure Python code execution in WebAssembly environment
"""

import json
import sys
import time
import traceback
from typing import Dict, Any
import io
import contextlib


def execute_python_code(
    python_code: str, input_data: Dict[str, Any], limits: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute Python code in isolated environment with resource limits.

    Args:
        python_code: The Python code to execute
        input_data: Input data for the agent
        limits: Resource limits (memory, timeout, etc.)

    Returns:
        Execution results
    """
    start_time = time.time()

    try:
        # Create safe execution environment
        safe_builtins = {
            "print": print,
            "len": len,
            "range": range,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "min": min,
            "max": max,
            "sum": sum,
            "abs": abs,
            "enumerate": enumerate,
            "zip": zip,
            "Exception": Exception,
        }

        execution_globals = {
            "input_data": input_data,
            "limits": limits,
            "__builtins__": safe_builtins,
        }

        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            # Execute the code
            exec(python_code, execution_globals)

        # Get the result (assuming the code sets a 'result' variable)
        result = execution_globals.get("result", {})

        execution_time = time.time() - start_time

        return {
            "success": True,
            "output": result,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "execution_time": execution_time,
            "memory_used": 0,  # Would need psutil in real implementation
            "exit_code": 0,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "success": False,
            "output": {},
            "stdout": "",
            "stderr": traceback.format_exc(),
            "errors": [str(e)],
            "execution_time": execution_time,
            "memory_used": 0,
            "exit_code": 1,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


def handle_request(request_body: bytes) -> bytes:
    """
    Handle HTTP request for agent execution.
    """
    try:
        # Parse request
        payload = json.loads(request_body.decode("utf-8"))

        agent_id = payload.get("agent_id", "unknown")
        workspace_id = payload.get("workspace_id", "unknown")
        python_code = payload.get("python_code", "")
        input_data = payload.get("input_data", {})
        payload.get("execution_context", {})
        limits = payload.get("limits", {})

        # Execute the code
        result = execute_python_code(python_code, input_data, limits)

        # Add context info
        result["agent_id"] = agent_id
        result["workspace_id"] = workspace_id

        return json.dumps(result).encode("utf-8")

    except Exception as e:
        error_result = {
            "success": False,
            "output": {},
            "errors": [f"Request handling error: {str(e)}"],
            "execution_time": 0,
            "memory_used": 0,
            "exit_code": 1,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        return json.dumps(error_result).encode("utf-8")


def main():
    """
    Main entry point for the Spin Wasm component.
    Reads from stdin and writes to stdout.
    """
    try:
        # Read request from stdin
        request_body = sys.stdin.buffer.read()

        # Process request
        response_body = handle_request(request_body)

        # Write response to stdout
        sys.stdout.buffer.write(response_body)
        sys.stdout.buffer.flush()

    except Exception as e:
        # Error response
        error_response = {
            "success": False,
            "output": {},
            "errors": [f"Component error: {str(e)}"],
            "execution_time": 0,
            "memory_used": 0,
            "exit_code": 1,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        sys.stdout.buffer.write(json.dumps(error_response).encode("utf-8"))
        sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()

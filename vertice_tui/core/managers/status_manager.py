"""
StatusManager - System Health and Permissions.

Extracted from Bridge as part of SCALE & SUSTAIN Phase 1.1.

Manages:
- System health checks
- Permission settings
- Sandbox mode

Author: JuanCS Dev
Date: 2025-11-26
"""

from typing import Any, Callable, Dict, Optional

from vertice_tui.core.interfaces import IStatusManager


class StatusManager(IStatusManager):
    """
    System status and health manager.

    Implements IStatusManager interface for:
    - Health checks across components
    - Permission management
    - Sandbox mode control
    """

    def __init__(
        self,
        llm_checker: Optional[Callable[[], bool]] = None,
        tool_counter: Optional[Callable[[], int]] = None,
        agent_counter: Optional[Callable[[], int]] = None,
    ):
        """
        Initialize StatusManager.

        Args:
            llm_checker: Callable that returns True if LLM is connected.
            tool_counter: Callable that returns tool count.
            agent_counter: Callable that returns agent count.
        """
        self._sandbox = False
        self._llm_checker = llm_checker
        self._tool_counter = tool_counter
        self._agent_counter = agent_counter

    def check_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Comprehensive system health check with detailed metrics.

        Returns:
            Dictionary with detailed health status for each component.
        """
        import time
        import psutil
        import os

        health = {}
        start_time = time.time()

        # System-level metrics
        health["System"] = self._check_system_health()

        # Check LLM with detailed metrics
        if self._llm_checker:
            llm_start = time.time()
            is_connected = self._llm_checker()
            llm_check_time = time.time() - llm_start

            health["LLM"] = {
                "ok": is_connected,
                "status": "healthy" if is_connected else "unhealthy",
                "message": "Connected" if is_connected else "Not connected",
                "response_time_ms": round(llm_check_time * 1000, 2),
                "last_check": time.time(),
            }
        else:
            health["LLM"] = {
                "ok": False,
                "status": "unhealthy",
                "message": "LLM checker not configured",
                "severity": "critical",
            }

        # Check tools with detailed metrics
        if self._tool_counter:
            tool_count = self._tool_counter()
            health["Tools"] = {
                "ok": tool_count > 0,
                "status": "healthy" if tool_count > 0 else "degraded",
                "message": f"{tool_count} tools loaded",
                "count": tool_count,
                "threshold": {"min": 1, "recommended": 10},
                "severity": "warning" if tool_count < 5 else "info",
            }
        else:
            health["Tools"] = {
                "ok": False,
                "status": "unhealthy",
                "message": "Tool counter not configured",
                "severity": "critical",
            }

        # Check agents with detailed metrics
        if self._agent_counter:
            agent_count = self._agent_counter()
            health["Agents"] = {
                "ok": agent_count > 0,
                "status": "healthy"
                if agent_count >= 3
                else "degraded"
                if agent_count > 0
                else "unhealthy",
                "message": f"{agent_count} agents available",
                "count": agent_count,
                "threshold": {"min": 1, "recommended": 5},
                "severity": "warning" if agent_count < 3 else "info",
            }
        else:
            health["Agents"] = {
                "ok": False,
                "status": "unhealthy",
                "message": "Agent counter not configured",
                "severity": "critical",
            }

        # Check sandbox status
        health["Sandbox"] = {
            "ok": True,
            "status": "healthy",
            "message": "Enabled" if self._sandbox else "Disabled",
            "enabled": self._sandbox,
            "severity": "info",
        }

        # Overall health assessment
        total_time = time.time() - start_time
        critical_issues = sum(
            1
            for component in health.values()
            if isinstance(component, dict) and component.get("severity") == "critical"
        )
        warning_issues = sum(
            1
            for component in health.values()
            if isinstance(component, dict) and component.get("severity") == "warning"
        )

        overall_status = "healthy"
        if critical_issues > 0:
            overall_status = "critical"
        elif warning_issues > 0:
            overall_status = "warning"

        health["Overall"] = {
            "ok": critical_issues == 0,
            "status": overall_status,
            "message": f"System {overall_status}: {critical_issues} critical, {warning_issues} warnings",
            "check_duration_ms": round(total_time * 1000, 2),
            "timestamp": time.time(),
            "critical_issues": critical_issues,
            "warning_issues": warning_issues,
            "total_components": len(health) - 2,  # Exclude System and Overall
        }

        return health

    def _check_system_health(self) -> Dict[str, Any]:
        """Check system-level health metrics."""
        try:
            import psutil
            import os

            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage_percent = memory.percent
            memory_usage_gb = round(memory.used / (1024**3), 2)

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_usage_percent = disk.percent

            # Process info
            process = psutil.Process(os.getpid())
            process_memory_mb = round(process.memory_info().rss / (1024**2), 2)
            process_cpu_percent = process.cpu_percent(interval=0.1)

            # Determine status based on thresholds
            status = "healthy"
            severity = "info"

            if memory_usage_percent > 90 or cpu_percent > 95 or disk_usage_percent > 95:
                status = "critical"
                severity = "critical"
            elif memory_usage_percent > 80 or cpu_percent > 80 or disk_usage_percent > 85:
                status = "warning"
                severity = "warning"

            return {
                "ok": status != "critical",
                "status": status,
                "severity": severity,
                "memory": {
                    "usage_percent": memory_usage_percent,
                    "usage_gb": memory_usage_gb,
                    "available_gb": round(memory.available / (1024**3), 2),
                },
                "cpu": {"usage_percent": cpu_percent},
                "disk": {"usage_percent": disk_usage_percent},
                "process": {
                    "memory_mb": process_memory_mb,
                    "cpu_percent": process_cpu_percent,
                    "pid": os.getpid(),
                },
            }

        except ImportError:
            return {
                "ok": True,
                "status": "degraded",
                "severity": "warning",
                "message": "psutil not available - limited system metrics",
                "memory": {"usage_percent": "unknown"},
                "cpu": {"usage_percent": "unknown"},
                "disk": {"usage_percent": "unknown"},
                "process": {"memory_mb": "unknown", "cpu_percent": "unknown"},
            }

        except Exception as e:
            return {
                "ok": False,
                "status": "error",
                "severity": "warning",
                "message": f"System health check failed: {e}",
                "error": str(e),
            }

    def get_permissions(self) -> Dict[str, bool]:
        """
        Get current system permissions.

        Returns:
            Dictionary of permission flags.
        """
        return {
            "read_files": True,
            "write_files": not self._sandbox,
            "execute_commands": not self._sandbox,
            "network_access": True,
            "sandbox_mode": self._sandbox,
        }

    def set_sandbox(self, enabled: bool) -> None:
        """
        Enable or disable sandbox mode.

        Args:
            enabled: True to enable sandbox mode.
        """
        self._sandbox = enabled

    def is_sandbox_enabled(self) -> bool:
        """
        Check if sandbox mode is enabled.

        Returns:
            True if sandbox mode is enabled.
        """
        return self._sandbox

    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of system status."""
        health = self.check_health()
        all_ok = all(comp.get("ok", False) for comp in health.values())
        return {
            "healthy": all_ok,
            "components": len(health),
            "failed": [name for name, status in health.items() if not status.get("ok", False)],
            "sandbox": self._sandbox,
        }

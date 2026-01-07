
import asyncio
import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AuditSwarm")

PROJECT_ROOT = Path("/media/juan/DATA/Vertice-Code")
REPORT_FILE = PROJECT_ROOT / "BRUTAL_AIRGAP_REPORT.md"

class AuditAgent:
    def __init__(self, name: str, mission: str):
        self.name = name
        self.mission = mission
        self.issues = []
        self.status = "PENDING"

    async def run(self):
        self.status = "RUNNING"
        try:
            await self.audit()
            if not self.issues:
                self.status = "PASSED"
            else:
                self.status = "FAILED"
        except Exception as e:
            self.status = "CRASHED"
            self.issues.append(f"CRITICAL: Agent crashed with error: {str(e)}")

    async def audit(self):
        raise NotImplementedError

    def report_issue(self, severity: str, description: str, location: str = "General"):
        self.issues.append({
            "severity": severity,
            "description": description,
            "location": location
        })

# --- Helper Functions ---
async def read_file_safe(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""

def get_python_files(root: Path):
    return root.rglob("*.py")

# --- The 10 Agents ---

class ProviderAudit(AuditAgent):
    async def audit(self):
        # Check Vertex AI
        env_loc = os.getenv("VERTEX_AI_LOCATION")
        if env_loc == "global":
            self.report_issue("CRITICAL", "VERTEX_AI_LOCATION is set to 'global'. This causes immediate 404s/crashes with recent SDKs.", ".env / Shell Env")
        
        # Check Imports to see if dependencies exist
        try:
            import google.generativeai
        except ImportError:
            self.report_issue("HIGH", "google.generativeai package missing (pip install google-generativeai)", "Environment")
            
        # Check Providers directory
        providers_dir = PROJECT_ROOT / "providers"
        if not providers_dir.exists():
            self.report_issue("MEDIUM", "Providers directory missing", "providers/")
        else:
            files = list(providers_dir.glob("*.py"))
            if not any("vertex_ai" in f.name for f in files):
                 self.report_issue("HIGH", "vertex_ai.py provider wrapper missing", "providers/")

class ToolingAudit(AuditAgent):
    async def audit(self):
        # We can't easily instantiate tools without deps, but we can check files
        tools_dir = PROJECT_ROOT / "vertice_cli" / "tools"
        if not tools_dir.exists():
             self.report_issue("MEDIUM", "vertice_cli/tools directory not found", str(tools_dir))
             return

        for tool_file in tools_dir.glob("*.py"):
            content = await read_file_safe(tool_file)
            if "class" in content and "(Tool)" in content:
                # Check for schema definition
                if "def get_schema" not in content and "def _get_schema" not in content:
                     self.report_issue("HIGH", f"Tool {tool_file.name} lacks explicit get_schema method. May fail JSON serialization.", tool_file.name)
                
                # Check for return type
                if "-> dict" not in content and "-> Dict" not in content:
                     self.report_issue("MEDIUM", f"Tool {tool_file.name} missing type hints on schema/execute.", tool_file.name)

class CoderAuditAgent(AuditAgent):
    async def audit(self) -> Dict:
        self.log("Inspecting CoderAgent capabilities...")
        try:
            # Dynamically import CoderAgent to avoid circular dependencies or missing imports
            # This assumes the current working directory or PROJECT_ROOT is in sys.path
            sys.path.insert(0, str(PROJECT_ROOT))
            from agents.coder.agent import CoderAgent
            sys.path.pop(0) # Clean up sys.path
            
            agent = CoderAgent()
            
            # Check 1: Tool Definitions
            # We can't easily check private methods, but we can check if tools are imported
            content = await self.read_file("agents/coder/agent.py")
            if "WriteFileTool" not in content:
                 self.report_issue("CRITICAL", "CoderAgent missing WriteFileTool import", "agents/coder/agent.py")
            
            # Check 2: System Prompt Injection
            if "DO NOT wrap tool calls in markdown" not in agent.SYSTEM_PROMPT:
                self.report_issue("CRITICAL", "CoderAgent System Prompt missing text-based tool forbidden instruction", "agents/coder/agent.py")
                
            # Check 3: Regex Robustness (Static Check for the new pattern)
            # Using a more robust regex pattern check
            if not re.search(r"write_file\s*\(\s*['\"]", content): # Escaped regex roughly
                 self.report_issue("HIGH", "CoderAgent Regex seems to be the old fragile version", "agents/coder/agent.py")
            
            # Check 4: TextWrap import
            if "import textwrap" not in content:
                self.report_issue("MEDIUM", "CoderAgent missing textwrap for dedenting", "agents/coder/agent.py")

        except ImportError:
            self.report_issue("CRITICAL", "CoderAgent module not found. Check path or file existence.", "agents/coder/agent.py")
        except Exception as e:
            self.report_issue("CRITICAL", f"CoderAgent Instantiation Failed or Audit Error: {e}", "agents/coder/agent.py")
            
        return self.issues

class OrchestratorAudit(AuditAgent):
    async def audit(self):
        path = PROJECT_ROOT / "agents" / "orchestrator" / "agent.py"
        if not path.exists(): return
        
        content = await read_file_safe(path)
        
        # Truncation Check
        if "[:50]" in content or "[:100]" in content:
             self.report_issue("CRITICAL", "Orchestrator truncates user request ([:50] or similar) before passing to sub-agents. Context is destroyed.", "agents/orchestrator/agent.py")

        # Routing Check
        if "router" not in content.lower():
             self.report_issue("HIGH", "Orchestrator seems hardcoded, no dynamic router usage detected.", "agents/orchestrator/agent.py")

class ExceptionAudit(AuditAgent):
    async def audit(self):
        # Scan for bare excepts in core logic
        for py_file in get_python_files(PROJECT_ROOT / "core"):
            content = await read_file_safe(py_file)
            if "except Exception:" in content or "except:" in content:
                # Check if it has a raise or log
                if "pass" in content or "print" in content:
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if "except Exception:" in line or "except:" in line:
                            # Crude check for next line
                            if i+1 < len(lines) and ("pass" in lines[i+1] or "print" in lines[i+1]):
                                self.report_issue("HIGH", f"Silent swallow detected in {py_file.name}", f"Line {i+1}")

class EnvironmentAudit(AuditAgent):
    async def audit(self):
        env_file = PROJECT_ROOT / ".env"
        example_file = PROJECT_ROOT / ".env.example"
        
        if not env_file.exists():
            self.report_issue("CRITICAL", ".env file missing. System running blind.", ".env")
            return
            
        env_content = await read_file_safe(env_file)
        example_content = await read_file_safe(example_file)
        
        required_keys = re.findall(r'([A-Z_]+)=', example_content)
        present_keys = re.findall(r'([A-Z_]+)=', env_content)
        
        missing = set(required_keys) - set(present_keys)
        if missing:
            self.report_issue("HIGH", f"Missing environment variables: {', '.join(missing)}", ".env")

class TestAudit(AuditAgent):
    async def audit(self):
        test_dir = PROJECT_ROOT / "tests"
        if not test_dir.exists(): return
        
        skipped_count = 0
        empty_count = 0
        
        for test_file in test_dir.rglob("test_*.py"):
            content = await read_file_safe(test_file)
            skipped_count += content.count("@pytest.mark.skip")
            # Crude check for empty tests
            if "def test_" in content and "pass" in content:
                 # Refine this regex later if needed
                 pass
        
        if skipped_count > 10:
             self.report_issue("MEDIUM", f"High number of skipped tests detected ({skipped_count}). Mocks might be hiding failures.", "tests/")

class FileSystemAudit(AuditAgent):
    async def audit(self):
        # Check .gemini permissions
        gemini_dir = Path("/home/juan/.gemini")
        if not os.access(gemini_dir, os.W_OK):
             self.report_issue("CRITICAL", f"Cannot write to {gemini_dir}. Agents cannot persist memory.", str(gemini_dir))
        
        # Check Project write
        if not os.access(PROJECT_ROOT, os.W_OK):
             self.report_issue("CRITICAL", "Cannot write to Project Root.", str(PROJECT_ROOT))

class LogAudit(AuditAgent):
    async def audit(self):
        # Look for logs
        logs = list(PROJECT_ROOT.glob("*.log"))
        logs.extend(list((PROJECT_ROOT / "logs").glob("*.log")))
        
        found_errs = 0
        for log in logs:
            content = await read_file_safe(log)
            if "Error" in content or "Exception" in content or "Traceback" in content:
                found_errs += 1
                
        if found_errs > 0:
             self.report_issue("MEDIUM", f"Found {found_errs} log files containing existing Error traces. Review required.", "logs/")

class AgencyStructureAuditAgent(AuditAgent):
    async def audit(self) -> Dict:
        self.log("Auditing Agency Structure...")
        
        agency_file = PROJECT_ROOT / "core" / "agency.py"
        if not agency_file.exists():
             self.report_issue("HIGH", "core/agency.py missing. Central nervous system absent.", "core/agency.py")
             return
             
        # Check 1: Explorer Alias
        try:
            # Dynamically import Agency to avoid circular dependencies or missing imports
            sys.path.insert(0, str(PROJECT_ROOT))
            from core.agency import Agency
            sys.path.pop(0) # Clean up sys.path

            agency = Agency()
            agency._lazy_init() # Ensure agents are initialized
            if "explorer" not in agency._agents:
                 self.report_issue("CRITICAL", "Agency missing 'explorer' alias (User Requirement)", "core/agency.py")
            else:
                self.log("✅ Explorer Agent alias found.")
        except ImportError:
            self.report_issue("CRITICAL", "Agency module not found. Check path or file existence.", "core/agency.py")
        except Exception as e:
             self.report_issue("HIGH", f"Agency Instantiation Failed or Audit Error: {e}", "core/agency.py")

        content = await read_file_safe(agency_file)
        if "Agent" not in content:
             self.report_issue("HIGH", "Agency definition seems devoid of Agents.", "core/agency.py")

async def run_swarm():
    agents = [
        ProviderAudit("ProviderAudit", "Check Model & API Connectivity"),
        ToolingAudit("ToolingAudit", "Verify Tool Schemas"),
        CoderAuditAgent("CoderAudit", "Audit Code Gen Logic"),
        OrchestratorAudit("OrchestratorAudit", "Check Routing & Context"),
        ExceptionAudit("ExceptionAudit", "Find Swallowed Errors"),
        EnvironmentAudit("EnvironmentAudit", "Check Config Drift"),
        TestAudit("TestAudit", "Check Test Integrity"),
        FileSystemAudit("FileSystemAudit", "Verify Permissions"),
        LogAudit("LogAudit", "Scan for Zombie Logs"),
        AgencyStructureAuditAgent("AgencyAudit", "Verify Agency Structure")
    ]
    
    print(f"🚀 Launching 10-Agent Swarm Audit on {PROJECT_ROOT}...")
    start_time = datetime.now()
    
    await asyncio.gather(*(agent.run() for agent in agents))
    
    duration = datetime.now() - start_time
    print(f"🏁 Audit Complete in {duration.total_seconds():.2f}s")
    
    generate_report(agents)

def generate_report(agents: List[AuditAgent]):
    total_issues = sum(len(a.issues) for a in agents)
    
    md_report = f"""# BRUTAL AIRGAP REPORT
    
**Date:** {datetime.now().isoformat()}
**Total Issues Found:** {total_issues}

## Executive Summary
Per user instruction, we searched for AIRGAPS—silent failures where integration breaks.

"""
    
    for agent in agents:
        icon = "✅" if agent.status == "PASSED" else "❌" if agent.status == "FAILED" else "⚠️"
        md_report += f"### {icon} Agent: {agent.name}\n"
        md_report += f"**Mission:** {agent.mission}\n"
        
        if not agent.issues:
            md_report += "- *No issues found.*\n"
        else:
            for issue in agent.issues:
                if isinstance(issue, str):
                    md_report += f"- 🚨 **CRITICAL**: {issue}\n"
                else:
                    md_report += f"- **{issue['severity']}** [{issue['location']}]: {issue['description']}\n"
        md_report += "\n"

    print(md_report)
    with open(REPORT_FILE, "w") as f:
        f.write(md_report)
    print(f"Report saved to {REPORT_FILE}")

if __name__ == "__main__":
    try:
        asyncio.run(run_swarm())
    except Exception as e:
        print(f"Swarm Fatal Error: {e}")

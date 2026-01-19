#!/usr/bin/env python3
"""
Gather System Context Script.
Launches 12 Core Agents in parallel to analyze the system and generate a comprehensive context report.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vertice_cli.core.llm import LLMClient
from vertice_cli.core.mcp_client import MCPClient
from vertice_cli.agents.base import AgentTask
from vertice_cli.agents.planner import PlannerAgent
from vertice_cli.agents.reviewer import ReviewerAgent
from vertice_cli.agents.refactorer import RefactorerAgent
from vertice_cli.agents.explorer import ExplorerAgent
from vertice_cli.agents.executor import NextGenExecutorAgent, ExecutionMode, SecurityLevel
from vertice_cli.agents.architect import ArchitectAgent
from vertice_cli.agents.security import SecurityAgent
from vertice_cli.agents.performance import PerformanceAgent
from vertice_cli.agents.testing import TestRunnerAgent
from vertice_cli.agents.documentation import DocumentationAgent
from vertice_cli.agents.data_agent_production import create_data_agent
from vertice_cli.agents.devops import create_devops_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_agent(name: str, agent, prompt: str) -> Dict:
    """Run a single agent and return the result."""
    logger.info(f"🚀 Launching {name}...")
    try:
        task = AgentTask(
            request=prompt,
            context={"system_context_gathering": True},
            metadata={
                "interface": "gather_context_script",
                "timestamp": datetime.now().isoformat(),
            },
        )
        # Handle streaming agents vs regular agents
        if hasattr(agent, "execute_streaming"):
            # Consume stream for result (simplified)
            result = None
            async for update in agent.execute_streaming(task):
                if update.get("type") == "result":
                    result = update.get("data")
            response = result
        else:
            response = await agent.execute(task)

        logger.info(f"✅ {name} finished.")
        return {
            "name": name,
            "success": True,
            "data": response.data if hasattr(response, "data") else response,
        }
    except Exception as e:
        logger.error(f"❌ {name} failed: {e}")
        return {"name": name, "success": False, "error": str(e)}


async def main():
    load_dotenv()

    logger.info("Initializing Clients...")
    llm = LLMClient()
    mcp = MCPClient()

    logger.info("Initializing Agents...")
    explorer = ExplorerAgent(llm, mcp)

    agents = {
        "Executor": NextGenExecutorAgent(
            llm,
            mcp,
            execution_mode=ExecutionMode.LOCAL,
            security_level=SecurityLevel.PERMISSIVE,
            approval_callback=None,
        ),
        "Explorer": explorer,
        "Planner": PlannerAgent(llm, mcp),
        "Reviewer": ReviewerAgent(llm, mcp),
        "Refactorer": RefactorerAgent(llm, mcp, explorer),
        "Architect": ArchitectAgent(llm, mcp),
        "Security": SecurityAgent(llm, mcp),
        "Performance": PerformanceAgent(llm, mcp),
        "Testing": TestRunnerAgent(llm, mcp),
        "Documentation": DocumentationAgent(llm, mcp),
        "Data": create_data_agent(llm, mcp),
        "DevOps": create_devops_agent(llm, mcp),
    }

    # Define prompts for each agent to gather context
    prompts = {
        "Executor": "List the top-level directories and files in current directory to verify basic access.",
        "Explorer": "Analyze the project structure and identifying key components and relationships. map the 'core' module.",
        "Planner": "create a high-level roadmap for 'System Overhaul' based on standard best practices for a python project.",
        "Reviewer": "Review 'scripts/maestro_v10_integrated.py' and identify potential code quality issues.",
        "Refactorer": "Identify one file in 'vertice_tui' that needs refactoring and propose changes (do not apply).",
        "Architect": "Describe the likely high-level architecture of this system based on the file structure 'vertice_cli', 'vertice_tui', 'providers'.",
        "Security": "Scan 'providers/vertex_ai.py' for potential security risks or bad practices.",
        "Performance": "Analyze 'vertice_tui/core/streaming/gemini/config.py' for potential performance bottlenecks.",
        "Testing": "Suggest a test plan for 'vertice_cli/agents/manager.py'.",
        "Documentation": "Generate a summary overview for 'vertice_cli/agents/base.py'.",
        "Data": "Analyze if there are any obvious database schema definitions in 'vertice_cli/schemas' or similar.",
        "DevOps": "Check for Dockerfile or CI/CD configuration files in the root directory.",
    }

    logger.info("Running 12 Agents in Parallel...")
    tasks = []
    for name, agent in agents.items():
        if name in prompts:
            tasks.append(run_agent(name, agent, prompts[name]))

    results = await asyncio.gather(*tasks)

    # Generate Report
    report_content = "# System Context Report\n\n"
    report_content += f"Generated at: {datetime.now().isoformat()}\n\n"

    for res in results:
        status = "✅" if res["success"] else "❌"
        report_content += f"## {status} {res['name']}\n\n"
        if res["success"]:
            report_content += f"{res['data']}\n\n"
        else:
            report_content += f"Error: {res['error']}\n\n"

    output_path = "/home/juan/.gemini/antigravity/brain/a9b1ab8b-6794-4156-b7cb-d58d8cf81640/SYSTEM_CONTEXT_REPORT.md"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report_content)

    logger.info(f"Report saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())

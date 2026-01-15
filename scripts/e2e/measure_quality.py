
import sys
import os
import asyncio
import ast
from typing import AsyncIterator, List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

try:
    from vertice_tui.core.chat.controller import ChatController
    from vertice_tui.core.bridge import ToolBridge, AgentManager, GovernanceObserver
    from vertice_cli.tools.base import ToolRegistry
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

class ScriptedLLM:
    """A deterministic LLM that follows a script of responses."""
    
    def __init__(self, script: List[str]):
        self.script = script
        self.script_index = 0
        
    async def stream(self, message: str, **kwargs) -> AsyncIterator[str]:
        """Yields the next response from the script."""
        if self.script_index < len(self.script):
            response = self.script[self.script_index]
            self.script_index += 1
            
            # Simulate streaming
            chunk_size = 10
            for i in range(0, len(response), chunk_size):
                yield response[i:i+chunk_size]
                await asyncio.sleep(0.01)
        else:
            yield "I have completed the task."


from unittest.mock import MagicMock
import argparse

async def run_quality_test():
    parser = argparse.ArgumentParser(description="Run TUI Quality Test")
    parser.add_argument("--real", action="store_true", help="Use real LLM via Bridge")
    parser.add_argument("--model", type=str, default="gemini-2.0-flash-exp", help="Model name for real execution")
    parser.add_argument("--scenario", type=str, default=None, help="Scenario name (e.g. complex_feature)")
    args = parser.parse_args()

    print("🚀 Starting Heavy Duty Quality Test...")
    print(f"   Mode: {'REAL LLM' if args.real else 'SCRIPTED (Mock)'}")
    
    # Load Scenario
    scenario_data = {}
    if args.scenario:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("scenario", f"scripts/e2e/scenarios/{args.scenario}.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            scenario_data['setup'] = getattr(module, 'SETUP_FILES', {})
            scenario_data['prompt'] = getattr(module, 'PROMPT', "")
            scenario_data['validation'] = getattr(module, 'VALIDATION_RULES', [])
            scenario_data['expected'] = getattr(module, 'EXPECTED_FILES', [])
            print(f"   Loaded Scenario: {args.scenario}")
        except Exception as e:
            print(f"❌ Failed to load scenario {args.scenario}: {e}")
            return
    else:
        # Default Fibonacci
        scenario_data['setup'] = {}
        scenario_data['prompt'] = "Create a fibonacci script"
        # ... (Validation logic below needs to be generic or adapt)
        # For default, we stick to the inline logic or minimal adaptation
        pass

    # Setup Setup Files
    for name, content in scenario_data.get('setup', {}).items():
        with open(name, "w") as f:
            f.write(content)
        print(f"   Prepared setup file: {name}")

    # 1. Infrastructure
    print("1. Initializing TUI Core...")
    
    if args.real:
        from vertice_tui.core.bridge import get_bridge
        bridge = get_bridge()
        if not bridge.is_connected:
            print("❌ Error: Bridge not connected to LLM. Check credentials.")
            return
            
        print(f"   Connected to: {bridge.get_model_name()}")
        
        controller = ChatController(
            tools=bridge.tools,
            history=bridge.history,
            governance=bridge.governance,
            agents=bridge.agents,
            agent_registry=bridge.agents._agents if hasattr(bridge.agents, '_agents') else {}
        )
        llm = bridge.llm
        system_prompt = bridge._get_system_prompt()
        
    else:
        # MOCKED / SCRIPTED MODE
        # If scenario is provided, we need a script for it. 
        # Generating a dynamic script for complex scenarios is hard.
        # So we only support Default Fibonacci in Mock mode for now, 
        # UNLESS we define a 'MOCK_SCRIPT' in the scenario file?
        # Let's keep mock simple: strict Fibonacci
        
        if args.scenario:
            print("⚠️ Mock mode only supports default Fibonacci scenario fully. Running with generic mock response...")
            script = ["I am a mock response. I cannot execute dynamic scenarios without a predefined script."]
        else:
            # Default Fib Script
            fib_code = "def fibonacci(n): return n if n<=1 else fib(n-1)+fib(n-2)"
            import json
            tool_args = json.dumps({"path": "fib_output.py", "content": fib_code})
            script = [
                f"I will write a Fibonacci script.\n[TOOL_CALL:write_file:{tool_args}]",
                "I have created 'fib_output.py'. You can run it now."
            ]
            
        bridge = ToolBridge()
        agent_manager = AgentManager(llm_client=None)
        governance = GovernanceObserver()
        history = MagicMock()
        
        llm = ScriptedLLM(script)
        
        controller = ChatController(
            tools=bridge,
            history=history,
            governance=governance,
            agents=agent_manager,
            agent_registry={}
        )
        controller.agents.router = type('MockRouter', (), {
            "route": lambda self, m: None, 
            "get_routing_suggestion": lambda self, m: None
        })()
        system_prompt = "You are a helpful assistant."

    print("2. Infrastructure Ready. Starting Simulation...")
    prompt = scenario_data.get('prompt', "Create a fibonacci script")
    print(f"   User Request: '{prompt[:50]}...'")
    
    # 3. Execution Loop
    try:
        async for chunk in controller.chat(llm, prompt, system_prompt):
            print(chunk, end='', flush=True)
    except Exception as e:
        print(f"\n❌ Execution Error: {e}")
        return

    print("\n\n3. Assessing Result Quality...")
    
    # Generic Validation
    if args.scenario:
        passed = 0
        total = len(scenario_data['validation'])
        for rule in scenario_data['validation']:
            try:
                if rule():
                    passed += 1
            except Exception as e:
                print(f"   Rule Check Failed: {e}")
        
        print(f"   Score: {passed}/{total}")
        if passed == total:
            print("   ✅ SCENARIO PASSED")
        else:
            print("   ❌ SCENARIO FAILED")
            
        # Cleanup
        for f in scenario_data.get('expected', []) + list(scenario_data.get('setup', {}).keys()):
            if os.path.exists(f):
                os.remove(f)
                
    else:
        # Default Fib Check (Legacy)
        if os.path.exists("fib_output.py"):
             print("   ✅ File 'fib_output.py' was created.")
             os.remove("fib_output.py")
        else:
             print("   ❌ File was NOT created.")

if __name__ == "__main__":
    asyncio.run(run_quality_test())

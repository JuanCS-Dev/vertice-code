import argparse
import sys
import os
import asyncio
import importlib.util

# Ensure we can import system components
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

# Force Vertex AI Configuration
os.environ["GOOGLE_CLOUD_PROJECT"] = "vertice-ai"
os.environ["VERTEX_AI_LOCATION"] = "us-central1"

from vertice_tui.core.bridge import get_bridge
from vertice_tui.core.chat.controller import ChatController
from vertice_cli.modes.noesis_mode import NoesisMode, ConsciousnessState


async def run_self_healing_session(scenario_name: str, max_retries: int = 3, model: str = None):
    print(f"🌌 Initializing Noesis Self-Healing Loop for scenario: '{scenario_name}'")

    # 1. Load Scenario
    try:
        spec = importlib.util.spec_from_file_location(
            "scenario", f"scripts/e2e/scenarios/{scenario_name}.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        setup_files = getattr(module, "SETUP_FILES", {})
        initial_prompt = getattr(module, "PROMPT", "")
        validation_rules = getattr(module, "VALIDATION_RULES", [])
        expected_files = getattr(module, "EXPECTED_FILES", [])
    except Exception as e:
        print(f"❌ Failed to load scenario: {e}")
        return

    # 2. Setup Environment
    for name, content in setup_files.items():
        with open(name, "w") as f:
            f.write(content)
        print(f"   📝 Created setup file: {name}")

    # 3. Initialize Bridge & Noesis
    bridge = get_bridge()
    if not bridge.is_connected:
        print("❌ Bridge not connected (Real LLM required).")
        return

    controller = ChatController(
        tools=bridge.tools,
        history=bridge.history,
        governance=bridge.governance,
        agents=bridge.agents,
        agent_registry=bridge.agents._agents if hasattr(bridge.agents, "_agents") else {},
    )
    print("   ✅ Bridge initialized.")
    if hasattr(bridge.llm, "set_provider"):
        bridge.llm.set_provider("vertex-ai")

    if hasattr(bridge.llm, "get_current_provider_name"):
        provider = bridge.llm.get_current_provider_name()
        print(f"   🤖 Active Provider: {provider.upper()}")
        if provider != "vertex-ai":
            print("   ⚠️  WARNING: Not using Vertex AI! Check configuration.")

    # 3. Mode Activation
    noesis = NoesisMode()
    await noesis.activate()
    print("   🧠 Noesis Mode: ACTIVATED")

    # 4. The Loop
    # Append tool use mandate with PYTHON FORMAT (Easier for Gemini)
    mandate = (
        "\nIMPORTANT: You must USE TOOLS to apply changes."
        "\nFORMAT: tool_name(arg='value')"
        "\nExample: write_file(path='file.py', content='print(1)')"
        "\nDo not use markdown code blocks or JSON blocks. Just write the function call."
    )
    current_prompt = initial_prompt + mandate

    history_ctx = []  # Keep context across retries if needed, or rely on bridge history

    for attempt in range(1, max_retries + 1):
        print(f"\n🔄 Attempt {attempt}/{max_retries}")
        print(f"   Prompt: {current_prompt[:60]}...")

        # Execute Generation
        response_text = ""
        try:
            async for chunk in controller.chat(
                bridge.llm, current_prompt, bridge._get_system_prompt()
            ):
                print(chunk, end="", flush=True)
                response_text += chunk
        except Exception as e:
            print(f"\n❌ LLM Error: {e}")
            import traceback

            traceback.print_exc()
            break

        print("\n\n   ⚖️ Tribunal Validation...")

        # Validate
        errors = []
        passed_count = 0
        for i, rule in enumerate(validation_rules):
            try:
                if rule():
                    passed_count += 1
                else:
                    errors.append(f"Rule {i+1} failed validation.")
            except Exception as e:
                errors.append(f"Rule {i+1} raised exception: {str(e)}")

        if len(errors) == 0:
            print("   ✅ SUCCESS! All validation rules passed.")
            noesis.consciousness_state = ConsciousnessState.VERDICT_READY
            break
        else:
            print(f"   ❌ FAILURE ({len(errors)} errors).")
            print(f"      Errors: {errors}")

            if attempt < max_retries:
                print("   🩹 Self-Healing Triggered: Feeding errors back to agent...")
                noesis.consciousness_state = ConsciousnessState.DEEP_REASONING
                # Update prompt with feedback
                current_prompt = (
                    f"The previous attempt failed with these errors:\n"
                    f"{chr(10).join(errors)}\n"
                    f"Please fix the code and try again.\n"
                    f"Ensure you RE-WRITE the files correctly."
                )
            else:
                print("   💀 Max retries reached. Noesis Loop terminated.")

    # Cleanup
    await noesis.deactivate()
    print("\n🏁 Session Complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()

    asyncio.run(run_self_healing_session(args.scenario, args.retries))

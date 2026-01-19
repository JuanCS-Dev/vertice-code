import asyncio
import os
import sys

# Ensure imports work
sys.path.insert(0, os.path.abspath("src"))

from providers.vertice_router import get_router, TaskComplexity


async def test_router_v3_e2e():
    print("🚀 E2E TEST: Router -> VertexAI (Gemini 3)")
    router = get_router()

    # Request a COMPLEX task (should route to pro-3)
    print("\nRouting COMPLEX task...")
    decision = router.route(
        task_description="Explain the architectural implications of Gemini 3's thinking mode.",
        complexity=TaskComplexity.COMPLEX,
    )

    print(f"Decision: {decision.provider_name} | {decision.model_name}")
    print(f"Reasoning: {decision.reasoning}")

    if decision.model_name == "pro-3":
        print("✅ Router correctly selected pro-3.")
    else:
        print(f"❌ Router selected {decision.model_name} instead of pro-3.")
        # Return if selection failed to avoid invalid provider call
        return

    # Execute Chat
    print("\nExecuting Stream Chat...")
    provider = router.get_provider(decision.provider_name)

    response_text = ""
    async for chunk in provider.stream_chat(
        messages=[{"role": "user", "content": "Briefly describe Gemini 3 features."}],
        model=decision.model_name,
    ):
        print(chunk, end="", flush=True)
        response_text += chunk

    print("\n\n✅ E2E SUCCESS!")


if __name__ == "__main__":
    # Ensure ADC is present
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        os.environ["GOOGLE_CLOUD_PROJECT"] = "vertice-ai"

    asyncio.run(test_router_v3_e2e())

import asyncio
import logging
import sys
import os

sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from vertice_cli.core.providers.anthropic_vertex import AnthropicVertexProvider


async def main():
    logger.info("Starting Global Location Audit for Protovolt Studio...")

    project_id = "protovolt-studio"
    # However, some docs suggest location="global" or "us-central1" (aggregated).
    # We will test "us-central1" (which acts as global often) AND "us-east5" (where we saw the model).
    # AND explicitly "global" if the SDK supports it (AnthropicVertex SDK usually requires a region, not 'global').

    # Let's test standard publishing regions again, assuming "Global" means "Standard Quota".

    regions = ["us-east5", "europe-west4", "us-central1"]

    logger.info(f"Target Project: {project_id}")

    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id

    models = ["opus-4.5", "sonnet-4.5"]

    for model in models:
        for region in regions:
            logger.info(f"--- Probing {model} in {region} ---")
            try:
                # We do NOT set os.environ["ANTHROPIC_VERTEX_LOCATION"] here to avoid polluting the loop
                # We pass it directly to constructor
                provider = AnthropicVertexProvider(
                    model_name=model, location=region, project=project_id
                )
                messages = [{"role": "user", "content": "Ping"}]

                response = await provider.generate(messages, max_tokens=1)
                logger.info(f"✅ SUCCESS {model} in {region}: {response}")
                # If one works, we are good?
            except Exception as e:
                logger.error(f"❌ FAILURE {model} in {region}: {e}")


if __name__ == "__main__":
    asyncio.run(main())

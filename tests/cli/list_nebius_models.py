
import asyncio
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

async def list_models():
    print("Listing Nebius Models...")
    try:
        from src.providers.nebius import NebiusProvider
        provider = NebiusProvider()
        
        if not provider.is_available():
            print("ERROR: Nebius Provider unavailable")
            return

        models = await provider.client.models.list()
        print("\nAvailable Models:")
        for model in models.data:
            print(f"- {model.id}")
            
    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())

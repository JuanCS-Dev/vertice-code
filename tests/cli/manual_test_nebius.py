
import asyncio
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

async def test_nebius():
    print("Testing Nebius Provider...")
    try:
        from src.providers.nebius import NebiusProvider
        provider = NebiusProvider()
        
        if not provider.is_available():
            print("ERROR: Nebius Provider unavailable (check API Key)")
            return

        print(f"Provider: {provider.model_name}")
        
        # Test Generation
        response = await provider.generate([{
            "role": "user", 
            "content": "Hello DeepSeek! Calculate 5 + 5."
        }])
        print(f"\nResponse:\n{response}")
        
    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_nebius())

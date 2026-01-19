import asyncio
import os
import sys

sys.path.append(os.getcwd())


async def test():
    print("Testing Nebius...")
    from src.providers.nebius import NebiusProvider

    p = NebiusProvider()
    res = await p.generate([{"role": "user", "content": "1+1"}])
    print(f"Nebius Result: {res}")


if __name__ == "__main__":
    asyncio.run(test())

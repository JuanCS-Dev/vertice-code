#!/usr/bin/env python3
"""
DEBUG FLASK TEST - Check what LLM actually generates
"""

import asyncio
from vertice_tui import VerticeApp


async def debug_flask():
    """Debug what the LLM generates for Flask."""
    app = VerticeApp()

    prompt = """
    Create a simple Flask app with one route that returns 'Hello World'.
    Include proper imports and app.run().
    """

    print("Prompt:", prompt)
    print("\nResponse:")
    print("=" * 50)

    chunks = []
    async for chunk in app.bridge.chat(prompt):
        chunks.append(chunk)
        print(chunk, end="", flush=True)

    response = "".join(chunks)
    print("\n" + "=" * 50)

    # Check for Flask elements
    flask_checks = {
        "from flask": "from flask" in response,
        "Flask": "Flask" in response,
        "app.route": "app.route" in response,
        "app.run": "app.run" in response,
        "Hello World": "Hello World" in response,
    }

    print("Flask elements found:")
    for element, found in flask_checks.items():
        status = "✓" if found else "✗"
        print(f"  {status} {element}")


if __name__ == "__main__":
    asyncio.run(debug_flask())

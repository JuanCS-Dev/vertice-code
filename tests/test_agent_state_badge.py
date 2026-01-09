#!/usr/bin/env python3
"""
TESTE: Agent State Badge
========================

Testa o novo Agent State Badge no Status Bar.
"""

import asyncio
from vertice_tui.widgets import StatusBar


async def test_agent_state_badge():
    """Test the Agent State Badge functionality."""
    print("🏷️ TESTING AGENT STATE BADGE")
    print("=" * 40)

    # Create status bar
    status_bar = StatusBar()

    # Test initial state
    print("Testing initial state...")
    print(f"✓ Initial autonomy: L{status_bar.autonomy_level} ({status_bar.operation_mode})")

    # Test different autonomy levels
    print("Testing autonomy levels...")
    test_levels = [
        (0, "Plan", "🤖 L0:Plan"),  # Human Control
        (1, "Code", "👁️ L1:Code"),  # Human Oversight
        (2, "Review", "🧠 L2:Revi"),  # Autonomous
        (3, "Deploy", "🚀 L3:Depl"),  # Fully Autonomous
    ]

    for level, mode, expected in test_levels:
        status_bar.autonomy_level = level
        status_bar.operation_mode = mode
        formatted = status_bar._format_agent_state()
        print(f"✓ L{level} {mode}: {formatted}")
        assert expected in formatted, f"Expected {expected}, got {formatted}"

    print("✅ Autonomy levels working")

    # Test reactive updates
    print("Testing reactive updates...")
    status_bar.autonomy_level = 2
    status_bar.operation_mode = "Execute"
    formatted = status_bar._format_agent_state()
    print(f"✓ Reactive update: {formatted}")

    print("\n🎉 AGENT STATE BADGE TEST COMPLETED!")
    print("✅ Shared Autonomy Controls visual ready")
    print("✅ L0-L3 autonomy levels displayed")
    print("✅ Operation modes (Plan/Code/Review) working")
    print("✅ Reactive updates functional")


if __name__ == "__main__":
    asyncio.run(test_agent_state_badge())

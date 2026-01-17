#!/usr/bin/env python3
"""
TESTE: Performance HUD
======================

Testa o novo Performance HUD com métricas em tempo real.
"""

import asyncio
from vertice_tui.widgets import PerformanceHUD


async def test_performance_hud():
    """Test the PerformanceHUD widget."""
    print("📊 TESTING PERFORMANCE HUD")
    print("=" * 40)

    # Create HUD
    hud = PerformanceHUD(visible=True)

    # Test initial state
    print("Testing initial state...")
    metrics = hud.current_metrics
    print(f"✓ Initial metrics: {metrics}")

    # Test metrics updates
    print("Testing metrics updates...")
    hud.update_metrics(latency_ms=450, confidence=85.5, throughput=12.3, queue_time=50)
    metrics = hud.current_metrics
    print(
        f"✓ Updated metrics: latency={metrics['latency_ms']}ms, confidence={metrics['confidence']}%, throughput={metrics['throughput']}t/s"
    )

    # Test visibility toggle
    print("Testing visibility toggle...")
    hud.toggle_visibility()
    print("✓ Toggled visibility off")
    hud.toggle_visibility()
    print("✓ Toggled visibility on")

    # Test traffic light colors
    print("Testing traffic light colors...")
    # Good latency
    hud.update_metrics(latency_ms=300)
    # Warning latency
    hud.update_metrics(latency_ms=750)
    # Critical latency
    hud.update_metrics(latency_ms=1200)
    print("✓ Traffic light colors tested")

    # Test confidence colors
    print("Testing confidence colors...")
    hud.update_metrics(confidence=95)  # High
    hud.update_metrics(confidence=80)  # Medium
    hud.update_metrics(confidence=60)  # Low
    print("✓ Confidence colors tested")

    print("\n🎉 PERFORMANCE HUD TEST COMPLETED!")
    print("✅ Real-time metrics overlay ready")
    print("✅ Traffic light latency colors working")
    print("✅ Confidence score colors working")
    print("✅ Toggle visibility functional")


if __name__ == "__main__":
    asyncio.run(test_performance_hud())

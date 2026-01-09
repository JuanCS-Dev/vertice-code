#!/usr/bin/env python3
"""
TESTE: Double Buffering & Viewport Buffering
===========================================

Testa as novas implementações de performance para 60fps.
"""

import asyncio
import time
from vertice_cli.tui.components.streaming_markdown.widget import StreamingMarkdownWidget


async def test_performance_improvements():
    """Test the new performance improvements."""
    print("🧪 TESTING DOUBLE BUFFERING & VIEWPORT BUFFERING")
    print("=" * 60)

    # Create widget
    widget = StreamingMarkdownWidget(target_fps=60)

    # Start streaming
    await widget.start_stream()

    # Test 1: Small content (should be fast)
    print("\n📝 Test 1: Small content rendering")
    start = time.time()
    await widget.append_chunk("Hello **world**!\n\nThis is a test.")
    small_time = time.time() - start
    print(".2f")

    # Test 2: Large content with viewport buffering
    print("\n📊 Test 2: Large content with viewport buffering")
    large_content = "# Large Document\n\n" + "\n".join(
        [f"Line {i}: Some content here" for i in range(100)]
    )
    start = time.time()
    await widget.append_chunk(large_content)
    large_time = time.time() - start
    print(".2f")

    # Check metrics
    print("\n📈 PERFORMANCE METRICS:")
    print(f"  • Frames rendered: {widget._metrics.frames_rendered}")
    print(f"  • Dropped frames: {widget._metrics.dropped_frames}")
    print(f"  • Total render time: {widget._metrics.total_render_time_ms:.2f}ms")
    print(f"  • Line cache size: {len(widget._line_cache)} lines")
    print(f"  • Viewport size: {widget._viewport_size} lines")

    # Test 3: Streaming simulation
    print("\n⚡ Test 3: Streaming simulation (60fps target)")
    chunk_times = []
    for i in range(10):
        start = time.time()
        await widget.append_chunk(f"Chunk {i}: More content here with **markdown**.\n")
        chunk_time = time.time() - start
        chunk_times.append(chunk_time)

    avg_chunk_time = sum(chunk_times) / len(chunk_times)
    print(".2f")
    print(".2f")
    print(".2f")

    # Performance validation
    print("\n✅ VALIDATION:")
    if avg_chunk_time < 0.016:  # 60fps = ~16.67ms
        print("  ✅ 60fps target achieved!")
    else:
        print("  ⚠️ Performance below 60fps target")

    if len(widget._line_cache) > 0:
        print("  ✅ Viewport buffering active")
    else:
        print("  ❌ Viewport buffering not working")

    print("\n🎉 PERFORMANCE TEST COMPLETED!")
    return True


if __name__ == "__main__":
    asyncio.run(test_performance_improvements())

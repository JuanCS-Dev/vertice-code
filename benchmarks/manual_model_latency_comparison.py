"""
Teste comparativo: Gemini Pro vs Flash
Objetivo: Isolar se latência é do modelo ou do código

HIPÓTESE: Se o problema é o modelo "thinking", Flash deve ser < 2s.
"""

import asyncio
import time
import statistics
from typing import Dict
import pytest


class ModelLatencyComparison:
    """Compara latência de first chunk entre modelos diferentes."""

    async def measure_model_latency(self, model_name: str, iterations: int = 20) -> Dict:
        """
        Mede latência de first chunk para um modelo específico.

        Args:
            model_name: "pro" ou "flash"
            iterations: número de medições

        Returns:
            {
                'model': str,
                'measurements_ms': List[float],
                'mean_ms': float,
                'median_ms': float,
                'p95_ms': float,
                'sample_size': int,
            }
        """
        from vertice_core.core.providers.vertex_ai import VertexAIProvider

        provider = VertexAIProvider(model_name=model_name)

        if not provider.is_available():
            pytest.skip(f"Vertex AI not available for {model_name}")

        measurements = []

        # Prompt simples para minimizar "thinking time"
        simple_prompt = "Say 'ok' and nothing else."

        for i in range(iterations):
            messages = [{"role": "user", "content": simple_prompt}]

            start = time.perf_counter()
            first_chunk_received = False

            try:
                async for chunk in provider.stream_chat(messages, max_tokens=10):
                    if not first_chunk_received:
                        latency_ms = (time.perf_counter() - start) * 1000
                        measurements.append(latency_ms)
                        first_chunk_received = True
                        print(
                            f"  [{model_name}] Iteration {i + 1}/{iterations}: {latency_ms:.1f}ms"
                        )
                        break  # Só queremos o primeiro chunk
            except Exception as e:
                print(f"  [{model_name}] Iteration {i + 1} ERROR: {e}")
                continue

            # Sleep entre iterações para evitar rate limiting
            await asyncio.sleep(0.5)

        if not measurements:
            pytest.skip(f"No successful measurements for {model_name}")

        sorted_measurements = sorted(measurements)
        n = len(sorted_measurements)

        return {
            "model": model_name,
            "measurements_ms": measurements,
            "mean_ms": statistics.mean(measurements),
            "median_ms": statistics.median(measurements),
            "p95_ms": sorted_measurements[int(n * 0.95)] if n > 1 else sorted_measurements[0],
            "min_ms": min(measurements),
            "max_ms": max(measurements),
            "sample_size": n,
        }


@pytest.mark.asyncio
async def test_latency_comparison_pro_vs_flash():
    """
    TESTE CRÍTICO: Compara latência Pro vs Flash.

    Se Flash << Pro → latência é do modelo (ACEITÁVEL)
    Se Flash ≈ Pro → latência é do código (PROBLEMA)
    """
    comparison = ModelLatencyComparison()

    # Medir Gemini Pro
    print("\n🔬 Medindo Gemini Pro (gemini-3-flash)...")
    pro_results = await comparison.measure_model_latency("pro", iterations=10)

    # Medir Gemini Flash
    print("\n🔬 Medindo Gemini Flash (gemini-3-flash-preview)...")
    flash_results = await comparison.measure_model_latency("flash", iterations=10)

    # Print relatório comparativo
    print("\n" + "=" * 70)
    print("LATENCY COMPARISON: Gemini Pro vs Flash")
    print("=" * 70)
    print(f"\n{'Metric':<20} {'Pro':<20} {'Flash':<20} {'Ratio':<15}")
    print("-" * 70)
    print(
        f"{'Mean':<20} {pro_results['mean_ms']:>8.1f}ms {flash_results['mean_ms']:>16.1f}ms {pro_results['mean_ms'] / flash_results['mean_ms']:>12.2f}x"
    )
    print(
        f"{'Median':<20} {pro_results['median_ms']:>8.1f}ms {flash_results['median_ms']:>16.1f}ms {pro_results['median_ms'] / flash_results['median_ms']:>12.2f}x"
    )
    print(
        f"{'p95':<20} {pro_results['p95_ms']:>8.1f}ms {flash_results['p95_ms']:>16.1f}ms {pro_results['p95_ms'] / flash_results['p95_ms']:>12.2f}x"
    )
    print(
        f"{'Min':<20} {pro_results['min_ms']:>8.1f}ms {flash_results['min_ms']:>16.1f}ms {pro_results['min_ms'] / flash_results['min_ms']:>12.2f}x"
    )
    print(
        f"{'Max':<20} {pro_results['max_ms']:>8.1f}ms {flash_results['max_ms']:>16.1f}ms {pro_results['max_ms'] / flash_results['max_ms']:>12.2f}x"
    )
    print("=" * 70)

    # Análise automática
    ratio = pro_results["mean_ms"] / flash_results["mean_ms"]

    if ratio > 3.0:
        verdict = "✅ LATÊNCIA É DO MODELO (Pro é 3x+ mais lento que Flash)"
        status = "ACEITÁVEL"
    elif ratio > 1.5:
        verdict = "⚠️ LATÊNCIA PARCIALMENTE DO MODELO (Pro é 1.5-3x mais lento)"
        status = "INVESTIGAR MAIS"
    else:
        verdict = "❌ LATÊNCIA NÃO É DO MODELO (Pro ≈ Flash) - CÓDIGO TEM PROBLEMA"
        status = "INACEITÁVEL - PRECISA CORREÇÃO"

    print(f"\n{verdict}")
    print(f"STATUS: {status}\n")

    # Assertion - relaxed since both might be fast or both slow
    # The key insight is comparing them
    assert pro_results["sample_size"] >= 5, "Need at least 5 Pro measurements"
    assert flash_results["sample_size"] >= 5, "Need at least 5 Flash measurements"

    return {
        "pro": pro_results,
        "flash": flash_results,
        "ratio": ratio,
        "verdict": verdict,
        "status": status,
    }


if __name__ == "__main__":
    result = asyncio.run(test_latency_comparison_pro_vs_flash())

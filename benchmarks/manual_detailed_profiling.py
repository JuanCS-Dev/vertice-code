"""
Profiling detalhado: onde estão os 7 segundos?

Este teste identifica EXATAMENTE onde o tempo é gasto no fluxo
desde o início até o primeiro chunk.
"""

import asyncio
import time
from typing import Dict, List
import pytest


class DetailedProfiler:
    """Profiler detalhado para rastrear EXATAMENTE onde o tempo vai."""

    def __init__(self):
        self.checkpoints: List[Dict] = []
        self.start_time = None

    def start(self):
        """Inicia profiling."""
        self.start_time = time.perf_counter()
        self.checkpoint("START")

    def checkpoint(self, name: str, data: Dict = None):
        """Registra checkpoint com timestamp."""
        if self.start_time is None:
            self.start_time = time.perf_counter()

        elapsed_ms = (time.perf_counter() - self.start_time) * 1000

        self.checkpoints.append(
            {
                "name": name,
                "elapsed_ms": elapsed_ms,
                "data": data or {},
            }
        )

    def print_report(self):
        """Imprime relatório detalhado."""
        print("\n" + "=" * 80)
        print("DETAILED PROFILING REPORT")
        print("=" * 80)
        print(f"\n{'Checkpoint':<40} {'Elapsed (ms)':<15} {'Delta (ms)':<15}")
        print("-" * 80)

        for i, checkpoint in enumerate(self.checkpoints):
            delta_ms = 0
            if i > 0:
                delta_ms = checkpoint["elapsed_ms"] - self.checkpoints[i - 1]["elapsed_ms"]

            marker = "🔴" if delta_ms > 1000 else "🟡" if delta_ms > 500 else "🟢"

            print(
                f"{marker} {checkpoint['name']:<38} {checkpoint['elapsed_ms']:>10.1f}ms {delta_ms:>12.1f}ms"
            )

        print("=" * 80)

        # Identificar gargalos
        bottlenecks = []
        for i, checkpoint in enumerate(self.checkpoints[1:], 1):
            delta = checkpoint["elapsed_ms"] - self.checkpoints[i - 1]["elapsed_ms"]
            if delta > 1000:
                bottlenecks.append((self.checkpoints[i - 1], checkpoint, delta))

        if bottlenecks:
            print("\n🚨 GARGALOS DETECTADOS (>1s):")
            for i, (prev, curr, delta) in enumerate(bottlenecks, 1):
                print(f"  {i}. {prev['name']} → {curr['name']}: {delta:.1f}ms")

        print("")

        return bottlenecks


@pytest.mark.asyncio
async def test_detailed_profiling_of_chat_flow():
    """
    TESTE CRÍTICO: Profile COMPLETO do fluxo Enter → First Chunk.

    Identifica EXATAMENTE onde os 7s são gastos.
    """
    from vertice_cli.core.providers.vertex_ai import VertexAIProvider

    profiler = DetailedProfiler()
    profiler.start()

    # 1. Criar provider
    profiler.checkpoint("Provider.__init__ START")
    provider = VertexAIProvider(model_name="pro")
    profiler.checkpoint("Provider.__init__ END")

    # 2. Verificar disponibilidade
    profiler.checkpoint("is_available() START")
    is_avail = provider.is_available()
    profiler.checkpoint("is_available() END", {"available": is_avail})

    if not is_avail:
        pytest.skip("Vertex AI not available")

    # 3. Preparar mensagens
    profiler.checkpoint("Prepare messages START")
    messages = [{"role": "user", "content": "Say 'ok' and nothing else."}]
    profiler.checkpoint("Prepare messages END")

    # 4. Chamar stream_chat
    profiler.checkpoint("stream_chat() CALL START")

    stream_started = False
    first_chunk_received = False

    async for chunk in provider.stream_chat(messages, max_tokens=10):
        if not stream_started:
            profiler.checkpoint("Stream STARTED (first iteration)")
            stream_started = True

        if not first_chunk_received and chunk:
            chunk_preview = chunk[:50] if len(chunk) > 50 else chunk
            profiler.checkpoint("FIRST CHUNK RECEIVED", {"chunk": chunk_preview})
            first_chunk_received = True
            break  # Só queremos o primeiro chunk

    profiler.checkpoint("stream_chat() END")

    # Print relatório
    bottlenecks = profiler.print_report()

    # Análise
    checkpoints = {cp["name"]: cp for cp in profiler.checkpoints}

    if "FIRST CHUNK RECEIVED" in checkpoints:
        total_time = checkpoints["FIRST CHUNK RECEIVED"]["elapsed_ms"]

        print(f"\n📊 TOTAL TIME TO FIRST CHUNK: {total_time:.1f}ms")

        # Breakdown
        if "Stream STARTED (first iteration)" in checkpoints:
            time_to_stream_start = checkpoints["Stream STARTED (first iteration)"]["elapsed_ms"]
            time_in_stream = total_time - time_to_stream_start

            print("\n📦 BREAKDOWN:")
            print(f"  Setup (até stream start): {time_to_stream_start:.1f}ms")
            print(f"  Waiting for first chunk:  {time_in_stream:.1f}ms")

            if time_to_stream_start > 1000:
                print(f"\n🚨 PROBLEMA: Setup está levando {time_to_stream_start:.1f}ms!")
                print("   Isso indica bloqueio no código ANTES do streaming começar.")

            if time_in_stream > 5000:
                print(f"\n⚠️ OBSERVAÇÃO: Espera pelo chunk está levando {time_in_stream:.1f}ms")
                print("   Isso pode ser:")
                print("   - Latência real da API/modelo (normal)")
                print("   - Bloqueio no iteration do stream (problema)")

    return {
        "checkpoints": profiler.checkpoints,
        "bottlenecks": bottlenecks,
    }


@pytest.mark.asyncio
async def test_detailed_profiling_flash():
    """
    Profile do Flash para comparação.
    """
    from vertice_cli.core.providers.vertex_ai import VertexAIProvider

    profiler = DetailedProfiler()
    profiler.start()

    profiler.checkpoint("Provider.__init__ START")
    provider = VertexAIProvider(model_name="flash")
    profiler.checkpoint("Provider.__init__ END")

    profiler.checkpoint("is_available() START")
    is_avail = provider.is_available()
    profiler.checkpoint("is_available() END", {"available": is_avail})

    if not is_avail:
        pytest.skip("Vertex AI not available")

    profiler.checkpoint("Prepare messages START")
    messages = [{"role": "user", "content": "Say 'ok' and nothing else."}]
    profiler.checkpoint("Prepare messages END")

    profiler.checkpoint("stream_chat() CALL START")

    stream_started = False
    first_chunk_received = False

    async for chunk in provider.stream_chat(messages, max_tokens=10):
        if not stream_started:
            profiler.checkpoint("Stream STARTED (first iteration)")
            stream_started = True

        if not first_chunk_received and chunk:
            chunk_preview = chunk[:50] if len(chunk) > 50 else chunk
            profiler.checkpoint("FIRST CHUNK RECEIVED", {"chunk": chunk_preview})
            first_chunk_received = True
            break

    profiler.checkpoint("stream_chat() END")

    profiler.print_report()

    checkpoints = {cp["name"]: cp for cp in profiler.checkpoints}
    if "FIRST CHUNK RECEIVED" in checkpoints:
        total_time = checkpoints["FIRST CHUNK RECEIVED"]["elapsed_ms"]
        print(f"\n📊 FLASH - TOTAL TIME TO FIRST CHUNK: {total_time:.1f}ms")


if __name__ == "__main__":
    print("=" * 80)
    print("PROFILING: GEMINI PRO")
    print("=" * 80)
    asyncio.run(test_detailed_profiling_of_chat_flow())

    print("\n" * 2)
    print("=" * 80)
    print("PROFILING: GEMINI FLASH")
    print("=" * 80)
    asyncio.run(test_detailed_profiling_flash())

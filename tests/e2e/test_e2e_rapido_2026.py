#!/usr/bin/env python3
"""
VERTICE - TESTE E2E RAPIDO COM TIMEOUT
======================================

Testa todos os 20 agents com timeout individual.
Gera tabela de resultados no final.
"""
import asyncio
import sys
from datetime import datetime
from typing import Dict, List, Tuple

sys.path.insert(0, "/media/juan/DATA/Vertice-Code")

# Timeout por agente (segundos)
AGENT_TIMEOUT = 15

# Configuracao de todos os 20 agents
AGENTS = {
    # CLI (14)
    "planner": ("CLI", "Planeje criar uma API REST", ["passo|step", "api|rest"]),
    "executor": ("CLI", "Execute echo teste", ["echo|teste|execut"]),
    "architect": ("CLI", "Analise arquitetura de cache", ["cache|arquitetura"]),
    "reviewer": ("CLI", "Revise: def soma(a,b): return a+b", ["review|analise|soma"]),
    "explorer": ("CLI", "Encontre arquivos com Agent", ["agent|arquivo|found"]),
    "refactorer": ("CLI", "Refatore: def f(x): return x*2", ["refator|def|return"]),
    "testing": ("CLI", "Gere teste para: def add(a,b): return a+b", ["test|def|assert"]),
    "security": ("CLI", "Analise: os.system(input())", ["security|injection|vulnerab"]),
    "documentation": ("CLI", "Documente: class Calc: pass", ["calc|doc|class"]),
    "performance": ("CLI", "Analise: for i in range(n): for j in range(n): pass", ["loop|O(n|complex"]),
    "devops": ("CLI", "Configure CI/CD basico", ["ci|cd|pipeline|docker"]),
    "justica": ("CLI", "Avalie etica de coletar dados sem permissao", ["etica|consent|violacao"]),
    "sofia": ("CLI", "Reflita sobre IA e privacidade", ["ia|privac|reflex"]),
    "data": ("CLI", "Otimize: SELECT * FROM users", ["sql|select|index"]),
    # CORE (6)
    "orchestrator_core": ("CORE", "Orquestre tarefa de login", ["login|orquestr|task"]),
    "coder_core": ("CORE", "Implemente fibonacci", ["def|fibonacci|return"]),
    "reviewer_core": ("CORE", "Revise: if x > 0: return True", ["review|if|return"]),
    "architect_core": ("CORE", "Projete sistema de chat", ["chat|arquitetura|websocket"]),
    "researcher_core": ("CORE", "Pesquise sobre REST APIs", ["api|rest|pesquis"]),
    "devops_core": ("CORE", "Configure Kubernetes", ["kubernetes|k8s|deploy"]),
}


async def invocar_com_timeout(agente: str, prompt: str) -> Tuple[str, float, str]:
    """Invoca agente com timeout. Retorna (output, tempo, status)."""
    try:
        from vertice_tui.core.agents.manager import AgentManager

        manager = AgentManager()
        chunks = []
        context = {"user_message": prompt, "cwd": "/media/juan/DATA/Vertice-Code"}

        inicio = datetime.now()

        async def collect():
            async for chunk in manager.invoke(agente, prompt, context):
                chunks.append(chunk)

        await asyncio.wait_for(collect(), timeout=AGENT_TIMEOUT)
        tempo = (datetime.now() - inicio).total_seconds()

        return "".join(chunks), tempo, "OK"

    except asyncio.TimeoutError:
        return "", AGENT_TIMEOUT, "TIMEOUT"
    except Exception as e:
        return str(e), 0, "ERRO"


def avaliar(output: str, criterios: List[str]) -> Tuple[int, int, str]:
    """Avalia output contra criterios. Retorna (atendidos, total, veredicto)."""
    output_lower = output.lower()
    atendidos = 0

    for criterio in criterios:
        keywords = criterio.split("|")
        if any(kw.lower() in output_lower for kw in keywords):
            atendidos += 1

    total = len(criterios)

    if len(output) < 20:
        return atendidos, total, "FALHA"
    elif atendidos == total:
        return atendidos, total, "EXCELENTE"
    elif atendidos >= total * 0.5:
        return atendidos, total, "BOM"
    else:
        return atendidos, total, "PARCIAL"


async def main():
    print("=" * 80)
    print("VERTICE E2E - TESTE RAPIDO DE TODOS OS 20 AGENTS")
    print("=" * 80)
    print(f"Timeout por agente: {AGENT_TIMEOUT}s")
    print()

    resultados = []

    for agente, (tipo, prompt, criterios) in AGENTS.items():
        print(f"Testando {agente:<20} ... ", end="", flush=True)

        output, tempo, status = await invocar_com_timeout(agente, prompt)

        if status == "OK":
            atendidos, total, veredicto = avaliar(output, criterios)
            emoji = {"EXCELENTE": "🏆", "BOM": "✅", "PARCIAL": "⚠️", "FALHA": "❌"}.get(veredicto, "")
            print(f"{emoji} {veredicto} ({atendidos}/{total}) [{tempo:.1f}s] [{len(output)}c]")
        elif status == "TIMEOUT":
            veredicto = "TIMEOUT"
            atendidos, total = 0, len(criterios)
            print(f"⏱️ TIMEOUT [{AGENT_TIMEOUT}s]")
        else:
            veredicto = "ERRO"
            atendidos, total = 0, len(criterios)
            print(f"💀 ERRO: {output[:50]}")

        resultados.append({
            "agente": agente,
            "tipo": tipo,
            "veredicto": veredicto,
            "score": f"{atendidos}/{total}",
            "tempo": tempo,
            "output_len": len(output),
            "status": status
        })

    # Gerar tabela
    print()
    print("=" * 100)
    print("TABELA DE RESULTADOS")
    print("=" * 100)
    print(f"{'AGENTE':<22} {'TIPO':<6} {'VEREDICTO':<12} {'SCORE':<8} {'TEMPO':<8} {'OUTPUT':<10}")
    print("-" * 100)

    for r in sorted(resultados, key=lambda x: (x["tipo"], x["agente"])):
        emoji = {"EXCELENTE": "🏆", "BOM": "✅", "PARCIAL": "⚠️", "FALHA": "❌", "TIMEOUT": "⏱️", "ERRO": "💀"}.get(r["veredicto"], "")
        print(f"{r['agente']:<22} {r['tipo']:<6} {emoji} {r['veredicto']:<10} {r['score']:<8} {r['tempo']:.1f}s     {r['output_len']}c")

    print("-" * 100)

    # Resumo
    contagem = {}
    for r in resultados:
        v = r["veredicto"]
        contagem[v] = contagem.get(v, 0) + 1

    total = len(resultados)
    sucesso = contagem.get("EXCELENTE", 0) + contagem.get("BOM", 0)
    taxa = (sucesso / total * 100) if total > 0 else 0

    print()
    print("📊 RESUMO:")
    print(f"   🏆 EXCELENTE: {contagem.get('EXCELENTE', 0)}")
    print(f"   ✅ BOM:       {contagem.get('BOM', 0)}")
    print(f"   ⚠️ PARCIAL:   {contagem.get('PARCIAL', 0)}")
    print(f"   ❌ FALHA:     {contagem.get('FALHA', 0)}")
    print(f"   ⏱️ TIMEOUT:   {contagem.get('TIMEOUT', 0)}")
    print(f"   💀 ERRO:      {contagem.get('ERRO', 0)}")
    print()
    print(f"   TOTAL: {total} agents")
    print(f"   SUCESSO: {sucesso}/{total} ({taxa:.1f}%)")
    print()
    print("=" * 100)

    if taxa >= 80:
        print("🏆 RESULTADO: EXCELENTE!")
    elif taxa >= 60:
        print("✅ RESULTADO: BOM")
    elif taxa >= 40:
        print("⚠️ RESULTADO: PARCIAL")
    else:
        print("❌ RESULTADO: NECESSITA CORRECOES")

    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())

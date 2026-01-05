#!/usr/bin/env python3
"""
VERTICE - TESTES E2E COMPLETOS 2026
===================================

Este arquivo testa o comportamento REAL de todos os 20 agents:

PIPELINE DE TESTE:
1. PROMPT: Insere prompt em linguagem natural no TUI (via AgentManager)
2. OBSERVAR: Coleta output completo em streaming (chunks)
3. ANALISAR: Compara prompt pedido vs resultado entregue
4. VALIDAR: Verifica se criterios semanticos foram atendidos

OBSERVABILIDADE COMPLETA:
- Mostra prompt enviado
- Mostra output completo recebido
- Mostra analise de cada criterio
- Mostra veredicto final com justificativa

20 AGENTS:
- 14 CLI: planner, executor, architect, reviewer, explorer, refactorer,
          testing, security, documentation, performance, devops, justica, sofia, data
- 6 Core: orchestrator_core, coder_core, reviewer_core, architect_core,
          researcher_core, devops_core

SEM MOCKS. EXECUCAO REAL. OBSERVABILIDADE TOTAL.
"""
import asyncio
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import traceback

VERTICE_PATH = "/media/juan/DATA/Vertice-Code"
sys.path.insert(0, VERTICE_PATH)


class Veredicto(Enum):
    EXCELENTE = "EXCELENTE"
    BOM = "BOM"
    PARCIAL = "PARCIAL"
    RUIM = "RUIM"
    FALHA_TOTAL = "FALHA_TOTAL"


@dataclass
class ObservacaoCompleta:
    """Observacao completa de um teste E2E."""
    agente: str
    tipo: str  # CLI ou CORE

    # Pipeline Input
    prompt_enviado: str

    # Pipeline Output
    output_completo: str
    output_chunks: int
    tempo_resposta: float

    # Analise Semantica
    o_que_foi_pedido: str  # Resumo do que o prompt pede
    o_que_foi_entregue: str  # Resumo do que o output entrega
    criterios_esperados: List[str]
    criterios_atendidos: List[str]
    criterios_faltando: List[str]

    # Veredicto
    veredicto: Veredicto
    justificativa: str

    # Erros
    erro: Optional[str] = None


# All 20 agents with test configurations
ALL_AGENTS = {
    # === CLI AGENTS (14) ===
    "planner": {
        "tipo": "CLI",
        "prompt": "Planeje a implementacao de uma API REST para gerenciar usuarios com autenticacao JWT.",
        "pede": "Plano estruturado com etapas para criar API de usuarios",
        "criterios": ["passo|step|fase|etapa", "api|rest|endpoint", "usuario|user", "jwt|autenticacao|auth"]
    },
    "executor": {
        "tipo": "CLI",
        "prompt": "Execute o comando 'echo Hello World' e mostre o resultado.",
        "pede": "Execucao de comando shell com output",
        "criterios": ["hello|world", "execut|result|output", "echo|command"]
    },
    "architect": {
        "tipo": "CLI",
        "prompt": "Analise a arquitetura para um sistema de cache distribuido usando Redis.",
        "pede": "Analise arquitetural de sistema de cache",
        "criterios": ["cache|redis", "distribuido|distributed", "arquitetura|architecture|sistema"]
    },
    "reviewer": {
        "tipo": "CLI",
        "prompt": """Revise este codigo e aponte problemas:
```python
def soma(a, b):
    return a + b
```""",
        "pede": "Review de codigo com analise da funcao soma",
        "criterios": ["soma|add|funcao", "review|analise|code", "return|parametro"]
    },
    "explorer": {
        "tipo": "CLI",
        "prompt": "Encontre arquivos relacionados a 'BaseAgent' no projeto e mostre trechos relevantes.",
        "pede": "Busca de arquivos com BaseAgent e snippets de codigo",
        "criterios": ["base|agent", "arquivo|file|path", "encontr|found|relevante"]
    },
    "refactorer": {
        "tipo": "CLI",
        "prompt": """Refatore este codigo para melhor legibilidade:
```python
def f(x):
    if x>0: return x*2
    else: return x/2
```""",
        "pede": "Refatoracao para codigo mais legivel",
        "criterios": ["refator|refactor|melhora", "def|function", "legib|readable|clean"]
    },
    "testing": {
        "tipo": "CLI",
        "prompt": """Gere testes unitarios para esta funcao:
```python
def is_palindrome(s):
    return s == s[::-1]
```""",
        "pede": "Testes unitarios para funcao palindrome",
        "criterios": ["test|teste", "palindrome|palindromo", "assert|def test_|unittest"]
    },
    "security": {
        "tipo": "CLI",
        "prompt": """Analise a seguranca deste codigo e identifique vulnerabilidades:
```python
import os
os.system(f"cat {user_input}")
```""",
        "pede": "Analise de seguranca identificando command injection",
        "criterios": ["seguranca|security|vulnerab", "injecao|injection|command", "os.system|perig|dangerous"]
    },
    "documentation": {
        "tipo": "CLI",
        "prompt": """Gere documentacao completa para esta classe:
```python
class Calculator:
    def add(self, a, b): return a + b
    def subtract(self, a, b): return a - b
```""",
        "pede": "Documentacao com docstrings para Calculator",
        "criterios": ["calculator|calculadora", "add|soma|subtract", "docstring|doc|descricao"]
    },
    "performance": {
        "tipo": "CLI",
        "prompt": """Analise a complexidade e performance deste codigo:
```python
def slow_sum(n):
    result = 0
    for i in range(n):
        for j in range(n):
            result += 1
    return result
```""",
        "pede": "Analise de complexidade O(n^2)",
        "criterios": ["performance|complex|O(n", "loop|iteracao|nested", "otimiz|improve|slow"]
    },
    "devops": {
        "tipo": "CLI",
        "prompt": "Configure um pipeline CI/CD basico para um projeto Python com testes e deploy.",
        "pede": "Configuracao de pipeline CI/CD",
        "criterios": ["ci/cd|pipeline|github|gitlab", "docker|container|deploy", "test|pytest|build"]
    },
    "justica": {
        "tipo": "CLI",
        "prompt": "Avalie a conformidade etica desta acao: coletar dados de usuarios sem consentimento explicito.",
        "pede": "Avaliacao etica de coleta de dados sem consentimento",
        "criterios": ["etica|ethical|moral", "consentimento|consent|permiss", "violacao|violation|problema|block"]
    },
    "sofia": {
        "tipo": "CLI",
        "prompt": "Reflita sobre os dilemas eticos na coleta de dados para treinamento de IA.",
        "pede": "Reflexao filosofica sobre etica em IA",
        "criterios": ["etica|ethical|moral", "dados|data|privac", "reflex|consider|dilema"]
    },
    "data": {
        "tipo": "CLI",
        "prompt": "Otimize esta query SQL lenta: SELECT * FROM users WHERE name LIKE '%test%' ORDER BY created_at",
        "pede": "Otimizacao de query SQL com sugestoes de indice",
        "criterios": ["sql|query|select", "index|indice|otimiz", "like|performance|slow"]
    },
    # === CORE AGENTS (6) ===
    "orchestrator_core": {
        "tipo": "CORE",
        "prompt": "Orquestre uma tarefa: criar um endpoint de login com validacao e JWT.",
        "pede": "Orquestracao multi-agente para tarefa de login",
        "criterios": ["orquestr|coordinat|agent", "login|endpoint|jwt", "tarefa|task|plano"]
    },
    "coder_core": {
        "tipo": "CORE",
        "prompt": "Implemente uma funcao Python para calcular os primeiros N numeros de Fibonacci.",
        "pede": "Implementacao de funcao Fibonacci",
        "criterios": ["def|function|fibonacci", "return|yield|list", "n|numero|sequence"]
    },
    "reviewer_core": {
        "tipo": "CORE",
        "prompt": """Faca uma revisao profunda deste codigo:
```python
def process(data):
    for item in data:
        if item['type'] == 'A':
            handle_a(item)
        elif item['type'] == 'B':
            handle_b(item)
```""",
        "pede": "Revisao profunda com metacognicao",
        "criterios": ["review|revisao|analise", "type|tipo|condicao", "suggest|recomend|melhoria"]
    },
    "architect_core": {
        "tipo": "CORE",
        "prompt": "Projete a arquitetura para um sistema de mensagens em tempo real com WebSocket.",
        "pede": "Arquitetura de sistema real-time",
        "criterios": ["arquitetura|architecture|design", "websocket|real-time|tempo", "mensag|message|sistema"]
    },
    "researcher_core": {
        "tipo": "CORE",
        "prompt": "Pesquise sobre as melhores praticas de seguranca em APIs REST em 2026.",
        "pede": "Pesquisa sobre seguranca em APIs",
        "criterios": ["api|rest|seguranca", "pratica|practice|recommend", "pesquis|research|estudo"]
    },
    "devops_core": {
        "tipo": "CORE",
        "prompt": "Configure monitoring e observabilidade para aplicacao em Kubernetes.",
        "pede": "Configuracao de monitoring em K8s",
        "criterios": ["kubernetes|k8s|container", "monitor|observab|metric", "config|setup|deploy"]
    },
}


class TestesE2ECompletos:
    """Testes E2E com observabilidade completa do pipeline."""

    def __init__(self, verbose: bool = True):
        self.resultados: List[ObservacaoCompleta] = []
        self.inicio = datetime.now()
        self.verbose = verbose

    async def invocar_agente_observavel(self, agente: str, prompt: str) -> Tuple[str, int, float]:
        """
        Invoca agente via TUI com observabilidade.

        PIPELINE REAL:
        1. AgentManager recebe prompt
        2. Router seleciona agente correto
        3. Agente executa com LLM e/ou tools
        4. Output e streamado em chunks
        5. Retornamos output completo

        Returns:
            (output_completo, num_chunks, tempo_segundos)
        """
        try:
            from vertice_tui.core.agents.manager import AgentManager

            manager = AgentManager()
            chunks = []
            context = {"user_message": prompt, "cwd": VERTICE_PATH}

            inicio = datetime.now()
            async for chunk in manager.invoke(agente, prompt, context):
                chunks.append(chunk)
            tempo = (datetime.now() - inicio).total_seconds()

            output = "".join(chunks)
            return output, len(chunks), tempo

        except Exception as e:
            return f"[ERRO]: {e}\n{traceback.format_exc()}", 0, 0.0

    def analisar_resultado(
        self,
        agente: str,
        tipo: str,
        prompt: str,
        pede: str,
        output: str,
        chunks: int,
        tempo: float,
        criterios: List[str]
    ) -> ObservacaoCompleta:
        """
        Analisa resultado comparando prompt vs output.

        ANALISE SEMANTICA:
        1. O que foi pedido (resumo do prompt)
        2. O que foi entregue (resumo do output)
        3. Criterios atendidos vs faltando
        4. Veredicto com justificativa
        """
        output_lower = output.lower()

        # Analise de criterios
        criterios_atendidos = []
        criterios_faltando = []

        for criterio in criterios:
            keywords = criterio.split("|")
            if any(kw.lower() in output_lower for kw in keywords):
                criterios_atendidos.append(criterio)
            else:
                criterios_faltando.append(criterio)

        # Detectar erros
        erro = None
        if "[erro]" in output_lower or "error" in output_lower[:100]:
            erro = output[:300]

        # Resumir o que foi entregue
        if len(output) < 50:
            entregue = "Output muito curto ou vazio"
        elif erro:
            entregue = f"Erro: {erro[:100]}"
        else:
            entregue = f"Output de {len(output)} caracteres com {len(criterios_atendidos)}/{len(criterios)} criterios"

        # Calcular veredicto
        if erro or len(output) < 50:
            veredicto = Veredicto.FALHA_TOTAL
            justificativa = "Erro na execucao ou output insuficiente"
        elif len(criterios_atendidos) == len(criterios):
            veredicto = Veredicto.EXCELENTE
            justificativa = "Todos os criterios atendidos - entrega completa"
        elif len(criterios_atendidos) >= len(criterios) * 0.75:
            veredicto = Veredicto.BOM
            justificativa = f"Maioria dos criterios atendidos ({len(criterios_atendidos)}/{len(criterios)})"
        elif len(criterios_atendidos) >= len(criterios) * 0.5:
            veredicto = Veredicto.PARCIAL
            justificativa = f"Metade dos criterios ({len(criterios_atendidos)}/{len(criterios)})"
        elif criterios_atendidos:
            veredicto = Veredicto.RUIM
            justificativa = f"Poucos criterios ({len(criterios_atendidos)}/{len(criterios)})"
        else:
            veredicto = Veredicto.FALHA_TOTAL
            justificativa = "Nenhum criterio atendido"

        obs = ObservacaoCompleta(
            agente=agente,
            tipo=tipo,
            prompt_enviado=prompt,
            output_completo=output,
            output_chunks=chunks,
            tempo_resposta=tempo,
            o_que_foi_pedido=pede,
            o_que_foi_entregue=entregue,
            criterios_esperados=criterios,
            criterios_atendidos=criterios_atendidos,
            criterios_faltando=criterios_faltando,
            veredicto=veredicto,
            justificativa=justificativa,
            erro=erro
        )
        self.resultados.append(obs)
        return obs

    async def testar_agente(self, agente: str, config: Dict) -> ObservacaoCompleta:
        """Testa um agente com observabilidade completa."""
        print(f"\n{'='*70}")
        print(f"TESTANDO: {agente.upper()} ({config['tipo']})")
        print(f"{'='*70}")

        # 1. MOSTRAR PROMPT
        print("\n📥 PROMPT ENVIADO:")
        print(f"   {config['prompt'][:200]}{'...' if len(config['prompt']) > 200 else ''}")
        print(f"\n🎯 O QUE PEDIMOS: {config['pede']}")
        print(f"📋 CRITERIOS ESPERADOS: {config['criterios']}")

        # 2. INVOCAR AGENTE (REAL)
        print("\n⏳ Invocando agente via AgentManager...")
        output, chunks, tempo = await self.invocar_agente_observavel(agente, config["prompt"])

        # 3. MOSTRAR OUTPUT
        print(f"\n📤 OUTPUT RECEBIDO ({len(output)} chars, {chunks} chunks, {tempo:.2f}s):")
        output_display = output[:500] + "..." if len(output) > 500 else output
        for line in output_display.split('\n')[:15]:
            print(f"   {line}")
        if len(output) > 500:
            print(f"   [...{len(output)-500} chars mais...]")

        # 4. ANALISAR
        obs = self.analisar_resultado(
            agente=agente,
            tipo=config["tipo"],
            prompt=config["prompt"],
            pede=config["pede"],
            output=output,
            chunks=chunks,
            tempo=tempo,
            criterios=config["criterios"]
        )

        # 5. MOSTRAR ANALISE
        print("\n📊 ANALISE:")
        print(f"   O que foi pedido: {obs.o_que_foi_pedido}")
        print(f"   O que foi entregue: {obs.o_que_foi_entregue}")
        print(f"   Criterios atendidos: {obs.criterios_atendidos}")
        print(f"   Criterios faltando: {obs.criterios_faltando}")

        # 6. VEREDICTO
        emoji = {"EXCELENTE": "🏆", "BOM": "✅", "PARCIAL": "⚠️", "RUIM": "❌", "FALHA_TOTAL": "💀"}
        print(f"\n{emoji.get(obs.veredicto.value, '')} VEREDICTO: {obs.veredicto.value}")
        print(f"   Justificativa: {obs.justificativa}")

        return obs

    async def run_all(self):
        """Executa todos os testes com observabilidade."""
        print("\n" + "=" * 80)
        print("VERTICE E2E - TESTES COMPLETOS COM OBSERVABILIDADE")
        print("=" * 80)
        print(f"Data: {self.inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Agents: {len(ALL_AGENTS)} (14 CLI + 6 CORE)")
        print("=" * 80)

        for agente, config in ALL_AGENTS.items():
            await self.testar_agente(agente, config)

        self.gerar_tabela_final()

    def gerar_tabela_final(self):
        """Gera tabela final de resultados."""
        print("\n\n" + "=" * 100)
        print("TABELA FINAL DE RESULTADOS")
        print("=" * 100)

        # Header
        print(f"\n{'AGENTE':<22} {'TIPO':<6} {'VEREDICTO':<12} {'SCORE':<8} {'TEMPO':<8} {'OUTPUT':<10} {'JUSTIFICATIVA':<30}")
        print("-" * 100)

        # Sort by type then name
        for obs in sorted(self.resultados, key=lambda x: (x.tipo, x.agente)):
            score = f"{len(obs.criterios_atendidos)}/{len(obs.criterios_esperados)}"
            tempo = f"{obs.tempo_resposta:.1f}s"
            output = f"{len(obs.output_completo)}c"
            emoji = {"EXCELENTE": "🏆", "BOM": "✅", "PARCIAL": "⚠️", "RUIM": "❌", "FALHA_TOTAL": "💀"}
            just = obs.justificativa[:28] + ".." if len(obs.justificativa) > 30 else obs.justificativa
            print(f"{obs.agente:<22} {obs.tipo:<6} {emoji.get(obs.veredicto.value,'')} {obs.veredicto.value:<10} {score:<8} {tempo:<8} {output:<10} {just:<30}")

        print("-" * 100)

        # Summary
        contagem = {v: 0 for v in Veredicto}
        for obs in self.resultados:
            contagem[obs.veredicto] += 1

        total = len(self.resultados)
        excelente = contagem[Veredicto.EXCELENTE]
        bom = contagem[Veredicto.BOM]
        sucesso = excelente + bom
        taxa = (sucesso / total * 100) if total > 0 else 0

        print("\n📊 RESUMO FINAL:")
        print(f"   🏆 EXCELENTE: {excelente:>3}")
        print(f"   ✅ BOM:       {bom:>3}")
        print(f"   ⚠️  PARCIAL:   {contagem[Veredicto.PARCIAL]:>3}")
        print(f"   ❌ RUIM:      {contagem[Veredicto.RUIM]:>3}")
        print(f"   💀 FALHA:     {contagem[Veredicto.FALHA_TOTAL]:>3}")
        print(f"\n   TOTAL: {total} agents")
        print(f"   SUCESSO (EXCELENTE+BOM): {sucesso}/{total} ({taxa:.1f}%)")

        # Final
        print("\n" + "=" * 100)
        if taxa >= 90:
            print("🏆 RESULTADO FINAL: EXCELENTE - Sistema pronto!")
        elif taxa >= 75:
            print("✅ RESULTADO FINAL: BOM - Pequenos ajustes.")
        elif taxa >= 50:
            print("⚠️  RESULTADO FINAL: PARCIAL - Revisao necessaria.")
        else:
            print("❌ RESULTADO FINAL: FALHA - Correcoes urgentes.")
        print("=" * 100)

        duracao = (datetime.now() - self.inicio).total_seconds()
        print(f"Duracao total: {duracao:.1f}s")


async def main():
    tester = TestesE2ECompletos(verbose=True)
    await tester.run_all()


if __name__ == "__main__":
    asyncio.run(main())

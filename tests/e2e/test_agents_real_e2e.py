#!/usr/bin/env python3
"""
VERTICE - TESTES E2E REAIS E COMPLETOS
======================================

Este arquivo executa TODOS os agentes com tarefas REAIS,
LEIA os resultados, ANALISA se estão corretos e gera
um RELATÓRIO DETALHADO explicando cada resultado.

SEM MOCKS. EXECUÇÃO REAL. ANÁLISE CRÍTICA.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

VERTICE_PATH = "/media/juan/DATA/Vertice-Code"
sys.path.insert(0, VERTICE_PATH)


class Veredicto(Enum):
    EXCELENTE = "EXCELENTE"
    BOM = "BOM"
    PARCIAL = "PARCIAL"
    RUIM = "RUIM"
    FALHA_TOTAL = "FALHA_TOTAL"


@dataclass
class AnaliseDetalhada:
    """Análise detalhada de um resultado de teste."""

    teste_nome: str
    agente: str
    tarefa: str
    output_completo: str
    output_resumo: str

    # Expectativas
    esperado: List[str]
    encontrado: List[str]
    nao_encontrado: List[str]

    # Análise crítica
    veredicto: Veredicto
    justificativa: str
    pontos_positivos: List[str]
    pontos_negativos: List[str]
    sugestoes_melhoria: List[str]

    duracao: float = 0.0


class TesteE2EReal:
    """Executor de testes E2E reais com análise crítica."""

    def __init__(self):
        self.resultados: List[AnaliseDetalhada] = []
        self.inicio = datetime.now()

    async def invocar_agente(self, agente: str, tarefa: str, arquivos: List[str]) -> str:
        """Invoca um agente REAL e retorna o output."""
        from vertice_tui.core.agents.manager import AgentManager

        context = {
            "cwd": str(Path.cwd()),
            "files": arquivos,
            "project_name": Path.cwd().name,
        }

        manager = AgentManager()
        chunks = []

        try:
            async for chunk in manager.invoke(agente, tarefa, context):
                chunks.append(chunk)
        except Exception as e:
            chunks.append(f"\n[ERRO]: {e}")
            import traceback

            chunks.append(traceback.format_exc())

        return "".join(chunks)

    def analisar_resultado(
        self, nome: str, agente: str, tarefa: str, output: str, expectativas: Dict[str, Any]
    ) -> AnaliseDetalhada:
        """Analisa criticamente o resultado de um teste."""

        # Verificar o que foi encontrado vs esperado
        esperado = expectativas.get("keywords", [])
        output_lower = output.lower()

        encontrado = [kw for kw in esperado if kw.lower() in output_lower]
        nao_encontrado = [kw for kw in esperado if kw.lower() not in output_lower]

        # Determinar veredicto
        if not output or len(output) < 20:
            veredicto = Veredicto.FALHA_TOTAL
        elif len(encontrado) == len(esperado):
            veredicto = Veredicto.EXCELENTE
        elif len(encontrado) >= len(esperado) * 0.7:
            veredicto = Veredicto.BOM
        elif len(encontrado) >= len(esperado) * 0.4:
            veredicto = Veredicto.PARCIAL
        elif encontrado:
            veredicto = Veredicto.RUIM
        else:
            veredicto = Veredicto.FALHA_TOTAL

        # Análise crítica baseada no conteúdo
        pontos_positivos = []
        pontos_negativos = []
        sugestoes = []

        # Verificar estrutura do output
        if "##" in output or "**" in output:
            pontos_positivos.append("Output formatado com markdown")
        else:
            pontos_negativos.append("Output sem formatação estruturada")
            sugestoes.append("Adicionar formatação markdown para melhor legibilidade")

        # Verificar se tem informações específicas
        if "file:" in output.lower() or "linha" in output.lower() or "line" in output.lower():
            pontos_positivos.append("Referencia arquivos/linhas específicas")
        else:
            pontos_negativos.append("Não referencia localizações específicas no código")
            sugestoes.append("Incluir referências a arquivos e linhas")

        # Verificar erros
        if "error" in output.lower() or "erro" in output.lower() or "fail" in output.lower():
            if "All providers exhausted" in output:
                pontos_negativos.append("Falha de infraestrutura: provedores LLM não disponíveis")
                sugestoes.append("Configurar pelo menos um provedor LLM (Anthropic, Google, etc)")
            elif "not found" in output.lower():
                pontos_negativos.append("Recursos não encontrados durante execução")

        # Verificar conteúdo específico por tipo de agente
        if agente == "security":
            if "sql" in output.lower() and "injection" in output.lower():
                pontos_positivos.append("Detectou SQL Injection corretamente")
            if "md5" in output.lower() or "weak" in output.lower():
                pontos_positivos.append("Detectou criptografia fraca")
            if "password" in output.lower() or "secret" in output.lower():
                pontos_positivos.append("Detectou credenciais expostas")
            if "owasp" in output.lower():
                pontos_positivos.append("Referencia padrões OWASP")

        elif agente == "reviewer":
            if "score" in output.lower():
                pontos_positivos.append("Fornece score de qualidade")
            if "issue" in output.lower() or "problem" in output.lower():
                pontos_positivos.append("Identifica problemas")
            if "recommendation" in output.lower() or "suggest" in output.lower():
                pontos_positivos.append("Fornece recomendações")

        elif agente == "explorer":
            if "file" in output.lower():
                pontos_positivos.append("Lista arquivos")
            if "class" in output.lower() or "function" in output.lower():
                pontos_positivos.append("Identifica estruturas de código")

        elif agente == "performance":
            if "bottleneck" in output.lower() or "optimization" in output.lower():
                pontos_positivos.append("Identifica gargalos/otimizações")
            if "complexity" in output.lower() or "o(" in output.lower():
                pontos_positivos.append("Analisa complexidade")

        # Gerar justificativa
        if veredicto == Veredicto.EXCELENTE:
            justificativa = f"Todos os {len(esperado)} critérios esperados foram atendidos. O agente executou a tarefa com sucesso."
        elif veredicto == Veredicto.BOM:
            justificativa = f"Encontrou {len(encontrado)}/{len(esperado)} critérios. Resultado satisfatório mas pode melhorar."
        elif veredicto == Veredicto.PARCIAL:
            justificativa = f"Encontrou apenas {len(encontrado)}/{len(esperado)} critérios. Funcionalidade parcial."
        elif veredicto == Veredicto.RUIM:
            justificativa = f"Encontrou apenas {len(encontrado)}/{len(esperado)} critérios. Precisa de correções."
        else:
            justificativa = "Falha total. Nenhum critério atendido ou output vazio/erro."

        # Criar resumo do output
        if len(output) > 500:
            resumo = output[:500] + "..."
        else:
            resumo = output

        return AnaliseDetalhada(
            teste_nome=nome,
            agente=agente,
            tarefa=tarefa,
            output_completo=output,
            output_resumo=resumo,
            esperado=esperado,
            encontrado=encontrado,
            nao_encontrado=nao_encontrado,
            veredicto=veredicto,
            justificativa=justificativa,
            pontos_positivos=pontos_positivos,
            pontos_negativos=pontos_negativos,
            sugestoes_melhoria=sugestoes,
        )

    async def executar_teste(
        self,
        nome: str,
        agente: str,
        tarefa: str,
        expectativas: Dict[str, Any],
        arquivos: Optional[List[str]] = None,
    ) -> AnaliseDetalhada:
        """Executa um teste completo com análise."""

        print(f"\n{'='*80}")
        print(f"TESTE: {nome}")
        print(f"AGENTE: {agente}")
        print(f"TAREFA: {tarefa}")
        print(f"{'='*80}\n")

        if arquivos is None:
            cwd = Path.cwd()
            arquivos = [
                str(cwd / "src" / "user_service.py"),
                str(cwd / "src" / "data_processor.py"),
            ]

        inicio = datetime.now()
        output = await self.invocar_agente(agente, tarefa, arquivos)
        duracao = (datetime.now() - inicio).total_seconds()

        print(f"OUTPUT ({len(output)} chars):")
        print("-" * 40)
        print(output[:1000])
        if len(output) > 1000:
            print(f"... ({len(output) - 1000} chars omitidos)")
        print("-" * 40)

        analise = self.analisar_resultado(nome, agente, tarefa, output, expectativas)
        analise.duracao = duracao

        self.resultados.append(analise)

        print(f"\nVEREDICTO: {analise.veredicto.value}")
        print(f"JUSTIFICATIVA: {analise.justificativa}")

        return analise

    async def executar_todos_testes(self):
        """Executa bateria completa de testes."""

        print("=" * 80)
        print("VERTICE - TESTES E2E REAIS E COMPLETOS")
        print(f"Iniciado: {self.inicio.isoformat()}")
        print("=" * 80)

        # ================================================================
        # TESTE 1: SECURITY AGENT - Detecção de Vulnerabilidades
        # ================================================================
        await self.executar_teste(
            nome="Security - Detecção de SQL Injection e Credenciais",
            agente="security",
            tarefa="Faça uma auditoria de segurança completa deste código",
            expectativas={
                "keywords": [
                    "sql",
                    "injection",  # SQL Injection
                    "password",
                    "secret",  # Credenciais expostas
                    "md5",  # Criptografia fraca
                    "vulnerability",
                    "critical",  # Severidade
                ]
            },
        )

        # ================================================================
        # TESTE 2: REVIEWER AGENT - Análise de Qualidade
        # ================================================================
        await self.executar_teste(
            nome="Reviewer - Análise de Qualidade de Código",
            agente="reviewer",
            tarefa="Revise a qualidade deste código, identifique problemas e dê recomendações",
            expectativas={
                "keywords": [
                    "score",  # Score de qualidade
                    "issue",
                    "problem",  # Problemas identificados
                    "function",  # Análise de funções
                    "recommendation",  # Recomendações
                ]
            },
        )

        # ================================================================
        # TESTE 3: EXPLORER AGENT - Exploração de Codebase
        # ================================================================
        await self.executar_teste(
            nome="Explorer - Mapeamento de Estrutura",
            agente="explorer",
            tarefa="Explore este codebase e liste todos os arquivos, classes e funções principais",
            expectativas={
                "keywords": [
                    "file",
                    "src",  # Arquivos
                    "class",
                    "userservice",  # Classes
                    "function",
                    "def",  # Funções
                ]
            },
        )

        # ================================================================
        # TESTE 4: PERFORMANCE AGENT - Análise de Performance
        # ================================================================
        await self.executar_teste(
            nome="Performance - Identificação de Bottlenecks",
            agente="performance",
            tarefa="Analise a performance deste código e identifique gargalos",
            expectativas={
                "keywords": [
                    "performance",  # Tema
                    "bottleneck",
                    "optimization",  # Problemas
                    "score",  # Métricas
                ]
            },
        )

        # ================================================================
        # TESTE 5: REFACTORER AGENT - Sugestões de Refatoração
        # ================================================================
        await self.executar_teste(
            nome="Refactorer - Oportunidades de Melhoria",
            agente="refactorer",
            tarefa="Identifique oportunidades de refatoração neste código",
            expectativas={
                "keywords": [
                    "refactor",  # Tema
                    "duplicate",
                    "extract",  # Padrões
                    "improve",  # Melhorias
                ]
            },
        )

        # ================================================================
        # TESTE 6: TESTING AGENT - Geração de Testes
        # ================================================================
        await self.executar_teste(
            nome="Testing - Geração de Casos de Teste",
            agente="testing",
            tarefa="Gere casos de teste para as funções principais",
            expectativas={
                "keywords": [
                    "test",
                    "assert",  # Estrutura de teste
                    "def test_",  # Funções de teste
                    "case",  # Casos
                ]
            },
        )

        # ================================================================
        # TESTE 7: DOCUMENTATION AGENT - Geração de Documentação
        # ================================================================
        await self.executar_teste(
            nome="Documentation - Geração de Docstrings",
            agente="documentation",
            tarefa="Gere documentação para as funções e classes",
            expectativas={
                "keywords": [
                    "docstring",
                    "documentation",  # Tipo
                    "param",
                    "return",  # Estrutura
                    "function",  # Escopo
                ]
            },
        )

        # ================================================================
        # TESTE 8: ARCHITECT AGENT - Análise de Arquitetura
        # ================================================================
        await self.executar_teste(
            nome="Architect - Análise de Design",
            agente="architect",
            tarefa="Analise a arquitetura deste código e sugira melhorias",
            expectativas={
                "keywords": [
                    "architecture",
                    "design",  # Tema
                    "module",
                    "component",  # Estrutura
                    "pattern",  # Padrões
                ]
            },
        )

        # ================================================================
        # TESTE 9: PLANNER AGENT - Planejamento de Tarefa
        # ================================================================
        await self.executar_teste(
            nome="Planner - Planejamento de Feature",
            agente="planner",
            tarefa="Planeje como adicionar autenticação JWT a este código",
            expectativas={
                "keywords": [
                    "plan",
                    "step",  # Estrutura
                    "task",
                    "implementation",  # Detalhes
                ]
            },
        )

        # ================================================================
        # TESTE 10: DEVOPS AGENT - Configuração de Infraestrutura
        # ================================================================
        await self.executar_teste(
            nome="DevOps - Configuração de Deploy",
            agente="devops",
            tarefa="Sugira configuração de deploy para este projeto",
            expectativas={
                "keywords": [
                    "deploy",
                    "docker",  # Ferramentas
                    "configuration",  # Config
                    "infrastructure",  # Infra
                ]
            },
        )

        return self.gerar_relatorio()

    def gerar_relatorio(self) -> str:
        """Gera relatório detalhado de todos os testes."""

        linhas = []
        linhas.append("=" * 80)
        linhas.append("RELATÓRIO DETALHADO DE TESTES E2E - VERTICE FRAMEWORK")
        linhas.append(f"Gerado em: {datetime.now().isoformat()}")
        linhas.append(f"Duração total: {(datetime.now() - self.inicio).total_seconds():.1f}s")
        linhas.append("=" * 80)

        # Sumário executivo
        excelente = sum(1 for r in self.resultados if r.veredicto == Veredicto.EXCELENTE)
        bom = sum(1 for r in self.resultados if r.veredicto == Veredicto.BOM)
        parcial = sum(1 for r in self.resultados if r.veredicto == Veredicto.PARCIAL)
        ruim = sum(1 for r in self.resultados if r.veredicto == Veredicto.RUIM)
        falha = sum(1 for r in self.resultados if r.veredicto == Veredicto.FALHA_TOTAL)
        total = len(self.resultados)

        linhas.append("\n" + "=" * 80)
        linhas.append("SUMÁRIO EXECUTIVO")
        linhas.append("=" * 80)
        linhas.append(f"\nTotal de testes: {total}")
        linhas.append(f"  - EXCELENTE: {excelente} ({100*excelente/total:.0f}%)")
        linhas.append(f"  - BOM:       {bom} ({100*bom/total:.0f}%)")
        linhas.append(f"  - PARCIAL:   {parcial} ({100*parcial/total:.0f}%)")
        linhas.append(f"  - RUIM:      {ruim} ({100*ruim/total:.0f}%)")
        linhas.append(f"  - FALHA:     {falha} ({100*falha/total:.0f}%)")

        aprovados = excelente + bom
        linhas.append(f"\nTaxa de aprovação: {100*aprovados/total:.0f}% ({aprovados}/{total})")

        # Detalhes de cada teste
        linhas.append("\n" + "=" * 80)
        linhas.append("ANÁLISE DETALHADA POR TESTE")
        linhas.append("=" * 80)

        for i, r in enumerate(self.resultados, 1):
            linhas.append(f"\n{'─'*80}")
            linhas.append(f"TESTE {i}: {r.teste_nome}")
            linhas.append(f"{'─'*80}")

            linhas.append(f"\n📋 AGENTE: {r.agente}")
            linhas.append(f"📝 TAREFA: {r.tarefa}")
            linhas.append(f"⏱️  DURAÇÃO: {r.duracao:.2f}s")

            # Veredicto com emoji
            emoji_map = {
                Veredicto.EXCELENTE: "🌟",
                Veredicto.BOM: "✅",
                Veredicto.PARCIAL: "⚠️",
                Veredicto.RUIM: "❌",
                Veredicto.FALHA_TOTAL: "💀",
            }
            linhas.append(f"\n{emoji_map[r.veredicto]} VEREDICTO: {r.veredicto.value}")
            linhas.append(f"💬 JUSTIFICATIVA: {r.justificativa}")

            # O que foi esperado vs encontrado
            linhas.append("\n📊 ANÁLISE DE CRITÉRIOS:")
            linhas.append(f"   Esperado: {r.esperado}")
            linhas.append(f"   Encontrado: {r.encontrado}")
            if r.nao_encontrado:
                linhas.append(f"   Não encontrado: {r.nao_encontrado}")

            # Pontos positivos
            if r.pontos_positivos:
                linhas.append("\n✨ PONTOS POSITIVOS:")
                for p in r.pontos_positivos:
                    linhas.append(f"   • {p}")

            # Pontos negativos
            if r.pontos_negativos:
                linhas.append("\n⚠️  PONTOS NEGATIVOS:")
                for p in r.pontos_negativos:
                    linhas.append(f"   • {p}")

            # Sugestões
            if r.sugestoes_melhoria:
                linhas.append("\n💡 SUGESTÕES DE MELHORIA:")
                for s in r.sugestoes_melhoria:
                    linhas.append(f"   • {s}")

            # Output resumido
            linhas.append("\n📄 OUTPUT (resumo):")
            linhas.append("   " + "-" * 60)
            for linha in r.output_resumo.split("\n")[:15]:
                linhas.append(f"   {linha}")
            if r.output_resumo.count("\n") > 15:
                linhas.append(f"   ... (+ {r.output_resumo.count(chr(10)) - 15} linhas)")
            linhas.append("   " + "-" * 60)

        # Conclusão
        linhas.append("\n" + "=" * 80)
        linhas.append("CONCLUSÃO E RECOMENDAÇÕES")
        linhas.append("=" * 80)

        if aprovados >= total * 0.7:
            linhas.append("\n✅ SISTEMA EM BOM ESTADO")
            linhas.append("A maioria dos agentes está funcionando corretamente.")
        elif aprovados >= total * 0.4:
            linhas.append("\n⚠️  SISTEMA PARCIALMENTE FUNCIONAL")
            linhas.append("Alguns agentes precisam de correções.")
        else:
            linhas.append("\n❌ SISTEMA COM PROBLEMAS CRÍTICOS")
            linhas.append("Muitos agentes não estão funcionando adequadamente.")

        # Agentes que precisam de atenção
        problematicos = [
            r for r in self.resultados if r.veredicto in [Veredicto.RUIM, Veredicto.FALHA_TOTAL]
        ]
        if problematicos:
            linhas.append("\n🔧 AGENTES QUE PRECISAM DE ATENÇÃO:")
            for r in problematicos:
                linhas.append(f"   • {r.agente}: {r.justificativa}")

        # Top issues
        todos_negativos = []
        for r in self.resultados:
            todos_negativos.extend(r.pontos_negativos)

        if todos_negativos:
            from collections import Counter

            mais_comuns = Counter(todos_negativos).most_common(5)
            linhas.append("\n🔴 PROBLEMAS MAIS FREQUENTES:")
            for problema, count in mais_comuns:
                linhas.append(f"   • {problema} ({count}x)")

        relatorio = "\n".join(linhas)

        # Imprimir e salvar
        print("\n\n" + relatorio)

        with open("RELATORIO_E2E_DETALHADO.txt", "w") as f:
            f.write(relatorio)

        # Salvar outputs completos separadamente
        with open("OUTPUTS_COMPLETOS.txt", "w") as f:
            for r in self.resultados:
                f.write(f"\n{'='*80}\n")
                f.write(f"TESTE: {r.teste_nome}\n")
                f.write(f"AGENTE: {r.agente}\n")
                f.write(f"{'='*80}\n\n")
                f.write(r.output_completo)
                f.write("\n\n")

        print(f"\n\n📁 Relatório salvo em: {Path.cwd()}/RELATORIO_E2E_DETALHADO.txt")
        print(f"📁 Outputs completos em: {Path.cwd()}/OUTPUTS_COMPLETOS.txt")

        return relatorio


async def main():
    os.chdir("/tmp/vertice_e2e_test")
    print(f"Diretório de trabalho: {os.getcwd()}")

    # Verificar arquivos de teste
    arquivos = list(Path("src").glob("*.py"))
    print(f"Arquivos de teste: {arquivos}")

    teste = TesteE2EReal()
    await teste.executar_todos_testes()


if __name__ == "__main__":
    asyncio.run(main())

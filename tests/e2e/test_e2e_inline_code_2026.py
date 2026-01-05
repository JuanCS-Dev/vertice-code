#!/usr/bin/env python3
"""
VERTICE - TESTES E2E REAIS PARA FIXES 2026
==========================================

Este arquivo executa testes E2E REAIS para validar os fixes de inline code.
SEM MOCKS. EXECUÇÃO REAL. ANÁLISE CRÍTICA.

Valida:
1. Testing Agent processa inline code (antes: "No source code provided")
2. Reviewer Agent processa inline code (antes: "No files provided")
3. Documentation Agent processa inline code (antes: usava target_path)
4. Explorer Agent retorna snippets (antes: só paths)
5. Prometheus valida skills (antes: aceitava qualquer skill)

Baseado em: Claude Code 2026 + Gemini CLI 2026 patterns
"""
import asyncio
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any
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
class AnaliseResultado:
    """Análise de um resultado de teste E2E."""
    teste_nome: str
    agente: str
    prompt_natural: str  # O prompt em linguagem natural
    output_completo: str
    output_resumo: str

    # Validação do fix
    problema_anterior: str  # O que acontecia antes do fix
    comportamento_esperado: str  # O que deveria acontecer após fix
    comportamento_real: str  # O que realmente aconteceu

    # Critérios de sucesso
    criterios: List[str]
    criterios_atendidos: List[str]
    criterios_nao_atendidos: List[str]

    # Veredicto
    veredicto: Veredicto
    justificativa: str
    duracao: float = 0.0


class TestesE2EInlineCode:
    """Testes E2E reais para validar fixes de inline code."""

    def __init__(self):
        self.resultados: List[AnaliseResultado] = []
        self.inicio = datetime.now()

    async def invocar_agente(self, agente: str, prompt: str, context: Dict[str, Any]) -> str:
        """Invoca um agente REAL via AgentManager."""
        try:
            from vertice_tui.core.agents.manager import AgentManager

            manager = AgentManager()
            chunks = []

            async for chunk in manager.invoke(agente, prompt, context):
                chunks.append(chunk)

            return "".join(chunks)
        except Exception as e:
            import traceback
            return f"[ERRO]: {e}\n{traceback.format_exc()}"

    def analisar_fix(
        self,
        nome: str,
        agente: str,
        prompt: str,
        output: str,
        problema_anterior: str,
        comportamento_esperado: str,
        criterios: List[str],
        duracao: float
    ) -> AnaliseResultado:
        """Analisa se o fix funcionou baseado no output real."""

        output_lower = output.lower()

        # Verificar critérios
        criterios_atendidos = []
        criterios_nao_atendidos = []

        for criterio in criterios:
            # Cada critério pode ter múltiplas keywords separadas por |
            keywords = criterio.split("|")
            if any(kw.lower() in output_lower for kw in keywords):
                criterios_atendidos.append(criterio)
            else:
                criterios_nao_atendidos.append(criterio)

        # Verificar se o problema anterior ainda ocorre
        problema_resolvido = True
        comportamento_real = ""

        # Detectar falhas conhecidas
        if "no source code" in output_lower:
            problema_resolvido = False
            comportamento_real = "FALHA: Ainda diz 'No source code provided'"
        elif "no files provided" in output_lower:
            problema_resolvido = False
            comportamento_real = "FALHA: Ainda diz 'No files provided'"
        elif "error" in output_lower and "all providers exhausted" in output_lower:
            problema_resolvido = False  # Não podemos avaliar
            comportamento_real = "INFRA: Sem provedores LLM disponíveis"
        elif len(output) < 50:
            problema_resolvido = False
            comportamento_real = f"FALHA: Output muito curto ({len(output)} chars)"
        else:
            comportamento_real = f"OK: Output de {len(output)} chars gerado"

        # Determinar veredicto
        if not problema_resolvido:
            if "all providers exhausted" in output_lower:
                veredicto = Veredicto.PARCIAL  # Não é culpa do fix
            else:
                veredicto = Veredicto.FALHA_TOTAL
        elif len(criterios_atendidos) == len(criterios):
            veredicto = Veredicto.EXCELENTE
        elif len(criterios_atendidos) >= len(criterios) * 0.7:
            veredicto = Veredicto.BOM
        elif len(criterios_atendidos) >= len(criterios) * 0.4:
            veredicto = Veredicto.PARCIAL
        elif criterios_atendidos:
            veredicto = Veredicto.RUIM
        else:
            veredicto = Veredicto.FALHA_TOTAL

        # Justificativa
        if veredicto == Veredicto.EXCELENTE:
            justificativa = f"FIX VALIDADO: Todos os {len(criterios)} critérios atendidos"
        elif veredicto == Veredicto.BOM:
            justificativa = f"FIX PARCIALMENTE VALIDADO: {len(criterios_atendidos)}/{len(criterios)} critérios"
        elif "all providers exhausted" in output_lower:
            justificativa = "INCONCLUSIVO: Sem provedores LLM para testar"
        else:
            justificativa = f"FIX NÃO VALIDADO: Apenas {len(criterios_atendidos)}/{len(criterios)} critérios"

        return AnaliseResultado(
            teste_nome=nome,
            agente=agente,
            prompt_natural=prompt,
            output_completo=output[:2000],
            output_resumo=output[:300],
            problema_anterior=problema_anterior,
            comportamento_esperado=comportamento_esperado,
            comportamento_real=comportamento_real,
            criterios=criterios,
            criterios_atendidos=criterios_atendidos,
            criterios_nao_atendidos=criterios_nao_atendidos,
            veredicto=veredicto,
            justificativa=justificativa,
            duracao=duracao
        )

    # =========================================================================
    # TESTE 1: Testing Agent - Inline Code
    # =========================================================================
    async def teste_testing_agent_inline_code(self) -> AnaliseResultado:
        """
        TESTE E2E REAL: Testing Agent deve processar código inline.

        ANTES DO FIX: Retornava "No source code provided"
        APÓS O FIX: Deve gerar testes para o código inline
        """
        print("\n" + "="*60)
        print("TESTE 1: Testing Agent - Inline Code")
        print("="*60)

        prompt = """Gere testes unitários para esta função:

```python
def calculate_fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
```

Inclua testes para casos base e casos de borda."""

        context = {
            "cwd": VERTICE_PATH,
            "user_message": prompt,  # O fix verifica user_message primeiro!
        }

        print(f"Prompt: {prompt[:100]}...")
        inicio = datetime.now()
        output = await self.invocar_agente("testing", prompt, context)
        duracao = (datetime.now() - inicio).total_seconds()
        print(f"Output ({len(output)} chars): {output[:200]}...")

        return self.analisar_fix(
            nome="Testing Agent Inline Code",
            agente="testing",
            prompt=prompt,
            output=output,
            problema_anterior="Retornava 'No source code provided' ignorando código inline",
            comportamento_esperado="Deve analisar o código fibonacci e gerar testes",
            criterios=[
                "test|pytest|unittest",  # Gerou testes
                "fibonacci|fib",  # Mencionou a função
                "assert|assertEqual",  # Tem assertions
                "0|1|base",  # Testa casos base
            ],
            duracao=duracao
        )

    # =========================================================================
    # TESTE 2: Reviewer Agent - Inline Code
    # =========================================================================
    async def teste_reviewer_agent_inline_code(self) -> AnaliseResultado:
        """
        TESTE E2E REAL: Reviewer Agent deve processar código inline.

        ANTES DO FIX: Retornava "No files provided"
        APÓS O FIX: Deve revisar o código inline
        """
        print("\n" + "="*60)
        print("TESTE 2: Reviewer Agent - Inline Code")
        print("="*60)

        prompt = """Revise este código e identifique problemas de segurança:

```python
def unsafe_query(user_input):
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return db.execute(query)

def weak_hash(password):
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()
```

Aponte as vulnerabilidades e sugira correções."""

        context = {
            "cwd": VERTICE_PATH,
            "user_message": prompt,
        }

        print(f"Prompt: {prompt[:100]}...")
        inicio = datetime.now()
        output = await self.invocar_agente("reviewer", prompt, context)
        duracao = (datetime.now() - inicio).total_seconds()
        print(f"Output ({len(output)} chars): {output[:200]}...")

        return self.analisar_fix(
            nome="Reviewer Agent Inline Code",
            agente="reviewer",
            prompt=prompt,
            output=output,
            problema_anterior="Retornava 'No files provided' ignorando código inline",
            comportamento_esperado="Deve identificar SQL injection e MD5 fraco",
            criterios=[
                "sql|injection|injeção",  # Detectou SQL injection
                "md5|hash|weak|fraco",  # Detectou hash fraco
                "parameterized|prepared|parâmetro",  # Sugeriu fix SQL
                "bcrypt|argon|sha256|scrypt",  # Sugeriu hash melhor
            ],
            duracao=duracao
        )

    # =========================================================================
    # TESTE 3: Documentation Agent - Inline Code
    # =========================================================================
    async def teste_documentation_agent_inline_code(self) -> AnaliseResultado:
        """
        TESTE E2E REAL: Documentation Agent deve processar código inline.

        ANTES DO FIX: Usava target_path ignorando código inline
        APÓS O FIX: Deve documentar o código inline diretamente
        """
        print("\n" + "="*60)
        print("TESTE 3: Documentation Agent - Inline Code")
        print("="*60)

        prompt = """Gere documentação detalhada para esta classe:

```python
class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.cache = {}

    def process(self, data):
        if data in self.cache:
            return self.cache[data]
        result = self._transform(data)
        self.cache[data] = result
        return result

    def _transform(self, data):
        return data.upper()
```

Inclua docstrings no estilo Google."""

        context = {
            "cwd": VERTICE_PATH,
            "user_message": prompt,
        }

        print(f"Prompt: {prompt[:100]}...")
        inicio = datetime.now()
        output = await self.invocar_agente("documentation", prompt, context)
        duracao = (datetime.now() - inicio).total_seconds()
        print(f"Output ({len(output)} chars): {output[:200]}...")

        return self.analisar_fix(
            nome="Documentation Agent Inline Code",
            agente="documentation",
            prompt=prompt,
            output=output,
            problema_anterior="Scaneava target_path ignorando código inline",
            comportamento_esperado="Deve gerar docstrings para DataProcessor",
            criterios=[
                "DataProcessor",  # Mencionou a classe
                "process|_transform",  # Documentou métodos
                "Args:|Parameters:|param",  # Formato docstring
                "Returns:|return",  # Documentou retorno
            ],
            duracao=duracao
        )

    # =========================================================================
    # TESTE 4: Explorer Agent - Content Snippets
    # =========================================================================
    async def teste_explorer_agent_snippets(self) -> AnaliseResultado:
        """
        TESTE E2E REAL: Explorer Agent deve retornar snippets de conteúdo.

        ANTES DO FIX: Só retornava paths sem conteúdo
        APÓS O FIX: Deve incluir snippets de código real
        """
        print("\n" + "="*60)
        print("TESTE 4: Explorer Agent - Content Snippets")
        print("="*60)

        prompt = """Encontre arquivos relacionados a 'BaseAgent' e mostre o conteúdo relevante.
Quero ver trechos de código que definem ou usam BaseAgent."""

        context = {
            "cwd": VERTICE_PATH,
        }

        print(f"Prompt: {prompt[:100]}...")
        inicio = datetime.now()
        output = await self.invocar_agente("explorer", prompt, context)
        duracao = (datetime.now() - inicio).total_seconds()
        print(f"Output ({len(output)} chars): {output[:200]}...")

        return self.analisar_fix(
            nome="Explorer Agent Snippets",
            agente="explorer",
            prompt=prompt,
            output=output,
            problema_anterior="Só retornava paths sem mostrar conteúdo",
            comportamento_esperado="Deve incluir snippets de código com BaseAgent",
            criterios=[
                "BaseAgent|base.py",  # Encontrou arquivo
                "class|def",  # Mostrou código
                ".py",  # Listou arquivos Python
                "agent|Agent",  # Contexto relevante
            ],
            duracao=duracao
        )

    # =========================================================================
    # TESTE 5: Skill Registry - Anti-Hallucination
    # =========================================================================
    async def teste_skill_registry(self) -> AnaliseResultado:
        """
        TESTE E2E REAL: Skill Registry deve validar skills.

        ANTES DO FIX: Aceitava qualquer skill (hallucination)
        APÓS O FIX: Só aceita skills do registry
        """
        print("\n" + "="*60)
        print("TESTE 5: Skill Registry - Anti-Hallucination")
        print("="*60)

        # Este teste é unitário, não precisa de agente
        from prometheus.core.skill_registry import validate_skills, VALID_SKILLS

        # Simular skills detectadas (algumas válidas, algumas alucinadas)
        skills_detectadas = [
            "python_basics",  # VÁLIDA
            "super_mega_coding",  # ALUCINADA
            "testing",  # VÁLIDA
            "quantum_debugging",  # ALUCINADA
            "async_programming",  # VÁLIDA
        ]

        validadas = validate_skills(skills_detectadas)

        # Criar output para análise
        output = f"""
SKILL REGISTRY VALIDATION TEST
==============================

Skills detectadas: {skills_detectadas}
Skills validadas: {validadas}
Total no registry: {len(VALID_SKILLS)}

Skills aceitas:
{chr(10).join(f'  - {s}' for s in validadas)}

Skills rejeitadas (alucinadas):
{chr(10).join(f'  - {s}' for s in skills_detectadas if s not in validadas)}
"""
        print(output)

        # Verificar se filtrou corretamente
        skills_validas_esperadas = {"python_basics", "testing", "async_programming"}
        skills_rejeitadas = set(skills_detectadas) - set(validadas)

        criterios_atendidos = []
        criterios = [
            "python_basics aceita",
            "testing aceita",
            "super_mega_coding rejeitada",
            "quantum_debugging rejeitada",
        ]

        if "python_basics" in validadas:
            criterios_atendidos.append(criterios[0])
        if "testing" in validadas:
            criterios_atendidos.append(criterios[1])
        if "super_mega_coding" not in validadas:
            criterios_atendidos.append(criterios[2])
        if "quantum_debugging" not in validadas:
            criterios_atendidos.append(criterios[3])

        veredicto = Veredicto.EXCELENTE if len(criterios_atendidos) == 4 else Veredicto.RUIM

        return AnaliseResultado(
            teste_nome="Skill Registry Anti-Hallucination",
            agente="prometheus",
            prompt_natural="Validar skills detectadas contra registry",
            output_completo=output,
            output_resumo=f"Validadas: {validadas}",
            problema_anterior="Aceitava qualquer skill name (hallucination)",
            comportamento_esperado="Só aceita skills do VALID_SKILLS",
            comportamento_real=f"Filtrou {len(skills_rejeitadas)} skills alucinadas",
            criterios=criterios,
            criterios_atendidos=criterios_atendidos,
            criterios_nao_atendidos=[c for c in criterios if c not in criterios_atendidos],
            veredicto=veredicto,
            justificativa=f"{'VALIDADO' if veredicto == Veredicto.EXCELENTE else 'FALHOU'}: {len(criterios_atendidos)}/4 critérios",
            duracao=0.0
        )

    # =========================================================================
    # EXECUTAR TODOS OS TESTES
    # =========================================================================
    async def executar_todos(self):
        """Executa todos os testes E2E e gera relatório."""
        print("\n" + "="*70)
        print("VERTICE E2E - VALIDAÇÃO DOS FIXES 2026")
        print("Baseado em: Claude Code + Gemini CLI 2026 patterns")
        print("="*70)

        # Executar testes
        self.resultados.append(await self.teste_testing_agent_inline_code())
        self.resultados.append(await self.teste_reviewer_agent_inline_code())
        self.resultados.append(await self.teste_documentation_agent_inline_code())
        self.resultados.append(await self.teste_explorer_agent_snippets())
        self.resultados.append(await self.teste_skill_registry())

        # Gerar relatório
        self.gerar_relatorio()

    def gerar_relatorio(self):
        """Gera relatório detalhado dos testes."""
        print("\n" + "="*70)
        print("RELATÓRIO FINAL - VALIDAÇÃO E2E FIXES 2026")
        print("="*70)

        total = len(self.resultados)
        excelentes = sum(1 for r in self.resultados if r.veredicto == Veredicto.EXCELENTE)
        bons = sum(1 for r in self.resultados if r.veredicto == Veredicto.BOM)
        parciais = sum(1 for r in self.resultados if r.veredicto == Veredicto.PARCIAL)
        ruins = sum(1 for r in self.resultados if r.veredicto == Veredicto.RUIM)
        falhas = sum(1 for r in self.resultados if r.veredicto == Veredicto.FALHA_TOTAL)

        print("\nRESUMO:")
        print(f"  Total de testes: {total}")
        print(f"  EXCELENTE: {excelentes}")
        print(f"  BOM: {bons}")
        print(f"  PARCIAL: {parciais}")
        print(f"  RUIM: {ruins}")
        print(f"  FALHA_TOTAL: {falhas}")

        taxa_sucesso = (excelentes + bons) / total * 100 if total > 0 else 0
        print(f"\n  Taxa de Sucesso: {taxa_sucesso:.1f}%")

        print("\n" + "-"*70)
        print("DETALHES POR TESTE:")
        print("-"*70)

        for r in self.resultados:
            icon = {
                Veredicto.EXCELENTE: "✅",
                Veredicto.BOM: "✓",
                Veredicto.PARCIAL: "⚠️",
                Veredicto.RUIM: "❌",
                Veredicto.FALHA_TOTAL: "💀",
            }.get(r.veredicto, "?")

            print(f"\n{icon} {r.teste_nome}")
            print(f"   Agente: {r.agente}")
            print(f"   Veredicto: {r.veredicto.value}")
            print(f"   {r.justificativa}")
            print(f"   Problema anterior: {r.problema_anterior}")
            print(f"   Comportamento real: {r.comportamento_real}")
            print(f"   Critérios atendidos: {len(r.criterios_atendidos)}/{len(r.criterios)}")
            if r.criterios_nao_atendidos:
                print(f"   Critérios faltando: {r.criterios_nao_atendidos}")
            print(f"   Duração: {r.duracao:.2f}s")

        print("\n" + "="*70)
        print("FIM DO RELATÓRIO")
        print("="*70)


# =========================================================================
# MAIN
# =========================================================================
async def main():
    """Executa os testes E2E."""
    tester = TestesE2EInlineCode()
    await tester.executar_todos()


if __name__ == "__main__":
    asyncio.run(main())

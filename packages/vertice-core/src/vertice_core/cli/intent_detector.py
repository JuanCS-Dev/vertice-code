"""
Intent Detection - Detecta automaticamente qual agent usar.

Upgraded to use SemanticIntentClassifier with LLM support.
Falls back to heuristic patterns when LLM unavailable.

Reference: HEROIC_IMPLEMENTATION_PLAN.md Sprint 1.1
"""

import asyncio
from typing import Optional, Tuple, Any

from vertice_core.core.intent_classifier import (
    Intent,
    IntentResult,
    get_classifier,
)


# Map Intent enum to agent names
INTENT_TO_AGENT = {
    Intent.PLANNING: "planner",
    Intent.CODING: None,  # Default chat, no specific agent
    Intent.REVIEW: "reviewer",
    Intent.DEBUG: None,  # Handled by default coder
    Intent.REFACTOR: "refactorer",
    Intent.TEST: "testing",
    Intent.DOCS: "documentation",
    Intent.EXPLORE: "explorer",
    Intent.ARCHITECTURE: "architect",
    Intent.PERFORMANCE: "performance",
    Intent.SECURITY: "security",
    Intent.GENERAL: None,
}


class IntentDetector:
    """
    Detecta intenção do usuário para rotear para agent correto.

    Now uses SemanticIntentClassifier for better accuracy.
    """

    def __init__(self, llm_client: Optional[Any] = None):
        # Initialize semantic classifier
        self._classifier = get_classifier(llm_client)
        self._llm = llm_client
        self._last_result: Optional[IntentResult] = None

        # Legacy patterns kept for reference/fallback
        self.intent_patterns = {
            "planner": {
                "keywords": [
                    "plan",
                    "plano",
                    "planeje",
                    "planning",
                    "planear",
                    "dominar",
                    "estratégia",
                    "strategy",
                    "roadmap",
                    "objetivos",
                    "goals",
                    "metas",
                    "como fazer",
                    "passo a passo",
                    "etapas",
                    "fases",
                ],
                "patterns": [
                    r"como (posso|fazer|criar|desenvolver)",
                    r"qual (o|a) (melhor )?(forma|jeito|maneira)",
                    r"vamos (criar|fazer|planejar)",
                    r"preciso (criar|fazer|planejar)",
                ],
            },
            "architect": {
                "keywords": [
                    "arquitetura",
                    "architecture",
                    "design",
                    "desenhar",
                    "estrutura",
                    "structure",
                    "sistema",
                    "system",
                    "microservices",
                    "api",
                    "database",
                    "banco de dados",
                    "escalabilidade",
                    "scalability",
                ],
                "patterns": [
                    r"como (estruturar|organizar|arquitetar)",
                    r"qual arquitetura",
                    r"design de sistema",
                ],
            },
            "refactor": {
                "keywords": [
                    "refactor",
                    "refatorar",
                    "melhorar",
                    "improve",
                    "otimizar",
                    "optimize",
                    "limpar",
                    "clean",
                    "reescrever",
                    "rewrite",
                ],
                "patterns": [
                    r"como melhorar (este|esse|o|a)",
                    r"refatora(r|ção)",
                    r"pode melhorar",
                ],
            },
            "test": {
                "keywords": [
                    "test",
                    "teste",
                    "testes",
                    "testing",
                    "unit test",
                    "integration test",
                    "e2e",
                    "coverage",
                    "cobertura",
                    "pytest",
                    "jest",
                ],
                "patterns": [
                    r"criar testes",
                    r"testar (este|esse|o|a)",
                    r"unit test",
                ],
            },
            "reviewer": {
                "keywords": [
                    "review",
                    "revisar",
                    "revisão",
                    "analise",
                    "análise",
                    "code review",
                    "feedback",
                    "melhorias",
                    "bugs",
                    "problemas",
                    "issues",
                    "crítica",
                    "avalie",
                    "avaliação",
                ],
                "patterns": [
                    r"(faz|faça|fazer) (um |o )?review",
                    r"revisa(r|ção)",
                    r"analisa(r|análise)",
                    r"o que (está|esta) errado",
                    r"tem (bug|problema|erro)",
                    r"avali(a|e|ar|ação)",
                ],
            },
            "docs": {
                "keywords": [
                    "documentar",
                    "document",
                    "documentação",
                    "documentation",
                    "readme",
                    "doc",
                    "docs",
                    "explicar",
                    "explain",
                    "comentários",
                    "comments",
                ],
                "patterns": [
                    r"documenta(r|ção)",
                    r"criar (readme|doc)",
                    r"explica(r|ção)",
                ],
            },
            "explorer": {
                "keywords": [
                    "explorar",
                    "explore",
                    "navegar",
                    "navigate",
                    "procurar",
                    "search",
                    "encontrar",
                    "find",
                    "onde está",
                    "where is",
                    "mostrar",
                    "show",
                ],
                "patterns": [
                    r"onde (está|fica|tem)",
                    r"mostra(r|me)",
                    r"encontra(r|me)",
                ],
            },
            "performance": {
                "keywords": [
                    "performance",
                    "performar",
                    "otimizar",
                    "optimize",
                    "rápido",
                    "velocidade",
                    "speed",
                    "lento",
                    "slow",
                    "benchmark",
                    "profile",
                    "profiling",
                ],
                "patterns": [
                    r"otimiza(r|ção)",
                    r"melhorar performance",
                    r"mais rápido",
                    r"(está|ta) lento",
                ],
            },
            "security": {
                "keywords": [
                    "segurança",
                    "security",
                    "vulnerabilidade",
                    "vulnerability",
                    "hack",
                    "exploit",
                    "ataque",
                    "attack",
                    "sql injection",
                    "xss",
                    "csrf",
                    "proteção",
                    "protection",
                ],
                "patterns": [
                    r"vulnerabilidad(e|es)",
                    r"falha de segurança",
                    r"security (issue|flaw|bug)",
                    r"pode ser hackeado",
                ],
            },
        }

    def detect(self, message: str) -> Optional[str]:
        """
        Detecta qual agent deve ser usado baseado na mensagem.

        Uses SemanticIntentClassifier for better accuracy.

        Returns:
            Nome do agent ou None se não detectar nada específico.
        """
        # Use async classifier synchronously
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, use sync fallback
                result = self._classify_sync(message)
            else:
                result = loop.run_until_complete(self._classifier.classify(message))
        except RuntimeError:
            # No event loop, create one
            result = asyncio.run(self._classifier.classify(message))

        self._last_result = result

        # Map intent to agent name
        agent = INTENT_TO_AGENT.get(result.intent)

        # Only return agent if confidence is sufficient
        if agent and result.confidence >= 0.4:
            return agent

        return None

    def _classify_sync(self, message: str) -> IntentResult:
        """Synchronous classification using heuristics only."""
        return self._classifier._classify_heuristic(message)

    async def detect_async(self, message: str) -> Optional[str]:
        """
        Async version of detect for use in async contexts.

        Returns:
            Nome do agent ou None se não detectar nada específico.
        """
        result = await self._classifier.classify(message)
        self._last_result = result

        agent = INTENT_TO_AGENT.get(result.intent)

        if agent and result.confidence >= 0.4:
            return agent

        return None

    def should_use_agent(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        Verifica se deve usar um agent e qual.

        Returns:
            (should_use, agent_name)
        """
        agent = self.detect(message)
        return (agent is not None, agent)

    async def should_use_agent_async(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        Async version for use in async contexts.

        Returns:
            (should_use, agent_name)
        """
        agent = await self.detect_async(message)
        return (agent is not None, agent)

    def get_last_result(self) -> Optional[IntentResult]:
        """Get the last classification result with full details."""
        return self._last_result

    def get_confidence(self) -> float:
        """Get confidence of last classification."""
        return self._last_result.confidence if self._last_result else 0.0

    def get_reasoning(self) -> str:
        """Get reasoning for last classification."""
        return self._last_result.reasoning if self._last_result else ""

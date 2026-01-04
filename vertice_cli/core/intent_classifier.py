"""
Semantic Intent Classifier

Model-based intent classification to replace pattern matching.
Uses LLM for semantic understanding with fallback to keywords.

Reference: HEROIC_IMPLEMENTATION_PLAN.md Sprint 1.1
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """
    Normalize text for accent-insensitive matching.

    Phase 10.2: Uses Unicode NFD decomposition to remove accents.
    Handles: á->a, é->e, ç->c, ã->a, etc.

    Examples:
        "código" -> "codigo"
        "função" -> "funcao"
        "não" -> "nao"
    """
    # NFD decomposes characters: é -> e + combining accent
    nfd = unicodedata.normalize("NFD", text)
    # Remove combining diacritical marks (category 'Mn')
    without_accents = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return without_accents.lower()


class Intent(str, Enum):
    """Available intent types."""

    PLANNING = "planning"
    CODING = "coding"
    REVIEW = "review"
    DEBUG = "debug"
    REFACTOR = "refactor"
    TEST = "test"
    DOCS = "docs"
    EXPLORE = "explore"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    SECURITY = "security"
    GENERAL = "general"


@dataclass
class IntentResult:
    """Result of intent classification."""

    intent: Intent
    confidence: float
    reasoning: str
    secondary_intents: List[Intent] = field(default_factory=list)
    method: str = "semantic"  # "semantic" or "heuristic"

    def to_dict(self) -> Dict[str, Any]:
        """Convert intent result to dictionary for serialization."""
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "secondary_intents": [i.value for i in self.secondary_intents],
            "method": self.method,
        }

    @classmethod
    def from_json(cls, response: str, method: str = "semantic") -> "IntentResult":
        """Parse LLM response into IntentResult."""
        try:
            # Extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])

                intent_str = data.get("intent", "general").lower()
                try:
                    intent = Intent(intent_str)
                except ValueError:
                    intent = Intent.GENERAL

                secondary = []
                for s in data.get("secondary_intents", []):
                    try:
                        secondary.append(Intent(s.lower()))
                    except ValueError:
                        pass

                return cls(
                    intent=intent,
                    confidence=float(data.get("confidence", 0.5)),
                    reasoning=data.get("reasoning", ""),
                    secondary_intents=secondary,
                    method=method,
                )
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse intent response: {e}")

        return cls(
            intent=Intent.GENERAL,
            confidence=0.3,
            reasoning="Failed to parse response",
            method=method,
        )


class SemanticIntentClassifier:
    """
    Semantic intent classification using LLM.

    Replaces regex patterns with model-based understanding.
    Falls back to heuristic classification when LLM is unavailable.
    """

    INTENT_SCHEMA = {
        "planning": "User wants to plan, design strategy, or create a roadmap",
        "coding": "User wants to write, modify, or generate code",
        "review": "User wants code review, feedback, or quality analysis",
        "debug": "User wants to fix bugs, troubleshoot, or resolve errors",
        "refactor": "User wants to improve code structure without changing behavior",
        "test": "User wants to create, run, or improve tests",
        "docs": "User wants documentation, comments, or explanations generated",
        "explore": "User wants to understand, navigate, or search the codebase",
        "architecture": "User wants system design, structure, or architectural decisions",
        "performance": "User wants to optimize speed, memory, or efficiency",
        "security": "User wants to find or fix security vulnerabilities",
        "general": "General conversation or unclear intent",
    }

    # Heuristic fallback patterns (word-boundary safe)
    # Phase 10.1: Added imperative PT forms (mostra, faz, busca, etc.)
    HEURISTIC_PATTERNS = {
        Intent.PLANNING: {
            "keywords": [
                # English
                "plan",
                "strategy",
                "roadmap",
                "goals",
                "design",
                "architect",
                # Portuguese infinitive
                "plano",
                "metas",
                "planejamento",
                "estrategia",
                # Portuguese imperative (tu/voce)
                "planeja",
                "planeja ai",
                "faz um plano",
                "monta um plano",
                # Portuguese colloquial
                "como fazer",
                "como implementar",
                "passo a passo",
                "etapas",
                "me ajuda a planejar",
            ],
            "weight": 2,
        },
        Intent.CODING: {
            "keywords": [
                # English
                "code",
                "implement",
                "create",
                "build",
                "write",
                "function",
                "class",
                "api",
                # Portuguese infinitive
                "codigo",
                "implementar",
                "criar",
                "construir",
                "escrever",
                "funcao",
                "classe",
                # Portuguese imperative
                "cria",
                "faz",
                "escreve",
                "implementa",
                "adiciona",
                "bota",
                "coloca",
                "poe",
                # Portuguese colloquial
                "desenvolver",
                "programar",
                "fazer",
                "adicionar",
                "faz ai",
                "cria ai",
            ],
            "weight": 2,
        },
        Intent.REVIEW: {
            "keywords": [
                # English
                "review",
                "feedback",
                "analyze",
                "check",
                "look at",
                "examine",
                # Portuguese infinitive
                "revisar",
                "analisar",
                "verificar",
                "checar",
                # Portuguese imperative
                "revisa",
                "analisa",
                "verifica",
                "checa",
                "olha",
                "da uma olhada",
                "avalia",
                # Portuguese colloquial
                "revisao",
                "avalie",
                "analise",
                "ve ai",
            ],
            "weight": 3,
        },
        Intent.DEBUG: {
            "keywords": [
                # English
                "debug",
                "fix",
                "error",
                "bug",
                "issue",
                "problem",
                "broken",
                "crash",
                "failing",
                # Portuguese infinitive
                "depurar",
                "corrigir",
                "consertar",
                "arrumar",
                "resolver",
                # Portuguese imperative
                "conserta",
                "arruma",
                "resolve",
                "corrige",
                "acha o erro",
                "acha o bug",
                # Portuguese colloquial
                "erro",
                "problema",
                "falha",
                "nao funciona",
                "bugado",
                "ta quebrado",
                "deu pau",
            ],
            "weight": 3,
        },
        Intent.REFACTOR: {
            "keywords": [
                # English
                "refactor",
                "improve",
                "clean",
                "restructure",
                "rewrite",
                "simplify",
                "reorganize",
                # Portuguese infinitive
                "refatorar",
                "melhorar",
                "limpar",
                "reestruturar",
                "reescrever",
                "simplificar",
                # Portuguese imperative
                "refatora",
                "melhora",
                "limpa",
                "reorganiza",
                "simplifica",
                "reestrutura",
                # Portuguese colloquial
                "deixa mais limpo",
                "melhora isso",
                "organiza melhor",
            ],
            "weight": 3,
        },
        Intent.TEST: {
            "keywords": [
                # English
                "test",
                "tests",
                "pytest",
                "unittest",
                "coverage",
                "spec",
                "testing",
                # Portuguese infinitive
                "teste",
                "testes",
                "testar",
                "cobertura",
                # Portuguese imperative
                "testa",
                "roda os testes",
                "executa os testes",
                "roda pytest",
                # Portuguese colloquial
                "faz um teste",
                "cria um teste",
                "teste unitario",
            ],
            "weight": 3,
        },
        Intent.DOCS: {
            "keywords": [
                # English
                "document",
                "documentation",
                "readme",
                "explain",
                "comment",
                "docstring",
                # Portuguese infinitive
                "documentar",
                "documentacao",
                "explicar",
                "comentar",
                # Portuguese imperative
                "documenta",
                "explica",
                "comenta",
                "escreve doc",
                "faz a doc",
                # Portuguese colloquial
                "me explica",
                "coloca comentario",
                "documenta isso",
            ],
            "weight": 2,
        },
        Intent.EXPLORE: {
            "keywords": [
                # English
                "explore",
                "find",
                "search",
                "where",
                "show",
                "navigate",
                "locate",
                "list",
                # Portuguese infinitive
                "explorar",
                "encontrar",
                "buscar",
                "mostrar",
                "navegar",
                "localizar",
                # Portuguese imperative
                "mostra",
                "busca",
                "encontra",
                "acha",
                "lista",
                "procura",
                "localiza",
                # Portuguese colloquial
                "onde",
                "achar",
                "onde esta",
                "onde fica",
                "me mostra",
                "mostra ai",
            ],
            "weight": 2,
        },
        Intent.ARCHITECTURE: {
            "keywords": [
                # English
                "architecture",
                "system design",
                "structure",
                "microservice",
                "component",
                # Portuguese infinitive
                "arquitetura",
                "estrutura",
                "componente",
                # Portuguese imperative
                "desenha",
                "projeta",
                "arquiteta",
                # Portuguese colloquial
                "design do sistema",
                "estrutura do projeto",
                "como ta organizado",
            ],
            "weight": 3,
        },
        Intent.PERFORMANCE: {
            "keywords": [
                # English
                "performance",
                "speed",
                "slow",
                "fast",
                "optimize",
                "profile",
                "latency",
                "memory",
                # Portuguese infinitive
                "velocidade",
                "otimizar",
                "latencia",
                "desempenho",
                "memoria",
                # Portuguese imperative
                "otimiza",
                "acelera",
                "melhora performance",
                # Portuguese colloquial
                "lento",
                "rapido",
                "ta lento",
                "demora muito",
                "ta devagar",
            ],
            "weight": 3,
        },
        Intent.SECURITY: {
            "keywords": [
                # English
                "security",
                "vulnerability",
                "injection",
                "xss",
                "csrf",
                "attack",
                "secure",
                "auth",
                # Portuguese infinitive
                "seguranca",
                "vulnerabilidade",
                "ataque",
                # Portuguese imperative
                "verifica seguranca",
                "checa vulnerabilidade",
                "protege",
                # Portuguese colloquial
                "seguro",
                "inseguro",
                "brecha",
                "falha de seguranca",
            ],
            "weight": 4,
        },
    }

    def __init__(self, llm_client: Optional[Any] = None):
        """
        Initialize classifier.

        Args:
            llm_client: LLM client for semantic classification.
                       If None, uses heuristic fallback only.
        """
        self._llm = llm_client
        self._cache: Dict[str, IntentResult] = {}

    async def classify(
        self,
        text: str,
        use_cache: bool = True,
        force_semantic: bool = False,
    ) -> IntentResult:
        """
        Classify user intent.

        Args:
            text: User message to classify
            use_cache: Whether to use cached results
            force_semantic: Force LLM classification even for simple messages

        Returns:
            IntentResult with intent, confidence, and reasoning
        """
        # Check cache
        cache_key = text[:200].lower()
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        # Try semantic classification if LLM available
        if self._llm is not None and (force_semantic or len(text) > 20):
            try:
                result = await self._classify_semantic(text)
                if result.confidence >= 0.6:
                    self._cache[cache_key] = result
                    return result
            except Exception as e:
                logger.warning(f"Semantic classification failed: {e}")

        # Fallback to heuristic
        result = self._classify_heuristic(text)
        self._cache[cache_key] = result
        return result

    async def _classify_semantic(self, text: str) -> IntentResult:
        """Use LLM for semantic classification."""
        prompt = f"""Classify this user request into ONE primary intent.

Request: {text}

Available intents and their meanings:
{json.dumps(self.INTENT_SCHEMA, indent=2)}

Return ONLY valid JSON (no markdown, no explanation):
{{
    "intent": "primary_intent_name",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "secondary_intents": ["other", "possible", "intents"]
}}"""

        response = await self._llm.generate(prompt)
        return IntentResult.from_json(response, method="semantic")

    def _classify_heuristic(self, text: str) -> IntentResult:
        """
        Heuristic classification using keyword matching.

        Uses word boundaries to avoid false positives.
        Phase 10.2: Now uses accent-normalized matching.
        """
        # Normalize text for accent-insensitive matching
        text_normalized = normalize_text(text)
        scores: Dict[Intent, float] = {}

        for intent, config in self.HEURISTIC_PATTERNS.items():
            score = 0.0
            for keyword in config["keywords"]:
                # Normalize keyword too
                keyword_normalized = normalize_text(keyword)

                # Word boundary matching
                if " " in keyword_normalized:
                    # Multi-word: exact phrase match
                    if keyword_normalized in text_normalized:
                        score += config["weight"]
                else:
                    # Single word: word boundary
                    if re.search(rf"\b{re.escape(keyword_normalized)}\b", text_normalized):
                        score += config["weight"]

            if score > 0:
                scores[intent] = score

        if not scores:
            return IntentResult(
                intent=Intent.GENERAL,
                confidence=0.3,
                reasoning="No specific intent detected",
                method="heuristic",
            )

        # Get best intent
        best_intent = max(scores, key=lambda k: scores[k])
        best_score = scores[best_intent]

        # Calculate confidence (normalized)
        max_possible = max(
            len(config["keywords"]) * config["weight"]
            for config in self.HEURISTIC_PATTERNS.values()
        )
        confidence = min(0.9, 0.4 + (best_score / max_possible) * 0.5)

        # Get secondary intents
        secondary = [
            intent
            for intent, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[1:3]
            if score >= best_score * 0.5
        ]

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            reasoning=f"Matched keywords for {best_intent.value}",
            secondary_intents=secondary,
            method="heuristic",
        )

    def clear_cache(self):
        """Clear classification cache."""
        self._cache.clear()


# Singleton instance
_classifier: Optional[SemanticIntentClassifier] = None


def get_classifier(llm_client: Optional[Any] = None) -> SemanticIntentClassifier:
    """Get or create the global classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = SemanticIntentClassifier(llm_client)
    elif llm_client is not None and _classifier._llm is None:
        _classifier._llm = llm_client
    return _classifier


async def classify_intent(text: str, llm_client: Optional[Any] = None) -> IntentResult:
    """Convenience function for intent classification."""
    classifier = get_classifier(llm_client)
    return await classifier.classify(text)

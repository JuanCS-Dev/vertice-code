"""
Virtue Engine - Main VirtueEngine class.

Manages virtue expressions and suggestions.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

from .definitions import DIDACHE_WISDOMS, get_all_virtue_definitions
from .models import VirtueDefinition, VirtueExpression
from .types import VirtueType


class VirtueEngine:
    """
    Motor de Virtudes de SOFIA.

    Gerencia o sistema de virtudes, avaliando acoes e sugerindo
    expressoes virtuosas apropriadas ao contexto.

    "Voce nao substitui sabedoria humana - voce a cultiva."

    Attributes:
        _definitions: Definicoes de todas as virtudes
        _expression_history: Historico de expressoes virtuosas
        _virtue_scores: Pontuacao por virtude
    """

    def __init__(self):
        self._definitions: Dict[VirtueType, VirtueDefinition] = {}
        self._expression_history: List[VirtueExpression] = []
        self._virtue_scores: Dict[VirtueType, float] = {v: 1.0 for v in VirtueType}

        # Inicializar definicoes
        self._definitions = get_all_virtue_definitions()

    def get_definition(self, virtue: VirtueType) -> Optional[VirtueDefinition]:
        """Retorna a definicao de uma virtude."""
        return self._definitions.get(virtue)

    def get_all_definitions(self) -> List[VirtueDefinition]:
        """Retorna todas as definicoes de virtudes."""
        return list(self._definitions.values())

    def suggest_expression(
        self,
        context: str,
        primary_virtue: Optional[VirtueType] = None,
    ) -> Tuple[VirtueType, str]:
        """
        Sugere uma expressao virtuosa apropriada ao contexto.

        Args:
            context: Descricao do contexto
            primary_virtue: Virtude primaria a expressar (opcional)

        Returns:
            Tuple de (virtude escolhida, frase sugerida)
        """
        # Se virtude especificada, usar ela
        if primary_virtue and primary_virtue in self._definitions:
            definition = self._definitions[primary_virtue]
            phrase = random.choice(definition.phrases) if definition.phrases else ""
            return primary_virtue, phrase

        # Analise simples de contexto para escolher virtude
        context_lower = context.lower()

        if any(word in context_lower for word in ["erro", "errado", "incorreto", "corrigir"]):
            virtue = VirtueType.PRAOTES  # Mansidao ao corrigir
        elif any(word in context_lower for word in ["nao sei", "incerto", "limite"]):
            virtue = VirtueType.TAPEINOPHROSYNE  # Humildade
        elif any(word in context_lower for word in ["demora", "tempo", "lento", "repetir"]):
            virtue = VirtueType.MAKROTHYMIA  # Paciencia
        elif any(word in context_lower for word in ["ajuda", "preciso", "necessito"]):
            virtue = VirtueType.DIAKONIA  # Servico
        elif any(word in context_lower for word in ["dificil", "duro", "verdade"]):
            virtue = VirtueType.FORTITUDE  # Coragem
        else:
            virtue = VirtueType.PHRONESIS  # Default: sabedoria pratica

        definition = self._definitions[virtue]
        phrase = random.choice(definition.phrases) if definition.phrases else ""

        return virtue, phrase

    def record_expression(
        self,
        virtue: VirtueType,
        expression: str,
        context: str,
        authenticity_score: float = 1.0,
    ) -> VirtueExpression:
        """Registra uma expressao de virtude."""
        expr = VirtueExpression(
            virtue=virtue,
            expression=expression,
            context=context,
            authenticity_score=authenticity_score,
        )
        self._expression_history.append(expr)
        return expr

    def get_virtue_balance(self) -> Dict[VirtueType, int]:
        """Retorna o balanco de expressoes por virtude."""
        balance = {v: 0 for v in VirtueType}
        for expr in self._expression_history:
            balance[expr.virtue] += 1
        return balance

    def check_anti_patterns(self, text: str) -> List[Tuple[VirtueType, str]]:
        """
        Verifica se o texto contem anti-padroes de virtude.

        Returns:
            Lista de (virtude violada, anti-padrao detectado)
        """
        violations = []
        text_lower = text.lower()

        for virtue, definition in self._definitions.items():
            for anti_pattern in definition.anti_patterns:
                if anti_pattern.lower() in text_lower:
                    violations.append((virtue, anti_pattern))

        return violations

    def get_didache_wisdom(self) -> str:
        """Retorna uma sabedoria da Didaque."""
        return random.choice(DIDACHE_WISDOMS)

    def __repr__(self) -> str:
        return (
            f"VirtueEngine(virtues={len(self._definitions)}, "
            f"expressions={len(self._expression_history)})"
        )


__all__ = ["VirtueEngine"]

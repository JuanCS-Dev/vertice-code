"""
Tipos e Enums para o Sistema de Deliberação.

Framework Dual-Process (Kahneman):
- Sistema 1: Rápido, intuitivo, automático
- Sistema 2: Lento, deliberado, analítico
"""

from enum import Enum, auto


class ThinkingMode(Enum):
    """Modos de pensamento (Framework Dual-Process)."""

    SYSTEM_1 = auto()  # Rápido, intuitivo
    SYSTEM_2 = auto()  # Lento, deliberado


class DeliberationTrigger(Enum):
    """Gatilhos que ativam Sistema 2."""

    # Complexidade Ética
    ETHICAL_DILEMMA = auto()          # Dilema ético complexo
    VALUES_CONFLICT = auto()          # Valores em conflito
    MORAL_UNCERTAINTY = auto()        # Incerteza moral significativa

    # Risco e Consequência
    HIGH_STAKES = auto()              # Decisão de alto risco
    IRREVERSIBLE = auto()             # Consequências irreversíveis
    AFFECTS_OTHERS = auto()           # Impacta múltiplas pessoas

    # Novidade e Complexidade
    NOVEL_PROBLEM = auto()            # Problema novo sem precedentes
    MULTI_DIMENSIONAL = auto()        # Múltiplas dimensões a considerar
    AMBIGUITY = auto()                # Alta ambiguidade

    # Sinais do Usuário
    USER_UNCERTAINTY = auto()         # Usuário expressa incerteza
    EXPLICIT_REQUEST = auto()         # Pedido explícito de análise profunda
    EMOTIONAL_WEIGHT = auto()         # Carga emocional significativa

    # Contexto
    LONG_TERM_IMPACT = auto()         # Impacto de longo prazo
    STRATEGIC_DECISION = auto()       # Decisão estratégica


class DeliberationPhase(Enum):
    """Fases do processo de deliberação Sistema 2."""

    DECOMPOSITION = auto()        # Decompor em sub-questões
    PERSPECTIVE_TAKING = auto()   # Múltiplas perspectivas
    CONSEQUENCE_ANALYSIS = auto() # Análise de consequências
    VALUES_EXAMINATION = auto()   # Examinar valores e trade-offs
    PRECEDENT_SEARCH = auto()     # Buscar precedentes e sabedoria
    SYNTHESIS = auto()            # Sintetizar recomendação
    META_REFLECTION = auto()      # Reflexão sobre o processo

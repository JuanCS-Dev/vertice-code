"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                      DELIBERAÇÃO SISTEMA 2 DE SOFIA                          ║
║                                                                              ║
║                  Pensamento Deliberado para Decisões Complexas               ║
║                                                                              ║
║  "20 segundos de deliberação = escalar modelo 100.000x" (OpenAI, 2024)       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Framework Dual-Process (Kahneman):
- Sistema 1: Rápido, intuitivo, automático
- Sistema 2: Lento, deliberado, analítico

Quando Ativar Sistema 2:
1. Dilemas éticos complexos
2. Decisões de alto risco
3. Pensamento estratégico longo prazo
4. Problemas novos sem precedentes
5. Usuário expressa incerteza significativa

Processo de Deliberação:
1. Decompor em sub-questões
2. Múltiplas perspectivas éticas
3. Consequências curto/longo prazo
4. Valores em conflito, trade-offs
5. Precedentes, sabedoria estabelecida
6. Sintetizar recomendação ponderada
7. Comunicar raciocínio transparente

Baseado em: Kahneman (Pensamento Rápido e Lento), DeepMind (Talker-Reasoner),
OpenAI (o1 reasoning), e Phronesis (sabedoria prática aristotélica).

Estrutura do módulo:
- types.py: Enums (ThinkingMode, DeliberationTrigger, DeliberationPhase)
- models.py: Dataclasses (Perspective, ConsequenceAnalysis, DeliberationResult)
- constants.py: Keywords, frameworks éticos, templates
- phases.py: Implementação das 7 fases de deliberação
- engine.py: DeliberationEngine orquestrador
- formatting.py: Formatação de output e métricas
"""

from .types import (
    ThinkingMode,
    DeliberationTrigger,
    DeliberationPhase,
)

from .models import (
    Perspective,
    ConsequenceAnalysis,
    DeliberationResult,
)

from .constants import (
    TRIGGER_KEYWORDS,
    ETHICAL_FRAMEWORKS,
    DECOMPOSITION_TEMPLATES,
    CONSEQUENCE_PROMPTS,
    SYNTHESIS_TEMPLATES,
    VALUE_KEYWORDS,
    COMMON_TENSION_PAIRS,
)

from .engine import DeliberationEngine

from .formatting import (
    format_deliberation_output,
    get_thinking_mode_indicator,
    get_trigger_description,
    get_metrics,
)


__all__ = [
    # Types
    "ThinkingMode",
    "DeliberationTrigger",
    "DeliberationPhase",
    # Models
    "Perspective",
    "ConsequenceAnalysis",
    "DeliberationResult",
    # Constants
    "TRIGGER_KEYWORDS",
    "ETHICAL_FRAMEWORKS",
    "DECOMPOSITION_TEMPLATES",
    "CONSEQUENCE_PROMPTS",
    "SYNTHESIS_TEMPLATES",
    "VALUE_KEYWORDS",
    "COMMON_TENSION_PAIRS",
    # Engine
    "DeliberationEngine",
    # Formatting
    "format_deliberation_output",
    "get_thinking_mode_indicator",
    "get_trigger_description",
    "get_metrics",
]

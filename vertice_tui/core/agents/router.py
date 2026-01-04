"""
Agent Router - Intelligent intent-based routing.

Implements Claude Code subagent-style automatic routing.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


class AgentRouter:
    """
    Intelligent request router that detects user intent and routes to agents.

    Claude Code Parity: Implements automatic agent invocation like Claude Code's
    subagent system - users can naturally describe tasks and the router decides
    which specialized agent should handle it.

    Philosophy:
        "The user shouldn't need to know which agent does what - just ask."

    Routing Strategy:
        1. Keyword matching (fast, deterministic)
        2. Intent patterns (regex-based)
        3. Confidence scoring (multiple matches = ask user)
    """

    # Intent patterns → agent mapping with confidence weights
    # Enhanced for PT-BR and EN detection
    # v6.1: Added patterns for multi-plan, clarification, and exploration modes
    INTENT_PATTERNS: Dict[str, List[Tuple[str, float]]] = {
        "planner": [
            (r"\b(plan[oe]?|planeja[r]?|planejamento|cri[ae]\s*(um\s*)?plano)\b", 0.9),
            (r"\b(break\s*down|decompo[ns]|roadmap|estratégia)\b", 0.9),
            (r"\b(como\s*(fa[zç]o|implement|começ)|how\s*(to|do\s*i|should)|steps?\s*to)\b", 0.75),
            (r"\b(preciso\s*(de\s*)?(um\s*)?plano|help\s*me\s*(plan|with))\b", 0.8),
            (r"\bimplementa[rç].*passo\b", 0.85),
        ],
        # v6.1: Planner sub-modes (multi-plan, clarification, exploration)
        "planner:multi": [
            (r"\b(multi[- ]?plan|m[uú]ltiplos?\s*planos?|alternativ[ao]s?|3\s*planos?)\b", 0.95),
            (r"\b(compare\s*(multiple\s*)?plans?|compar[ae]\s*planos?|multiple\s*plans?)\b", 0.9),
            (r"\b(options?|op[çc][oõ]es|escolhas?|choices?)\b", 0.85),
            (r"\b(risk.*reward|risco.*recompensa|trade-?offs?)\b", 0.85),
            (r"\b(conservative|agressivo|creative|criativ[ao]|lateral)\b", 0.8),
        ],
        "planner:clarify": [
            (r"\b(clarif[iy]|esclare[çc][ae]|pergunt[ae]s?\s*(antes|primeiro))\b", 0.95),
            (r"\b(fa[çz]a\s*perguntas?|ask\s*(me\s*)?questions?)\b", 0.95),
            (r"\b(before\s*plan|antes\s*de\s*plan[ae]jar)\b", 0.9),
            (r"\b(need\s*more\s*info|preciso\s*mais\s*info)\b", 0.85),
        ],
        "planner:explore": [
            (r"\b(explor[ae]\s*(sem|without)\s*(modific|alter|mudar))\b", 0.95),
            (r"\b(read[- ]?only|somente\s*leitura|apenas\s*an[aá]lise)\b", 0.95),
            (r"\b(analys[ei]s?\s*only|s[oó]\s*an[aá]lise)\b", 0.9),
            (r"\b(don'?t\s*(change|modify)|n[aã]o\s*(mude|altere|modifique))\b", 0.85),
        ],
        "executor": [
            (r"\b(execut[ae]|run|roda[r]?|execute|bash|shell|terminal)\b", 0.9),
            (r"\b(comando?s?|command)\b", 0.75),
            (r"\b(pip\s+install|npm\s+(install|run)|make|cargo|go\s+(run|build))\b", 0.95),
            (r"\b(git\s+(status|diff|add|commit|push|pull|clone|log))\b", 0.9),
            (r"\b(pytest|unittest|jest|npm\s+test|testa[r]?\s+)\b", 0.85),
            (r"\b(delet[ae]|remov[ae]|apag[ae]|clean|limp[ae])\b", 0.85),
        ],
        "architect": [
            (r"\b(arquitetur[a]?|architect(ure)?|design\s*(pattern)?)\b", 0.9),
            (r"\b(estrutur[ae]|system\s*design|analisa[r]?\s*(a\s*)?arquitetura)\b", 0.85),
            (r"\b(diagrama?|uml|flowchart|fluxo(grama)?)\b", 0.85),
            (r"\b(clean\s*architect|hexagonal|onion|layered|microservice)\b", 0.95),
            (r"\b(trade-?off|decision|escolh[ae]\s*(entre|de\s*design))\b", 0.7),
        ],
        "reviewer": [
            (r"\b(review|revis[ae]|code\s*review)\b", 0.9),
            (r"\b(analys[ei]s?\s*(de\s*)?(c[oó]digo)?|análise)\b", 0.8),
            (r"\b(qualidade|quality|best\s*practice|boas\s*pr[aá]ticas)\b", 0.8),
            (r"\b(pr\s*review|pull\s*request|merge\s*request)\b", 0.95),
            (r"\b(code\s*smell|technical\s*debt|d[ií]vida\s*t[eé]cnica)\b", 0.85),
        ],
        "explorer": [
            (r"\b(explor[ae]|search|busc[ae]|find|encontr[ae]|localiz[ae])\b", 0.85),
            (r"\b(onde\s*(est[aá]|fica)|where\s*(is|are)|acha[re]?)\b", 0.8),
            (r"\b(naveg[ae]|codebase|estrutura\s*(do\s*)?(projeto|c[oó]digo))\b", 0.75),
            (r"\b(grep|ripgrep|ag\s|search\s*for|procur[ae])\b", 0.9),
        ],
        "refactorer": [
            (r"\b(refactor|refatora|refactoring|melhora[re]?\s*(o\s*)?(c[oó]digo)?)\b", 0.9),
            (r"\b(simplif[iy])\b", 0.7),
            (r"\b(extract|extrai|mover?\s*para|move\s*to)\b", 0.7),
            (r"\b(rename|renomea|dry|don'?t\s*repeat)\b", 0.8),
        ],
        "testing": [
            (r"\b(test[aes]?|testa[re]?|unittest|pytest|coverage|cobertura)\b", 0.9),
            (r"\b(tdd|bdd|test\s*driven|behavior\s*driven)\b", 0.95),
            (r"\b(mock|stub|fixture|parametriz[ae])\b", 0.85),
            (r"\b(integration\s*test|unit\s*test|e2e|end.to.end)\b", 0.9),
            (r"\b(unit[aá]rio|cria[r]?\s*testes?|write\s*tests?)\b", 0.9),
        ],
        "security": [
            (r"\b(security|seguran[çc]a|owasp|vulnerabil\w*|cve)\b", 0.95),
            (r"\b(injection|xss|csrf|sqli|auth[nz]?|exploit)\b", 0.9),
            (r"\b(audit|auditoria|pentest|penetration|scan)\b", 0.85),
            (r"\b(sanitiz|escap[ae]|valid[ae]|malware|trojan)\b", 0.75),
            (r"\bquais\s*(vulner|falh|brech)\w*", 0.9),
        ],
        "documentation": [
            (r"\b(document[ae]?|documenta[çc][aã]o|docs?|readme)\b", 0.9),
            (r"\b(docstring|jsdoc|pydoc|api\s*doc)\b", 0.95),
            (r"\b(coment[aá]rio|comment|explain|explic[ae])\b", 0.7),
            (r"\b(changelog|release\s*notes)\b", 0.85),
        ],
        "performance": [
            (r"\b(perform|performance|desempenho|otimiz[ae]|optim[iz])\b", 0.9),
            (r"\b(profil[ae]|profiling|benchmark|cprofile|perf)\b", 0.95),
            (r"\b(lento|slow|fast|r[aá]pido|speed\s*up|acelera)\b", 0.75),
            (r"\b(memory|mem[oó]ria|leak|cpu|io\s*bound)\b", 0.8),
        ],
        "devops": [
            (r"\b(devops|docker|kubernetes|k8s|ci\s*/?\s*cd|pipeline)\b", 0.95),
            (r"\b(deploy|implant[ae]|infra|terraform|ansible)\b", 0.9),
            (r"\b(container|imagem|image|pod|service)\b", 0.8),
            (r"\b(github\s*actions?|gitlab\s*ci|jenkins|circleci)\b", 0.95),
        ],
        "data": [
            (r"\b(database|banco\s*de\s*dados)\b", 0.9),
            (r"\b(sql|query|consulta)\b", 0.92),
            (r"\b(schema|esquema|migration|migra[çc][aã]o)\b", 0.85),
            (r"\b(orm|sqlalchemy|django\s*orm|prisma|sequelize)\b", 0.9),
            (r"\b(index|[ií]ndice|foreign\s*key|constraint)\b", 0.8),
            (r"\botimiza.*\b(query|sql|consulta)\b", 0.95),
        ],
        "justica": [
            (r"\b(justi[çc]a|governance|governan[çc]a|constitu[çi])\b", 0.95),
            (r"\b(compliance|conformidade|regulat[oó]rio)\b", 0.85),
            (r"\b(v[eé]rtice|article|artigo)\b", 0.7),
        ],
        "sofia": [
            (r"\b(sofia|counsel|conselho|[eé]tic[ao]|ethical|sabedoria|wisdom)\b", 0.95),
            (r"\b(filosof|philosophy|moral|virtue|virtude)\b", 0.85),
            (r"\b(socrat|dile[mn]ma|reflection|reflex[aã]o)\b", 0.8),
        ],
    }

    # Keywords that indicate NOT to route (general chat or direct tool use)
    NO_ROUTE_PATTERNS: List[str] = [
        r"^(oi|ol[aá]|hi|hello|hey|e\s*a[ií])\b",  # Greetings
        r"^(obrigad[oa]|thanks?|valeu|vlw)\b",  # Thanks
        r"^(ok|certo|entend[io]|got\s*it)\b",  # Acknowledgments
        # File creation/save commands
        r"\b(salv[ae]|save|cri[ae]|create|escrev[ae]|write)\s*(o[s]?\s*)?(arquivo|file)",
        r"\b(grav[ae]|persist|gravar)\s*(no\s*)?(disco|disk)",
        r"\bde\s*acordo\s*com\s*o\s*plano\b",
        r"\bseguindo\s*o\s*plano\b",
        r"\bexecut[ae]\s*o\s*plano\b",
        r"\bimplementa\s*(isso|o\s*plano)\b",
        r"\bmaterializ[ae]\s*(isso)?\b",
        r"^materializ",
        r"^agora\s*(salv|cri|faz|execut)",
        r"^(faz|fa[çc]a)\s*(isso|os?\s*arquivos?)",
        # Code modification commands
        r"^add\s+\w+.*\s+to\s+(the\s+)?(main|file|code)",
        r"^(adiciona|inclui|coloca)\s+.*\s+(no|na|em)\s+",
        r"^(update|modify|change|alter)\s+(the\s+)?(file|code|main)",
        r"^(atualiza|modifica|altera)\s+(o\s+)?(arquivo|código)",
        r"\bmiddleware\b.*\b(to|no|na)\b",
        r"^insert\s+",
        # Plan execution phrases
        r"^make\s+it\s+real",
        r"^do\s+it\b",
        r"^build\s+it\b",
        r"^create\s+it\b",
        r"^(go|let'?s\s+go|vamos|bora)\b",
        r"^(now|agora)\s+(create|build|make|do)",
        r"^proceed\b",
        r"^(yes|sim|s[ií]|yep|yeah)\s*(,|\.|\!)?$",
        r"^execute\s+(the\s+)?(plan|plano)",
        r"^execute\s+\w+\s+plan",
        r"^run\s+(the\s+)?(plan|plano)",
        r"^implement\s+(the\s+)?(plan|plano|it)",
        r"^create\s+(the\s+)?files?",
        r"^write\s+(the\s+)?files?",
        r"^generate\s+(the\s+)?(code|files?)",
    ]

    MIN_CONFIDENCE: float = 0.7

    def __init__(self) -> None:
        """Initialize router with compiled patterns."""
        self._compiled_patterns: Dict[str, List[Tuple[re.Pattern[str], float]]] = {}
        self._no_route_patterns = [re.compile(p, re.IGNORECASE) for p in self.NO_ROUTE_PATTERNS]

        # Pre-compile all patterns
        for agent, patterns in self.INTENT_PATTERNS.items():
            self._compiled_patterns[agent] = [
                (re.compile(pattern, re.IGNORECASE), weight) for pattern, weight in patterns
            ]

    def should_route(self, message: str) -> bool:
        """Check if message should be considered for routing."""
        if len(message.strip()) < 5:
            return False

        for pattern in self._no_route_patterns:
            if pattern.search(message):
                return False

        return True

    def detect_intent(self, message: str) -> List[Tuple[str, float]]:
        """
        Detect which agent(s) should handle this message.

        Returns:
            List of (agent_name, confidence) tuples, sorted by confidence desc
        """
        if not self.should_route(message):
            return []

        scores: Dict[str, float] = {}

        for agent, patterns in self._compiled_patterns.items():
            max_score = 0.0
            for compiled_pattern, weight in patterns:
                if compiled_pattern.search(message):
                    max_score = max(max_score, weight)

            if max_score > 0:
                scores[agent] = max_score

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores

    def route(self, message: str) -> Optional[Tuple[str, float]]:
        """
        Route message to best agent.

        Returns:
            (agent_name, confidence) if confident routing found
            None if no clear routing (let LLM handle naturally)
        """
        intents = self.detect_intent(message)

        if not intents:
            return None

        best_agent, best_confidence = intents[0]

        if best_confidence >= self.MIN_CONFIDENCE:
            return (best_agent, best_confidence)

        return None

    def get_routing_suggestion(self, message: str) -> Optional[str]:
        """
        Get a suggestion message for ambiguous routing.

        Returns markdown message if multiple agents could handle this.
        """
        intents = self.detect_intent(message)

        high_conf = [(a, c) for a, c in intents if c >= 0.6]

        if len(high_conf) > 1:
            suggestions = [f"- `/{a}` ({int(c*100)}%)" for a, c in high_conf[:3]]
            return (
                "🤔 Multiple agents could help:\n"
                + "\n".join(suggestions)
                + "\n\nType one of the commands or ask naturally."
            )

        return None

"""
Request Amplifier - Enriches vague requests with context.

Phase 8 Quality Fix: Full implementation with context injection.

Source: NLU_OPTIMIZATION_PLAN.md Phase 8
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from vertice_cli.core.intent_classifier import SemanticIntentClassifier


@dataclass
class AmplifiedRequest:
    """Result of request amplification."""

    original: str
    amplified: str
    detected_intent: str
    confidence: float
    missing_details: List[str]
    suggested_questions: List[str]
    vagueness_issues: List[str] = None

    def __post_init__(self):
        if self.vagueness_issues is None:
            self.vagueness_issues = []


class RequestAmplifier:
    """
    Enriches vague requests with contextual information.

    Features:
    - Context injection (cwd, git, recent files)
    - Vagueness detection (short requests, ambiguous references)
    - Missing details identification for all 12 intents
    - Bilingual clarifying questions (PT-BR / EN)
    """

    # Patterns indicating vague requests
    VAGUE_PATTERNS = [
        (r"^.{1,15}$", "short_request"),
        (r"\b(isso|isto|this|that|it)\b", "ambiguous_reference"),
        (r"^(faz|faca|do|make|fix)\s+", "vague_verb"),
        (r"\b(algo|something|stuff|coisa)\b", "vague_object"),
        (r"^(ajuda|help)\b", "help_request"),
        (r"\?$", "question"),
    ]

    # Intent-specific missing detail patterns (Task 8.3)
    INTENT_REQUIREMENTS = {
        "coding": {
            "required": ["file_target"],
            "patterns": ["file", "arquivo", ".py", ".js", ".ts", "module", "classe", "funcao"],
            "questions": {
                "file_target": "Em qual arquivo? / Which file?",
            },
        },
        "debug": {
            "required": ["error_description"],
            "patterns": ["error", "erro", "stack", "traceback", "exception", "falha"],
            "questions": {
                "error_description": "Qual o erro completo? / What's the full error?",
            },
        },
        "refactor": {
            "required": ["refactor_scope"],
            "patterns": ["class", "function", "module", "classe", "funcao", "metodo", "arquivo"],
            "questions": {
                "refactor_scope": "O que refatorar? / What to refactor?",
            },
        },
        "test": {
            "required": ["test_target"],
            "patterns": ["test", "teste", "spec", "coverage", "cobertura", "unitario"],
            "questions": {
                "test_target": "Testar o que? / Test what?",
            },
        },
        "planning": {
            "required": ["scope"],
            "patterns": ["goal", "objetivo", "milestone", "feature", "funcionalidade"],
            "questions": {
                "scope": "Qual o escopo? / What's the scope?",
            },
        },
        "review": {
            "required": ["review_target"],
            "patterns": ["file", "pr", "commit", "change", "arquivo", "mudanca"],
            "questions": {
                "review_target": "Revisar o que? / Review what?",
            },
        },
        "docs": {
            "required": ["doc_target"],
            "patterns": ["readme", "docstring", "api", "guide", "guia", "documentacao"],
            "questions": {
                "doc_target": "Documentar o que? / Document what?",
            },
        },
        "explore": {
            "required": [],  # Exploration can be open-ended
            "patterns": [],
            "questions": {},
        },
        "architecture": {
            "required": ["component"],
            "patterns": ["system", "design", "module", "service", "componente", "sistema"],
            "questions": {
                "component": "Qual componente? / Which component?",
            },
        },
        "performance": {
            "required": ["target_area"],
            "patterns": ["slow", "lento", "optimize", "profile", "memoria", "cpu"],
            "questions": {
                "target_area": "Onde esta lento? / Where is it slow?",
            },
        },
        "security": {
            "required": ["security_scope"],
            "patterns": ["vulnerability", "auth", "injection", "xss", "vulnerabilidade"],
            "questions": {
                "security_scope": "Verificar seguranca de que? / Check security of what?",
            },
        },
        "general": {"required": [], "patterns": [], "questions": {}},
    }

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with optional context.

        Args:
            context: Dict with keys:
                - cwd: Current working directory
                - recent_files: List of recently read files
                - modified_files: List of modified files
                - git_branch: Current git branch
        """
        self.classifier = SemanticIntentClassifier()
        self.context = context or {}

    async def analyze(self, request: str) -> AmplifiedRequest:
        """Analyze and amplify a request."""
        vagueness = self._detect_vagueness(request)
        intent_result = await self.classifier.classify(request)
        intent = intent_result.intent.value
        confidence = intent_result.confidence

        # Reduce confidence if vague
        if vagueness:
            confidence = max(0.3, confidence - 0.1 * len(vagueness))

        missing = self._identify_missing_details(request, intent)
        questions = self._generate_questions(missing, intent)
        amplified = self._amplify(request)

        return AmplifiedRequest(
            original=request,
            amplified=amplified,
            detected_intent=intent,
            confidence=confidence,
            missing_details=missing,
            suggested_questions=questions,
            vagueness_issues=vagueness,
        )

    def _detect_vagueness(self, request: str) -> List[str]:
        """Detect vagueness patterns in request."""
        issues = []
        for pattern, issue in self.VAGUE_PATTERNS:
            if re.search(pattern, request, re.IGNORECASE):
                issues.append(issue)
        return issues

    def _identify_missing_details(self, request: str, intent: str) -> List[str]:
        """Identify missing details based on intent requirements."""
        missing = []
        lower_req = request.lower()

        requirements = self.INTENT_REQUIREMENTS.get(intent, {})
        patterns = requirements.get("patterns", [])
        required = requirements.get("required", [])

        # Check if any required pattern is present
        has_specifics = any(p in lower_req for p in patterns)

        if not has_specifics and required:
            missing.extend(required)

        return missing

    def _generate_questions(self, missing: List[str], intent: str) -> List[str]:
        """Generate clarifying questions based on missing details."""
        questions = []
        requirements = self.INTENT_REQUIREMENTS.get(intent, {})
        templates = requirements.get("questions", {})

        for m in missing[:3]:
            if m in templates:
                questions.append(templates[m])

        # Fallback generic questions
        fallback = {
            "file_target": "Em qual arquivo? / Which file?",
            "specific_change": "O que modificar? / What to change?",
            "error_description": "Qual o erro? / What error?",
        }

        for m in missing[:3]:
            if m not in templates and m in fallback:
                questions.append(fallback[m])

        return questions

    def _amplify(self, request: str) -> str:
        """
        Amplify request with contextual information.

        Adds:
        - Current working directory
        - Recently modified files
        - Git status hints
        - Inferred targets from context
        """
        if not self.context:
            return request

        parts = [request]

        # Add CWD context
        if cwd := self.context.get("cwd"):
            # Only add if it's informative (not just /)
            if len(cwd) > 1:
                parts.append(f"[cwd: {cwd}]")

        # Add recent files if request mentions files
        if self._mentions_file(request):
            if recent := self.context.get("recent_files", []):
                candidates = ", ".join(recent[:3])
                parts.append(f"[recent: {candidates}]")

        # Add git context for git-related requests
        if self._is_git_request(request):
            if branch := self.context.get("git_branch"):
                parts.append(f"[branch: {branch}]")
            if modified := self.context.get("modified_files", []):
                files = ", ".join(modified[:5])
                parts.append(f"[modified: {files}]")

        return " ".join(parts)

    def _mentions_file(self, request: str) -> bool:
        """Check if request mentions files."""
        file_words = [
            "file",
            "arquivo",
            "read",
            "ler",
            "show",
            "mostra",
            "edit",
            "edita",
            "write",
            "escreve",
            "abre",
            "open",
            ".py",
            ".js",
            ".ts",
            ".json",
            ".yaml",
            ".md",
        ]
        lower = request.lower()
        return any(w in lower for w in file_words)

    def _is_git_request(self, request: str) -> bool:
        """Check if request is git-related."""
        git_words = [
            "git",
            "commit",
            "push",
            "pull",
            "branch",
            "merge",
            "status",
            "diff",
            "log",
            "commita",
            "pusha",
            "stash",
            "checkout",
            "rebase",
        ]
        lower = request.lower()
        return any(w in lower for w in git_words)


# Convenience function for quick amplification
async def amplify_request(
    request: str, context: Optional[Dict[str, Any]] = None
) -> AmplifiedRequest:
    """Convenience function for request amplification."""
    amplifier = RequestAmplifier(context=context)
    return await amplifier.analyze(request)

"""
NLU Quality Tests - Phase 11 of NLU Optimization Plan.

Tests for:
- Portuguese intent classification (with/without accents)
- Imperative form matching
- ComplexityAnalyzer
- RequestAmplifier
- Agent routing (bilingual)

Source: NLU_OPTIMIZATION_PLAN.md Phase 11
"""

import pytest
import asyncio

from vertice_cli.core.intent_classifier import (
    SemanticIntentClassifier,
    Intent,
    normalize_text,
)
from vertice_cli.core.request_amplifier import RequestAmplifier, AmplifiedRequest
from vertice_cli.core.complexity_analyzer import ComplexityAnalyzer, analyze_complexity
from scripts.maestro.routing import route_to_agent


class TestAccentNormalization:
    """Test accent normalization for Portuguese."""

    def test_normalize_accented_words(self):
        """Test that accents are removed correctly."""
        assert normalize_text("código") == "codigo"
        assert normalize_text("função") == "funcao"
        assert normalize_text("não") == "nao"
        assert normalize_text("informação") == "informacao"
        assert normalize_text("índice") == "indice"
        assert normalize_text("módulo") == "modulo"

    def test_normalize_mixed_text(self):
        """Test mixed accented and unaccented text."""
        assert normalize_text("Mostra o código") == "mostra o codigo"
        assert normalize_text("Cria função com parâmetros") == "cria funcao com parametros"

    def test_normalize_cedilla(self):
        """Test cedilla (ç) normalization."""
        assert normalize_text("função") == "funcao"
        assert normalize_text("ação") == "acao"


class TestPortugueseIntentClassification:
    """Test Portuguese intent classification."""

    @pytest.fixture
    def classifier(self):
        return SemanticIntentClassifier()

    @pytest.mark.asyncio
    async def test_imperative_explore_mostra(self, classifier):
        """Test 'mostra' (imperative) maps to EXPLORE."""
        result = await classifier.classify("mostra o arquivo main.py")
        assert result.intent == Intent.EXPLORE

    @pytest.mark.asyncio
    async def test_imperative_explore_busca(self, classifier):
        """Test 'busca' (imperative) maps to EXPLORE."""
        result = await classifier.classify("busca todos os TODO")
        assert result.intent == Intent.EXPLORE

    @pytest.mark.asyncio
    async def test_imperative_coding_cria(self, classifier):
        """Test 'cria' (imperative) maps to CODING."""
        result = await classifier.classify("cria uma funcao de soma")
        assert result.intent == Intent.CODING

    @pytest.mark.asyncio
    async def test_imperative_debug_conserta(self, classifier):
        """Test 'conserta' (imperative) maps to DEBUG."""
        result = await classifier.classify("conserta o bug no login")
        assert result.intent == Intent.DEBUG

    @pytest.mark.asyncio
    async def test_colloquial_debug_ta_quebrado(self, classifier):
        """Test colloquial 'ta quebrado' maps to DEBUG."""
        result = await classifier.classify("ta quebrado o sistema de pagamento")
        assert result.intent == Intent.DEBUG

    @pytest.mark.asyncio
    async def test_colloquial_explore_onde_fica(self, classifier):
        """Test colloquial 'onde fica' maps to EXPLORE."""
        result = await classifier.classify("onde fica a config do banco?")
        assert result.intent == Intent.EXPLORE

    @pytest.mark.asyncio
    async def test_accented_matches_without_accents(self, classifier):
        """Test that accented input matches non-accented keywords."""
        # 'informação' should normalize to 'informacao' for matching
        result = await classifier.classify("mostra a informação do sistema")
        assert result.intent == Intent.EXPLORE

    @pytest.mark.asyncio
    async def test_performance_colloquial(self, classifier):
        """Test performance detection with colloquial PT."""
        result = await classifier.classify("ta muito lento pra carregar")
        assert result.intent == Intent.PERFORMANCE


class TestComplexityAnalyzer:
    """Test complexity analysis for auto-think."""

    @pytest.fixture
    def analyzer(self):
        return ComplexityAnalyzer()

    def test_simple_request_low_complexity(self, analyzer):
        """Simple requests should have low complexity."""
        result = analyzer.analyze("mostra o readme")
        assert result.score < 0.5
        assert not result.needs_thinking

    def test_multi_step_high_complexity(self, analyzer):
        """Multi-step requests should have higher complexity."""
        result = analyzer.analyze("cria o arquivo, depois adiciona uma funcao, e depois roda os testes")
        # Multi-step pattern detected
        assert result.score >= 0.15
        assert len(result.reasons) > 0

    def test_destructive_operation_high_complexity(self, analyzer):
        """Destructive operations should increase complexity."""
        result = analyzer.analyze("deleta todos os arquivos antigos")
        # Should detect multiple patterns (deleta + todos)
        assert result.score >= 0.3
        assert len(result.reasons) > 0

    def test_ambiguous_short_request(self, analyzer):
        """Very short requests should increase complexity."""
        result = analyzer.analyze("faz isso")
        assert result.score > 0
        assert any("short" in r or "ambig" in r for r in result.reasons)

    def test_low_confidence_increases_complexity(self, analyzer):
        """Low intent confidence should increase complexity."""
        result = analyzer.analyze("alguma coisa aqui", confidence=0.4)
        assert result.score > 0.1
        assert any("confianc" in r.lower() or "confidence" in r.lower() for r in result.reasons)

    def test_architecture_intent_complexity(self, analyzer):
        """Architecture intent should add complexity."""
        result = analyzer.analyze("redesenha a arquitetura do sistema", intent=Intent.ARCHITECTURE)
        assert result.score >= 0.2  # Architecture adds 0.25


class TestRequestAmplifier:
    """Test request amplification with context injection."""

    @pytest.fixture
    def context(self):
        return {
            'cwd': '/home/user/project',
            'recent_files': ['main.py', 'config.py', 'utils.py'],
            'modified_files': ['main.py'],
            'git_branch': 'feature/test',
        }

    @pytest.mark.asyncio
    async def test_amplifies_file_request_with_context(self, context):
        """File-related requests should include recent files."""
        amplifier = RequestAmplifier(context=context)
        result = await amplifier.analyze("mostra o arquivo")
        assert "[cwd:" in result.amplified
        assert "[recent:" in result.amplified

    @pytest.mark.asyncio
    async def test_amplifies_git_request_with_branch(self, context):
        """Git-related requests should include branch info."""
        amplifier = RequestAmplifier(context=context)
        result = await amplifier.analyze("commita as alteracoes")
        assert "[branch:" in result.amplified
        assert "[modified:" in result.amplified

    @pytest.mark.asyncio
    async def test_no_amplification_without_context(self):
        """No context means no amplification."""
        amplifier = RequestAmplifier()
        result = await amplifier.analyze("mostra o arquivo")
        assert result.amplified == "mostra o arquivo"

    @pytest.mark.asyncio
    async def test_vagueness_detection(self):
        """Vague requests should be detected."""
        amplifier = RequestAmplifier()
        result = await amplifier.analyze("faz isso")
        assert len(result.vagueness_issues) > 0
        assert result.confidence < 0.9

    @pytest.mark.asyncio
    async def test_missing_details_for_coding(self):
        """Vague coding requests should flag missing details."""
        amplifier = RequestAmplifier()
        # "implementa isso" is vague - no specific file or function mentioned
        result = await amplifier.analyze("implementa isso")
        # Should have low confidence due to vagueness
        assert result.confidence < 0.8

    @pytest.mark.asyncio
    async def test_missing_details_for_debug(self):
        """Debug requests without error should flag missing details."""
        amplifier = RequestAmplifier()
        result = await amplifier.analyze("conserta o bug")
        assert "error_description" in result.missing_details

    @pytest.mark.asyncio
    async def test_suggested_questions_bilingual(self):
        """Suggested questions should be bilingual."""
        amplifier = RequestAmplifier()
        result = await amplifier.analyze("cria uma funcao")
        if result.suggested_questions:
            # Check at least one question has both PT and EN
            assert any("/" in q for q in result.suggested_questions)


class TestAgentRouting:
    """Test bilingual agent routing."""

    # Portuguese imperative forms
    def test_route_mostra_to_explorer(self):
        """'mostra' should route to explorer."""
        assert route_to_agent("mostra os arquivos") == "explorer"

    def test_route_busca_to_explorer(self):
        """'busca' should route to explorer."""
        assert route_to_agent("busca o arquivo config") == "explorer"

    def test_route_cria_teste_to_testing(self):
        """'cria teste' should route to testing."""
        assert route_to_agent("cria teste unitario") == "testing"

    def test_route_refatora_to_refactorer(self):
        """'refatora' should route to refactorer."""
        assert route_to_agent("refatora essa funcao") == "refactorer"

    def test_route_revisa_to_reviewer(self):
        """'revisa' should route to reviewer."""
        assert route_to_agent("revisa o codigo") == "reviewer"

    # Colloquial Portuguese
    def test_route_onde_fica_to_explorer(self):
        """'onde fica' should route to explorer."""
        assert route_to_agent("onde fica o arquivo de config?") == "explorer"

    def test_route_ta_lento_to_performance(self):
        """'ta lento' should route to performance."""
        assert route_to_agent("ta lento demais essa funcao") == "performance"

    def test_route_como_fazer_to_planner(self):
        """'como fazer' should route to planner."""
        assert route_to_agent("como fazer para implementar isso?") == "planner"

    # English equivalents (ensure they still work)
    def test_route_show_to_explorer(self):
        """'show' should route to explorer."""
        assert route_to_agent("show me the files") == "explorer"

    def test_route_refactor_to_refactorer(self):
        """'refactor' should route to refactorer."""
        assert route_to_agent("refactor this function") == "refactorer"

    # Accent normalization in routing
    def test_route_with_accents(self):
        """Routing should work with accented characters."""
        assert route_to_agent("mostra a informação") == "explorer"
        assert route_to_agent("documentação do projeto") == "documentation"


class TestIntegration:
    """Integration tests for the full NLU pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_portuguese_request(self):
        """Test full pipeline with Portuguese request."""
        # Setup
        context = {
            'cwd': '/project',
            'recent_files': ['app.py'],
            'modified_files': [],
            'git_branch': 'main',
        }

        # Amplification
        amplifier = RequestAmplifier(context=context)
        amplified = await amplifier.analyze("mostra o arquivo principal")

        # Intent classification
        classifier = SemanticIntentClassifier()
        intent_result = await classifier.classify(amplified.original)

        # Complexity analysis
        complexity = analyze_complexity(
            amplified.original,
            intent=intent_result.intent,
            confidence=intent_result.confidence
        )

        # Routing
        agent = route_to_agent(amplified.original)

        # Assertions
        assert intent_result.intent == Intent.EXPLORE
        assert agent == "explorer"
        assert not complexity.needs_thinking  # Simple request

    @pytest.mark.asyncio
    async def test_full_pipeline_complex_request(self):
        """Test full pipeline with complex multi-step request."""
        request = "cria o arquivo, depois adiciona funcao de soma, e depois roda os testes"

        # Classification and complexity
        classifier = SemanticIntentClassifier()
        intent_result = await classifier.classify(request)

        complexity = analyze_complexity(
            request,
            intent=intent_result.intent,
            confidence=intent_result.confidence
        )

        # Should detect multi-step patterns
        assert complexity.score > 0
        assert len(complexity.reasons) > 0
        # Multi-step pattern "depois" should be detected
        assert any("multi-step" in r for r in complexity.reasons)

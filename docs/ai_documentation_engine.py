"""
AI-Powered Documentation Engine

Sistema de documentação viva e inteligente que se auto-atualiza
e personaliza conteúdo baseado no usuário e uso real.

Generated with ❤️ by Vertex AI Codey
"""

import json
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import hashlib

from google.cloud import bigquery, firestore
from vertexai.generative_models import GenerativeModel
from github import Github

logger = logging.getLogger(__name__)


@dataclass
class DocumentationRequest:
    """Request for documentation generation."""

    topic: str
    user_profile: Dict[str, Any]
    context: Dict[str, Any]
    format: str = "html"  # html, markdown, pdf, json
    language: str = "en"


@dataclass
class GeneratedDocumentation:
    """Generated documentation content."""

    content_id: str
    topic: str
    content: str
    format: str
    language: str
    user_profile: Dict[str, Any]
    generated_at: datetime
    source_code_hash: str
    ai_model: str


class AIDocumentationEngine:
    """
    Engine de documentação alimentado por IA.

    Gera documentação viva que se adapta aos usuários,
    se auto-atualiza com mudanças no código, e aprende
    com padrões de uso real.
    """

    def __init__(self, project_id: str, github_token: str):
        self.project_id = project_id
        self.bq_client = bigquery.Client(project=project_id)
        self.firestore_client = firestore.Client(project=project_id)
        self.ai_model = GenerativeModel("gemini-2.0-pro")

        # GitHub integration
        self.github = Github(github_token)
        self.repo = self.github.get_repo("juancs/vertice-code")

        # Cache de documentação
        self.documentation_cache: Dict[str, GeneratedDocumentation] = {}

    async def generate_documentation(self, request: DocumentationRequest) -> GeneratedDocumentation:
        """Gera documentação personalizada baseada na solicitação."""

        # Verifica cache primeiro
        cache_key = self._generate_cache_key(request)
        if cache_key in self.documentation_cache:
            cached = self.documentation_cache[cache_key]
            # Verifica se ainda é válido (código não mudou)
            if await self._is_cache_valid(cached):
                return cached

        # Coleta informações contextuais
        code_context = await self._collect_code_context(request.topic)
        usage_patterns = await self._analyze_usage_patterns(request.topic)
        user_context = await self._personalize_for_user(request.user_profile, request.topic)

        # Gera conteúdo com IA
        content = await self._generate_ai_content(
            request, code_context, usage_patterns, user_context
        )

        # Formata conteúdo
        formatted_content = await self._format_content(content, request.format)

        # Cria objeto de documentação
        documentation = GeneratedDocumentation(
            content_id=hashlib.md5(
                f"{request.topic}_{request.user_profile.get('id', 'anonymous')}_{datetime.now().isoformat()}".encode()
            ).hexdigest(),
            topic=request.topic,
            content=formatted_content,
            format=request.format,
            language=request.language,
            user_profile=request.user_profile,
            generated_at=datetime.now(),
            source_code_hash=await self._get_current_code_hash(),
            ai_model="gemini-2.0-pro",
        )

        # Armazena no cache e banco
        self.documentation_cache[cache_key] = documentation
        await self._store_documentation(documentation)

        return documentation

    async def _collect_code_context(self, topic: str) -> Dict[str, Any]:
        """Coleta contexto de código relacionado ao tópico."""

        # Busca arquivos relacionados ao tópico
        query = f"""
        SELECT file_path, content, last_modified
        FROM `vertice_docs.code_files`
        WHERE LOWER(content) LIKE LOWER('%{topic}%')
          AND last_modified > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        ORDER BY last_modified DESC
        LIMIT 10
        """

        try:
            results = self.bq_client.query(query).result()

            code_files = []
            for row in results:
                code_files.append(
                    {
                        "path": row.file_path,
                        "content": row.content[:1000],  # Limita tamanho
                        "modified": row.last_modified.isoformat(),
                    }
                )

            return {
                "related_files": code_files,
                "file_count": len(code_files),
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Erro coletando contexto de código: {e}")
            return {"related_files": [], "file_count": 0}

    async def _analyze_usage_patterns(self, topic: str) -> Dict[str, Any]:
        """Analisa padrões de uso da documentação."""

        query = f"""
        SELECT
          user_id,
          search_query,
          time_spent_seconds,
          helpfulness_rating,
          timestamp
        FROM `vertice_docs.documentation_usage`
        WHERE LOWER(search_query) LIKE LOWER('%{topic}%')
          AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        ORDER BY timestamp DESC
        LIMIT 100
        """

        try:
            results = self.bq_client.query(query).result()

            patterns = {
                "total_searches": 0,
                "avg_time_spent": 0.0,
                "avg_helpfulness": 0.0,
                "common_questions": [],
                "user_segments": {},
            }

            total_time = 0
            total_rating = 0

            for row in results:
                patterns["total_searches"] += 1
                total_time += row.time_spent_seconds or 0
                total_rating += row.helpfulness_rating or 0

            if patterns["total_searches"] > 0:
                patterns["avg_time_spent"] = total_time / patterns["total_searches"]
                patterns["avg_helpfulness"] = total_rating / patterns["total_searches"]

            return patterns

        except Exception as e:
            logger.error(f"Erro analisando padrões de uso: {e}")
            return {"total_searches": 0, "avg_time_spent": 0.0, "avg_helpfulness": 0.0}

    async def _personalize_for_user(
        self, user_profile: Dict[str, Any], topic: str
    ) -> Dict[str, Any]:
        """Personaliza conteúdo baseado no perfil do usuário."""

        prompt = f"""
        Analisa o perfil do usuário e determina como personalizar
        a documentação sobre "{topic}".

        PERFIL DO USUÁRIO:
        - Nível de experiência: {user_profile.get("experience_level", "unknown")}
        - Linguagem preferida: {user_profile.get("preferred_language", "unknown")}
        - Estilo de aprendizado: {user_profile.get("learning_style", "unknown")}
        - Contexto atual: {user_profile.get("current_context", "unknown")}
        - Objetivos: {", ".join(user_profile.get("goals", []))}

        DETERMINE:
        1. Nível de detalhe apropriado (beginner, intermediate, advanced)
        2. Exemplos mais relevantes
        3. Ordem de apresentação do conteúdo
        4. Terminologia a usar
        5. Ângulos de abordagem mais efetivos
        """

        response = await self.ai_model.generate_content(prompt)

        try:
            personalization = json.loads(response.text)
        except json.JSONDecodeError:
            personalization = {
                "detail_level": user_profile.get("experience_level", "intermediate"),
                "examples_priority": ["practical", "code", "visual"],
                "content_order": ["overview", "examples", "deep_dive"],
                "terminology": "standard",
                "approach": "hands_on",
            }

        return personalization

    async def _generate_ai_content(
        self,
        request: DocumentationRequest,
        code_context: Dict[str, Any],
        usage_patterns: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> str:
        """Gera conteúdo de documentação usando IA."""

        prompt = f"""
        Gera documentação abrangente e personalizada sobre "{request.topic}".

        CONTEXTO TÉCNICO:
        {json.dumps(code_context, indent=2)}

        PADRÕES DE USO:
        {json.dumps(usage_patterns, indent=2)}

        PERSONALIZAÇÃO PARA USUÁRIO:
        {json.dumps(user_context, indent=2)}

        REQUISITOS GERAIS:
        - Linguagem: {request.language}
        - Formato: {request.format}
        - Tópico: {request.topic}
        - Contexto adicional: {json.dumps(request.context, indent=2)}

        CRIA DOCUMENTAÇÃO QUE INCLUA:
        1. Introdução clara e envolvente
        2. Exemplos práticos executáveis
        3. Explicações passo-a-passo
        4. Boas práticas e dicas
        5. Troubleshooting comum
        6. Recursos adicionais

        A documentação deve ser:
        - Precisa e factual
        - Adaptada ao nível do usuário
        - Prática e acionável
        - Bem estruturada e fácil de navegar
        - Sempre atualizada com o código real
        """

        response = await self.ai_model.generate_content(prompt)
        return response.text

    async def _format_content(self, content: str, format_type: str) -> str:
        """Formata conteúdo no formato solicitado."""

        if format_type == "html":
            return await self._format_as_html(content)
        elif format_type == "markdown":
            return await self._format_as_markdown(content)
        elif format_type == "pdf":
            return await self._format_as_pdf(content)
        elif format_type == "json":
            return json.dumps({"content": content, "metadata": {}})
        else:
            return content

    async def _format_as_html(self, content: str) -> str:
        """Formata conteúdo como HTML."""

        prompt = f"""
        Converte o seguinte conteúdo de documentação para HTML bem formatado:

        {content}

        Gera HTML com:
        - Estrutura semântica (h1, h2, p, ul, ol, etc.)
        - Classes CSS apropriadas
        - Syntax highlighting para código
        - Navegação interna
        - Responsive design
        """

        response = await self.ai_model.generate_content(prompt)
        return response.text

    async def _format_as_markdown(self, content: str) -> str:
        """Formata conteúdo como Markdown."""

        prompt = f"""
        Converte o seguinte conteúdo para Markdown bem formatado:

        {content}

        Usa:
        - Headers apropriados (# ## ###)
        - Code blocks com syntax highlighting
        - Links e referências
        - Tabelas quando apropriado
        - Listas organizadas
        """

        response = await self.ai_model.generate_content(prompt)
        return response.text

    async def _format_as_pdf(self, content: str) -> str:
        """Formata conteúdo para PDF (retorna HTML que pode ser convertido)."""
        # Para PDF, retornamos HTML que pode ser convertido
        return await self._format_as_html(content)

    def _generate_cache_key(self, request: DocumentationRequest) -> str:
        """Gera chave de cache para a solicitação."""
        key_data = f"{request.topic}_{request.user_profile.get('id', 'anon')}_{request.format}_{request.language}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def _is_cache_valid(self, cached_doc: GeneratedDocumentation) -> bool:
        """Verifica se documentação em cache ainda é válida."""

        # Verifica se código fonte mudou
        current_hash = await self._get_current_code_hash()
        return current_hash == cached_doc.source_code_hash

    async def _get_current_code_hash(self) -> str:
        """Obtém hash atual do código fonte."""

        try:
            # Pega último commit
            commits = list(self.repo.get_commits()[:1])
            if commits:
                return commits[0].sha
            return "no-commits"
        except Exception as e:
            logger.error(f"Erro obtendo hash do código: {e}")
            return "error"

    async def _store_documentation(self, documentation: GeneratedDocumentation):
        """Armazena documentação gerada."""

        # Armazena no Firestore
        doc_ref = self.firestore_client.collection("generated_documentation").document(
            documentation.content_id
        )

        doc_data = {
            "topic": documentation.topic,
            "content": documentation.content,
            "format": documentation.format,
            "language": documentation.language,
            "user_profile": documentation.user_profile,
            "generated_at": documentation.generated_at,
            "source_code_hash": documentation.source_code_hash,
            "ai_model": documentation.ai_model,
        }

        try:
            await doc_ref.set(doc_data)
        except Exception as e:
            logger.error(f"Erro armazenando documentação: {e}")

    async def update_documentation_on_code_change(self, changed_files: List[str]):
        """Atualiza documentação quando código muda."""

        # Identifica tópicos afetados pelas mudanças
        affected_topics = await self._identify_affected_topics(changed_files)

        # Invalida cache para tópicos afetados
        for topic in affected_topics:
            # Remove entradas de cache relacionadas
            keys_to_remove = [k for k in self.documentation_cache.keys() if topic in k]
            for key in keys_to_remove:
                del self.documentation_cache[key]

        # Log da atualização
        logger.info(f"Documentação invalidada para tópicos: {affected_topics}")

    async def _identify_affected_topics(self, changed_files: List[str]) -> List[str]:
        """Identifica tópicos de documentação afetados pelas mudanças."""

        # Mapeia arquivos para tópicos
        file_topic_mapping = {
            "sdk/python/": "python-sdk",
            "sdk/typescript/": "typescript-sdk",
            "prometheus/": "prometheus-core",
            "mcp_server/": "mcp-server",
            "distributed/": "distributed-systems",
        }

        affected_topics = set()

        for file_path in changed_files:
            for file_prefix, topic in file_topic_mapping.items():
                if file_prefix in file_path:
                    affected_topics.add(topic)

        return list(affected_topics)

    async def get_documentation_analytics(self) -> Dict[str, Any]:
        """Obtém analytics da documentação gerada."""

        query = """
        SELECT
          COUNT(*) as total_docs,
          AVG(LENGTH(content)) as avg_content_length,
          COUNT(DISTINCT topic) as unique_topics,
          COUNT(DISTINCT user_profile.id) as unique_users
        FROM `vertice_docs.generated_documentation`
        WHERE generated_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        """

        try:
            results = self.bq_client.query(query).result()

            analytics = {}
            for row in results:
                analytics = {
                    "total_documents_generated": row.total_docs,
                    "avg_content_length": row.avg_content_length,
                    "unique_topics_covered": row.unique_topics,
                    "unique_users_served": row.unique_users,
                    "generated_at": datetime.now().isoformat(),
                }

            return analytics

        except Exception as e:
            logger.error(f"Erro obtendo analytics: {e}")
            return {"error": str(e)}

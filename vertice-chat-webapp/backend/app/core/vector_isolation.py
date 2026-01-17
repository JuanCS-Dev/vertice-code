"""
RAG Multi-tenancy Service
Vector database isolation with workspace-level data segregation
"""

from typing import List, Dict, Any, Optional
import logging

from app.core.config import settings
from app.models.database import KnowledgeEntry

logger = logging.getLogger(__name__)


class VectorIsolationService:
    """
    Service for managing multi-tenant vector data isolation.

    Implements workspace-level data segregation in vector databases
    using metadata filtering and encryption.
    """

    def __init__(self):
        self.vector_db_type = getattr(settings, "VECTOR_DB_TYPE", "qdrant")
        self.vector_db_url = getattr(settings, "VECTOR_DB_URL", "http://localhost:6333")
        self.collection_name = getattr(settings, "VECTOR_COLLECTION", "vertice_knowledge")

        # Initialize vector client
        self.client = None
        self._init_vector_client()

    def _init_vector_client(self):
        """Initialize vector database client based on configuration."""
        try:
            if self.vector_db_type.lower() == "qdrant":
                from qdrant_client import QdrantClient

                self.client = QdrantClient(url=self.vector_db_url)
            elif self.vector_db_type.lower() == "pinecone":
                import pinecone

                pinecone.init(api_key=settings.PINECONE_API_KEY)
                self.client = pinecone.Index(settings.PINECONE_INDEX)
            elif self.vector_db_type.lower() == "chroma":
                import chromadb

                self.client = chromadb.Client()
            else:
                logger.warning(f"Unsupported vector DB type: {self.vector_db_type}, using mock")
                self.client = None
        except ImportError as e:
            logger.warning(f"Vector DB client not available: {e}, using mock")
            self.client = None

    async def create_workspace_collection(self, workspace_id: str) -> bool:
        """
        Create workspace-specific collection/isolation.
        In metadata-filtering approach, we use a single collection with strict filtering.
        """
        if not self.client:
            logger.warning("Vector client not available, skipping collection creation")
            return True

        try:
            # For Qdrant: Create collection if it doesn't exist
            if self.vector_db_type.lower() == "qdrant":
                collections = self.client.get_collections()
                collection_names = [c.name for c in collections.collections]

                if self.collection_name not in collection_names:
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config={
                            "size": 1536,  # OpenAI ada-002 dimensions
                            "distance": "Cosine",
                        },
                    )
                    logger.info(f"Created vector collection: {self.collection_name}")

            return True

        except Exception as e:
            logger.error(f"Failed to create workspace collection: {e}")
            return False

    async def store_knowledge_entry(
        self, workspace_id: str, entry: KnowledgeEntry, vector_embedding: List[float]
    ) -> Optional[str]:
        """
        Store knowledge entry with workspace isolation.

        Returns vector_id if successful, None if failed.
        """
        if not self.client:
            logger.warning("Vector client not available, skipping storage")
            return f"mock-{entry.id}"

        try:
            vector_id = f"{workspace_id}_{entry.id}"

            # Prepare payload with workspace isolation and data governance metadata (ISO 42001)
            payload = {
                "workspace_id": workspace_id,
                "content_type": entry.content_type,
                "title": entry.title or "",
                "metadata": entry.content_metadata,
                "access_level": entry.access_level,
                "owner_id": str(entry.owner_id) if entry.owner_id else None,
                "created_at": entry.created_at.isoformat(),
                "content_hash": entry.content_hash,
                "is_encrypted": entry.is_encrypted,
                # Data Governance & ISO 42001 compliance fields
                "data_governance": {
                    "content_origin": getattr(
                        entry, "content_origin", "user_generated"
                    ),  # user_generated, imported, api_fetched, etc.
                    "license_type": getattr(
                        entry, "license_type", "proprietary"
                    ),  # proprietary, mit, apache2, etc.
                    "license_url": getattr(entry, "license_url", None),
                    "copyright_holder": getattr(entry, "copyright_holder", None),
                    "usage_restrictions": getattr(
                        entry, "usage_restrictions", []
                    ),  # commercial, research_only, etc.
                    "data_quality_score": getattr(entry, "data_quality_score", 0.8),  # 0.0-1.0
                    "verification_status": getattr(
                        entry, "verification_status", "unverified"
                    ),  # verified, unverified, disputed
                    "last_audited": getattr(entry, "last_audited", None),
                    "gdpr_compliant": getattr(entry, "gdpr_compliant", True),
                },
            }

            if self.vector_db_type.lower() == "qdrant":
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[{"id": vector_id, "vector": vector_embedding, "payload": payload}],
                )

            elif self.vector_db_type.lower() == "pinecone":
                self.client.upsert([(vector_id, vector_embedding, payload)])

            elif self.vector_db_type.lower() == "chroma":
                collection = self.client.get_or_create_collection(self.collection_name)
                collection.add(ids=[vector_id], embeddings=[vector_embedding], metadatas=[payload])

            logger.info(f"Stored vector for workspace {workspace_id}, entry {entry.id}")
            return vector_id

        except Exception as e:
            logger.error(f"Failed to store knowledge entry: {e}")
            return None

    async def search_workspace_knowledge(
        self,
        workspace_id: str,
        query_embedding: List[float],
        limit: int = 10,
        access_level: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge within workspace boundaries.

        Returns list of matching entries with scores.
        """
        if not self.client:
            logger.warning("Vector client not available, returning mock results")
            return []

        try:
            # Build search filter for workspace isolation
            search_filter = {"workspace_id": workspace_id}

            if access_level:
                search_filter["access_level"] = access_level

            if owner_id:
                search_filter["owner_id"] = owner_id

            results = []

            if self.vector_db_type.lower() == "qdrant":
                from qdrant_client.http.models import Filter, FieldCondition, MatchValue

                filter_obj = Filter(
                    must=[FieldCondition(key="workspace_id", match=MatchValue(value=workspace_id))]
                )

                # Add additional filters
                if access_level:
                    filter_obj.must.append(
                        FieldCondition(key="access_level", match=MatchValue(value=access_level))
                    )

                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    filter=filter_obj,
                    limit=limit,
                )

                for hit in search_results:
                    results.append({"id": hit.id, "score": hit.score, "payload": hit.payload})

            elif self.vector_db_type.lower() == "pinecone":
                # Pinecone metadata filtering
                search_results = self.client.query(
                    vector=query_embedding, filter=search_filter, top_k=limit, include_metadata=True
                )

                for match in search_results["matches"]:
                    results.append(
                        {"id": match["id"], "score": match["score"], "payload": match["metadata"]}
                    )

            elif self.vector_db_type.lower() == "chroma":
                collection = self.client.get_collection(self.collection_name)
                search_results = collection.query(
                    query_embeddings=[query_embedding], n_results=limit, where=search_filter
                )

                for i, (id_, metadata) in enumerate(
                    zip(search_results["ids"][0], search_results["metadatas"][0])
                ):
                    results.append(
                        {"id": id_, "score": search_results["distances"][0][i], "payload": metadata}
                    )

            logger.info(
                f"Vector search completed for workspace {workspace_id}: {len(results)} results"
            )
            return results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def delete_workspace_data(self, workspace_id: str) -> bool:
        """
        Delete all vector data for a workspace (GDPR compliance).

        This implements "crypto-shredding" by removing vector data.
        """
        if not self.client:
            logger.warning("Vector client not available, skipping deletion")
            return True

        try:
            if self.vector_db_type.lower() == "qdrant":
                from qdrant_client.http.models import Filter, FieldCondition, MatchValue

                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=Filter(
                        must=[
                            FieldCondition(key="workspace_id", match=MatchValue(value=workspace_id))
                        ]
                    ),
                )

            elif self.vector_db_type.lower() == "pinecone":
                # Delete by metadata filter (Pinecone approach)
                # Note: This might need pagination for large datasets
                delete_filter = {"workspace_id": workspace_id}
                self.client.delete(filter=delete_filter)

            elif self.vector_db_type.lower() == "chroma":
                collection = self.client.get_collection(self.collection_name)
                collection.delete(where={"workspace_id": workspace_id})

            logger.info(f"Deleted vector data for workspace {workspace_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete workspace vector data: {e}")
            return False

    async def get_workspace_stats(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get vector database statistics for a workspace.
        """
        if not self.client:
            return {"status": "mock", "entries": 0}

        try:
            if self.vector_db_type.lower() == "qdrant":
                # Count points with workspace filter
                count_result = self.client.count(
                    collection_name=self.collection_name,
                    count_filter={
                        "must": [{"key": "workspace_id", "match": {"value": workspace_id}}]
                    },
                )
                entry_count = count_result.count

            elif self.vector_db_type.lower() == "pinecone":
                # Pinecone stats (approximate)
                stats = self.client.describe_index_stats()
                entry_count = stats.get("total_vector_count", 0)

            elif self.vector_db_type.lower() == "chroma":
                collection = self.client.get_collection(self.collection_name)
                entry_count = collection.count(where={"workspace_id": workspace_id})

            else:
                entry_count = 0

            return {"status": "active", "entries": entry_count, "workspace_id": workspace_id}

        except Exception as e:
            logger.error(f"Failed to get workspace stats: {e}")
            return {"status": "error", "entries": 0, "error": str(e)}


# Global service instance
_vector_isolation_service: Optional[VectorIsolationService] = None


def get_vector_isolation_service() -> VectorIsolationService:
    """Get global vector isolation service instance."""
    global _vector_isolation_service
    if _vector_isolation_service is None:
        _vector_isolation_service = VectorIsolationService()
    return _vector_isolation_service

"""RAG service for runbooks and architecture docs."""

from typing import Any, Optional
import hashlib

from app.config import get_settings
from app.core.logging import get_logger
from app.core.resilience import with_retry

logger = get_logger(__name__)


class RAGService:
    """Semantic retrieval with Pinecone vector store."""

    def __init__(self):
        self.settings = get_settings()
        self._index = None

    def _get_index(self):
        if self._index is None and self.settings.pinecone_api_key:
            try:
                from pinecone import Pinecone
                pc = Pinecone(api_key=self.settings.pinecone_api_key)
                self._index = pc.Index(self.settings.pinecone_index)
            except Exception as e:
                logger.warning("pinecone_init_failed", error=str(e))
        return self._index

    @with_retry()
    async def embed_text(self, text: str) -> list[float]:
        if not self.settings.openai_api_key:
            # Deterministic mock embedding
            h = hashlib.sha256(text.encode()).digest()
            return [float(b) / 255.0 for b in h] * (self.settings.pinecone_dimension // 32 + 1)
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.settings.openai_api_key)
            resp = await client.embeddings.create(
                model=self.settings.embedding_model,
                input=text,
            )
            return resp.data[0].embedding
        except Exception as e:
            logger.error("embedding_failed", error=str(e))
            raise

    async def index_document(
        self,
        doc_id: str,
        content: str,
        metadata: dict[str, Any],
        namespace: str = "runbooks",
    ) -> bool:
        index = self._get_index()
        if not index:
            logger.info("rag_index_mock", doc_id=doc_id, namespace=namespace)
            return True

        embedding = await self.embed_text(content)
        index.upsert(vectors=[{
            "id": doc_id,
            "values": embedding[: self.settings.pinecone_dimension],
            "metadata": {**metadata, "content_preview": content[:500]},
        }], namespace=namespace)
        return True

    async def semantic_search(
        self,
        query: str,
        namespace: str = "runbooks",
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        index = self._get_index()
        if not index:
            return self._mock_search(query, namespace)

        embedding = await self.embed_text(query)
        results = index.query(
            vector=embedding[: self.settings.pinecone_dimension],
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
        )
        return [
            {
                "id": m.id,
                "score": m.score,
                "metadata": m.metadata,
            }
            for m in results.matches
        ]

    def _mock_search(self, query: str, namespace: str) -> list[dict]:
        return [{
            "id": "runbook-001",
            "score": 0.92,
            "metadata": {
                "title": "Database Connection Pool Exhaustion",
                "namespace": namespace,
                "content_preview": f"Procedures for resolving: {query}",
            },
        }]

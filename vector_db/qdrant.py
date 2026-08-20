"""Qdrant vector store — one point per unique content_hash.

Per-occurrence provenance (which patient/document a chunk came from) lives in Postgres
(models/vectors.py Chunk table), not here. Qdrant only needs one vector per unique
content_hash for similarity search — storage/chunk_store.py.sync_to_qdrant calls
upsert_one only for hashes it hasn't seen in this store yet.
"""

import uuid
from typing import cast

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from settings import settings
from vector_db.base import VectorStore

CONTENT_HASH_FIELD = "content_hash"
KEYWORD_INDEX_FIELDS = ["source_type", "patient_mrn", "provider_specialty", "document_type", "tags"]


class QdrantVectorStore(VectorStore):
    def __init__(
        self,
        collection_name: str = "medical_chunks",
        url: str | None = None,
        vector_size: int = 2048,
        client: QdrantClient | None = None,
    ):
        self.collection_name = collection_name
        self.client = client or QdrantClient(url=url or settings.qdrant_url)
        self._ensure_collection(vector_size)

    def _ensure_collection(self, vector_size: int) -> None:
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=vector_size, distance=qmodels.Distance.COSINE
                ),
            )
        self._ensure_payload_indexes()

    def _ensure_payload_indexes(self) -> None:
        """Idempotent: create_payload_index on an already-indexed field is a no-op,
        so this is safe to call on every startup (existing or fresh collection)."""
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name=CONTENT_HASH_FIELD,
            field_schema=qmodels.PayloadSchemaType.KEYWORD,
        )
        for field_name in KEYWORD_INDEX_FIELDS:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name=field_name,
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )

    def find_by_hash(self, content_hash: str) -> list[float] | None:
        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key=CONTENT_HASH_FIELD, match=qmodels.MatchValue(value=content_hash)
                    )
                ]
            ),
            limit=1,
            with_vectors=True,
        )
        if not points:
            return None
        vector = points[0].vector
        if not isinstance(vector, list) or (vector and not isinstance(vector[0], float)):
            raise TypeError(
                f"Expected a flat float vector for a single unnamed vector collection, got {type(vector)}"
            )
        return cast(list[float], vector)

    def upsert_one(
        self, content_hash: str, embedding: list[float], metadata: dict, text: str
    ) -> None:
        """Write a single point. Caller (ChunkStore.sync_to_qdrant) guarantees content_hash
        is new to this store, so no reuse/dedup check happens here."""
        point = qmodels.PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={CONTENT_HASH_FIELD: content_hash, **metadata, "text": text},
        )
        self.client.upsert(collection_name=self.collection_name, points=[point])

    def search(self, query_vector: list[float], limit: int = 3):
        """Search for similar vectors."""
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
        )
        return response.points

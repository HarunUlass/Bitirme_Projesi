import chromadb
from chromadb.config import Settings as ChromaSettings
import os
from typing import Optional

# Module-level singleton client — aynı path'e birden fazla client açmayı önler
_client: Optional[chromadb.PersistentClient] = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        os.makedirs(persist_dir, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


class VectorStore:
    def __init__(self, collection_name: str = None):
        self.client = _get_client()
        if collection_name is None:
            collection_name = os.getenv("CHROMA_COLLECTION_NAME", "legal_contracts")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, doc_id: str, embedding: list[float], text: str, metadata: dict):
        self.collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
        )

    def query(self, embedding: list[float], n_results: int = 5, where: Optional[dict] = None):
        kwargs = dict(query_embeddings=[embedding], n_results=n_results, include=["documents", "metadatas", "distances"])
        if where:
            kwargs["where"] = where
        return self.collection.query(**kwargs)

    def delete(self, doc_id: str):
        try:
            self.collection.delete(ids=[doc_id])
        except Exception:
            pass

    def count(self) -> int:
        return self.collection.count()

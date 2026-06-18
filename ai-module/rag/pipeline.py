from rag.vector_store import VectorStore
from gemini.client import GeminiClient
from typing import Optional


class RAGPipeline:
    def __init__(self):
        self.store = VectorStore()
        self.client = GeminiClient.get()

    def add_document(self, doc_id: str, text: str, metadata: dict, summary: Optional[str] = None):
        """Index a document. `summary` is stored as human-readable description."""
        embedding = self.client.embed(text[:8000])
        # Store summary in metadata so search results can return it
        if summary:
            metadata = {**metadata, "summary": summary}
        # Store a compact text chunk as the document body (fallback display)
        chunk = text[:2000]
        self.store.add(doc_id=doc_id, embedding=embedding, text=chunk, metadata=metadata)

    def search(self, text: str, n_results: int = 5) -> list[dict]:
        if self.store.count() == 0:
            return []

        n = min(n_results, self.store.count())
        query_embedding = self.client.embed_query(text[:3000])
        results = self.store.query(embedding=query_embedding, n_results=n)

        similar = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            score = 1 - distance  # cosine distance -> similarity
            if score < 0.2:
                continue
            meta = results["metadatas"][0][i]
            # Prefer stored summary, fall back to raw text snippet
            raw_text = results["documents"][0][i]
            stored_summary = meta.get("summary") or (raw_text[:300] + "..." if len(raw_text) > 300 else raw_text)
            similar.append({
                "doc_id": results["ids"][0][i],
                "filename": meta.get("filename", "Bilinmiyor"),
                "score": round(score, 4),
                "summary": stored_summary,
                "raw_text": raw_text,  # kept for comparison prompt
            })

        similar.sort(key=lambda x: x["score"], reverse=True)
        return similar

    def remove_document(self, doc_id: str):
        self.store.delete(doc_id)

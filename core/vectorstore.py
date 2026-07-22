"""Embedding + ChromaDB wrapper for storing/retrieving semantic wellness logs."""
from sentence_transformers import SentenceTransformer
import chromadb

from config import settings


class VectorStore:
    def __init__(self, persist_dir: str | None = None, model_name: str | None = None):
        self._client = chromadb.PersistentClient(path=persist_dir or settings.chroma_db_dir)
        self._collection = self._client.get_or_create_collection(
            name="wellness_logs",
            metadata={"description": "Embeddings of daily wellness logs"},
        )
        self._embedder = SentenceTransformer(model_name or settings.embedding_model)

    def add_log(self, date_str: str, text: str) -> None:
        embedding = self._embedder.encode(text).tolist()
        self._collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[{"type": "daily_log", "timestamp": date_str}],
            ids=[date_str],
        )

    def get_logs(self, dates: list[str]) -> list[str]:
        stored = self._collection.get(ids=dates)
        return [doc for doc in stored.get("documents", []) if doc]

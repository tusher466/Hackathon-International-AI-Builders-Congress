"""Thin wrapper over Chroma."""
from __future__ import annotations

import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.settings import get_settings

logger = logging.getLogger(__name__)

# Try import chroma, provide fallback in-memory store if not available
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except Exception as e:
    logger.warning(f"ChromaDB not available: {e}, using in-memory fallback")
    CHROMA_AVAILABLE = False


class InMemoryFallbackStore:
    """Simple in-memory vector store fallback when Chroma not available.

    Uses dummy cosine similarity based on simple embedding averaging? We'll store texts and do keyword match.
    """

    def __init__(self):
        self.docs: List[Dict[str, Any]] = []

    def upsert(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        # upsert by id
        id_to_idx = {doc["id"]: idx for idx, doc in enumerate(self.docs)}
        for i, doc_id in enumerate(ids):
            if doc_id in id_to_idx:
                self.docs[id_to_idx[doc_id]] = {
                    "id": doc_id,
                    "text": documents[i],
                    "metadata": metadatas[i],
                    "embedding": embeddings[i],
                }
            else:
                self.docs.append({
                    "id": doc_id,
                    "text": documents[i],
                    "metadata": metadatas[i],
                    "embedding": embeddings[i],
                })

    def query(self, query_embedding: List[float], k: int, where: Optional[Dict] = None) -> Dict[str, Any]:
        # simple cosine similarity
        import numpy as np
        results = []
        for doc in self.docs:
            # filter
            if where:
                # where may contain machine_type filter, check metadata
                match = True
                for wk, wv in where.items():
                    if doc["metadata"].get(wk) != wv:
                        # also handle $in etc – simple
                        if isinstance(wv, dict) and "$in" in wv:
                            if doc["metadata"].get(wk) not in wv["$in"]:
                                match = False
                                break
                        else:
                            match = False
                            break
                if not match:
                    continue
            # cosine
            emb = doc["embedding"]
            # dot product normalized
            try:
                a = np.array(query_embedding)
                b = np.array(emb)
                denom = (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
                sim = float(np.dot(a, b) / denom)
            except Exception:
                # fallback keyword overlap
                sim = 0.0
            results.append((sim, doc))
        results.sort(key=lambda x: x[0], reverse=True)
        top = results[:k]
        return {
            "ids": [[doc["id"] for _, doc in top]],
            "documents": [[doc["text"] for _, doc in top]],
            "metadatas": [[doc["metadata"] for _, doc in top]],
            "distances": [[1.0 - sim for sim, _ in top]],
        }

    def count(self) -> int:
        return len(self.docs)

    def reset(self) -> None:
        self.docs.clear()


class VectorStore:
    """Wrapper over Chroma with fallback."""

    def __init__(self, persist_path: Optional[str] = None, collection_name: Optional[str] = None):
        settings = get_settings()
        self.persist_path = persist_path or settings.CHROMA_PERSIST_PATH
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        Path(self.persist_path).mkdir(parents=True, exist_ok=True)
        self._client = None
        self._collection = None
        self._fallback = None

        if CHROMA_AVAILABLE:
            try:
                self._client = chromadb.PersistentClient(path=self.persist_path)
                self._collection = self._client.get_or_create_collection(name=self.collection_name)
                logger.info(f"Chroma collection {self.collection_name} ready at {self.persist_path} count={self._collection.count()}")
            except Exception as e:
                logger.warning(f"Chroma init failed: {e}, using fallback")
                self._fallback = InMemoryFallbackStore()
        else:
            self._fallback = InMemoryFallbackStore()

    def upsert(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        if self._collection is not None:
            try:
                self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
                return
            except Exception as e:
                logger.warning(f"Chroma upsert failed: {e}, falling back")
                if self._fallback is None:
                    self._fallback = InMemoryFallbackStore()

        if self._fallback:
            self._fallback.upsert(ids, documents, metadatas, embeddings)

    def query(self, query_embedding: List[float], k: int = 5, where: Optional[Dict] = None) -> Dict[str, Any]:
        if self._collection is not None:
            try:
                # chroma where filter: if machine_type provided, filter
                result = self._collection.query(query_embeddings=[query_embedding], n_results=k, where=where)
                return result
            except Exception as e:
                logger.warning(f"Chroma query failed: {e}")

        if self._fallback:
            return self._fallback.query(query_embedding, k, where)

        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    def count(self) -> int:
        if self._collection is not None:
            try:
                return self._collection.count()
            except Exception:
                pass
        if self._fallback:
            return self._fallback.count()
        return 0

    def reset(self) -> None:
        if self._collection is not None:
            try:
                # delete collection and recreate
                self._client.delete_collection(self.collection_name)
                self._collection = self._client.get_or_create_collection(name=self.collection_name)
            except Exception as e:
                logger.warning(f"Chroma reset failed: {e}")
        if self._fallback:
            self._fallback.reset()
        logger.info("Vector store reset")


# Global singleton holder
_global_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _global_store
    if _global_store is None:
        _global_store = VectorStore()
    return _global_store

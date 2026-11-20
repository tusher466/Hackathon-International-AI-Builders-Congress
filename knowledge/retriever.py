"""Retriever with embedding and citation formatting."""
from __future__ import annotations

import logging
import hashlib
from typing import List, Dict, Any, Optional

from config.settings import get_settings
from knowledge.vector_store import get_vector_store

logger = logging.getLogger(__name__)

# Embedding handling with fallback
try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except Exception as e:
    logger.warning(f"sentence-transformers not available: {e}")
    ST_AVAILABLE = False

_embedding_model = None
_fallback_dim = 384  # same as MiniLM


def _get_embedding_model():
    global _embedding_model
    settings = get_settings()
    if not ST_AVAILABLE:
        return None
    if _embedding_model is None:
        try:
            _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}, using dummy")
            _embedding_model = None
    return _embedding_model


def _dummy_embedding(text: str, dim: int = _fallback_dim) -> List[float]:
    """Deterministic dummy embedding via hashing, to keep offline operation."""
    # Use hashlib to generate pseudo-random but deterministic vector
    # hash each chunk of text
    h = hashlib.sha256(text.encode()).digest()
    # Expand to dim via repeated hashing
    vals = []
    counter = 0
    while len(vals) < dim:
        hh = hashlib.sha256((text + str(counter)).encode()).digest()
        for b in hh:
            vals.append((b / 255.0) * 2 - 1)  # -1 to 1
            if len(vals) >= dim:
                break
        counter += 1
    # normalize
    import math
    norm = math.sqrt(sum(x * x for x in vals)) + 1e-8
    return [x / norm for x in vals]


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = _get_embedding_model()
    if model is not None:
        try:
            embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True).tolist()
            return embeddings
        except Exception as e:
            logger.warning(f"Embedding encode failed: {e}, using dummy")
    # fallback
    return [_dummy_embedding(t) for t in texts]


def embed_query(query: str) -> List[float]:
    return embed_texts([query])[0]


def retrieve(query: str, machine_type: Optional[str] = None, k: int = 5) -> List[Dict[str, Any]]:
    """Retrieve chunks with citations.

    Returns list of {text, source, section, page, score, chunk_id}
    """
    settings = get_settings()
    k = k or settings.RETRIEVAL_K
    threshold = settings.RETRIEVAL_SCORE_THRESHOLD

    store = get_vector_store()
    q_emb = embed_query(query)

    where = None
    if machine_type:
        # Filter: either machine_type tag contains this type or generic
        # Chroma where filtering: we have metadata field machine_type tags might be list; we stored as string? We'll not strictly filter to avoid missing
        # For simplicity, if machine_type, we try filter but fallback to no filter if no results
        where = None  # We'll handle after, or pass if collection supports

    result = store.query(q_emb, k=k, where=where)

    # result format: ids [[...]], documents [[...]], metadatas [[...]], distances [[...]]
    docs_out: List[Dict[str, Any]] = []
    try:
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        for idx in range(len(documents)):
            dist = distances[idx] if idx < len(distances) else 1.0
            # Convert distance to similarity score: chroma uses L2 or cosine? Assume similarity = 1 - distance
            # For cosine distance, score = 1 - dist
            score = 1.0 - dist if dist <= 1.0 else 1.0 / (1.0 + dist)
            if score < threshold:
                # still keep but lower ranked? spec says apply minimum threshold, so filter
                # we keep only if above threshold, but if none above threshold, keep top 1
                if len(docs_out) == 0 and idx == len(documents) - 1:
                    # if this is last and no docs, keep at least one
                    pass
                else:
                    if score < threshold:
                        continue

            meta = metadatas[idx] if idx < len(metadatas) else {}
            docs_out.append({
                "text": documents[idx],
                "source": meta.get("source", "unknown"),
                "section": meta.get("section", ""),
                "page": meta.get("page"),
                "score": float(score),
                "chunk_id": ids[idx] if idx < len(ids) else f"chunk_{idx}",
                "metadata": meta,
            })
        # if filtered everything, keep top one anyway with low score
        if not docs_out and documents:
            # take first
            meta = metadatas[0] if metadatas else {}
            docs_out.append({
                "text": documents[0],
                "source": meta.get("source", "unknown"),
                "section": meta.get("section", ""),
                "page": meta.get("page"),
                "score": float(1.0 - distances[0]) if distances else 0.0,
                "chunk_id": ids[0] if ids else "chunk_0",
                "metadata": meta,
            })

    except Exception as e:
        logger.warning(f"Retriever parsing failed: {e}")

    # Optional secondary filter by machine_type if metadata contains machine_type_tags
    if machine_type and docs_out:
        filtered = [d for d in docs_out if machine_type in d.get("metadata", {}).get("machine_type_tags", []) or "all" in d.get("metadata", {}).get("machine_type_tags", [])]
        if filtered:
            docs_out = filtered

    # sort by score desc
    docs_out.sort(key=lambda x: x["score"], reverse=True)
    return docs_out[:k]


def format_citations(chunks: List[Dict[str, Any]]) -> List[str]:
    """Returns citation strings like [1] file, section."""
    citations = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.get("source", "unknown")
        section = chunk.get("section", "")
        page = chunk.get("page")
        if page:
            cit = f"[{i}] {source}, {section} (p. {page})"
        else:
            if section:
                cit = f"[{i}] {source}, {section}"
            else:
                cit = f"[{i}] {source}"
        citations.append(cit)
    return citations


def build_retrieval_query(alert: Dict[str, Any]) -> str:
    """Build query from alert: machine type + top sensors + alert type."""
    parts = []
    parts.append(f"Machine type {alert.get('machine_type')} alert type {alert.get('alert_type')} severity {alert.get('severity')}")
    top_sensors = alert.get("top_sensors", [])
    if top_sensors:
        sensor_names = ", ".join([s.get("name", "") for s in top_sensors[:5]])
        parts.append(f"Top deviating sensors: {sensor_names}")
    if alert.get("predicted_rul") is not None:
        parts.append(f"Predicted RUL {alert.get('predicted_rul')} cycles indicates degradation")
    if alert.get("defect_probability") is not None:
        parts.append(f"Defect probability {alert.get('defect_probability')}")
    return " ".join(parts)

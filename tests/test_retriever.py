"""Retriever returns citations."""
from knowledge.vector_store import get_vector_store
from knowledge.retriever import retrieve, format_citations, embed_texts
from knowledge.ingest_docs import ingest_manuals


def test_retriever_returns_citations():
    # Ensure store has docs
    store = get_vector_store()
    if store.count() == 0:
        ingest_manuals("./data/manuals", reset=False)

    results = retrieve("turbofan compressor fouling s7 temperature", machine_type="turbofan", k=3)
    assert len(results) > 0
    assert "text" in results[0]
    assert "source" in results[0]
    assert "score" in results[0]
    assert "chunk_id" in results[0]

    citations = format_citations(results)
    assert len(citations) == len(results)
    assert citations[0].startswith("[1]")


def test_retriever_with_machine_filter():
    results = retrieve("torque calibration", machine_type="bosch", k=2)
    assert len(results) > 0

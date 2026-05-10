from __future__ import annotations

import pytest

from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.index_store import VectorIndexStore


pytestmark = [pytest.mark.integration]


def test_vector_index_store_builds_and_searches(tmp_path, small_corpus) -> None:
    store = VectorIndexStore(tmp_path / "index.json", backend=EmbeddingBackend(dimension=32))
    records = store.build(small_corpus)
    results = store.search("stress and sleep", topic="burnout_sleep", k=2)

    assert records
    assert results
    assert results[0][0].chunk.topic in {"burnout_sleep", "stress_anxiety"}


def test_faiss_store_builds_and_searches(tmp_faiss_store) -> None:
    store, embedder, _ = tmp_faiss_store
    results = store.search(embedder.embed("stress and sleep"), topic="burnout_sleep", k=2)

    assert results
    assert results[0][0].topic in {"burnout_sleep", "stress_anxiety"}

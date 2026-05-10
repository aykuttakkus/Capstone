from __future__ import annotations

import pytest

from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.faiss_store import FaissIndexStore
from tests.factories.retrieval import build_small_knowledge_base


@pytest.fixture
def small_corpus():
    return build_small_knowledge_base()


@pytest.fixture
def tmp_faiss_store(tmp_path, small_corpus):
    embedder = EmbeddingBackend(dimension=32)
    store = FaissIndexStore(tmp_path / "faiss.index", tmp_path / "faiss_metadata.json")
    store.build(small_corpus, embedder)
    return store, embedder, small_corpus

from __future__ import annotations

import server.app.core.retrieval.hybrid_retriever as hybrid_module
from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.faiss_store import FaissIndexStore
from tests.factories.retrieval import build_small_knowledge_base


class FakeQdrantStore:
    def __init__(self, *args, **kwargs):
        self.available = True
        self.calls = 0

    def search_with_filters(self, query_embedding, topic=None, k=5, source_kind=None, language=None, min_confidence=None):
        self.calls += 1
        kb = build_small_knowledge_base()
        chunk = kb.chunks[0]
        return [(chunk, 0.99)]


class UnavailableQdrantStore:
    def __init__(self, *args, **kwargs):
        self.available = False

    def search_with_filters(self, *args, **kwargs):
        raise AssertionError("Qdrant should not be used when unavailable")


class FakeGraphStore:
    def __init__(self, *args, **kwargs):
        self.loaded = False
        self.built = False
        self.saved = False
        self.calls = 0

    def load(self):
        self.loaded = True
        return True

    def build(self, kb):
        self.built = True

    def save(self):
        self.saved = True

    def get_related_chunks(self, seed_topic=None, seed_keywords=None):
        self.calls += 1
        return ["stress-001"]


def test_hybrid_retriever_prefers_qdrant_when_enabled(monkeypatch, tmp_path) -> None:
    kb = build_small_knowledge_base()
    embedder = EmbeddingBackend(dimension=32)
    faiss_store = FaissIndexStore(tmp_path / "faiss.index", tmp_path / "faiss_metadata.json")
    faiss_store.build(kb, embedder)

    fake_qdrant = FakeQdrantStore()
    monkeypatch.setattr(hybrid_module, "RETRIEVAL_BACKEND", "qdrant")
    monkeypatch.setattr(hybrid_module, "QDRANT_URL", "http://localhost:6333")
    monkeypatch.setattr(hybrid_module, "QDRANT_COLLECTION", "calma_chunks")
    monkeypatch.setattr(hybrid_module.QdrantStore, "__init__", lambda self, url, collection_name: None)
    monkeypatch.setattr(hybrid_module.QdrantStore, "available", True, raising=False)
    monkeypatch.setattr(hybrid_module, "QdrantStore", lambda *args, **kwargs: fake_qdrant)

    retriever = hybrid_module.HybridRetriever(kb, faiss_store, embedder=embedder)
    results = retriever.retrieve("stress and sleep", topic="burnout_sleep", k=2)

    assert fake_qdrant.calls == 1
    assert results


def test_hybrid_retriever_falls_back_to_faiss_when_qdrant_unavailable(monkeypatch, tmp_path) -> None:
    kb = build_small_knowledge_base()
    embedder = EmbeddingBackend(dimension=32)
    faiss_store = FaissIndexStore(tmp_path / "faiss.index", tmp_path / "faiss_metadata.json")
    faiss_store.build(kb, embedder)

    monkeypatch.setattr(hybrid_module, "RETRIEVAL_BACKEND", "qdrant")
    monkeypatch.setattr(hybrid_module, "QDRANT_URL", "http://localhost:6333")
    monkeypatch.setattr(hybrid_module, "QDRANT_COLLECTION", "calma_chunks")
    monkeypatch.setattr(hybrid_module, "QdrantStore", lambda *args, **kwargs: UnavailableQdrantStore())

    retriever = hybrid_module.HybridRetriever(kb, faiss_store, embedder=embedder)
    results = retriever.retrieve("stress and sleep", topic="burnout_sleep", k=2)

    assert results
    assert results[0].chunk.topic in {"burnout_sleep", "stress_anxiety"}


def test_hybrid_retriever_keeps_graph_disabled_by_default(monkeypatch, tmp_path) -> None:
    kb = build_small_knowledge_base()
    embedder = EmbeddingBackend(dimension=32)
    faiss_store = FaissIndexStore(tmp_path / "faiss.index", tmp_path / "faiss_metadata.json")
    faiss_store.build(kb, embedder)

    monkeypatch.setattr(hybrid_module, "ENABLE_GRAPH_RAG", False)
    retriever = hybrid_module.HybridRetriever(kb, faiss_store, embedder=embedder)

    assert retriever.graph_store is None


def test_hybrid_retriever_uses_graph_only_for_graph_friendly_queries(monkeypatch, tmp_path) -> None:
    kb = build_small_knowledge_base()
    embedder = EmbeddingBackend(dimension=32)
    faiss_store = FaissIndexStore(tmp_path / "faiss.index", tmp_path / "faiss_metadata.json")
    faiss_store.build(kb, embedder)

    fake_graph = FakeGraphStore()
    monkeypatch.setattr(hybrid_module, "ENABLE_GRAPH_RAG", True)
    monkeypatch.setattr(hybrid_module, "GRAPH_RAG_MIN_CHUNKS", 1)
    monkeypatch.setattr(hybrid_module, "GRAPH_RAG_MIN_QUERY_TERMS", 4)
    monkeypatch.setattr(hybrid_module, "should_enable_graph_rag", lambda kb, min_chunks: True)
    monkeypatch.setattr(hybrid_module, "GraphStore", lambda *args, **kwargs: fake_graph)

    retriever = hybrid_module.HybridRetriever(kb, faiss_store, embedder=embedder)
    assert retriever.graph_store is fake_graph

    retriever.retrieve("How do stress, sleep, and family support interact?", topic="social_pressure", k=2)
    assert fake_graph.calls == 1

    fake_graph.calls = 0
    retriever.retrieve("Tell me about stress", topic="stress_anxiety", k=2)
    assert fake_graph.calls == 0

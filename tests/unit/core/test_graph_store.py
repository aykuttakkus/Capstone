from __future__ import annotations

from pathlib import Path

from server.app.core.retrieval.graph_store import GraphStore, is_graph_friendly_query, should_enable_graph_rag
from tests.factories.retrieval import build_small_knowledge_base


def test_graph_helpers_require_larger_corpus_and_graph_like_queries() -> None:
    kb = build_small_knowledge_base()

    assert should_enable_graph_rag(kb, min_chunks=10) is False
    assert is_graph_friendly_query("How do stress, sleep, and family support interact over time?", topic="social_pressure") is True
    assert is_graph_friendly_query("Tell me about anxiety", topic="stress_anxiety") is False


def test_graph_store_build_save_load_and_related_chunks(tmp_path: Path) -> None:
    kb = build_small_knowledge_base()
    store = GraphStore(storage_path=tmp_path / "graph.json")

    store.build(kb)
    related = store.get_related_chunks(seed_topic="stress_anxiety", seed_keywords=["stress", "sleep"])
    store.save()

    reloaded = GraphStore(storage_path=tmp_path / "graph.json")
    assert reloaded.load() is True
    assert related
    assert "stress-001" in related or "sleep-001" in related
    assert reloaded.get_related_chunks(seed_topic="stress_anxiety", seed_keywords=["stress"])

from __future__ import annotations

from server.app.core.retrieval.retriever import SimpleRetriever
from tests.factories.retrieval import build_chunk, build_small_knowledge_base


def test_simple_retriever_handles_common_typos() -> None:
    kb = build_small_knowledge_base()
    retriever = SimpleRetriever(kb)

    results = retriever.retrieve("i have anxiaty", topic="stress_anxiety", k=1)

    assert results
    assert results[0].chunk.topic == "stress_anxiety"


def test_simple_retriever_applies_metadata_filters() -> None:
    kb = build_small_knowledge_base()
    kb.chunks.append(
        build_chunk(
            "safety-001",
            topic="help_seeking",
            content="Seek professional support when symptoms persist.",
            keywords=["support", "professional"],
            source_kind="safety_reference",
            language="en",
            confidence=0.97,
        )
    )
    retriever = SimpleRetriever(kb)

    results = retriever.retrieve(
        "professional support",
        topic="help_seeking",
        k=3,
        source_kind="safety_reference",
        language="en",
        min_confidence=0.9,
    )

    assert results
    assert all(result.chunk.source_kind == "safety_reference" for result in results)
    assert all(result.chunk.language == "en" for result in results)
    assert all(result.chunk.confidence >= 0.9 for result in results)


def test_simple_retriever_treats_general_and_unknown_topics_as_unfiltered() -> None:
    kb = build_small_knowledge_base()
    retriever = SimpleRetriever(kb)

    baseline = retriever.retrieve("stress sleep", topic=None, k=2)
    general_results = retriever.retrieve("stress sleep", topic="general", k=2)
    unknown_results = retriever.retrieve("stress sleep", topic="not_a_real_topic", k=2)

    assert general_results
    assert unknown_results
    assert [result.chunk.id for result in general_results] == [result.chunk.id for result in baseline]
    assert [result.chunk.id for result in unknown_results] == [result.chunk.id for result in baseline]

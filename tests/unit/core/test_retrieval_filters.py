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


def test_simple_retriever_filters_by_allowed_use_and_evidence_level() -> None:
    kb = build_small_knowledge_base()
    kb.chunks.append(
        build_chunk(
            "coping-001",
            topic="stress_anxiety",
            content="A grounding step can help during stress.",
            keywords=["grounding", "stress"],
            allowed_use=["coping_strategy"],
            evidence_level="clinical_self_help",
        )
    )
    retriever = SimpleRetriever(kb)

    results = retriever.retrieve(
        "grounding stress",
        topic="stress_anxiety",
        k=5,
        intent="coping_strategy",
        allowed_use=["coping_strategy"],
        min_evidence_level="clinical_self_help",
    )

    assert results
    assert all("coping_strategy" in result.chunk.allowed_use for result in results)
    assert all(result.chunk.evidence_level in {"clinical_self_help", "peer_reviewed", "clinical_guideline"} for result in results)


def test_simple_retriever_filters_crisis_chunks_from_low_risk_context() -> None:
    kb = build_small_knowledge_base()
    kb.chunks.append(
        build_chunk(
            "crisis-001",
            topic="stress_anxiety",
            content="Immediate danger requires crisis support.",
            keywords=["stress", "danger"],
            allowed_use=["crisis"],
            risk_level="crisis",
            evidence_level="clinical_guideline",
        )
    )
    retriever = SimpleRetriever(kb)

    results = retriever.retrieve("stress danger", topic="stress_anxiety", k=5, risk_level="none")

    assert results
    assert all(result.chunk.risk_level != "crisis" for result in results)


def test_simple_retriever_can_select_isolated_crisis_scope() -> None:
    kb = build_small_knowledge_base()
    kb.chunks.append(
        build_chunk(
            "crisis-001",
            topic="help_seeking",
            content="If there is immediate danger, contact emergency support.",
            keywords=["immediate", "danger", "emergency"],
            allowed_use=["crisis"],
            risk_level="crisis",
            content_type="crisis_instruction",
            evidence_level="clinical_guideline",
            clinical_scope="crisis_support_only",
        )
    )
    retriever = SimpleRetriever(kb)

    results = retriever.retrieve(
        "immediate danger emergency",
        topic="help_seeking",
        k=5,
        intent="crisis",
        risk_level="crisis",
        allowed_use=["crisis"],
        clinical_scope="crisis_support_only",
    )

    assert results
    assert all(result.chunk.clinical_scope == "crisis_support_only" for result in results)

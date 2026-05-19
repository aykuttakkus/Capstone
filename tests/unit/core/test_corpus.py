"""
Unit Tests: KnowledgeChunk and KnowledgeBase Corpus

Tests the data integrity of the knowledge corpus — the foundation of
the RAG pipeline. If chunks are malformed, retrieval silently degrades.

These tests verify:
- KnowledgeChunk field validation and defaults
- Allowed-use / not-allowed metadata gates
- KnowledgeBase integrity properties
"""

from __future__ import annotations

import pytest
from server.app.core.retrieval.corpus import KnowledgeChunk, KnowledgeBase, metadata_matches_filters


# ── KnowledgeChunk: field validation ─────────────────────────────────────────

def test_chunk_has_required_fields(sample_chunks):
    for chunk in sample_chunks:
        assert chunk.id
        assert chunk.title
        assert chunk.topic
        assert chunk.source
        assert isinstance(chunk.content, str)


def test_chunk_content_not_empty(sample_chunks):
    for chunk in sample_chunks:
        assert len(chunk.content.strip()) > 0, f"Chunk {chunk.id} has empty content"


def test_chunk_confidence_in_valid_range(sample_chunks):
    for chunk in sample_chunks:
        assert 0.0 <= chunk.confidence <= 1.0, (
            f"Chunk {chunk.id} has invalid confidence: {chunk.confidence}"
        )


def test_chunk_language_set(sample_chunks):
    for chunk in sample_chunks:
        assert chunk.language in ("en", "tr", "de", "fr", "es"), (
            f"Unexpected language tag: {chunk.language}"
        )


def test_chunk_source_kind_valid(sample_chunks):
    valid_kinds = {"user_corpus", "safety_reference", "clinical_guideline", "educational"}
    for chunk in sample_chunks:
        assert chunk.source_kind in valid_kinds, (
            f"Chunk {chunk.id} has unknown source_kind: {chunk.source_kind}"
        )


# ── KnowledgeChunk: allowed_use gates ────────────────────────────────────────

def test_default_allowed_use_contains_psychoeducation():
    chunk = KnowledgeChunk(
        id="c1", title="Test", topic="anxiety",
        source="test.pdf", content="Anxiety is manageable",
    )
    assert "psychoeducation" in chunk.allowed_use


def test_default_not_allowed_contains_diagnosis():
    chunk = KnowledgeChunk(
        id="c1", title="Test", topic="anxiety",
        source="test.pdf", content="Anxiety is manageable",
    )
    assert "diagnosis" in chunk.not_allowed
    assert "medication_advice" in chunk.not_allowed


def test_from_dict_preserves_content():
    payload = {
        "id": "test_001",
        "title": "Loneliness and Social Connection",
        "topic": "loneliness",
        "source": "who_guidelines.pdf",
        "content": "Social isolation is linked to increased mental health burden.",
        "keywords": ["loneliness", "isolation", "social"],
        "confidence": 0.88,
        "source_kind": "user_corpus",
    }
    chunk = KnowledgeChunk.from_dict(payload)
    assert chunk.id == "test_001"
    assert chunk.topic == "loneliness"
    assert "isolation" in chunk.content
    assert chunk.confidence == 0.88


def test_from_dict_handles_missing_optional_fields():
    payload = {
        "id": "minimal_001",
        "title": "Minimal",
        "topic": "stress",
        "source": "test.pdf",
        "content": "Stress affects sleep quality.",
    }
    chunk = KnowledgeChunk.from_dict(payload)
    assert chunk.confidence == 1.0
    assert chunk.language in ("en", "tr")
    assert isinstance(chunk.allowed_use, list)
    assert isinstance(chunk.not_allowed, list)


# ── metadata_matches_filters ──────────────────────────────────────────────────

def test_allowed_use_filter_passes_matching_chunk():
    chunk = KnowledgeChunk(
        id="c1", title="T", topic="anxiety", source="s.pdf",
        content="Anxiety coping",
        allowed_use=["psychoeducation", "coping_strategy"],
    )
    assert metadata_matches_filters(chunk, allowed_use=["coping_strategy"]) is True


def test_allowed_use_filter_blocks_unmatching_chunk():
    chunk = KnowledgeChunk(
        id="c2", title="T", topic="anxiety", source="s.pdf",
        content="Anxiety info",
        allowed_use=["psychoeducation"],
    )
    assert metadata_matches_filters(chunk, allowed_use=["medication_advice"]) is False


def test_exclude_not_allowed_blocks_prohibited_use():
    chunk = KnowledgeChunk(
        id="c3", title="T", topic="medication", source="s.pdf",
        content="Medication dosage info",
        not_allowed=["medication_advice"],
    )
    assert metadata_matches_filters(chunk, exclude_not_allowed=["medication_advice"]) is False


def test_no_filters_matches_any_chunk(sample_chunks):
    for chunk in sample_chunks:
        assert metadata_matches_filters(chunk) is True


# ── KnowledgeBase integrity ───────────────────────────────────────────────────

def test_knowledge_base_chunks_are_unique_by_id(sample_chunks):
    ids = [c.id for c in sample_chunks]
    assert len(ids) == len(set(ids)), "Duplicate chunk IDs detected in sample corpus"


def test_knowledge_base_topics_are_strings(sample_chunks):
    for chunk in sample_chunks:
        assert isinstance(chunk.topic, str) and len(chunk.topic) > 0

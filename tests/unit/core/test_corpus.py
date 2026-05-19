from __future__ import annotations

import pytest

from server.app.core.retrieval.corpus import KnowledgeBase, KnowledgeChunk


pytestmark = [pytest.mark.unit]


def test_knowledge_chunk_serializes_phase5_metadata() -> None:
    chunk = KnowledgeChunk(
        id="x",
        title="Title",
        topic="stress_anxiety",
        source="Source",
        content="Content",
        subtopic="stress_anxiety",
        action_type="self_help",
        audience="adult",
        risk_level="standard",
        page_range="2-3",
    )

    payload = KnowledgeBase(chunks=[chunk]).signature()

    assert isinstance(payload, str)
    assert len(payload) == 16


def test_knowledge_chunk_defaults_remain_safe() -> None:
    chunk = KnowledgeChunk.from_dict({"id": "x", "title": "Title", "content": "Body"})

    assert chunk.topic == "general"
    assert chunk.subtopic == "general"
    assert chunk.action_type == "explanation"

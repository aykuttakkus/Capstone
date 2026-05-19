from __future__ import annotations

import pytest

from server.app.core.retrieval.ingestion.chunker import SemanticChunker


pytestmark = [pytest.mark.unit]


def test_chunker_splits_long_sections_into_smaller_chunks(monkeypatch) -> None:
    class FakeSplitter:
        def split_text(self, markdown_text: str):
            long_a = "Paragraph one. " + ("A" * 900)
            long_b = "Paragraph two is long enough to remain. " + ("B" * 900)
            long_c = "Paragraph three is also meaningful. " + ("C" * 900)
            return [type("Doc", (), {"metadata": {"Header_1": "Guide", "Header_2": "Section"}, "page_content": f"{long_a}\n\n{long_b}\n\n{long_c}"})()]

    chunker = SemanticChunker.__new__(SemanticChunker)
    chunker.splitter = FakeSplitter()

    chunks = chunker.chunk("# Guide")

    assert len(chunks) >= 2
    assert all("title" in chunk and "content" in chunk and "section" in chunk for chunk in chunks)

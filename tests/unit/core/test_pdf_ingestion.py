from __future__ import annotations

from pathlib import Path

import server.app.core.retrieval.pdf_ingestion as pdf_ingestion
from server.app.core.retrieval.ingestion.chunker import SemanticChunker


class _FakePdfPage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakePdfReader:
    def __init__(self, pages: list[str]) -> None:
        self.pages = [_FakePdfPage(text) for text in pages]


def test_extract_pdf_page_records_removes_noise_and_reference_tail(monkeypatch) -> None:
    pages = [
        "\n".join(
            [
                "Psychology Handbook",
                "Chapter 1",
                "1",
                "Introduction to anxiety",
                "Contact: editor@example.com doi:10.1000/xyz123",
                "This is grounded body text about anxiety and sleep.",
                "Footer Label",
            ]
        ),
        "\n".join(
            [
                "Psychology Handbook",
                "Chapter 1",
                "2",
                "This page continues the grounded explanation with coping skills.",
                "Footer Label",
            ]
        ),
        "\n".join(
            [
                "Psychology Handbook",
                "References",
                "3",
                "Smith, J. Example reference entry.",
                "Footer Label",
            ]
        ),
    ]
    monkeypatch.setattr(pdf_ingestion, "PdfReader", lambda _: _FakePdfReader(pages))

    cleaned = pdf_ingestion.extract_pdf_page_records(Path("dummy.pdf"))

    assert [page.page_number for page in cleaned] == [1, 2]
    combined = "\n".join(page.text for page in cleaned)
    assert "Psychology Handbook" not in combined
    assert "Footer Label" not in combined
    assert "References" not in combined
    assert "editor@example.com" not in combined
    assert "10.1000/xyz123" not in combined
    assert "grounded body text" in combined
    assert "coping skills" in combined


def test_extract_pdf_page_records_removes_late_author_contribution_tail(monkeypatch) -> None:
    pages = [
        "\n".join(
            [
                "Psychology Journal",
                "4",
                "This page contains grounded discussion of clinical findings and implications.",
            ]
        ),
        "\n".join(
            [
                "Psychology Journal",
                "5",
                "Author Contributions",
                "A.B. designed the study and wrote the manuscript.",
                "Declaration of Conflicting Interests",
                "The authors declared no conflicts.",
            ]
        ),
        "\n".join(
            [
                "Psychology Journal",
                "6",
                "Source(s) of Support",
                "No funding was received.",
            ]
        ),
    ]
    monkeypatch.setattr(pdf_ingestion, "PdfReader", lambda _: _FakePdfReader(pages))

    cleaned = pdf_ingestion.extract_pdf_page_records(Path("dummy.pdf"))

    assert [page.page_number for page in cleaned] == [4]
    assert "Author Contributions" not in cleaned[0].text


def test_semantic_chunker_creates_windowed_chunks_with_overlap_and_page_ranges() -> None:
    chunker = SemanticChunker()
    page_records = [
        {"page": 1, "text": " ".join(f"alpha{i}" for i in range(400))},
        {"page": 2, "text": " ".join(f"beta{i}" for i in range(400))},
        {"page": 3, "text": " ".join(f"gamma{i}" for i in range(400))},
    ]

    chunks = chunker.chunk(None, page_records=page_records, default_title="Psychology Textbook")

    assert len(chunks) == 2
    assert chunks[0]["page_start"] == 1
    assert chunks[0]["page_end"] == 2
    assert chunks[1]["page_start"] == 2
    assert chunks[1]["page_end"] == 3
    assert chunks[0]["word_count"] == 650
    assert chunks[1]["word_count"] == 650

    first_words = str(chunks[0]["content"]).split()
    second_words = str(chunks[1]["content"]).split()
    assert first_words[-100:] == second_words[:100]


def test_build_legacy_chunks_uses_page_ranges_and_word_counts(monkeypatch) -> None:
    page_records = [
        pdf_ingestion.PDFExtractedPage(page_number=1, text=" ".join(f"alpha{i}" for i in range(400))),
        pdf_ingestion.PDFExtractedPage(page_number=2, text=" ".join(f"beta{i}" for i in range(400))),
        pdf_ingestion.PDFExtractedPage(page_number=3, text=" ".join(f"gamma{i}" for i in range(400))),
    ]
    monkeypatch.setattr(pdf_ingestion, "extract_pdf_page_records", lambda _: page_records)

    chunks = pdf_ingestion._build_legacy_chunks_from_pdf(Path("stress-guide.pdf"))

    assert len(chunks) == 2
    assert chunks[0].page == 1
    assert chunks[0].page_start == 1
    assert chunks[0].page_end == 2
    assert chunks[0].word_count == 650
    assert chunks[1].page == 2
    assert chunks[1].page_start == 2
    assert chunks[1].page_end == 3
    assert chunks[1].word_count == 650


def test_low_quality_chunk_filter_discards_figure_and_reference_artifacts() -> None:
    figure_artifact = " ".join(["●"] * 250) + " Figure 1: Study 1. " + " ".join(["−2", "−1", "0", "1", "2"] * 30)
    assert pdf_ingestion._is_low_quality_chunk(
        title="Figure Artifact",
        content=figure_artifact,
        section="Pages 3-4",
        page_start=3,
        page_end=4,
        total_pages=10,
    )

    reference_tail = (
        "Author Contributions: A.B. wrote the draft. "
        "Declaration of Conflicting Interests: none. "
        "Source(s) of Support: no funding."
    )
    assert pdf_ingestion._is_low_quality_chunk(
        title="Late Tail",
        content=reference_tail,
        section="Pages 9-10",
        page_start=9,
        page_end=10,
        total_pages=10,
    )

    grounded_content = " ".join(
        [
            "This",
            "grounded",
            "psychoeducational",
            "discussion",
            "explains",
            "sleep",
            "stress",
            "and",
            "coping",
            "strategies",
        ]
        * 80
    )
    assert not pdf_ingestion._is_low_quality_chunk(
        title="Grounded Discussion",
        content=grounded_content,
        section="Methods and Discussion",
        page_start=4,
        page_end=5,
        total_pages=10,
    )

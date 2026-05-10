from __future__ import annotations

from pathlib import Path

from server.app.core.retrieval.corpus import KnowledgeBase
from server.app.services.pdf_pipeline import PDFIngestionResult
import server.app.workers.pdf_ingestion_worker as worker


def test_offline_pdf_worker_runs_ingestion_and_builds_index(monkeypatch, tmp_path: Path) -> None:
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()

    calls: dict[str, object] = {"ingest": 0, "build": 0}
    original_load = KnowledgeBase.load

    def fake_ingest_pdf_directory(*args, **kwargs):
        calls["ingest"] += 1
        return PDFIngestionResult(
            pdf_dir=pdf_dir,
            version="v123",
            inventory_path=tmp_path / "pdf_inventory.json",
            processed_corpus_path=tmp_path / "processed_knowledge_base.json",
            inventory_version_path=tmp_path / "pdf_inventory_versions" / "v123.json",
            processed_version_path=tmp_path / "processed_versions" / "v123.json",
            manifest_path=tmp_path / "corpus_manifest.json",
            total_pdfs=1,
            indexed_pdfs=1,
            skipped_pdfs=0,
            total_chunks=2,
        )

    class DummyEmbeddingBackend:
        def __init__(self, *args, **kwargs):
            self.dimension = 32

    class DummyIndexStore:
        def __init__(self, *args, **kwargs):
            pass

        def build(self, knowledge_base: KnowledgeBase, embedder) -> None:
            calls["build"] += 1

    def fake_load() -> KnowledgeBase:
        return original_load()

    monkeypatch.setattr(worker, "ingest_pdf_directory", fake_ingest_pdf_directory)
    monkeypatch.setattr(worker, "EmbeddingBackend", DummyEmbeddingBackend)
    monkeypatch.setattr(worker, "FaissIndexStore", DummyIndexStore)
    monkeypatch.setattr(worker.KnowledgeBase, "load", staticmethod(fake_load))

    result = worker.build_offline_pdf_corpus(pdf_dir)

    assert result.version == "v123"
    assert calls["ingest"] == 1
    assert calls["build"] == 1


def test_offline_pdf_worker_can_skip_index_build(monkeypatch, tmp_path: Path) -> None:
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()

    calls: dict[str, object] = {"build": 0}

    def fake_ingest_pdf_directory(*args, **kwargs):
        return PDFIngestionResult(
            pdf_dir=pdf_dir,
            version="v123",
            inventory_path=tmp_path / "pdf_inventory.json",
            processed_corpus_path=tmp_path / "processed_knowledge_base.json",
            inventory_version_path=tmp_path / "pdf_inventory_versions" / "v123.json",
            processed_version_path=tmp_path / "processed_versions" / "v123.json",
            manifest_path=tmp_path / "corpus_manifest.json",
            total_pdfs=1,
            indexed_pdfs=1,
            skipped_pdfs=0,
            total_chunks=2,
        )

    class DummyIndexStore:
        def __init__(self, *args, **kwargs):
            pass

        def build(self, knowledge_base: KnowledgeBase, embedder) -> None:
            calls["build"] += 1

    monkeypatch.setattr(worker, "ingest_pdf_directory", fake_ingest_pdf_directory)
    monkeypatch.setattr(worker, "EmbeddingBackend", lambda: object())
    monkeypatch.setattr(worker, "FaissIndexStore", DummyIndexStore)

    result = worker.build_offline_pdf_corpus(pdf_dir, build_index=False)

    assert result.version == "v123"
    assert calls["build"] == 0

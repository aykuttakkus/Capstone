from __future__ import annotations

from pathlib import Path

from server.app.services.pdf_pipeline import PDFIngestionResult
import server.app.workers.pdf_ingestion_worker as worker


def test_offline_pdf_worker_runs_ingestion_and_builds_index(monkeypatch, tmp_path: Path) -> None:
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()

    calls: dict[str, object] = {"ingest": 0, "build": 0}
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
        def __init__(self, index_path, metadata_path):
            calls["index_path"] = index_path
            calls["metadata_path"] = metadata_path

        def build(self, knowledge_base, embedder) -> None:
            calls["build"] += 1

    monkeypatch.setattr(worker, "ingest_pdf_directory", fake_ingest_pdf_directory)
    monkeypatch.setattr(worker, "EmbeddingBackend", DummyEmbeddingBackend)
    monkeypatch.setattr(worker, "FaissIndexStore", DummyIndexStore)
    monkeypatch.setattr(worker, "_load_knowledge_base_for_index", lambda path: object())

    result = worker.build_offline_pdf_corpus(pdf_dir)

    assert result.version == "v123"
    assert calls["ingest"] == 1
    assert calls["build"] == 1
    assert calls["index_path"] == worker.FAISS_INDEX_PATH
    assert calls["metadata_path"] == worker.FAISS_METADATA_PATH


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

        def build(self, knowledge_base, embedder) -> None:
            calls["build"] += 1

    monkeypatch.setattr(worker, "ingest_pdf_directory", fake_ingest_pdf_directory)
    monkeypatch.setattr(worker, "EmbeddingBackend", lambda: object())
    monkeypatch.setattr(worker, "FaissIndexStore", DummyIndexStore)

    result = worker.build_offline_pdf_corpus(pdf_dir, build_index=False)

    assert result.version == "v123"
    assert calls["build"] == 0


def test_offline_pdf_worker_dry_run_skips_index_build(monkeypatch, tmp_path: Path) -> None:
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()

    calls: dict[str, int] = {"build": 0}

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

        def build(self, knowledge_base, embedder) -> None:
            calls["build"] += 1

    monkeypatch.setattr(worker, "ingest_pdf_directory", fake_ingest_pdf_directory)
    monkeypatch.setattr(worker, "EmbeddingBackend", lambda: object())
    monkeypatch.setattr(worker, "FaissIndexStore", DummyIndexStore)

    result = worker.build_offline_pdf_corpus(pdf_dir, dry_run=True)

    assert result.version == "v123"
    assert calls["build"] == 0


def test_offline_pdf_worker_stages_index_paths(monkeypatch, tmp_path: Path) -> None:
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    staging_root = tmp_path / "staging"
    calls: dict[str, object] = {"build": 0}

    def fake_ingest_pdf_directory(*args, **kwargs):
        return PDFIngestionResult(
            pdf_dir=pdf_dir,
            version="v123",
            inventory_path=staging_root / "raw" / "pdf_inventory.json",
            processed_corpus_path=staging_root / "processed" / "processed_knowledge_base.json",
            inventory_version_path=staging_root / "raw" / "pdf_inventory_versions" / "v123.json",
            processed_version_path=staging_root / "processed" / "versions" / "v123.json",
            manifest_path=staging_root / "processed" / "corpus_manifest.json",
            total_pdfs=1,
            indexed_pdfs=1,
            skipped_pdfs=0,
            total_chunks=2,
        )

    class DummyIndexStore:
        def __init__(self, index_path, metadata_path):
            calls["index_path"] = index_path
            calls["metadata_path"] = metadata_path

        def build(self, knowledge_base, embedder) -> None:
            calls["build"] += 1

    monkeypatch.setattr(worker, "ingest_pdf_directory", fake_ingest_pdf_directory)
    monkeypatch.setattr(worker, "_load_knowledge_base_for_index", lambda path: object())
    monkeypatch.setattr(worker, "EmbeddingBackend", lambda: object())
    monkeypatch.setattr(worker, "FaissIndexStore", DummyIndexStore)

    worker.build_offline_pdf_corpus(pdf_dir, staging_root=staging_root)

    assert calls["build"] == 1
    assert str(calls["index_path"]).startswith(str(staging_root))
    assert str(calls["metadata_path"]).startswith(str(staging_root))

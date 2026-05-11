from __future__ import annotations

from pathlib import Path

import server.app.services.pdf_pipeline as pdf_pipeline
from server.app.services.pdf_pipeline import compute_corpus_version, ingest_pdf_directory
from server.app.utils.io import load_json


def test_pdf_pipeline_generates_stable_versioned_artifacts(tmp_path: Path, monkeypatch) -> None:
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()

    inventory_path = tmp_path / "pdf_inventory.json"
    processed_path = tmp_path / "processed_knowledge_base.json"
    inventory_history_path = tmp_path / "pdf_inventory_history.json"
    inventory_versions_dir = tmp_path / "pdf_inventory_versions"
    manifest_path = tmp_path / "corpus_manifest.json"
    processed_versions_dir = tmp_path / "processed_versions"
    fake_inventory = [
        {
            "filename": "depression.pdf",
            "title": "Depression",
            "topic": "low_mood",
            "include_in_index": True,
            "source_kind": "user_corpus",
        }
    ]
    fake_corpus = [
        {
            "id": "depression-p1-2-1",
            "title": "Depression - Pages 1-2",
            "topic": "low_mood",
            "source": "Depression (depression.pdf) pages 1-2",
            "content": "Grounded content",
            "keywords": ["depression"],
            "pdf_file": "depression.pdf",
            "page": 1,
            "page_start": 1,
            "page_end": 2,
            "source_kind": "user_corpus",
            "section": "Pages 1-2",
            "parser_mode": "legacy",
            "confidence": 1.0,
            "language": "en",
            "word_count": 600,
        }
    ]

    monkeypatch.setattr(pdf_pipeline, "PDF_INVENTORY_HISTORY_PATH", inventory_history_path)
    monkeypatch.setattr(pdf_pipeline, "PDF_INVENTORY_VERSIONS_DIR", inventory_versions_dir)
    monkeypatch.setattr(pdf_pipeline, "CORPUS_MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(pdf_pipeline, "PROCESSED_CORPUS_VERSIONS_DIR", processed_versions_dir)
    monkeypatch.setattr(pdf_pipeline, "build_inventory", lambda _: fake_inventory)
    monkeypatch.setattr(pdf_pipeline, "build_corpus_from_pdf_dir", lambda *args, **kwargs: fake_corpus)

    first = ingest_pdf_directory(pdf_dir, inventory_path=inventory_path, processed_corpus_path=processed_path)
    second = ingest_pdf_directory(pdf_dir, inventory_path=inventory_path, processed_corpus_path=processed_path)

    assert first.version == second.version
    assert compute_corpus_version(load_json(inventory_path), load_json(processed_path)) == first.version
    assert (inventory_versions_dir / f"{first.version}.json").exists()
    assert (processed_versions_dir / f"{first.version}.json").exists()
    assert inventory_history_path.exists()
    assert manifest_path.exists()


def test_pdf_pipeline_dry_run_and_staging_mode_do_not_touch_production_paths(tmp_path: Path, monkeypatch) -> None:
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    staging_root = tmp_path / "staging"
    fake_inventory = [
        {
            "filename": "stress.pdf",
            "title": "Stress",
            "topic": "stress_anxiety",
            "include_in_index": True,
            "source_kind": "user_corpus",
        }
    ]
    fake_corpus = [
        {
            "id": "stress-p1-1-1",
            "title": "Stress - Page 1",
            "topic": "stress_anxiety",
            "source": "Stress (stress.pdf) page 1",
            "content": "Evidence grounded stress content",
            "keywords": ["stress"],
            "pdf_file": "stress.pdf",
            "page": 1,
            "page_start": 1,
            "page_end": 1,
            "source_kind": "user_corpus",
            "section": "Page 1",
            "parser_mode": "legacy",
            "confidence": 1.0,
            "language": "en",
            "word_count": 550,
        }
    ]

    monkeypatch.setattr(pdf_pipeline, "build_inventory", lambda _: fake_inventory)
    monkeypatch.setattr(pdf_pipeline, "build_corpus_from_pdf_dir", lambda *args, **kwargs: fake_corpus)

    dry_run = ingest_pdf_directory(pdf_dir, dry_run=True, staging_root=staging_root)
    assert not dry_run.inventory_path.exists()
    assert not dry_run.processed_corpus_path.exists()
    assert not dry_run.inventory_version_path.exists()
    assert not dry_run.processed_version_path.exists()
    assert not dry_run.manifest_path.exists()

    staged = ingest_pdf_directory(pdf_dir, staging_root=staging_root)
    assert staged.inventory_path.exists()
    assert staged.processed_corpus_path.exists()
    assert staged.inventory_version_path.exists()
    assert staged.processed_version_path.exists()
    assert staged.manifest_path.exists()
    assert str(staged.inventory_path).startswith(str(staging_root))

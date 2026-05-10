from __future__ import annotations

import shutil
from pathlib import Path

import server.app.services.pdf_pipeline as pdf_pipeline
from server.app.services.pdf_pipeline import compute_corpus_version, ingest_pdf_directory
from server.app.utils.io import load_json


def test_pdf_pipeline_generates_stable_versioned_artifacts(tmp_path: Path, monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    source_pdf = repo_root / "data" / "raw" / "depression.pdf"
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    shutil.copy2(source_pdf, pdf_dir / source_pdf.name)

    inventory_path = tmp_path / "pdf_inventory.json"
    processed_path = tmp_path / "processed_knowledge_base.json"
    inventory_history_path = tmp_path / "pdf_inventory_history.json"
    inventory_versions_dir = tmp_path / "pdf_inventory_versions"
    manifest_path = tmp_path / "corpus_manifest.json"
    processed_versions_dir = tmp_path / "processed_versions"

    monkeypatch.setattr(pdf_pipeline, "PDF_INVENTORY_HISTORY_PATH", inventory_history_path)
    monkeypatch.setattr(pdf_pipeline, "PDF_INVENTORY_VERSIONS_DIR", inventory_versions_dir)
    monkeypatch.setattr(pdf_pipeline, "CORPUS_MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(pdf_pipeline, "PROCESSED_CORPUS_VERSIONS_DIR", processed_versions_dir)

    first = ingest_pdf_directory(pdf_dir, inventory_path=inventory_path, processed_corpus_path=processed_path)
    second = ingest_pdf_directory(pdf_dir, inventory_path=inventory_path, processed_corpus_path=processed_path)

    assert first.version == second.version
    assert compute_corpus_version(load_json(inventory_path), load_json(processed_path)) == first.version
    assert (inventory_versions_dir / f"{first.version}.json").exists()
    assert (processed_versions_dir / f"{first.version}.json").exists()
    assert inventory_history_path.exists()
    assert manifest_path.exists()

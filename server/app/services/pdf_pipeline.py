from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from server.app.core.config import (
    CORPUS_MANIFEST_PATH,
    PDF_INVENTORY_HISTORY_PATH,
    PDF_INVENTORY_PATH,
    PDF_INVENTORY_VERSIONS_DIR,
    PROCESSED_CORPUS_PATH,
    PROCESSED_CORPUS_VERSIONS_DIR,
)
from server.app.core.retrieval.pdf_ingestion import build_corpus_from_pdf_dir, build_inventory
from server.app.utils.io import load_json, save_json


@dataclass(slots=True)
class PDFIngestionResult:
    pdf_dir: Path
    version: str
    inventory_path: Path
    processed_corpus_path: Path
    inventory_version_path: Path
    processed_version_path: Path
    manifest_path: Path
    total_pdfs: int
    indexed_pdfs: int
    skipped_pdfs: int
    total_chunks: int


def _stable_dump(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_corpus_version(inventory: list[dict], corpus: list[dict]) -> str:
    digest = hashlib.sha256()
    digest.update(_stable_dump(inventory).encode("utf-8"))
    digest.update(b"|")
    digest.update(_stable_dump(corpus).encode("utf-8"))
    return digest.hexdigest()[:12]


def _append_history(path: Path, entry: dict) -> None:
    history = load_json(path, default=[])
    if not isinstance(history, list):
        history = []
    history.append(entry)
    save_json(path, history)


def ingest_pdf_directory(
    pdf_dir: Path,
    *,
    inventory_path: Path = PDF_INVENTORY_PATH,
    processed_corpus_path: Path = PROCESSED_CORPUS_PATH,
    include_non_indexable: bool = False,
    version: str | None = None,
) -> PDFIngestionResult:
    pdf_dir = Path(pdf_dir)
    if not pdf_dir.exists():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")

    inventory = build_inventory(pdf_dir)
    corpus = build_corpus_from_pdf_dir(pdf_dir, include_non_indexable=include_non_indexable)
    corpus_version = version or compute_corpus_version(inventory, corpus)

    inventory_version_path = PDF_INVENTORY_VERSIONS_DIR / f"{corpus_version}.json"
    processed_version_path = PROCESSED_CORPUS_VERSIONS_DIR / f"{corpus_version}.json"

    timestamp = datetime.now(timezone.utc).isoformat()
    history_entry = {
        "version": corpus_version,
        "generated_at": timestamp,
        "pdf_dir": str(pdf_dir),
        "inventory_path": str(inventory_path),
        "processed_corpus_path": str(processed_corpus_path),
        "inventory_version_path": str(inventory_version_path),
        "processed_version_path": str(processed_version_path),
        "total_pdfs": len(inventory),
        "indexed_pdfs": sum(1 for item in inventory if item.get("include_in_index")),
        "skipped_pdfs": sum(1 for item in inventory if not item.get("include_in_index")),
        "total_chunks": len(corpus),
    }

    save_json(inventory_path, inventory)
    save_json(processed_corpus_path, corpus)
    save_json(inventory_version_path, inventory)
    save_json(processed_version_path, corpus)
    _append_history(PDF_INVENTORY_HISTORY_PATH, history_entry)
    _append_history(CORPUS_MANIFEST_PATH, history_entry)

    indexed_pdfs = sum(1 for item in inventory if item.get("include_in_index"))
    total_pdfs = len(inventory)
    skipped_pdfs = total_pdfs - indexed_pdfs

    return PDFIngestionResult(
        pdf_dir=pdf_dir,
        version=corpus_version,
        inventory_path=inventory_path,
        processed_corpus_path=processed_corpus_path,
        inventory_version_path=inventory_version_path,
        processed_version_path=processed_version_path,
        manifest_path=CORPUS_MANIFEST_PATH,
        total_pdfs=total_pdfs,
        indexed_pdfs=indexed_pdfs,
        skipped_pdfs=skipped_pdfs,
        total_chunks=len(corpus),
    )

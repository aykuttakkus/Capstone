"""
scripts/ingest_pdfs.py
======================
Build the processed PDF corpus and inventory from the raw PDF directory.

Usage:
    python scripts/ingest_pdfs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from server.app.core.config import PDF_SOURCE_DIR
from server.app.services.pdf_pipeline import ingest_pdf_directory


def main() -> None:
    result = ingest_pdf_directory(PDF_SOURCE_DIR)

    print("Calma PDF ingestion complete")
    print(f"PDF directory      : {result.pdf_dir}")
    print(f"Corpus version     : {result.version}")
    print(f"Total PDFs         : {result.total_pdfs}")
    print(f"Indexed PDFs       : {result.indexed_pdfs}")
    print(f"Skipped PDFs       : {result.skipped_pdfs}")
    print(f"Total chunks       : {result.total_chunks}")
    print(f"Inventory written  : {result.inventory_path}")
    print(f"Corpus written     : {result.processed_corpus_path}")
    print(f"Inventory version  : {result.inventory_version_path}")
    print(f"Corpus version file : {result.processed_version_path}")
    print(f"Manifest           : {result.manifest_path}")


if __name__ == "__main__":
    main()

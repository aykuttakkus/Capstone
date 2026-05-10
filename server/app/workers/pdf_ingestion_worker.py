from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from server.app.core.config import FAISS_INDEX_PATH, FAISS_METADATA_PATH, RAW_DATA_DIR
from server.app.core.retrieval.corpus import KnowledgeBase
from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.faiss_store import FaissIndexStore
from server.app.services.pdf_pipeline import PDFIngestionResult, ingest_pdf_directory


def build_offline_pdf_corpus(
    pdf_dir: Path,
    *,
    include_non_indexable: bool = False,
    build_index: bool = True,
) -> PDFIngestionResult:
    """Run PDF ingestion outside the chat request path."""
    result = ingest_pdf_directory(pdf_dir, include_non_indexable=include_non_indexable)

    if build_index:
        knowledge_base = KnowledgeBase.load()
        index_store = FaissIndexStore(FAISS_INDEX_PATH, FAISS_METADATA_PATH)
        index_store.build(knowledge_base, EmbeddingBackend())

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the offline PDF corpus and FAISS index.")
    parser.add_argument("--pdf-dir", type=Path, default=RAW_DATA_DIR, help="Directory containing source PDFs")
    parser.add_argument("--skip-index-build", action="store_true", help="Only build corpus artifacts, skip FAISS index rebuild")
    parser.add_argument("--include-non-indexable", action="store_true", help="Include PDFs that are normally excluded")
    args = parser.parse_args()

    result = build_offline_pdf_corpus(
        args.pdf_dir,
        include_non_indexable=args.include_non_indexable,
        build_index=not args.skip_index_build,
    )

    print(json.dumps(asdict(result), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()

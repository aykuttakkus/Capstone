from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from server.app.core.config import DATA_DIR, FAISS_INDEX_PATH, FAISS_METADATA_PATH, RAW_CORPUS_PATH, RAW_DATA_DIR
from server.app.core.retrieval.corpus import KnowledgeBase, KnowledgeChunk
from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.faiss_store import FaissIndexStore
from server.app.services.pdf_pipeline import PDFIngestionResult, ingest_pdf_directory
from server.app.utils.io import load_json


def _resolve_output_path(path: Path, staging_root: Path | None = None) -> Path:
    if staging_root is None:
        return path
    try:
        return staging_root / path.relative_to(DATA_DIR)
    except ValueError:
        return staging_root / path.name


def _load_knowledge_base_for_index(processed_corpus_path: Path) -> KnowledgeBase:
    raw = load_json(RAW_CORPUS_PATH, default=[])
    processed = load_json(processed_corpus_path, default=[])
    merged = [*raw, *processed]
    return KnowledgeBase(chunks=[KnowledgeChunk.from_dict(item) for item in merged])


def build_offline_pdf_corpus(
    pdf_dir: Path,
    *,
    include_non_indexable: bool = False,
    build_index: bool = True,
    dry_run: bool = False,
    staging_root: Path | None = None,
    index_path: Path = FAISS_INDEX_PATH,
    metadata_path: Path = FAISS_METADATA_PATH,
) -> PDFIngestionResult:
    """Run PDF ingestion outside the chat request path."""
    staging_root = Path(staging_root) if staging_root is not None else None
    result = ingest_pdf_directory(
        pdf_dir,
        include_non_indexable=include_non_indexable,
        dry_run=dry_run,
        staging_root=staging_root,
    )

    if build_index and not dry_run:
        knowledge_base = _load_knowledge_base_for_index(result.processed_corpus_path)
        resolved_index_path = _resolve_output_path(Path(index_path), staging_root)
        resolved_metadata_path = _resolve_output_path(Path(metadata_path), staging_root)
        index_store = FaissIndexStore(resolved_index_path, resolved_metadata_path)
        index_store.build(knowledge_base, EmbeddingBackend())

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the offline PDF corpus and FAISS index.")
    parser.add_argument("--pdf-dir", type=Path, default=RAW_DATA_DIR, help="Directory containing source PDFs")
    parser.add_argument("--skip-index-build", action="store_true", help="Only build corpus artifacts, skip FAISS index rebuild")
    parser.add_argument("--include-non-indexable", action="store_true", help="Include PDFs that are normally excluded")
    parser.add_argument("--dry-run", action="store_true", help="Compute ingestion outputs without writing artifacts or building the index")
    parser.add_argument("--staging-root", type=Path, default=None, help="Write corpus and index artifacts under a staging directory")
    parser.add_argument("--index-path", type=Path, default=FAISS_INDEX_PATH, help="Override the FAISS index destination")
    parser.add_argument("--metadata-path", type=Path, default=FAISS_METADATA_PATH, help="Override the FAISS metadata destination")
    args = parser.parse_args()

    result = build_offline_pdf_corpus(
        args.pdf_dir,
        include_non_indexable=args.include_non_indexable,
        build_index=not args.skip_index_build,
        dry_run=args.dry_run,
        staging_root=args.staging_root,
        index_path=args.index_path,
        metadata_path=args.metadata_path,
    )

    print(json.dumps(asdict(result), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()

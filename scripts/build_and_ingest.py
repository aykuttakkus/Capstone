"""
scripts/build_and_ingest.py
============================
PDF → corpus → FAISS + Qdrant tam pipeline tek komutla.

Kullanım:
    python scripts/build_and_ingest.py [seçenekler]

Seçenekler:
    --pdf-dir PATH             PDF dizini (varsayılan: data/raw)
    --reset-collection         Qdrant koleksiyonunu sıfırla
    --dry-run                  PDF ingestion'ı çalıştır, index oluşturma
    --faiss-only               Sadece FAISS indexi oluştur (Qdrant atla)
    --qdrant-only              Sadece Qdrant indexi oluştur (FAISS atla)
    --contextual-prefix-local  Ollama ile contextual prefix ekle
    --contextual-prefix-claude Anthropic API ile contextual prefix ekle
"""
from __future__ import annotations

import argparse
import dataclasses
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from server.app.core.config import (
    FAISS_INDEX_PATH,
    FAISS_METADATA_PATH,
    PDF_SOURCE_DIR,
    QDRANT_COLLECTION,
    QDRANT_URL,
)
from server.app.core.retrieval.corpus import KnowledgeBase, KnowledgeChunk
from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.faiss_store import FaissIndexStore
from server.app.core.retrieval.qdrant_store import QdrantStore
from server.app.services.pdf_pipeline import ingest_pdf_directory


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calma full RAG pipeline")
    parser.add_argument("--pdf-dir", type=Path, default=PDF_SOURCE_DIR)
    parser.add_argument("--reset-collection", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--faiss-only", action="store_true")
    parser.add_argument("--qdrant-only", action="store_true")
    parser.add_argument("--contextual-prefix-local", action="store_true")
    parser.add_argument("--contextual-prefix-claude", action="store_true")
    return parser.parse_args()


def _maybe_add_contextual_prefix(
    chunks: list[KnowledgeChunk],
    *,
    use_local: bool = False,
    use_claude: bool = False,
) -> list[KnowledgeChunk]:
    if not (use_local or use_claude):
        return chunks

    try:
        from server.app.core.retrieval.ingestion.contextual_prefix import add_contextual_prefix  # type: ignore
    except ImportError:
        print("  UYARI: contextual_prefix modülü bulunamadı — atlandı.")
        return chunks

    updated = []
    for i, chunk in enumerate(chunks, start=1):
        if i % 50 == 0:
            print(f"  Contextual prefix: {i}/{len(chunks)}")
        updated.append(
            add_contextual_prefix(chunk, use_local=use_local, use_claude=use_claude)
        )
    return updated


def main() -> None:
    args = _parse_args()

    print("=" * 60)
    print("  Calma — Full RAG Pipeline")
    print("=" * 60)

    # Adım 1: PDF ingestion
    print(f"\n[1/5] PDF ingestion başlatılıyor: {args.pdf_dir}")
    t0 = time.time()
    result = ingest_pdf_directory(args.pdf_dir)
    print(f"      Toplam PDF    : {result.total_pdfs}")
    print(f"      Indexlenen    : {result.indexed_pdfs}")
    print(f"      Atlanan       : {result.skipped_pdfs}")
    print(f"      Toplam chunk  : {result.total_chunks}")
    print(f"      Corpus version: {result.version}")
    print(f"      Süre          : {time.time() - t0:.1f}s")

    if args.dry_run:
        print("\n[DRY-RUN] Index adımları atlandı.")
        return

    # Adım 2: KnowledgeBase yükleme
    print("\n[2/5] KnowledgeBase yükleniyor...")
    kb = KnowledgeBase.load()
    print(f"      {len(kb.chunks)} chunk yüklendi")

    # Adım 3: Contextual prefix (opsiyonel)
    if args.contextual_prefix_local or args.contextual_prefix_claude:
        print("\n[3/5] Contextual prefix ekleniyor...")
        t0 = time.time()
        enriched_chunks = _maybe_add_contextual_prefix(
            kb.chunks,
            use_local=args.contextual_prefix_local,
            use_claude=args.contextual_prefix_claude,
        )
        print(f"      Tamamlandı — {time.time() - t0:.1f}s")
        # KnowledgeBase yeniden oluştur
        from server.app.core.retrieval.corpus import KnowledgeBase as KB2  # noqa: PLC0415
        kb = KB2(chunks=enriched_chunks)
    else:
        print("\n[3/5] Contextual prefix atlandı (--contextual-prefix-local/claude ile aktifleştirilebilir).")

    # Adım 4: Embedding modeli yükleme
    print("\n[4/5] Embedding modeli yükleniyor (BGE-M3)...")
    t0 = time.time()
    embedder = EmbeddingBackend()
    print(f"      Boyut  : {embedder.dimension}")
    print(f"      Neural : {embedder.is_neural}")
    print(f"      Sparse : {embedder.sparse_available}")
    print(f"      Süre   : {time.time() - t0:.1f}s")

    # Adım 5a: FAISS
    if not args.qdrant_only:
        print("\n[5a/5] FAISS index oluşturuluyor...")
        faiss_store = FaissIndexStore(
            index_path=FAISS_INDEX_PATH,
            metadata_path=FAISS_METADATA_PATH,
        )
        t0 = time.time()
        faiss_store.build(kb, embedder)
        print(f"       {len(kb.chunks)} chunk — {time.time() - t0:.1f}s")
        print(f"       {FAISS_INDEX_PATH}")

    # Adım 5b: Qdrant
    if not args.faiss_only:
        print("\n[5b/5] Qdrant index oluşturuluyor...")
        qdrant = QdrantStore(QDRANT_URL, QDRANT_COLLECTION)
        if not qdrant.available:
            print(f"       HATA: Qdrant erişilemiyor ({QDRANT_URL})")
            print("       docker compose up qdrant -d komutunu çalıştırın.")
        else:
            qdrant.ensure_collection(embedder.dimension, reset=args.reset_collection)
            t0 = time.time()
            qdrant.upsert_chunks(kb.chunks, embedder)
            print(f"       {len(kb.chunks)} chunk Qdrant'a yüklendi — {time.time() - t0:.1f}s")

            # Smoke test
            q_dense = embedder.embed("stres ve kaygı")
            q_sparse = embedder.embed_sparse("stres ve kaygı") if embedder.sparse_available else {}
            hits = qdrant.hybrid_search(q_dense, q_sparse, k=2)
            if hits:
                print("       Smoke test OK:")
                for chunk, score in hits:
                    print(f"         [{score:.3f}] {chunk.title}")
            else:
                print("       UYARI: Smoke test sonuç döndürmedi.")

    print("\n" + "=" * 60)
    print("  Pipeline tamamlandı.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

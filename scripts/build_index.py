"""
scripts/build_index.py
======================
One-shot script to (re)build the FAISS vector index from the knowledge base.

Usage:
    python scripts/build_index.py

Options (environment variables):
    RAW_CORPUS_PATH   Path to the raw JSON knowledge base
    EMBEDDING_MODEL   sentence-transformers model name (default: all-MiniLM-L6-v2)
"""
from __future__ import annotations

import sys
import time
from collections import Counter
from pathlib import Path

# Make sure the project root is on the Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from server.app.core.config import FAISS_INDEX_PATH, FAISS_METADATA_PATH
from server.app.core.retrieval.corpus import KnowledgeBase
from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.faiss_store import FaissIndexStore


def main() -> None:
    print("=" * 60)
    print("Psychology RAG Assistant — Index Builder")
    print("=" * 60)

    # 1. Load knowledge base
    print("\n[1/4] Loading knowledge base from merged corpus")
    kb = KnowledgeBase.load()
    print(f"      Loaded {len(kb.chunks)} chunks")

    topic_counts = Counter(chunk.topic for chunk in kb.chunks)
    for topic, count in sorted(topic_counts.items()):
        print(f"        {topic}: {count} chunks")

    # 2. Load embedding model
    print("\n[2/4] Loading embedding model...")
    t0 = time.time()
    embedder = EmbeddingBackend()
    elapsed = time.time() - t0
    backend_type = "sentence-transformers (neural)" if embedder.is_neural else "hash fallback (no ML)"
    print(f"      Backend  : {backend_type}")
    print(f"      Dimension: {embedder.dimension}")
    print(f"      Load time: {elapsed:.1f}s")

    # 3. Build index
    print(f"\n[3/4] Building FAISS index...")
    store = FaissIndexStore(
        index_path=FAISS_INDEX_PATH,
        metadata_path=FAISS_METADATA_PATH,
    )
    t0 = time.time()
    store.build(kb, embedder)
    elapsed = time.time() - t0
    print(f"      Indexed   : {len(kb.chunks)} chunks in {elapsed:.1f}s")
    print(f"      Index file: {FAISS_INDEX_PATH}")
    print(f"      Metadata  : {FAISS_METADATA_PATH}")

    # 4. Quick smoke test
    print("\n[4/4] Smoke test — query: 'I feel anxious and stressed'")
    test_query = "I feel anxious and stressed"
    q_emb = embedder.embed(test_query)
    results = store.search(q_emb, topic="stress_anxiety", k=3)
    if results:
        print("      Top results:")
        for chunk, score in results:
            print(f"        [{score:.3f}] {chunk.title}  ({chunk.topic})")
    else:
        print("      WARNING: No results returned — check embedding or index.")

    print("\n✅  Index build complete.\n")


if __name__ == "__main__":
    main()

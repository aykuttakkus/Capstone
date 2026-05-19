"""
Rebuild FAISS index by extracting existing vectors for clean chunks.
No re-embedding needed - just extract vectors for kept chunks from old index.
"""
from __future__ import annotations

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from server.app.utils.io import load_json, save_json
from server.app.core.config import FAISS_INDEX_PATH, FAISS_METADATA_PATH
from server.app.core.retrieval.corpus import KnowledgeBase
from dataclasses import asdict

t0 = time.time()

print("Loading new (clean) knowledge base...", flush=True)
kb = KnowledgeBase.load()
print(f"New KB: {len(kb.chunks)} chunks", flush=True)

print("Loading old FAISS metadata...", flush=True)
old_meta = load_json(FAISS_METADATA_PATH, default={})
old_records = old_meta.get("records", []) if isinstance(old_meta, dict) else old_meta
print(f"Old metadata: {len(old_records)} records", flush=True)

print("Loading old FAISS vectors...", flush=True)
import faiss
old_index = faiss.read_index(str(FAISS_INDEX_PATH))
dim = old_index.d
n = old_index.ntotal
print(f"Old index: {n} vectors, dim={dim}", flush=True)
old_vectors = np.zeros((n, dim), dtype=np.float32)
old_index.reconstruct_n(0, n, old_vectors)
print("Vectors extracted", flush=True)

# Build matching key from old records
print("Building old content map...", flush=True)
content_to_pos: dict[str, int] = {}
for pos, rec in enumerate(old_records):
    title_val = str(rec.get("title", ""))
    content_val = str(rec.get("content", ""))[:80]
    pdf_val = str(rec.get("pdf_file", ""))
    key = f"{title_val}::{content_val}::{pdf_val}"
    content_to_pos[key] = pos
print(f"Old map size: {len(content_to_pos)}", flush=True)

# Match new chunks to old vector positions
print("Matching new chunks to old vectors...", flush=True)
matched_vectors: list[np.ndarray] = []
matched_records: list[dict] = []
missing: list[str] = []

for chunk in kb.chunks:
    key = f"{chunk.title}::{chunk.content[:80]}::{chunk.pdf_file}"
    pos = content_to_pos.get(key)
    if pos is not None:
        matched_vectors.append(old_vectors[pos])
        matched_records.append(asdict(chunk))
    else:
        missing.append(chunk.title[:60])

print(f"Matched: {len(matched_vectors)}, Missing: {len(missing)}", flush=True)
if missing[:5]:
    print(f"First missing titles: {missing[:5]}", flush=True)

if not matched_vectors:
    print("ERROR: No matches found! Aborting.", flush=True)
    sys.exit(1)

print(f"Building new FAISS index with {len(matched_vectors)} vectors...", flush=True)
new_matrix = np.vstack(matched_vectors).astype(np.float32)
faiss.normalize_L2(new_matrix)
new_idx = faiss.IndexFlatIP(dim)
new_idx.add(new_matrix)
FAISS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
faiss.write_index(new_idx, str(FAISS_INDEX_PATH))
print(f"FAISS index saved: {new_idx.ntotal} vectors", flush=True)

save_json(FAISS_METADATA_PATH, {
    "signature": kb.signature(),
    "dimension": dim,
    "chunk_count": len(matched_records),
    "records": matched_records,
})
print(f"Metadata saved: {len(matched_records)} records", flush=True)
print(f"REBUILD_COMPLETE in {time.time() - t0:.1f}s!", flush=True)

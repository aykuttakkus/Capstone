#!/usr/bin/env python3
"""Build FAISS indexes for 4-index retrieval system."""

import json
import pickle
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss

def build_faiss_indexes():
    """Build FAISS indexes from chunked data."""
    chunks_dir = Path("/Users/aykutakkus/Desktop/Projects/Capstone/data/indexes")
    output_dir = Path("/Users/aykutakkus/Desktop/Projects/Capstone/data/faiss_indexes")
    output_dir.mkdir(exist_ok=True)

    # Load embedding model
    print("Loading embedding model (multilingual-e5-large)...")
    model = SentenceTransformer("intfloat/multilingual-e5-large")
    embedding_dim = model.get_sentence_embedding_dimension()
    print(f"Embedding dimension: {embedding_dim}\n")

    index_names = [
        "psychoeducation_index",
        "coping_skills_index",
        "safety_crisis_index",
        "methodology_index",
    ]

    stats = {}

    for index_name in index_names:
        chunks_file = chunks_dir / f"{index_name}_chunks.jsonl"
        if not chunks_file.exists():
            print(f"⚠️  {index_name}: chunks file not found")
            continue

        print(f"Building {index_name}...")
        print(f"  Reading chunks...", end=" ", flush=True)

        # Load chunks
        chunks = []
        chunk_ids = []
        chunk_texts = []

        with open(chunks_file) as f:
            for line in f:
                chunk = json.loads(line)
                chunks.append(chunk)
                chunk_ids.append(chunk["id"])
                # Use title + content for embedding
                text = f"{chunk.get('title', '')} {chunk.get('content', '')}"
                chunk_texts.append(text)

        print(f"{len(chunks)} chunks")
        print(f"  Creating embeddings...", end=" ", flush=True)

        # Create embeddings in batches
        embeddings = []
        batch_size = 32
        for i in range(0, len(chunk_texts), batch_size):
            batch = chunk_texts[i:i+batch_size]
            batch_embeddings = model.encode(batch, convert_to_numpy=True)
            embeddings.extend(batch_embeddings)
            if (i + batch_size) % 128 == 0:
                print(f"{i+batch_size}", end=" ", flush=True)

        embeddings = np.array(embeddings, dtype=np.float32)
        print(f"done")

        # Build FAISS index
        print(f"  Building FAISS index...", end=" ", flush=True)
        index = faiss.IndexFlatL2(embedding_dim)
        index.add(embeddings)
        print(f"done")

        # Save index
        index_file = output_dir / f"{index_name}.faiss"
        faiss.write_index(index, str(index_file))

        # Save metadata
        metadata = {
            "index_name": index_name,
            "chunk_count": len(chunks),
            "embedding_model": "intfloat/multilingual-e5-large",
            "embedding_dim": embedding_dim,
            "chunk_ids": chunk_ids,
        }
        metadata_file = output_dir / f"{index_name}_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        # Save chunks (for retrieval)
        chunks_file = output_dir / f"{index_name}_chunks.pkl"
        with open(chunks_file, "wb") as f:
            pickle.dump(chunks, f)

        stats[index_name] = len(chunks)
        print(f"  Saved to {output_dir}\n")

    # Summary
    print("="*60)
    print("FAISS Indexes Built Successfully")
    print("="*60)
    for name, count in stats.items():
        print(f"  {name}: {count} chunks")
    print(f"\nOutput directory: {output_dir}")


if __name__ == "__main__":
    build_faiss_indexes()

#!/usr/bin/env python3
"""Build 4 separate FAISS indexes from 6,302 knowledge chunks."""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from server.app.core.retrieval.corpus import KnowledgeChunk


def build_4_indexes():
    """Build separate indexes for each CALMA index type."""
    chunks_path = Path("/Users/aykutakkus/Desktop/Projects/Capstone/data/knowledge_chunks.jsonl")
    output_dir = Path("/Users/aykutakkus/Desktop/Projects/Capstone/data/indexes")
    output_dir.mkdir(exist_ok=True)

    # Index definitions
    indexes = {
        "psychoeducation_index": {
            "description": "Educational content on mental health topics",
            "chunk_filter": lambda c: "psychoeducation_index" in c.get("allowed_indexes", []),
        },
        "coping_skills_index": {
            "description": "Practical techniques, exercises, and coping skills",
            "chunk_filter": lambda c: "coping_skills_index" in c.get("allowed_indexes", []),
        },
        "safety_crisis_index": {
            "description": "Crisis support, safety planning, emergency resources",
            "chunk_filter": lambda c: "safety_crisis_index" in c.get("allowed_indexes", []),
        },
        "methodology_index": {
            "description": "Technical documentation and RAG methodology",
            "chunk_filter": lambda c: "methodology_index" in c.get("allowed_indexes", []),
        },
    }

    # Load chunks
    chunks_by_index = {idx: [] for idx in indexes.keys()}
    total_chunks = 0

    print("Reading chunks from knowledge_chunks.jsonl...")
    with open(chunks_path) as f:
        for line_num, line in enumerate(f, 1):
            try:
                chunk_dict = json.loads(line)
                total_chunks += 1

                # Determine which indexes this chunk belongs to
                # Use source registry to determine allowed_indexes
                source_id = chunk_dict.get("id", "").split("_")[0]

                # For now, categorize based on clinical_risk and action_type
                if chunk_dict.get("clinical_risk") in ("high", "crisis"):
                    chunks_by_index["safety_crisis_index"].append(chunk_dict)
                if chunk_dict.get("action_type") in ("exercise", "self_help"):
                    chunks_by_index["coping_skills_index"].append(chunk_dict)
                if chunk_dict.get("action_type") == "explanation":
                    chunks_by_index["psychoeducation_index"].append(chunk_dict)

                # Methodology chunks
                if "methodology" in chunk_dict.get("content", "").lower():
                    chunks_by_index["methodology_index"].append(chunk_dict)

                # Default: psychoeducation for uncertain chunks
                if len([idx for idx, chunks in chunks_by_index.items() if chunk_dict in chunks]) == 0:
                    chunks_by_index["psychoeducation_index"].append(chunk_dict)

                if line_num % 500 == 0:
                    print(f"  Processed {line_num} chunks...")

            except json.JSONDecodeError as e:
                print(f"  Error parsing line {line_num}: {e}")

    print(f"\nTotal chunks loaded: {total_chunks}")

    # Save partitioned chunks
    print("\nPartitioning chunks by index...")
    index_stats = {}
    for index_name, chunks in chunks_by_index.items():
        index_stats[index_name] = len(chunks)
        output_file = output_dir / f"{index_name}_chunks.jsonl"

        with open(output_file, "w") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk) + "\n")

        print(f"  {index_name}: {len(chunks)} chunks → {output_file.name}")

    # Create index metadata
    metadata = {
        "version": "2.0",
        "created": datetime.now().isoformat(),
        "total_chunks": total_chunks,
        "indexes": {
            name: {
                "description": indexes[name]["description"],
                "chunk_count": index_stats[name],
                "file": f"{name}_chunks.jsonl",
            }
            for name in indexes.keys()
        },
    }

    metadata_file = output_dir / "index_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Index Metadata Summary:")
    print(f"  Total chunks: {total_chunks}")
    for name, count in sorted(index_stats.items()):
        pct = 100.0 * count / total_chunks if total_chunks > 0 else 0
        print(f"  {name}: {count:5d} chunks ({pct:.1f}%)")
    print(f"\nMetadata file: {metadata_file}")
    print(f"Saved to: {output_dir}")


if __name__ == "__main__":
    build_4_indexes()

"""FAISS-based multi-index retriever."""

import json
import pickle
from pathlib import Path
from typing import List, Tuple
import numpy as np
import faiss
from dataclasses import dataclass

from .embedding_service import EmbeddingService


@dataclass
class RetrievedChunk:
    """Retrieved chunk with metadata."""
    id: str
    content: str
    title: str
    source: str
    score: float
    index: str
    clinical_risk: str
    allowed_use: List[str]


class FAISSRetriever:
    """Multi-index FAISS retriever for 4-index RAG system."""

    INDEX_NAMES = [
        "psychoeducation_index",
        "coping_skills_index",
        "safety_crisis_index",
        "methodology_index",
    ]

    def __init__(self, faiss_dir: Path, embedding_service: EmbeddingService):
        self.faiss_dir = Path(faiss_dir)
        self.embedder = embedding_service
        self.indexes = {}
        self.chunks_cache = {}
        self.metadata_cache = {}

        # Load all indexes
        self._load_indexes()

    def _load_indexes(self):
        """Load all FAISS indexes and metadata."""
        for index_name in self.INDEX_NAMES:
            index_file = self.faiss_dir / f"{index_name}.faiss"
            chunks_file = self.faiss_dir / f"{index_name}_chunks.pkl"
            metadata_file = self.faiss_dir / f"{index_name}_metadata.json"

            if not index_file.exists():
                print(f"⚠️  Index not found: {index_file}")
                continue

            # Load FAISS index
            self.indexes[index_name] = faiss.read_index(str(index_file))

            # Load chunks
            with open(chunks_file, "rb") as f:
                self.chunks_cache[index_name] = pickle.load(f)

            # Load metadata
            with open(metadata_file) as f:
                self.metadata_cache[index_name] = json.load(f)

            print(f"✓ Loaded {index_name}: {len(self.chunks_cache[index_name])} chunks")

    def retrieve(
        self,
        query: str,
        target_indexes: List[str],
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> List[RetrievedChunk]:
        """Retrieve chunks from target indexes."""
        # Embed query
        query_embedding = self.embedder.embed(query)
        query_embedding = np.array([query_embedding], dtype=np.float32)

        results = []

        for index_name in target_indexes:
            if index_name not in self.indexes:
                continue

            index = self.indexes[index_name]
            chunks = self.chunks_cache[index_name]

            # Search
            distances, indices = index.search(query_embedding, min(top_k * 2, len(chunks)))

            # Convert distances to similarity scores (L2 distance -> cosine-like)
            scores = 1.0 / (1.0 + distances[0])

            # Collect results
            for idx, score in zip(indices[0], scores):
                if idx < len(chunks) and score >= score_threshold:
                    chunk = chunks[idx]
                    results.append(
                        RetrievedChunk(
                            id=chunk["id"],
                            content=chunk["content"],
                            title=chunk.get("title", ""),
                            source=chunk.get("source", ""),
                            score=float(score),
                            index=index_name,
                            clinical_risk=chunk.get("clinical_risk", "low"),
                            allowed_use=chunk.get("allowed_use", []),
                        )
                    )

        # Sort by score and limit
        results = sorted(results, key=lambda x: x.score, reverse=True)[:top_k]
        return results

    def retrieve_with_isolation(
        self,
        query: str,
        primary_intent: str,
        risk_level: int = 0,
        top_k: int = 5,
    ) -> Tuple[List[RetrievedChunk], str]:
        """Retrieve with crisis isolation enforcement."""

        # Determine target indexes based on risk level
        if risk_level >= 3:  # High risk → crisis index only
            target_indexes = ["safety_crisis_index"]
        else:
            # Normal retrieval: psychoeducation + coping, optionally safety
            target_indexes = ["psychoeducation_index", "coping_skills_index"]
            if risk_level >= 2:
                target_indexes.append("safety_crisis_index")

        results = self.retrieve(query, target_indexes, top_k)

        isolation_status = "enforced" if risk_level >= 3 else "normal"
        return results, isolation_status

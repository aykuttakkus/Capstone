from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from server.app.core.config import DATA_DIR
from server.app.core.retrieval.embeddings import EmbeddingBackend, embed_message, embed_summary


VECTOR_STORE_DIR = DATA_DIR / "store" / "vector_store"
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_PATH = VECTOR_STORE_DIR / "session_memories.jsonl"


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    total = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for l_value, r_value in zip(left, right):
        total += l_value * r_value
        left_norm += l_value * l_value
        right_norm += r_value * r_value
    if not left_norm or not right_norm:
        return 0.0
    return total / math.sqrt(left_norm * right_norm)


@dataclass(slots=True)
class VectorMemoryRecord:
    user_id: int
    session_id: int
    summary: str
    embedding: list[float]
    metadata: dict[str, Any]
    created_at: str


class TherapeuticVectorStore:
    def __init__(self, path: Path | None = None, embedder: EmbeddingBackend | None = None) -> None:
        self.path = path or VECTOR_STORE_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.embedder = embedder or EmbeddingBackend()

    def add_session_memory(
        self,
        user_id: int,
        session_id: int,
        summary: str,
        embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        record = VectorMemoryRecord(
            user_id=user_id,
            session_id=session_id,
            summary=summary,
            embedding=embedding or embed_summary(summary),
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    def retrieve_relevant(self, user_id: int, query_text: str, n_results: int = 3) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        query_embedding = embed_message(query_text)
        ranked: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    record = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                if int(record.get("user_id", -1)) != user_id:
                    continue
                score = _cosine_similarity(query_embedding, list(record.get("embedding", [])))
                ranked.append({**record, "score": round(score, 4)})

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[: max(1, n_results)]


vector_memory_store = TherapeuticVectorStore()

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from server.app.core.retrieval.corpus import KnowledgeBase, KnowledgeChunk
from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.utils.io import load_json, save_json
from server.app.utils.text import tokenize


@dataclass(slots=True)
class VectorRecord:
    chunk: KnowledgeChunk
    embedding: list[float]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sum(a * a for a in left) ** 0.5
    right_norm = sum(b * b for b in right) ** 0.5
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


class VectorIndexStore:
    def __init__(self, path: Path, backend: EmbeddingBackend | None = None) -> None:
        self.path = path
        self.backend = backend or EmbeddingBackend()

    def build(self, knowledge_base: KnowledgeBase) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for chunk in knowledge_base.chunks:
            text = f"{chunk.title} {chunk.content} {' '.join(chunk.keywords)}"
            records.append({"chunk": asdict(chunk), "embedding": self.backend.embed(text)})

        save_json(self.path, records)
        return records

    def load(self) -> list[VectorRecord]:
        raw = load_json(self.path, default=[])
        records: list[VectorRecord] = []
        for item in raw:
            chunk = KnowledgeChunk.from_dict(item.get("chunk", {}))
            embedding = [float(value) for value in item.get("embedding", [])]
            records.append(VectorRecord(chunk=chunk, embedding=embedding))
        return records

    def search(self, query: str, topic: str | None = None, k: int = 3) -> list[tuple[VectorRecord, float]]:
        query_embedding = self.backend.embed(query)
        records = self.load()
        scored: list[tuple[VectorRecord, float]] = []

        for record in records:
            similarity = cosine_similarity(query_embedding, record.embedding)
            keyword_bonus = 0.0
            if topic and record.chunk.topic == topic:
                keyword_bonus += 0.15
            if set(tokenize(topic or "")) & set(tokenize(record.chunk.topic)):
                keyword_bonus += 0.05
            scored.append((record, similarity + keyword_bonus))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:k]

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from server.app.core.retrieval.corpus import KnowledgeBase, KnowledgeChunk, metadata_matches_filters
from server.app.utils.io import load_json, save_json


@dataclass(slots=True)
class FaissRecord:
    chunk: KnowledgeChunk
    embedding: list[float]


class FaissIndexStore:
    def __init__(self, index_path: Path, metadata_path: Path) -> None:
        self.index_path = index_path
        self.metadata_path = metadata_path
        self._faiss = None
        self._numpy_index: np.ndarray | None = None
        self._metadata: list[dict] = []
        self._dimension: int = 0
        self._try_import_faiss()

    @staticmethod
    def _stable_dump(payload: object) -> str:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _bundle_from_raw(raw: object) -> tuple[list[dict], dict]:
        if isinstance(raw, dict):
            records = raw.get("records", [])
            if not isinstance(records, list):
                records = []
            meta = {k: v for k, v in raw.items() if k != "records"}
            return records, meta
        if isinstance(raw, list):
            return raw, {}
        return [], {}

    @staticmethod
    def _signature_for_chunks(chunks: list[KnowledgeChunk]) -> str:
        digest = hashlib.sha256()
        digest.update(FaissIndexStore._stable_dump([asdict(chunk) for chunk in chunks]).encode("utf-8"))
        return digest.hexdigest()[:16]

    @staticmethod
    def _signature_for_payload(payload: list[dict]) -> str:
        digest = hashlib.sha256()
        digest.update(FaissIndexStore._stable_dump(payload).encode("utf-8"))
        return digest.hexdigest()[:16]

    def _try_import_faiss(self) -> None:
        try:
            import faiss as _faiss  # type: ignore
            self._faiss = _faiss
        except ImportError:
            self._faiss = None

    def build(self, knowledge_base: KnowledgeBase, embedder) -> None:  # type: ignore[no-untyped-def]
        texts = [f"{chunk.title} {chunk.content} {' '.join(chunk.keywords)}" for chunk in knowledge_base.chunks]
        embeddings: list[list[float]] = embedder.embed_many(texts)
        self._metadata = [asdict(chunk) for chunk in knowledge_base.chunks]
        self._dimension = len(embeddings[0]) if embeddings else 0
        signature = knowledge_base.signature()

        matrix = np.array(embeddings, dtype=np.float32)

        if self._faiss is not None:
            index = self._faiss.IndexFlatIP(self._dimension)
            self._faiss.normalize_L2(matrix)
            index.add(matrix)
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self._faiss.write_index(index, str(self.index_path))
        else:
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1.0, norms)
            matrix = matrix / norms
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(str(self.index_path), matrix)

        save_json(
            self.metadata_path,
            {
                "signature": signature,
                "dimension": self._dimension,
                "chunk_count": len(self._metadata),
                "records": self._metadata,
            },
        )

    def _load_metadata_bundle(self) -> tuple[list[dict], dict]:
        raw = load_json(self.metadata_path, default=[])
        return self._bundle_from_raw(raw)

    def is_stale(self, knowledge_base: KnowledgeBase) -> bool:
        records, meta = self._load_metadata_bundle()
        if not records or not self.index_path.exists():
            return True
        stored_signature = str(meta.get("signature", ""))
        current_signature = knowledge_base.signature()
        return stored_signature != current_signature

    @staticmethod
    def _matches_filters(
        chunk: KnowledgeChunk,
        *,
        topic: str | None = None,
        source_kind: str | None = None,
        language: str | None = None,
        min_confidence: float | None = None,
        intent: str | None = None,
        risk_level: str | None = None,
        allowed_use: list[str] | None = None,
        exclude_not_allowed: list[str] | None = None,
        min_evidence_level: str | None = None,
        freshness_required: bool = False,
        clinical_scope: str | None = None,
    ) -> bool:
        if topic and chunk.topic != topic and not any(part in chunk.topic for part in topic.split("_") if part):
            return False
        if source_kind and chunk.source_kind != source_kind:
            return False
        if language and chunk.language != language:
            return False
        if min_confidence is not None and chunk.confidence < min_confidence:
            return False
        if not metadata_matches_filters(
            chunk,
            intent=intent,
            risk_level=risk_level,
            allowed_use=allowed_use,
            exclude_not_allowed=exclude_not_allowed,
            min_evidence_level=min_evidence_level,
            freshness_required=freshness_required,
            clinical_scope=clinical_scope,
        ):
            return False
        return True

    def search(
        self,
        query_embedding: list[float],
        topic: str | None = None,
        k: int = 5,
        *,
        source_kind: str | None = None,
        language: str | None = None,
        min_confidence: float | None = None,
        intent: str | None = None,
        risk_level: str | None = None,
        allowed_use: list[str] | None = None,
        exclude_not_allowed: list[str] | None = None,
        min_evidence_level: str | None = None,
        freshness_required: bool = False,
        clinical_scope: str | None = None,
    ) -> list[tuple[KnowledgeChunk, float]]:
        metadata, _ = self._load_metadata_bundle()
        if not metadata:
            return []

        q = np.array([query_embedding], dtype=np.float32)

        if self._faiss is not None and self.index_path.exists():
            try:
                index = self._faiss.read_index(str(self.index_path))
                self._faiss.normalize_L2(q)
                scores, indices = index.search(q, min(k * 2, len(metadata)))
                results = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx < 0:
                        continue
                    chunk = KnowledgeChunk.from_dict(metadata[idx])
                    if not self._matches_filters(
                        chunk,
                        topic=topic,
                        source_kind=source_kind,
                        language=language,
                        min_confidence=min_confidence,
                        intent=intent,
                        risk_level=risk_level,
                        allowed_use=allowed_use,
                        exclude_not_allowed=exclude_not_allowed,
                        min_evidence_level=min_evidence_level,
                        freshness_required=freshness_required,
                        clinical_scope=clinical_scope,
                    ):
                        continue
                    topic_bonus = self._topic_bonus(chunk.topic, topic)
                    results.append((chunk, float(score) + topic_bonus))
                results.sort(key=lambda x: x[1], reverse=True)
                return results[:k]
            except Exception:
                pass

        npy_path = self.index_path.with_suffix(".npy") if self.index_path.suffix != ".npy" else self.index_path
        if not npy_path.exists():
            return []

        matrix = np.load(str(npy_path))
        q_norm = q / (np.linalg.norm(q) or 1.0)
        scores_arr = (matrix @ q_norm.T).flatten()

        top_indices = np.argsort(-scores_arr)[: k * 2]
        results = []
        for idx in top_indices:
            if idx >= len(metadata):
                continue
            chunk = KnowledgeChunk.from_dict(metadata[int(idx)])
            if not self._matches_filters(
                chunk,
                topic=topic,
                source_kind=source_kind,
                language=language,
                min_confidence=min_confidence,
                intent=intent,
                risk_level=risk_level,
                allowed_use=allowed_use,
                exclude_not_allowed=exclude_not_allowed,
                min_evidence_level=min_evidence_level,
                freshness_required=freshness_required,
                clinical_scope=clinical_scope,
            ):
                continue
            topic_bonus = self._topic_bonus(chunk.topic, topic)
            results.append((chunk, float(scores_arr[idx]) + topic_bonus))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]

    def load_or_build(self, knowledge_base: KnowledgeBase, embedder) -> None:  # type: ignore[no-untyped-def]
        """Build index if missing or stale; otherwise rely on lazy-load in search()."""
        if self.is_stale(knowledge_base):
            self.build(knowledge_base, embedder)

    @staticmethod
    def _topic_bonus(chunk_topic: str, query_topic: str | None) -> float:
        if not query_topic:
            return 0.0
        if chunk_topic == query_topic:
            return 0.12
        if any(part in chunk_topic for part in query_topic.split("_")):
            return 0.04
        return 0.0

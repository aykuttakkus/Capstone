from __future__ import annotations

import json
import os

from server.app.core.retrieval.retriever import ScoredChunk, topic_matches


class EvidenceGate:
    def __init__(self, min_score: float | None = None, min_chunks: int | None = None) -> None:
        self.min_score = min_score if min_score is not None else float(os.getenv("EVIDENCE_MIN_SCORE", "0.22"))
        self.min_chunks = min_chunks if min_chunks is not None else int(os.getenv("EVIDENCE_MIN_CHUNKS", "1"))
        self.taxonomy = self._load_taxonomy()

    def has_enough_evidence(self, results: list[ScoredChunk], topic: str | None = None) -> bool:
        if not results:
            return False
        if topic in (None, "", "general"):
            candidates = results
        else:
            candidates = [r for r in results if topic_matches(topic, r.chunk.topic)]
            if not candidates:
                return False

        above = sum(1 for r in candidates if r.score >= self.min_score)
        return above >= self.min_chunks

    def gate_score(self, results: list[ScoredChunk]) -> float:
        return results[0].score if results else 0.0

    def _load_taxonomy(self) -> dict:
        try:
            path = os.path.join(os.path.dirname(__file__), "../../..", "data", "knowledge_base_taxonomy.json")
            with open(path) as f:
                return json.load(f)
        except Exception:
            return {"topics": []}

    def filter_by_intent(self, results: list[ScoredChunk], intent: str) -> list[ScoredChunk]:
        if not intent or intent == "unknown":
            return results

        intent_map = {
            "psychoeducation": ["psychoeducation"],
            "coping_strategy": ["coping_strategy"],
            "symptom_exploration": ["symptom_exploration"],
            "emotional_support": ["emotional_support"],
            "clarification": ["clarification"],
        }

        allowed_uses = intent_map.get(intent, [])
        if not allowed_uses:
            return results

        filtered = []
        for chunk in results:
            topic_id = self._get_topic_id(chunk.chunk.topic)
            if self._is_use_allowed(topic_id, intent):
                filtered.append(chunk)

        return filtered if filtered else results

    def filter_by_risk_level(self, results: list[ScoredChunk], risk_level: int) -> list[ScoredChunk]:
        if risk_level < 2:
            return results

        crisis_topics = {"grief_loss", "rumination", "anxiety", "depression"}
        filtered = []

        for chunk in results:
            topic_id = self._get_topic_id(chunk.chunk.topic)
            if topic_id not in crisis_topics or risk_level >= 3:
                filtered.append(chunk)

        return filtered if filtered else results

    def _get_topic_id(self, topic: str) -> str | None:
        if not self.taxonomy or "topics" not in self.taxonomy:
            return None

        topic_lower = topic.lower() if topic else ""
        for topic_entry in self.taxonomy["topics"]:
            if topic_entry.get("topic_id", "") == topic_lower:
                return topic_entry.get("topic_id")

        return None

    def _is_use_allowed(self, topic_id: str | None, intent: str) -> bool:
        if not topic_id or not self.taxonomy:
            return True

        for topic_entry in self.taxonomy["topics"]:
            if topic_entry.get("topic_id") == topic_id:
                allowed = topic_entry.get("allowed_uses", [])
                return intent in allowed

        return True

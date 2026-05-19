"""Multi-index retrieval architecture — spec §9, §604.

Four isolated FAISS stores route queries by intent and risk level:

  psychoeducation_index  — factual information, definitions
  coping_skills_index    — techniques and exercises
  safety_crisis_index    — RESTRICTED: crisis content only at risk >= HIGH
  methodology_index      — academic/thesis content

This replaces the monolithic single FAISS approach and guarantees
crisis content never leaks into normal conversation retrieval.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from server.app.core.retrieval.corpus import KnowledgeBase, KnowledgeChunk, metadata_matches_filters
from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.faiss_store import FaissIndexStore
from server.app.core.retrieval.retriever import ScoredChunk, SimpleRetriever


# ── Index routing constants ────────────────────────────────────────────────────

INDEX_PSYCHOEDUCATION = "psychoeducation_index"
INDEX_COPING = "coping_skills_index"
INDEX_SAFETY_CRISIS = "safety_crisis_index"
INDEX_METHODOLOGY = "methodology_index"

# Minimum risk_level (integer 0-5) to allow safety_crisis_index access
CRISIS_INDEX_MIN_RISK = 3

# Intent → preferred indexes (in priority order)
_INTENT_INDEX_MAP: dict[str, list[str]] = {
    "psychoeducation": [INDEX_PSYCHOEDUCATION, INDEX_COPING],
    "coping_strategy": [INDEX_COPING, INDEX_PSYCHOEDUCATION],
    "symptom_exploration": [INDEX_PSYCHOEDUCATION],
    "emotional_support": [INDEX_PSYCHOEDUCATION, INDEX_COPING],
    "clarification": [INDEX_PSYCHOEDUCATION],
    "clarification_needed": [INDEX_PSYCHOEDUCATION],
    "repair": [],
    "off_scope": [],
    "crisis": [INDEX_SAFETY_CRISIS],
    "methodology": [INDEX_METHODOLOGY],
}

# chunk_type → preferred index
_CHUNK_TYPE_INDEX_MAP: dict[str, str] = {
    "definition": INDEX_PSYCHOEDUCATION,
    "mechanism": INDEX_PSYCHOEDUCATION,
    "psychoeducation": INDEX_PSYCHOEDUCATION,
    "explanation": INDEX_PSYCHOEDUCATION,
    "symptom": INDEX_PSYCHOEDUCATION,
    "coping_step": INDEX_COPING,
    "exercise": INDEX_COPING,
    "grounding": INDEX_COPING,
    "breathing": INDEX_COPING,
    "self_help": INDEX_COPING,
    "crisis_instruction": INDEX_SAFETY_CRISIS,
    "safety_plan": INDEX_SAFETY_CRISIS,
    "crisis_resource": INDEX_SAFETY_CRISIS,
    "methodology": INDEX_METHODOLOGY,
}


@dataclass(slots=True)
class EvidencePack:
    """Structured retrieval output — spec Phase C output contract."""

    user_query: str
    intent: str
    risk_level: int
    retrieval_confidence: float
    confidence_action: str  # strong_evidence | usable_evidence_cautious | weak_evidence_general_only | fallback
    source_quality: str     # high | medium | low | none
    evidence: list[EvidenceItem]
    indexes_queried: list[str]
    warnings: list[str] = field(default_factory=list)
    metadata_match_ratio: float = 0.0


@dataclass(slots=True)
class EvidenceItem:
    """Single retrieved chunk with full provenance."""

    chunk_id: str
    text: str
    source_title: str
    organization: str
    evidence_level: str
    chunk_type: str          # action_type from KnowledgeChunk
    allowed_use: list[str]
    not_allowed: list[str]
    requires_disclaimer: bool
    topic: str
    score: float
    parent_id: str | None
    page: int
    section: str
    index_name: str


class MultiIndexRetriever:
    """Four-index retriever with intent-based routing and safety isolation."""

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        store_root: Path | None = None,
        embedder: EmbeddingBackend | None = None,
    ) -> None:
        self.knowledge_base = knowledge_base
        self.embedder = embedder or EmbeddingBackend()
        self.store_root = store_root or self._default_store_root()

        # Build per-index sub-bases and FAISS stores
        self._indexes: dict[str, FaissIndexStore] = {}
        self._sub_bases: dict[str, KnowledgeBase] = {}
        self._keyword_retrievers: dict[str, SimpleRetriever] = {}
        self._source_registry = self._load_source_registry()
        self._initialise_indexes()

    # ── Public API ────────────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        intent: str,
        risk_level: int = 0,
        topic: str | None = None,
        k: int = 8,
        language: str | None = None,
    ) -> EvidencePack:
        """Route query to correct indexes and return a structured EvidencePack."""
        warnings: list[str] = []
        target_indexes = self._select_indexes(intent, risk_level)

        if not target_indexes:
            return EvidencePack(
                user_query=query,
                intent=intent,
                risk_level=risk_level,
                retrieval_confidence=0.0,
                confidence_action="fallback",
                source_quality="none",
                evidence=[],
                indexes_queried=[],
                warnings=["No indexes available for this intent/risk combination"],
            )

        # Gather candidates from selected indexes
        all_candidates: list[tuple[ScoredChunk, str]] = []  # (chunk, index_name)
        for idx_name in target_indexes:
            per_index_k = max(k, 4)
            candidates = self._query_index(idx_name, query, topic=topic, k=per_index_k, language=language)
            all_candidates.extend((sc, idx_name) for sc in candidates)

        # Sort by score descending, take top-k
        all_candidates.sort(key=lambda x: x[0].score, reverse=True)
        top_k = all_candidates[:k]

        if not top_k:
            return EvidencePack(
                user_query=query,
                intent=intent,
                risk_level=risk_level,
                retrieval_confidence=0.0,
                confidence_action="fallback",
                source_quality="none",
                evidence=[],
                indexes_queried=target_indexes,
                warnings=["No evidence retrieved"],
            )

        # Build evidence items
        evidence_items = [
            self._to_evidence_item(sc, idx_name)
            for sc, idx_name in top_k
        ]

        # Score the pack
        scores = [sc.score for sc, _ in top_k]
        metadata_match = self._compute_metadata_match(top_k, intent)
        retrieval_confidence, confidence_action = _calculate_retrieval_confidence(
            scores, metadata_match
        )
        source_quality = _classify_source_quality(top_k)

        return EvidencePack(
            user_query=query,
            intent=intent,
            risk_level=risk_level,
            retrieval_confidence=retrieval_confidence,
            confidence_action=confidence_action,
            source_quality=source_quality,
            evidence=evidence_items,
            indexes_queried=target_indexes,
            warnings=warnings,
            metadata_match_ratio=metadata_match,
        )

    def get_index_stats(self) -> dict[str, Any]:
        stats: dict[str, Any] = {}
        for name, sub_base in self._sub_bases.items():
            stats[name] = {
                "chunk_count": len(sub_base.chunks),
                "indexed": name in self._indexes,
            }
        return stats

    # ── Initialisation ────────────────────────────────────────────────────────

    def _initialise_indexes(self) -> None:
        """Partition corpus into 4 sub-bases and load/build FAISS stores."""
        partition = self._partition_corpus()
        for idx_name, chunks in partition.items():
            if not chunks:
                continue
            sub_base = KnowledgeBase(chunks=chunks)
            self._sub_bases[idx_name] = sub_base
            self._keyword_retrievers[idx_name] = SimpleRetriever(sub_base)

            faiss_path = self.store_root / f"{idx_name}.index"
            meta_path = self.store_root / f"{idx_name}_meta.json"
            store = FaissIndexStore(faiss_path, meta_path)
            store.load_or_build(sub_base, self.embedder)
            self._indexes[idx_name] = store

    def _partition_corpus(self) -> dict[str, list[KnowledgeChunk]]:
        """Assign each chunk to an index based on metadata and source registry."""
        partition: dict[str, list[KnowledgeChunk]] = {
            INDEX_PSYCHOEDUCATION: [],
            INDEX_COPING: [],
            INDEX_SAFETY_CRISIS: [],
            INDEX_METHODOLOGY: [],
        }

        for chunk in self.knowledge_base.chunks:
            idx = self._classify_chunk(chunk)
            partition[idx].append(chunk)

        return partition

    def _classify_chunk(self, chunk: KnowledgeChunk) -> str:
        """Determine which index a chunk belongs to."""
        # Crisis content → safety index only
        if chunk.clinical_risk in {"crisis", "high"} or chunk.risk_level in {"crisis", "high"}:
            return INDEX_SAFETY_CRISIS

        # Methodology content
        if chunk.topic in {"methodology", "AI_safety", "evaluation", "NLP", "mental_health_AI"}:
            return INDEX_METHODOLOGY
        if "methodology" in (chunk.allowed_use or []):
            return INDEX_METHODOLOGY

        # Check source registry for index assignment
        registry_idx = self._registry_index_for_source(chunk.source)
        if registry_idx:
            return registry_idx

        # action_type / content_type routing
        chunk_idx = _CHUNK_TYPE_INDEX_MAP.get(chunk.action_type, "") or _CHUNK_TYPE_INDEX_MAP.get(chunk.content_type, "")
        if chunk_idx:
            return chunk_idx

        # allowed_use routing
        allowed = chunk.allowed_use or []
        if "coping_strategy" in allowed and "psychoeducation" not in allowed:
            return INDEX_COPING
        if "coping_strategy" in allowed:
            return INDEX_COPING  # prefer coping for dual-use

        return INDEX_PSYCHOEDUCATION  # default

    def _registry_index_for_source(self, source_title: str) -> str | None:
        """Look up preferred index from source registry."""
        if not self._source_registry:
            return None
        for entry in self._source_registry.get("sources", []):
            if entry.get("title", "") in source_title or source_title in entry.get("title", ""):
                indexes = entry.get("allowed_indexes", [])
                if indexes:
                    return indexes[0]  # first = preferred
        return None

    # ── Query execution ───────────────────────────────────────────────────────

    def _query_index(
        self,
        idx_name: str,
        query: str,
        topic: str | None,
        k: int,
        language: str | None,
    ) -> list[ScoredChunk]:
        if idx_name not in self._indexes:
            # Fallback to keyword-only if FAISS not available
            return self._keyword_only(idx_name, query, topic, k, language)

        store = self._indexes[idx_name]
        query_emb = self.embedder.embed(query)

        raw_semantic = store.search(query_emb, topic=topic, k=k * 3, language=language)
        semantic = [ScoredChunk(chunk=chunk, score=score) for chunk, score in raw_semantic]
        keyword = self._keyword_only(idx_name, query, topic, k, language)

        return _merge_results(semantic, keyword, semantic_weight=0.70, keyword_weight=0.30, k=k)

    def _keyword_only(
        self,
        idx_name: str,
        query: str,
        topic: str | None,
        k: int,
        language: str | None,
    ) -> list[ScoredChunk]:
        retriever = self._keyword_retrievers.get(idx_name)
        if not retriever:
            return []
        return retriever.retrieve(query, topic=topic, k=k, language=language)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _select_indexes(self, intent: str, risk_level: int) -> list[str]:
        """Return list of index names to query, with safety isolation enforced."""
        if risk_level >= CRISIS_INDEX_MIN_RISK:
            return [INDEX_SAFETY_CRISIS]

        preferred = _INTENT_INDEX_MAP.get(intent, [INDEX_PSYCHOEDUCATION])
        # Exclude crisis index unless risk threshold met
        return [idx for idx in preferred if idx != INDEX_SAFETY_CRISIS]

    def _compute_metadata_match(self, candidates: list[tuple[ScoredChunk, str]], intent: str) -> float:
        if not candidates:
            return 0.0
        matches = sum(
            1 for sc, _ in candidates
            if intent in (sc.chunk.allowed_use or [])
        )
        return matches / len(candidates)

    @staticmethod
    def _to_evidence_item(sc: ScoredChunk, index_name: str) -> EvidenceItem:
        chunk = sc.chunk
        return EvidenceItem(
            chunk_id=chunk.id,
            text=chunk.content,
            source_title=chunk.source,
            organization=chunk.organization,
            evidence_level=chunk.evidence_level,
            chunk_type=chunk.action_type,
            allowed_use=list(chunk.allowed_use),
            not_allowed=list(chunk.not_allowed),
            requires_disclaimer=chunk.requires_disclaimer,
            topic=chunk.topic,
            score=sc.score,
            parent_id=chunk.parent_id,
            page=chunk.page,
            section=chunk.section,
            index_name=index_name,
        )

    @staticmethod
    def _default_store_root() -> Path:
        base = Path(os.environ.get("VECTOR_STORE_PATH", "data/vector_store"))
        base.mkdir(parents=True, exist_ok=True)
        return base

    @staticmethod
    def _load_source_registry() -> dict:
        try:
            reg_path = Path("data/source_registry.json")
            if reg_path.exists():
                with open(reg_path) as f:
                    return json.load(f)
        except Exception:
            pass
        return {}


# ── Scoring functions ──────────────────────────────────────────────────────────

def _calculate_retrieval_confidence(
    scores: list[float],
    metadata_match_ratio: float,
) -> tuple[float, str]:
    """Weighted confidence score and action label — spec Phase C §C4."""
    if not scores:
        return 0.0, "fallback"

    import statistics
    avg_score = statistics.mean(scores)
    stdev = statistics.stdev(scores) if len(scores) > 1 else 0.0
    max_score = max(scores)
    consistency = 1.0 - min(stdev / (avg_score + 1e-9), 1.0)

    confidence = (
        0.50 * avg_score
        + 0.20 * consistency
        + 0.30 * metadata_match_ratio
    )
    confidence = min(confidence, 1.0)

    if confidence >= 0.80:
        action = "strong_evidence"
    elif confidence >= 0.60:
        action = "usable_evidence_cautious"
    elif confidence >= 0.40:
        action = "weak_evidence_general_only"
    else:
        action = "fallback"

    return round(confidence, 3), action


def _classify_source_quality(candidates: list[tuple[ScoredChunk, str]]) -> str:
    """high | medium | low | none — mirrors EvidenceGate.source_quality()."""
    if not candidates:
        return "none"
    top_score = candidates[0][0].score
    top_chunks = [sc for sc, _ in candidates[:3]]
    has_clinical = any(
        c.chunk.evidence_level in {"clinical_guideline", "peer_reviewed", "clinical_self_help", "global_public_health"}
        for c in top_chunks
    )
    if top_score >= 0.75 and has_clinical:
        return "high"
    if top_score >= 0.50:
        return "medium"
    if top_score >= 0.25:
        return "low"
    return "none"


def _merge_results(
    semantic: list[ScoredChunk],
    keyword: list[ScoredChunk],
    semantic_weight: float,
    keyword_weight: float,
    k: int,
) -> list[ScoredChunk]:
    """Merge semantic and keyword results with weighted RRF-style fusion."""
    seen: dict[str, float] = {}

    def rrf_score(rank: int) -> float:
        return 1.0 / (60 + rank + 1)

    for rank, sc in enumerate(semantic):
        seen[sc.chunk.id] = seen.get(sc.chunk.id, 0.0) + semantic_weight * rrf_score(rank)

    for rank, sc in enumerate(keyword):
        seen[sc.chunk.id] = seen.get(sc.chunk.id, 0.0) + keyword_weight * rrf_score(rank)

    # Build id → chunk map
    chunk_map: dict[str, KnowledgeChunk] = {sc.chunk.id: sc.chunk for sc in semantic + keyword}

    merged = sorted(seen.items(), key=lambda x: x[1], reverse=True)[:k]
    return [ScoredChunk(chunk=chunk_map[cid], score=score) for cid, score in merged if cid in chunk_map]

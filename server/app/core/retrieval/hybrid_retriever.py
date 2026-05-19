from __future__ import annotations

from pathlib import Path

from server.app.core.config import ENABLE_GRAPH_RAG, GRAPH_RAG_MIN_CHUNKS, GRAPH_RAG_MIN_QUERY_TERMS, RETRIEVAL_BACKEND, QDRANT_COLLECTION, QDRANT_URL
from server.app.core.retrieval.corpus import KnowledgeBase, metadata_matches_filters
from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.faiss_store import FaissIndexStore
from server.app.core.retrieval.graph_store import GraphStore, is_graph_friendly_query, should_enable_graph_rag
from server.app.core.retrieval.qdrant_store import QdrantStore
from server.app.core.retrieval.retriever import ScoredChunk, SimpleRetriever, topic_alignment_score
from server.app.utils.text import infer_language


class HybridRetriever:
    SEMANTIC_WEIGHT: float = 0.70
    KEYWORD_WEIGHT: float = 0.30

    def __init__(self, knowledge_base: KnowledgeBase, faiss_store: FaissIndexStore, embedder: EmbeddingBackend | None = None, graph_path: Path | None = None) -> None:
        self.knowledge_base = knowledge_base
        self.faiss_store = faiss_store
        self.embedder = embedder or EmbeddingBackend()
        self.keyword_retriever = SimpleRetriever(knowledge_base)
        self.graph_store = None
        self.qdrant_store = QdrantStore(QDRANT_URL, QDRANT_COLLECTION)
        if ENABLE_GRAPH_RAG and should_enable_graph_rag(knowledge_base, GRAPH_RAG_MIN_CHUNKS):
            self.graph_store = GraphStore(storage_path=graph_path)
            if not self.graph_store.load():
                self.graph_store.build(knowledge_base)
                self.graph_store.save()

    def retrieve(
        self,
        query: str,
        topic: str | None = None,
        k: int = 8,
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
    ) -> list[ScoredChunk]:
        query_embedding = self.embedder.embed(query)
        query_language = language or infer_language(query)

        # Broaden search to find more candidates before filtering
        semantic_results = []
        if RETRIEVAL_BACKEND == "qdrant" and self.qdrant_store.available:
            semantic_results = self.qdrant_store.search_with_filters(
                query_embedding,
                topic=topic,
                k=k * 3,
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
            )
        if not semantic_results:
            semantic_results = self.faiss_store.search(
                query_embedding,
                topic=topic,
                k=k * 3,
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
            )
        keyword_results = self.keyword_retriever.retrieve(
            query,
            topic=topic,
            k=k * 3,
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
        )
        
        print(f"[DEBUG] Raw semantic results: {len(semantic_results)}, Raw keyword: {len(keyword_results)}")
        max_kw_score = max((r.score for r in keyword_results), default=1.0) or 1.0

        semantic_map: dict[str, float] = {chunk.id: score for chunk, score in semantic_results}
        keyword_map: dict[str, float] = {r.chunk.id: r.score / max_kw_score for r in keyword_results}

        graph_map: dict[str, float] = {}
        if self.graph_store is not None and is_graph_friendly_query(query, topic, min_terms=GRAPH_RAG_MIN_QUERY_TERMS):
            import re

            query_kws = re.findall(r"\w{4,}", query.lower())
            graph_ids = self.graph_store.get_related_chunks(seed_topic=topic, seed_keywords=query_kws)
            graph_map = {cid: 0.12 for cid in graph_ids}

        all_ids = sorted(set(semantic_map) | set(keyword_map) | set(graph_map))
        chunk_lookup = {chunk.id: chunk for chunk in self.knowledge_base.chunks}

        scored: list[ScoredChunk] = []
        for cid in all_ids:
            if cid not in chunk_lookup:
                continue
            if source_kind and chunk_lookup[cid].source_kind != source_kind:
                continue
            if language and chunk_lookup[cid].language != language:
                continue
            if min_confidence is not None and chunk_lookup[cid].confidence < min_confidence:
                continue
            if not metadata_matches_filters(
                chunk_lookup[cid],
                intent=intent,
                risk_level=risk_level,
                allowed_use=allowed_use,
                exclude_not_allowed=exclude_not_allowed,
                min_evidence_level=min_evidence_level,
                freshness_required=freshness_required,
                clinical_scope=clinical_scope,
            ):
                continue
            sem = semantic_map.get(cid, 0.0)
            kw = keyword_map.get(cid, 0.0)
            graph_boost = graph_map.get(cid, 0.0)
            alignment_boost = topic_alignment_score(topic, chunk_lookup[cid].topic) * 0.12
            language_boost = 0.08 if chunk_lookup[cid].language == query_language else 0.0

            combined = (self.SEMANTIC_WEIGHT * sem) + (self.KEYWORD_WEIGHT * kw) + graph_boost + alignment_boost + language_boost
            scored.append(ScoredChunk(chunk=chunk_lookup[cid], score=combined))

        scored.sort(key=lambda x: (x.score, topic_alignment_score(topic, x.chunk.topic), x.chunk.id), reverse=True)
        
        if scored:
            print(f"[DEBUG] Top retrieval score: {scored[0].score:.4f} for topic {scored[0].chunk.topic}")

        return scored[:k]

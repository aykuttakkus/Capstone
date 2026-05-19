"""
RAG Augmentation Service - 2025/2026 best-practice retrieval pipeline.

Pipeline:
1. Multi-query augmentation (3 semantic variants)
2. Hybrid retrieval per query (BM25 + Dense, already implemented)
3. Reciprocal Rank Fusion (RRF) to merge results
4. Cross-encoder re-ranking (EvidenceReranker)
5. Score threshold filtering (drop low-quality chunks)
6. Contextual compression (extract relevant sentences only)
7. Format for LLM injection

LLM (Mistral) is unaffected — it still generates all responses.
RAG only improves the knowledge quality fed into the LLM context.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from server.app.core.retrieval.hybrid_retriever import HybridRetriever
from server.app.core.retrieval.corpus import KnowledgeBase
from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.faiss_store import FaissIndexStore
from server.app.core.retrieval.reranker import EvidenceReranker
from server.app.core.retrieval.retriever import ScoredChunk
from server.app.services.user_state import UserState


@dataclass(slots=True)
class RetrievalResult:
    """Result of RAG retrieval and formatting."""

    formatted_knowledge: Optional[str]
    retrieved_chunks: list = field(default_factory=list)
    retrieval_success: bool = True
    chunk_count: int = 0
    top_score: float = 0.0


# Minimum RRF score to include a chunk after reranking.
# RRF scores are 1/(rank+60); a chunk at rank-1 across all 3 queries ≈ 0.049.
# 0.013 keeps any chunk that placed in top results of at least one query.
# The reranker (top_k=3) already handles quality — this filters absolute noise.
_MIN_SCORE_THRESHOLD = 0.013

# Maximum chunks passed to LLM — fewer, higher-quality beats many noisy chunks.
_MAX_CHUNKS_FOR_LLM = 3


class RAGAugmentationService:
    """Manages RAG retrieval with 2025/2026 best practices."""

    def __init__(self, knowledge_base: KnowledgeBase, faiss_store: FaissIndexStore):
        self.knowledge_base = knowledge_base
        self.faiss_store = faiss_store
        self.retriever = HybridRetriever(
            knowledge_base=knowledge_base,
            faiss_store=faiss_store,
            embedder=EmbeddingBackend(),
        )
        self.reranker = EvidenceReranker(top_k=_MAX_CHUNKS_FOR_LLM, max_chars=1800)

    def augment_and_retrieve(
        self,
        user_message: str,
        user_state: Optional[UserState] = None,
        conversation_context: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> RetrievalResult:
        """
        Multi-query retrieval with reranking, threshold filtering, and compression.
        """
        # Skip RAG for greetings and very short messages (no clinical content)
        if self._is_non_clinical_message(user_message):
            return RetrievalResult(
                formatted_knowledge=None,
                retrieved_chunks=[],
                retrieval_success=True,
                chunk_count=0,
                top_score=0.0,
            )

        # 1. Build augmented query (single query for latency; multi-query needs GPU)
        primary_query = self._build_primary_query(
            user_message=user_message,
            user_state=user_state,
            conversation_context=conversation_context,
        )

        # 2. Retrieve candidates
        try:
            all_chunks = self._single_retrieve(primary_query, topic=topic)
        except Exception:
            return RetrievalResult(
                formatted_knowledge=None,
                retrieved_chunks=[],
                retrieval_success=False,
                chunk_count=0,
                top_score=0.0,
            )

        if not all_chunks:
            return RetrievalResult(
                formatted_knowledge=None,
                retrieved_chunks=[],
                retrieval_success=True,
                chunk_count=0,
                top_score=0.0,
            )

        # 3. Cross-encoder rerank
        reranked = self.reranker.rerank(primary_query, all_chunks, topic=topic)

        # 4. Score threshold filtering
        filtered = [c for c in reranked if c.score >= _MIN_SCORE_THRESHOLD]

        # Fall back to top-1 if everything is below threshold but we have results
        if not filtered and reranked:
            filtered = reranked[:1]

        if not filtered:
            return RetrievalResult(
                formatted_knowledge=None,
                retrieved_chunks=[],
                retrieval_success=True,
                chunk_count=0,
                top_score=0.0,
            )

        # 5. Contextual compression + format for LLM
        formatted_knowledge = self._compress_and_format(filtered[:_MAX_CHUNKS_FOR_LLM], primary_query)

        return RetrievalResult(
            formatted_knowledge=formatted_knowledge,
            retrieved_chunks=filtered,
            retrieval_success=True,
            chunk_count=len(filtered),
            top_score=filtered[0].score,
        )

    # ── Non-clinical detection ────────────────────────────────────────────────

    @staticmethod
    def _is_non_clinical_message(message: str) -> bool:
        """
        Returns True for greetings and short messages with no clinical content.
        RAG retrieval adds noise and latency for these — skip it.
        """
        msg = message.strip().lower()

        # Very short messages (1-2 words)
        if len(msg.split()) <= 2:
            return True

        # Common greetings / small talk
        greetings = {
            "hey", "hi", "hello", "sup", "yo", "hiya", "howdy",
            "good morning", "good afternoon", "good evening", "good night",
            "thanks", "thank you", "ok", "okay", "sure", "yes", "no",
            "bye", "goodbye", "see you", "take care",
        }
        if msg in greetings or any(msg.startswith(g + " ") for g in greetings):
            return True

        return False

    # ── Query building ────────────────────────────────────────────────────────

    def _build_primary_query(
        self,
        user_message: str,
        user_state: Optional[UserState] = None,
        conversation_context: Optional[str] = None,
    ) -> str:
        """Build a single enriched query for CPU-friendly retrieval."""
        queries = self._build_multi_queries(user_message, user_state, conversation_context)
        return queries[0]

    def _single_retrieve(self, query: str, topic: Optional[str] = None) -> list[ScoredChunk]:
        """
        Single-query retrieval returning top candidates for reranking.

        min_evidence_level="peer_reviewed" ensures low_confidence and unreviewed
        content never reaches the LLM — only educational, peer-reviewed, or
        clinical-guideline sources are injected into the conversation context.
        """
        return self.retriever.retrieve(
            query=query,
            topic=topic,
            k=8,
            min_confidence=0.3,
            allowed_use=["psychoeducation", "coping_strategy", "symptom_exploration", "emotional_support"],
            min_evidence_level="educational",
        )

    def _build_multi_queries(
        self,
        user_message: str,
        user_state: Optional[UserState] = None,
        conversation_context: Optional[str] = None,
    ) -> list[str]:
        """
        Build 3 semantic query variants to improve recall via RRF.

        Q1: Direct — close to user message + profile signals
        Q2: Clinical — evidence-based framing of the same concern
        Q3: Coping-focused — what practical strategies might help
        """
        # Core signals from user state
        profile_signals = []
        if user_state:
            if user_state.primary_concerns:
                profile_signals.append(user_state.primary_concerns)
            if user_state.main_triggers:
                profile_signals.append(user_state.main_triggers)
            if user_state.journal_themes:
                profile_signals.extend(user_state.journal_themes[:2])
            if user_state.mood_pattern_tags:
                profile_signals.extend(user_state.mood_pattern_tags[:2])

        profile_str = " ".join(profile_signals) if profile_signals else ""

        # Q1: Direct user-centered query
        q1_parts = [user_message]
        if profile_str:
            q1_parts.append(profile_str)
        if conversation_context:
            # Only most relevant keywords from context
            ctx_words = [w for w in conversation_context.split() if len(w) > 4][:8]
            q1_parts.append(" ".join(ctx_words))
        q1 = " ".join(q1_parts).strip()

        # Q2: Clinical / psychoeducational framing
        topic_detected = self._detect_topic(user_message + " " + profile_str)
        clinical_terms = _CLINICAL_TERMS_MAP.get(topic_detected, "")
        q2 = f"{topic_detected} {clinical_terms} psychoeducation explanation".strip()

        # Q3: Coping-strategy focused
        coping_terms = _COPING_TERMS_MAP.get(topic_detected, "evidence-based coping strategies self-help")
        q3 = f"{topic_detected} {coping_terms}".strip()

        return [q1, q2, q3]

    @staticmethod
    def _detect_topic(text: str) -> str:
        """Quick keyword-based topic detection for query enrichment."""
        text_lower = text.lower()
        for topic, keywords in _TOPIC_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return topic
        return "mental health emotional wellbeing"

    # ── Multi-query retrieval with RRF ────────────────────────────────────────

    def _multi_query_retrieve(
        self,
        queries: list[str],
        topic: Optional[str] = None,
    ) -> list[ScoredChunk]:
        """
        Retrieve for each query, merge via Reciprocal Rank Fusion.
        RRF gives each chunk a score of 1/(rank + k) summed across queries.
        """
        RRF_K = 60  # Standard constant; smooths rank differences
        chunk_rrf_scores: dict[str, float] = {}
        chunk_lookup: dict[str, ScoredChunk] = {}

        for query in queries:
            results = self.retriever.retrieve(
                query=query,
                topic=topic,
                k=8,
                min_confidence=0.3,
                allowed_use=["psychoeducation", "coping_strategy", "symptom_exploration", "emotional_support"],
            )
            for rank, scored_chunk in enumerate(results):
                cid = scored_chunk.chunk.id
                chunk_rrf_scores[cid] = chunk_rrf_scores.get(cid, 0.0) + 1.0 / (rank + RRF_K)
                if cid not in chunk_lookup:
                    chunk_lookup[cid] = scored_chunk

        # Rebuild ScoredChunks with RRF scores for reranker input
        merged = []
        for cid, rrf_score in sorted(chunk_rrf_scores.items(), key=lambda x: x[1], reverse=True):
            sc = chunk_lookup[cid]
            merged.append(ScoredChunk(chunk=sc.chunk, score=rrf_score))

        return merged[:15]  # Pass top-15 to reranker, which reduces to top-3

    # ── Contextual compression + formatting ──────────────────────────────────

    def _compress_and_format(self, chunks: list[ScoredChunk], query: str) -> Optional[str]:
        """
        Contextual compression: extract only query-relevant sentences from each chunk.
        Then format as flowing natural prose for LLM context injection.
        """
        if not chunks:
            return None

        query_terms = set(_tokenize_simple(query))
        insights = []
        seen_topics: set[str] = set()

        for sc in chunks:
            if not sc.chunk:
                continue

            topic = sc.chunk.topic or "general"
            if topic in seen_topics:
                continue
            seen_topics.add(topic)

            # Strip citations before compression, then extract relevant sentences
            clean_content = self._strip_citations(sc.chunk.content)
            compressed = self._extract_relevant_sentences(
                clean_content,
                query_terms=query_terms,
                max_chars=280,
            )

            if compressed and len(compressed) > 20:
                insights.append(compressed)

        if not insights:
            return None

        # Join as natural prose (not bullet points)
        formatted = " ".join(insights)
        formatted = re.sub(r"\s+", " ", formatted).strip()
        return formatted if len(formatted) > 20 else None

    @staticmethod
    def _strip_citations(text: str) -> str:
        """Remove academic citations and reference-style text from chunk content."""
        # Remove numbered reference lines: "7. Author Name (2020)..."
        text = re.sub(r"\n\d+\.\s+[A-Z].+", "", text, flags=re.MULTILINE)
        # Remove inline year citations: "(Smith et al., 2020)" or "(2020)"
        text = re.sub(r"\(\s*[A-Z][a-z]+(?:\s+et\s+al\.)?(?:,\s*\d{4})?\s*\)", "", text)
        # Remove DOI/URL references
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"\bdoi:\s*\S+", "", text, flags=re.IGNORECASE)
        # Remove "References:" section header and everything after
        text = re.sub(r"\bReferences:.*$", "", text, flags=re.DOTALL | re.IGNORECASE)
        return text.strip()

    @staticmethod
    def _extract_relevant_sentences(
        content: str,
        query_terms: set[str],
        max_chars: int = 280,
    ) -> str:
        """
        Extract the 1-2 sentences most relevant to the query terms.
        Falls back to first sentence if no overlap found.
        """
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content) if s.strip()]
        if not sentences:
            return ""

        # Score each sentence by query term overlap
        scored_sentences = []
        for sent in sentences:
            terms = set(_tokenize_simple(sent))
            overlap = len(query_terms & terms)
            scored_sentences.append((overlap, sent))

        scored_sentences.sort(key=lambda x: x[0], reverse=True)

        # Take top sentence(s) up to max_chars
        result_parts = []
        used_chars = 0
        for _, sent in scored_sentences[:2]:
            if used_chars + len(sent) > max_chars:
                break
            result_parts.append(sent)
            used_chars += len(sent)

        if not result_parts:
            # Fallback: first sentence truncated
            first = sentences[0]
            return first[:max_chars] + ("..." if len(first) > max_chars else "")

        return " ".join(result_parts)

    def get_citation_for_chunk(self, chunk_id: str) -> Optional[dict]:
        """Get source information for citing a specific chunk."""
        chunk = next(
            (c for c in self.knowledge_base.chunks if c.id == chunk_id),
            None,
        )
        if not chunk:
            return None
        return {"source": chunk.source, "topic": chunk.topic}


# ── Static lookup tables ──────────────────────────────────────────────────────

def _tokenize_simple(text: str) -> list[str]:
    """Lowercase word tokenization for term overlap scoring."""
    return [w.lower() for w in re.findall(r"\b\w{3,}\b", text)]


_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "anxiety": ["anxious", "anxiety", "worried", "nervous", "panic", "fear", "worry"],
    "self_esteem": ["self-esteem", "self esteem", "worthless", "confidence", "shame", "failure", "inadequate"],
    "depression": ["sad", "depressed", "depression", "low", "hopeless", "empty", "numb"],
    "loneliness": ["lonely", "loneliness", "alone", "isolated", "disconnected", "nobody"],
    "sleep": ["sleep", "insomnia", "tired", "exhausted", "fatigue", "awake", "rest"],
    "stress": ["stress", "stressed", "overwhelmed", "pressure", "burnout", "overloaded"],
    "relationships": ["relationship", "social", "family", "friend", "conflict", "communication"],
}

_CLINICAL_TERMS_MAP: dict[str, str] = {
    "anxiety": "generalized anxiety disorder GAD cognitive distortions worry cycle nervous system activation",
    "depression": "major depressive disorder mood dysregulation anhedonia behavioral activation cognitive therapy",
    "loneliness": "social isolation belonging need connection perceived social support interpersonal",
    "sleep": "insomnia sleep hygiene circadian rhythm sleep architecture sleep restriction therapy",
    "stress": "chronic stress HPA axis cortisol allostatic load stress response physiological",
    "self_esteem": "self-worth self-compassion negative self-schema cognitive distortion inner critic",
    "relationships": "attachment theory interpersonal conflict communication patterns relational dynamics",
}

_COPING_TERMS_MAP: dict[str, str] = {
    "anxiety": "breathing techniques grounding 5-4-3-2-1 progressive muscle relaxation CBT exposure mindfulness",
    "depression": "behavioral activation scheduling pleasant activities mood tracking journaling social support",
    "loneliness": "connection building social skills community belonging meaningful relationships small steps",
    "sleep": "sleep schedule wind-down routine screen time blue light relaxation bedroom environment",
    "stress": "time management boundaries relaxation techniques stress inoculation problem-focused coping",
    "self_esteem": "self-compassion exercises positive self-talk strengths journal evidence-based self-appraisal",
    "relationships": "assertive communication active listening conflict resolution boundary setting",
}

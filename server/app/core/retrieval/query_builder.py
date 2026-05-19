"""Context-aware query builder — spec Phase C §C1.

Enhances raw user messages with context signals before retrieval:
- Conversation history topic extraction
- Emotional state signals
- Intent-based metadata filter generation
- Risk-level-aware query modification
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# Allowed-use mapping per intent — used to populate metadata filters
_INTENT_ALLOWED_USE: dict[str, list[str]] = {
    "psychoeducation": ["psychoeducation"],
    "coping_strategy": ["coping_strategy"],
    "symptom_exploration": ["symptom_exploration", "psychoeducation"],
    "emotional_support": ["emotional_support", "psychoeducation"],
    "clarification": ["psychoeducation"],
    "clarification_needed": ["psychoeducation"],
    "crisis": ["crisis_support"],
    "methodology": ["methodology"],
}

# Preferred chunk types per intent
_INTENT_CHUNK_TYPES: dict[str, list[str]] = {
    "psychoeducation": ["definition", "mechanism", "explanation", "psychoeducation"],
    "coping_strategy": ["coping_step", "exercise", "grounding", "breathing", "self_help"],
    "symptom_exploration": ["symptom", "mechanism", "definition"],
    "emotional_support": ["explanation", "psychoeducation"],
    "crisis": ["crisis_instruction", "safety_plan", "crisis_resource"],
}

# Minimum evidence level per intent
_INTENT_MIN_EVIDENCE: dict[str, str] = {
    "psychoeducation": "educational",
    "coping_strategy": "educational",
    "symptom_exploration": "educational",
    "emotional_support": "educational",
    "crisis": "clinical_self_help",
}

# Confidence threshold per risk level
_RISK_CONFIDENCE_THRESHOLD: dict[int, float] = {
    0: 0.30,
    1: 0.35,
    2: 0.40,
    3: 0.50,
    4: 0.60,
    5: 0.70,
}

# Topic keywords for topic extraction from history
_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "anxiety": ["anxious", "anxiety", "panic", "worry", "nervous", "dread"],
    "depression": ["depressed", "depression", "hopeless", "low mood", "sad", "sadness"],
    "stress": ["stress", "stressed", "overwhelmed", "pressure", "burnout"],
    "loneliness": ["lonely", "alone", "isolated", "isolation", "solitary"],
    "self_esteem": ["self-worth", "self-esteem", "confidence", "worthless", "useless"],
    "sleep": ["sleep", "insomnia", "tired", "fatigue", "exhausted", "rest"],
    "relationships": ["relationship", "partner", "breakup", "love", "attachment"],
    "social_anxiety": ["social", "shy", "embarrassed", "judged", "social anxiety"],
    "grief_loss": ["grief", "loss", "grieving", "mourning", "loss", "death"],
    "rumination": ["rumination", "overthinking", "ruminate", "spiral", "intrusive"],
}


@dataclass(slots=True)
class EnhancedQuery:
    """Output of ContextAwareQueryBuilder.build()."""

    original_query: str
    enhanced_query: str
    intent: str
    risk_level: int
    extracted_topics: list[str]
    detected_emotional_state: str   # calm | distressed | crisis
    metadata_filters: dict[str, Any]
    target_indexes: list[str]
    confidence_threshold: float
    context_note: str               # brief explanation of enhancements applied


@dataclass
class QueryBuildContext:
    """Input to ContextAwareQueryBuilder.build()."""

    user_message: str
    intent: str
    risk_level: int = 0
    topic: str | None = None
    conversation_history: list[str] = field(default_factory=list)
    session_summary: dict[str, Any] = field(default_factory=dict)
    language: str = "en"


class ContextAwareQueryBuilder:
    """Builds retrieval-ready, context-enriched queries from raw user input."""

    def build(self, ctx: QueryBuildContext) -> EnhancedQuery:
        recent_history = ctx.conversation_history[-6:]  # last 3 turns
        extracted_topics = self._extract_topics(ctx.user_message, recent_history)
        emotional_state = self._assess_emotional_state(ctx.user_message, ctx.risk_level)
        enhanced = self._enhance_query(ctx.user_message, ctx.intent, extracted_topics, ctx.risk_level, emotional_state)
        metadata_filters = self._build_metadata_filters(ctx.intent, extracted_topics, ctx.risk_level)
        target_indexes = self._select_indexes(ctx.intent, ctx.risk_level)
        confidence_threshold = _RISK_CONFIDENCE_THRESHOLD.get(min(ctx.risk_level, 5), 0.40)

        notes: list[str] = []
        if extracted_topics:
            notes.append(f"topics: {', '.join(extracted_topics[:3])}")
        if emotional_state != "calm":
            notes.append(f"emotional_state: {emotional_state}")
        if ctx.risk_level >= 3:
            notes.append("elevated risk — safety filtering active")

        return EnhancedQuery(
            original_query=ctx.user_message,
            enhanced_query=enhanced,
            intent=ctx.intent,
            risk_level=ctx.risk_level,
            extracted_topics=extracted_topics,
            detected_emotional_state=emotional_state,
            metadata_filters=metadata_filters,
            target_indexes=target_indexes,
            confidence_threshold=confidence_threshold,
            context_note="; ".join(notes) if notes else "no enhancement",
        )

    # ── Private methods ──────────────────────────────────────────────────────

    def _extract_topics(self, user_message: str, recent_history: list[str]) -> list[str]:
        """Extract relevant topics from message and recent conversation."""
        all_text = " ".join([user_message] + recent_history).lower()
        found: list[str] = []
        for topic, keywords in _TOPIC_KEYWORDS.items():
            if any(kw in all_text for kw in keywords):
                found.append(topic)
        return found[:4]  # cap at 4 most relevant

    def _assess_emotional_state(self, message: str, risk_level: int) -> str:
        if risk_level >= 4:
            return "crisis"
        if risk_level >= 2:
            return "distressed"
        msg_lower = message.lower()
        distress_signals = [
            "overwhelmed", "can't cope", "falling apart", "breaking down",
            "desperate", "hopeless", "worthless", "exhausted", "can't do this",
        ]
        if any(s in msg_lower for s in distress_signals):
            return "distressed"
        return "calm"

    def _enhance_query(
        self,
        user_message: str,
        intent: str,
        topics: list[str],
        risk_level: int,
        emotional_state: str,
    ) -> str:
        enhanced = user_message

        # Append topic context if topics were detected and message is short
        if topics and len(user_message.split()) < 12:
            topic_str = " ".join(topics[:2]).replace("_", " ")
            enhanced = f"{user_message} [topic context: {topic_str}]"

        # Add intent signal for retrieval
        intent_signals = {
            "psychoeducation": "explain information about",
            "coping_strategy": "practical techniques and exercises for",
            "symptom_exploration": "understanding symptoms and patterns of",
            "emotional_support": "support for feelings about",
            "crisis": "crisis support and safety",
        }
        if intent in intent_signals and intent_signals[intent] not in enhanced.lower():
            enhanced = f"{intent_signals[intent]} {enhanced}"

        # Add safety note for elevated risk
        if risk_level >= 3:
            enhanced = f"{enhanced} [safety priority: elevated risk detected]"

        return enhanced.strip()

    def _build_metadata_filters(
        self,
        intent: str,
        topics: list[str],
        risk_level: int,
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {}

        # allowed_use
        filters["allowed_use"] = _INTENT_ALLOWED_USE.get(intent, ["psychoeducation"])

        # preferred chunk types
        if intent in _INTENT_CHUNK_TYPES:
            filters["preferred_chunk_types"] = _INTENT_CHUNK_TYPES[intent]

        # minimum evidence level
        filters["min_evidence_level"] = _INTENT_MIN_EVIDENCE.get(intent, "educational")

        # topic hint
        if topics:
            filters["topic_hints"] = topics

        # risk-based restrictions
        if risk_level <= 1:
            # Exclude high-risk content from low-risk conversations
            filters["max_chunk_risk"] = "low"
        elif risk_level >= 3:
            filters["requires_safety_filter"] = True

        # never retrieve medication or diagnosis advice
        filters["exclude_not_allowed"] = ["medication_advice", "diagnosis"]

        return filters

    def _select_indexes(self, intent: str, risk_level: int) -> list[str]:
        from server.app.core.retrieval.multi_index_retriever import (
            INDEX_COPING,
            INDEX_METHODOLOGY,
            INDEX_PSYCHOEDUCATION,
            INDEX_SAFETY_CRISIS,
            CRISIS_INDEX_MIN_RISK,
            _INTENT_INDEX_MAP,
        )
        if risk_level >= CRISIS_INDEX_MIN_RISK:
            return [INDEX_SAFETY_CRISIS]
        preferred = _INTENT_INDEX_MAP.get(intent, [INDEX_PSYCHOEDUCATION])
        return [idx for idx in preferred if idx != INDEX_SAFETY_CRISIS]


# Module-level singleton
query_builder = ContextAwareQueryBuilder()

"""Query processing and enhancement for RAG."""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ProcessedQuery:
    """Enhanced query for retrieval."""
    original: str
    enhanced: str
    intent: str
    risk_level: int
    keywords: List[str]
    metadata_filters: Dict[str, Any]


class QueryProcessor:
    """Process and enhance queries for retrieval."""

    INTENT_SIGNALS = {
        "psychoeducation": "explain what is",
        "coping_strategy": "practical techniques for",
        "symptom_exploration": "understand symptoms of",
        "emotional_support": "support for feeling",
        "crisis": "crisis emergency help",
    }

    def process(
        self,
        query: str,
        intent: str,
        risk_level: int,
    ) -> ProcessedQuery:
        """Process and enhance query."""
        # Extract keywords
        keywords = self._extract_keywords(query)

        # Enhance query
        enhanced = self._enhance_query(query, intent, keywords, risk_level)

        # Build metadata filters
        filters = self._build_filters(intent, risk_level, keywords)

        return ProcessedQuery(
            original=query,
            enhanced=enhanced,
            intent=intent,
            risk_level=risk_level,
            keywords=keywords,
            metadata_filters=filters,
        )

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query."""
        # Simple keyword extraction
        words = query.lower().split()
        stop_words = {"what", "how", "why", "is", "are", "the", "a", "an", "i", "me"}
        keywords = [w.strip(".,!?") for w in words if w not in stop_words and len(w) > 2]
        return list(dict.fromkeys(keywords))[:5]  # Unique, up to 5

    def _enhance_query(
        self,
        query: str,
        intent: str,
        keywords: List[str],
        risk_level: int,
    ) -> str:
        """Enhance query with context."""
        enhanced = query

        # Add intent signal if not already present
        if intent in self.INTENT_SIGNALS:
            signal = self.INTENT_SIGNALS[intent]
            if signal.split()[0].lower() not in query.lower():
                enhanced = f"{signal} {query}"

        # Add context for high-risk
        if risk_level >= 3:
            enhanced += " [urgent mental health crisis support needed]"

        return enhanced.strip()

    def _build_filters(
        self,
        intent: str,
        risk_level: int,
        keywords: List[str],
    ) -> Dict[str, Any]:
        """Build metadata filters for retrieval."""
        filters = {}

        # Intent-based allowed_use
        allowed_use_map = {
            "psychoeducation": ["psychoeducation"],
            "coping_strategy": ["coping_strategy", "psychoeducation"],
            "symptom_exploration": ["symptom_exploration", "psychoeducation"],
            "emotional_support": ["emotional_support", "psychoeducation"],
            "crisis": ["crisis_support"],
        }
        filters["allowed_use"] = allowed_use_map.get(intent, ["psychoeducation"])

        # Risk-based filters
        if risk_level <= 1:
            filters["max_clinical_risk"] = "low"
        elif risk_level >= 3:
            filters["requires_safety_filter"] = True

        # Always exclude medication and diagnosis
        filters["exclude_not_allowed"] = ["medication_advice", "diagnosis"]

        return filters

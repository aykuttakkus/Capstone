from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class IntentResult:
    intent: str
    confidence: float
    category: str
    rationale: str


class IntentDetector:
    INTENT_PATTERNS = {
        "psychoeducation": {
            "keywords": ["how does", "what is", "explain", "what causes", "why do", "tell me about"],
            "category": "information",
        },
        "coping_strategy": {
            "keywords": ["how can i", "help me", "what can i do", "techniques", "strategies", "manage"],
            "category": "action",
        },
        "symptom_exploration": {
            "keywords": [
                "why do i feel",
                "why am i",
                "what's happening",
                "understand my",
                "pattern",
                "trigger",
            ],
            "category": "understanding",
        },
        "clarification": {
            "keywords": ["what does", "what do you mean", "clarify", "confused", "don't understand"],
            "category": "clarification",
        },
        "emotional_support": {
            "keywords": ["feel", "struggling", "overwhelmed", "help", "support", "listen"],
            "category": "emotional",
        },
        "repair": {
            "keywords": ["sorry", "misunderstood", "didn't understand", "again", "clarify"],
            "category": "repair",
        },
    }

    def detect(self, message: str, topic: str | None = None, context: dict | None = None) -> IntentResult:
        """Detect user intent from message."""

        normalized = message.lower().strip()

        # Crisis detection (highest priority)
        if self._is_crisis(normalized):
            return IntentResult(
                intent="crisis",
                confidence=0.95,
                category="safety",
                rationale="Message contains crisis indicators",
            )

        # Check if off-scope
        if self._is_off_scope(normalized, topic):
            return IntentResult(
                intent="off_scope",
                confidence=0.85,
                category="boundary",
                rationale="Topic or request is outside scope",
            )

        # Score each intent pattern
        intent_scores = {}
        for intent, pattern_info in self.INTENT_PATTERNS.items():
            score = self._score_intent(normalized, pattern_info["keywords"])
            intent_scores[intent] = score

        # Find best match
        best_intent = max(intent_scores, key=intent_scores.get)
        best_score = intent_scores[best_intent]

        if best_score < 0.3:
            best_intent = "emotional_support"  # Default fallback
            best_score = 0.5

        return IntentResult(
            intent=best_intent,
            confidence=min(best_score, 0.95),
            category=self.INTENT_PATTERNS[best_intent]["category"],
            rationale=f"Matched pattern: {best_intent}",
        )

    def _is_crisis(self, message: str) -> bool:
        """Check if message contains crisis indicators."""

        crisis_indicators = [
            "suicide",
            "kill myself",
            "kill myself",
            "die",
            "goodbye",
            "letter",
            "end it",
            "not worth",
            "better off without",
            "hurt myself",
            "self-harm",
        ]

        return any(indicator in message for indicator in crisis_indicators)

    def _is_off_scope(self, message: str, topic: str | None = None) -> bool:
        """Check if request is off-scope."""

        off_scope_patterns = [
            "medical advice",
            "diagnosis",
            "prescription",
            "medication",
            "doctor",
            "therapy",
            "therapist",
            "legal advice",
            "financial advice",
            "relationship decision",
            "career advice",
        ]

        if any(pattern in message for pattern in off_scope_patterns):
            return True

        return False

    def _score_intent(self, message: str, keywords: list[str]) -> float:
        """Score how well message matches intent keywords."""

        if not keywords:
            return 0.0

        matches = sum(1 for kw in keywords if kw in message)
        return matches / len(keywords)

    def get_intent_distribution(self, message: str) -> dict[str, float]:
        """Get probability distribution across all intents."""

        normalized = message.lower()
        distribution = {}

        for intent, pattern_info in self.INTENT_PATTERNS.items():
            score = self._score_intent(normalized, pattern_info["keywords"])
            distribution[intent] = score

        # Normalize to sum to 1
        total = sum(distribution.values()) or 1
        return {intent: score / total for intent, score in distribution.items()}

    def explain_intent(self, result: IntentResult) -> str:
        """Generate human-readable explanation of detected intent."""

        explanations = {
            "psychoeducation": "You're asking for information or explanation",
            "coping_strategy": "You're looking for practical techniques or strategies",
            "symptom_exploration": "You're trying to understand patterns or triggers",
            "clarification": "You're asking me to clarify something",
            "emotional_support": "You're seeking emotional validation or support",
            "repair": "You're trying to clarify or repair understanding",
            "crisis": "You're expressing thoughts of self-harm (PRIORITY)",
            "off_scope": "Your request is outside my scope of support",
        }

        base = explanations.get(result.intent, "Unknown intent")
        return f"{base} (confidence: {result.confidence:.0%})"

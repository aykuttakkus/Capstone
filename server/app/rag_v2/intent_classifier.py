"""Intent classification engine for RAG queries."""

import unicodedata
import re
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class IntentResult:
    """Result of intent classification."""
    primary_intent: str
    confidence: float
    risk_level: int  # 0-5: none to crisis
    secondary_intents: List[str]


class IntentClassifier:
    """Classify user intent and risk level."""

    INTENTS = {
        "psychoeducation": {
            "keywords": [
                ("what is", 1.0), ("what are", 0.8), ("how does", 1.0),
                ("explain", 0.9), ("definition", 0.8), ("understand", 0.7),
                ("nedir", 1.0), ("nasıl", 0.8), ("anla", 0.7),
            ],
        },
        "coping_strategy": {
            "keywords": [
                ("how can i", 0.9), ("what can i do", 0.9), ("technique", 0.8),
                ("exercise", 0.8), ("skill", 0.7), ("try", 0.6),
                ("nasıl başa çık", 0.9), ("ne yapabilir", 0.9),
            ],
        },
        "symptom_exploration": {
            "keywords": [
                ("why am i", 0.8), ("why do i", 0.8), ("symptom", 0.9),
                ("sign", 0.7), ("feeling", 0.6), ("experiencing", 0.7),
                ("neden ben", 0.8), ("semptom", 0.9),
            ],
        },
        "emotional_support": {
            "keywords": [
                ("i feel", 0.7), ("i'm", 0.5), ("upset", 0.7), ("sad", 0.7),
                ("anxious", 0.7), ("scared", 0.7), ("hissediyorum", 0.7),
            ],
        },
        "crisis": {
            "keywords": [
                ("suicide", 2.0), ("kill myself", 2.0), ("die", 1.5),
                ("harm", 1.8), ("hurt myself", 1.8), ("hopeless", 1.3),
                ("no way out", 1.5), ("intihara", 2.0), ("kendimi", 1.8),
            ],
        },
    }

    RISK_KEYWORDS = {
        0: [],  # none
        1: ["worried", "stressed", "anxious"],  # low
        2: ["overwhelmed", "can't cope", "breaking down"],  # medium
        3: ["desperate", "hopeless", "worthless"],  # high
        4: ["self-harm", "hurt myself", "injury"],  # very high
        5: ["suicide", "kill myself", "die"],  # crisis
    }

    def __init__(self):
        pass

    def classify(self, message: str) -> IntentResult:
        """Classify intent and risk level."""
        normalized = self._normalize(message)

        # Detect intent
        intent_scores = self._score_intents(normalized)
        primary_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[primary_intent]

        # Detect risk level
        risk_level = self._detect_risk_level(normalized)

        # Boundary cases
        if self._is_off_scope(normalized):
            primary_intent = "off_scope"
            confidence = 0.9

        if risk_level >= 3:
            primary_intent = "crisis"
            confidence = max(confidence, 0.8)

        return IntentResult(
            primary_intent=primary_intent,
            confidence=min(confidence, 0.99),
            risk_level=risk_level,
            secondary_intents=[i for i in intent_scores if i != primary_intent][:2],
        )

    def _normalize(self, text: str) -> str:
        """Normalize text for matching."""
        # Unicode normalization for Turkish characters
        nfc = unicodedata.normalize("NFC", text)
        casefolded = nfc.casefold()
        # Remove diacriticals
        stripped = "".join(
            c for c in unicodedata.normalize("NFD", casefolded)
            if unicodedata.category(c) != "Mn"
        )
        return stripped.strip()

    def _score_intents(self, normalized_text: str) -> Dict[str, float]:
        """Score each intent."""
        scores = {intent: 0.0 for intent in self.INTENTS}

        for intent, data in self.INTENTS.items():
            for keyword, weight in data["keywords"]:
                if keyword in normalized_text:
                    scores[intent] += weight

        # Normalize scores
        max_score = max(scores.values()) if any(scores.values()) else 1.0
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}

        return scores

    def _detect_risk_level(self, normalized_text: str) -> int:
        """Detect risk level from keywords."""
        for level in range(5, -1, -1):
            keywords = self.RISK_KEYWORDS[level]
            if any(kw in normalized_text for kw in keywords):
                return level
        return 0

    def _is_off_scope(self, normalized_text: str) -> bool:
        """Check if message is off-scope."""
        off_scope_patterns = [
            r"recipe|cooking|pizza|movie|game|sport",
            r"weather|traffic|news|politics|sports",
            r"recipe| recipe",
        ]
        return any(re.search(p, normalized_text) for p in off_scope_patterns)

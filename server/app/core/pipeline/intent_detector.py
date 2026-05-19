from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(slots=True)
class IntentResult:
    primary_intent: str
    confidence: float
    category: str
    rationale: str
    secondary_intents: list[str]

    @property
    def intent(self) -> str:
        """Backward-compatible alias for the old single-intent contract."""
        return self.primary_intent


class IntentDetector:
    # Weighted keyword lists — tuples of (keyword, weight).
    # Higher weight = stronger signal.
    INTENT_PATTERNS: dict[str, dict] = {
        "psychoeducation": {
            "keywords": [
                ("what is", 1.0),
                ("what are", 0.8),
                ("how does", 1.0),
                ("how do", 0.7),
                ("explain", 0.9),
                ("what causes", 1.0),
                ("why does", 0.8),
                ("tell me about", 0.9),
                ("what happens", 0.7),
                ("how is it", 0.6),
                ("define", 0.8),
                ("definition of", 0.9),
                ("what exactly is", 1.0),
                ("can you explain", 0.9),
                ("i want to understand", 0.8),
                ("i want to know", 0.7),
                ("teach me", 0.8),
                ("how does anxiety", 1.0),
                ("how does stress", 1.0),
                ("how does depression", 1.0),
                ("how does sleep", 0.9),
                ("symptoms of", 0.8),
                ("signs of", 0.7),
                ("what does it mean", 0.8),
                ("how does the brain", 0.9),
                ("what is the science", 0.9),
                # Turkish question patterns
                ("nedir", 1.0),           # "what is" in Turkish
                ("nelerdir", 0.9),        # "what are" in Turkish
                ("nasıl", 0.8),           # "how" in Turkish
                ("neden", 0.8),           # "why" in Turkish
                ("anlat", 0.9),           # "explain" in Turkish
                ("nedir bu", 1.0),        # "what is this"
                ("nasil calişir", 0.9),   # "how does it work"
                ("ne demek", 0.9),        # "what does it mean"
            ],
            "category": "information",
        },
        "coping_strategy": {
            "keywords": [
                ("how can i", 1.0),
                ("what can i do", 1.0),
                ("what should i do", 1.0),
                ("what do i do", 0.9),
                ("techniques", 0.9),
                ("strategies", 0.9),
                ("manage", 0.7),
                ("cope with", 1.0),
                ("coping", 1.0),
                ("deal with", 0.8),
                ("breathing", 0.9),
                ("exercise", 0.6),
                ("grounding", 1.0),
                ("mindfulness", 0.9),
                ("meditation", 0.8),
                ("relaxation", 0.8),
                ("reduce my", 0.7),
                ("help me with", 0.8),
                ("what helps", 0.8),
                ("how to calm", 0.9),
                ("how to relax", 0.9),
                ("ways to", 0.7),
                ("tips for", 0.8),
                ("exercises for", 0.9),
                ("routine", 0.5),
                ("practice", 0.5),
                ("skill", 0.6),
                # Turkish coping patterns
                ("başa çıkma", 1.0),      # "coping"
                ("başa çıkmak", 1.0),
                ("yolları nelerdir", 0.9), # "what are the ways"
                ("nasıl başa", 0.9),       # "how to cope"
                ("teknikler", 0.9),        # "techniques"
                ("stratejiler", 0.9),      # "strategies"
                ("yöntemler", 0.8),        # "methods"
                ("ne yapabilirim", 0.9),   # "what can i do"
                ("nasıl azaltabilirim", 0.9), # "how can i reduce"
            ],
            "category": "action",
        },
        "symptom_exploration": {
            "keywords": [
                ("why do i feel", 1.0),
                ("why am i", 1.0),
                ("why do i", 0.9),
                ("what's happening to me", 1.0),
                ("understand my", 0.9),
                ("pattern", 0.7),
                ("trigger", 0.8),
                ("my symptoms", 0.9),
                ("i keep feeling", 0.9),
                ("i always feel", 0.8),
                ("i always push", 0.9),
                ("i keep pushing", 0.9),
                ("i always do this", 0.8),
                ("i always end up", 0.8),
                ("do i have", 1.0),
                ("am i depressed", 1.0),
                ("am i anxious", 1.0),
                ("could i have", 0.9),
                ("might i have", 0.9),
                ("do you think i have", 1.0),
                ("diagnose me", 1.0),
                ("what disorder", 0.9),
                ("what condition", 0.8),
                ("is this normal", 0.8),
                ("is it normal to", 0.8),
                ("something wrong with me", 0.9),
                ("i experience", 0.6),
                ("i've been experiencing", 0.7),
                ("my anxiety feels", 0.8),
                ("this happens when", 0.7),
                ("ever since", 0.5),
                ("terrified of", 0.9),
                ("afraid of", 0.8),
                ("scared of", 0.8),
                ("fear of", 0.8),
                ("phobia", 0.9),
                ("i can't stop thinking", 0.9),
                ("can't stop thinking", 0.9),
                ("keep thinking about", 0.8),
                ("overthinking", 0.9),
                ("intrusive thoughts", 0.9),
                ("panic attack", 0.7),   # secondary signal — coping gets boosted by "what should I do"
            ],
            "category": "understanding",
        },
        "clarification": {
            "keywords": [
                ("what does that mean", 1.0),
                ("what do you mean", 1.0),
                ("clarify", 0.9),
                ("confused", 0.7),
                ("don't understand", 0.9),
                ("can you repeat", 0.9),
                ("i didn't get", 0.8),
                ("can you say that again", 0.9),
                ("please explain", 0.8),
                ("what did you mean", 1.0),
                ("i'm not sure i follow", 0.9),
            ],
            "category": "clarification",
        },
        "emotional_support": {
            "keywords": [
                ("i feel", 0.6),
                ("i'm feeling", 0.7),
                ("feeling", 0.5),
                ("i'm struggling", 0.9),
                ("struggling", 0.7),
                ("overwhelmed", 0.9),
                ("i need support", 1.0),
                ("i need someone", 0.9),
                ("please listen", 0.9),
                ("i'm going through", 0.8),
                ("it's been hard", 0.8),
                ("having a hard time", 0.9),
                ("i can't cope", 0.9),
                ("i don't know what to do", 0.8),
                ("nobody understands", 0.9),
                ("so alone", 0.9),
                ("i'm exhausted", 0.7),
                ("i'm anxious", 0.7),
                ("i'm sad", 0.7),
                ("i'm scared", 0.7),
                ("i'm worried", 0.7),
                ("i'm stressed", 0.7),
                ("so overwhelmed", 0.9),
                ("really hard", 0.6),
                ("can you help me", 0.5),
                ("i've been feeling", 0.7),
                ("feeling down", 0.8),
                ("feeling low", 0.8),
                ("feeling blue", 0.8),
            ],
            "category": "emotional",
        },
        "repair": {
            "keywords": [
                ("sorry", 0.7),
                ("misunderstood", 0.9),
                ("didn't understand", 0.9),
                ("let me rephrase", 1.0),
                ("what i meant", 0.9),
                ("i meant to say", 0.9),
                ("i was trying to", 0.7),
                ("that's not what i meant", 1.0),
            ],
            "category": "repair",
        },
    }

    # Explicit crisis patterns — highest priority
    _CRISIS_PATTERNS = [
        "suicide", "suicidal", "kill myself", "end my life", "end it all",
        "take my life", "want to die", "wish i was dead", "can't go on",
        "not worth living", "no reason to live", "better off dead",
        "better off without me", "hurt myself", "self-harm", "self harm",
        "harm myself", "cut myself", "i want to hurt", "i want to kill",
        "overdose", "no way out", "i give up on life",
        "don't see a way out", "see no way out", "see no hope",
        "everything is hopeless", "feel hopeless", "feeling hopeless",
        "no hope left", "giving up on life", "ready to give up",
        # Turkish (casefold-safe — checked after casefold normalization)
        "intihar", "kendimi öldür", "yaşamak istemiyorum",
        "ölmek istiyorum", "kendime zarar", "hayatıma son",
        "yaşamaya değmez", "intihar et", "intihar düşün",
    ]

    # Explicit off-scope patterns — checked before intent scoring
    _OFF_SCOPE_PATTERNS = [
        # Financial / legal
        "stock market", "invest", "crypto", "bitcoin", "stocks", "trading",
        "legal advice", "lawyer", "court", "sue", "lawsuit",
        "tax", "insurance claim", "financial planning",
        # Non-mental-health topics
        "recipe", "cook", "cooking", "weather", "forecast",
        "sports", "football", "soccer", "basketball",
        "movie recommendation", "book recommendation", "song",
        "homework", "essay", "code for me",
        # Explicit out-of-scope medical
        "what medication should i take", "which pill", "which drug",
        "should i take antidepressants", "antidepressant dose",
        "prozac", "zoloft", "lexapro", "ssri", "snri", "benzodiazepine",
        "what dose", "dosage of",
    ]

    # Medication & diagnosis boundary — detected → off_scope with high confidence
    _MEDICATION_PATTERNS = [
        "should i take", "should i start", "can i take",
        "what medication", "which medication", "recommend medication",
        "antidepressant", "anti-depressant", "sleeping pill",
        "prescription", "prescribed", "dose", "dosage",
    ]

    _DIAGNOSIS_PATTERNS = [
        "do i have", "am i depressed", "am i anxious", "diagnose me",
        "what disorder do i have", "what condition do i have",
        "do you think i have", "could i be diagnosed",
        "is this anxiety", "is this depression", "is this ocd",
        "i think i have",
    ]

    # Risk-level keywords for subtle distress
    _RISK_KEYWORDS: dict[str, list[str]] = {
        "low": [
            "down", "sad", "not great", "not good", "struggling a bit",
            "a bit low", "feeling low", "feeling down", "a little blue",
            "kind of off", "not myself", "a little sad",
        ],
        "medium": [
            "hopeless", "worthless", "empty inside", "numb", "no point",
            "what's the point", "no purpose", "meaningless", "alone",
            "nobody cares", "nobody understands", "trapped", "stuck",
        ],
        "high": [
            "suicide", "end it", "kill myself", "no reason to live",
            "better off dead", "can't go on", "giving up",
        ],
    }

    def detect(self, message: str, topic: str | None = None, context: dict | None = None) -> IntentResult:
        # Normalize: NFC → casefold → strip combining marks for cross-locale matching
        normalized = self._normalize(message)

        # 1. Crisis (highest priority) — including compound patterns
        if self._is_crisis(normalized) or self._is_compound_crisis(normalized):
            return IntentResult(
                primary_intent="crisis",
                confidence=0.98,
                category="safety",
                rationale="Crisis indicators detected",
                secondary_intents=[],
            )

        # 2. Explicit off-scope content
        if self._is_hard_off_scope(normalized):
            return IntentResult(
                primary_intent="off_scope",
                confidence=0.90,
                category="boundary",
                rationale="Request outside mental-health scope",
                secondary_intents=[],
            )

        # 3. Medication boundary — still off_scope
        if self._is_medication_request(normalized):
            return IntentResult(
                primary_intent="off_scope",
                confidence=0.88,
                category="boundary",
                rationale="Medication advice is outside scope",
                secondary_intents=["psychoeducation"],
            )

        # 4. Diagnosis request → symptom_exploration (then safety layer enforces boundary)
        if self._is_diagnosis_request(normalized):
            return IntentResult(
                primary_intent="symptom_exploration",
                confidence=0.85,
                category="understanding",
                rationale="Diagnosis-seeking mapped to symptom exploration",
                secondary_intents=["emotional_support"],
            )

        # 5. Score all intents using weighted patterns
        intent_scores = self._score_all_intents(normalized)

        # 6. Apply question-word boost for psychoeducation.
        # Only applies when coping_strategy doesn't already have a strong raw signal —
        # "What are grounding techniques?" should remain coping, not flip to psychoeducation.
        if self._has_question_words(normalized):
            coping_raw = intent_scores.get("coping_strategy", 0.0)
            psychoed_raw = intent_scores.get("psychoeducation", 0.0)
            # Skip boost when message is clearly about methods/techniques (coping dominates)
            if coping_raw < 0.25:
                intent_scores["psychoeducation"] = psychoed_raw + 0.50
            elif psychoed_raw < coping_raw:
                # Psychoed has weaker raw signal — small boost only
                intent_scores["psychoeducation"] = psychoed_raw + 0.20

        # 6b. Mixed-intent: if message starts with question phrase, elevate psychoeducation
        # regardless of emotional content in the rest ("What is anxiety? I feel overwhelmed")
        if self._starts_with_question(normalized):
            intent_scores["psychoeducation"] = max(
                intent_scores.get("psychoeducation", 0.0),
                intent_scores.get("emotional_support", 0.0) + 0.15,
            )

        # 7. Normalize by max possible score per intent to get 0-1 range
        intent_scores = {k: min(v, 1.0) for k, v in intent_scores.items()}

        if not intent_scores or max(intent_scores.values()) < 0.10:
            # Default fallback
            return IntentResult(
                primary_intent="emotional_support",
                confidence=0.50,
                category="emotional",
                rationale="No strong pattern match — defaulting to emotional support",
                secondary_intents=[],
            )

        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        best_intent, best_score = sorted_intents[0]

        secondary = [
            intent for intent, score in sorted_intents[1:]
            if score > 0.05 and intent != best_intent
        ][:2]

        category = self.INTENT_PATTERNS.get(best_intent, {}).get("category", "emotional")

        return IntentResult(
            primary_intent=best_intent,
            confidence=min(best_score, 0.95),
            category=category,
            rationale=f"Top intent: {best_intent} (score={best_score:.2f})",
            secondary_intents=secondary,
        )

    @staticmethod
    def _normalize(message: str) -> str:
        """NFC → casefold → strip combining marks (handles Turkish İ, ş, etc.)."""
        nfc = unicodedata.normalize("NFC", message)
        casefolded = nfc.casefold()
        # Remove combining diacritical marks so İ→i, etc. match ASCII patterns
        stripped = "".join(
            c for c in unicodedata.normalize("NFD", casefolded)
            if unicodedata.category(c) != "Mn"
        )
        return stripped.strip()

    def detect_risk_level(self, message: str) -> str:
        """Return risk keyword level: none | low | medium | high."""
        normalized = self._normalize(message)
        for level in ("high", "medium", "low"):
            if any(kw in normalized for kw in self._RISK_KEYWORDS[level]):
                return level
        return "none"

    # ── private helpers ──────────────────────────────────────────────────────

    def _is_crisis(self, message: str) -> bool:
        return any(p in message for p in self._CRISIS_PATTERNS)

    def _is_compound_crisis(self, message: str) -> bool:
        """Detect crisis from combined signals (hopeless + no escape)."""
        hopeless_signals = ("hopeless", "no hope", "feels hopeless", "feel hopeless",
                            "everything is dark", "nothing will change", "never get better")
        no_escape_signals = ("no way out", "don't see a way", "see no way", "no escape",
                             "no exit", "there's no point", "what's the point")
        has_hopeless = any(s in message for s in hopeless_signals)
        has_no_escape = any(s in message for s in no_escape_signals)
        return has_hopeless and has_no_escape

    def _is_hard_off_scope(self, message: str) -> bool:
        return any(p in message for p in self._OFF_SCOPE_PATTERNS)

    def _is_medication_request(self, message: str) -> bool:
        return any(p in message for p in self._MEDICATION_PATTERNS)

    def _is_diagnosis_request(self, message: str) -> bool:
        return any(p in message for p in self._DIAGNOSIS_PATTERNS)

    def _has_question_words(self, message: str) -> bool:
        question_openers = (
            "what is", "what are", "how does", "how do", "explain",
            "why does", "why do", "what causes", "tell me about",
            "what exactly is", "can you explain",
            # Turkish (after normalization — diacritics stripped)
            "nedir", "nelerdir", "nasil", "neden", "anlat", "ne demek",
        )
        return any(message.startswith(q) or f" {q}" in message for q in question_openers)

    def _starts_with_question(self, message: str) -> bool:
        """True only when the message OPENS with a question phrase (strict)."""
        strict_openers = (
            "what is ", "what are ", "how does ", "how do ", "explain ",
            "what causes ", "what exactly is ", "tell me about ",
            "nedir ", "nasil ", "neden ",
        )
        return any(message.startswith(q) for q in strict_openers) or message.endswith("?") and any(
            q in message for q in ("what is", "what are", "how does", "nedir", "nelerdir")
        )

    def _score_all_intents(self, message: str) -> dict[str, float]:
        scores: dict[str, float] = {}
        for intent, pattern_info in self.INTENT_PATTERNS.items():
            scores[intent] = self._score_weighted(message, pattern_info["keywords"])
        return scores

    def _score_weighted(self, message: str, keywords: list[tuple[str, float]]) -> float:
        """Weighted match: sum of weights for matched keywords.

        Both message and keyword patterns are pre-normalized, so Turkish
        diacritics are stripped on both sides before comparison.
        """
        total_weight = sum(w for _, w in keywords)
        if total_weight == 0:
            return 0.0
        # Normalize patterns at match time (cheap since list is short)
        matched_weight = sum(
            w for kw, w in keywords
            if self._normalize(kw) in message  # message already normalized by caller
        )
        top3 = sum(w for _, w in sorted(keywords, key=lambda x: x[1], reverse=True)[:3])
        if top3 == 0:
            return 0.0
        return matched_weight / top3

    def get_intent_distribution(self, message: str) -> dict[str, float]:
        normalized = self._normalize(message)
        scores = self._score_all_intents(normalized)
        total = sum(scores.values()) or 1.0
        return {intent: score / total for intent, score in scores.items()}

    def explain_intent(self, result: IntentResult) -> str:
        explanations = {
            "psychoeducation": "You're asking for information or explanation",
            "coping_strategy": "You're looking for practical techniques or strategies",
            "symptom_exploration": "You're trying to understand your symptoms or patterns",
            "clarification": "You're asking me to clarify something",
            "clarification_needed": "You're asking me to clarify something",
            "emotional_support": "You're seeking emotional validation or support",
            "repair": "You're trying to clarify or correct a misunderstanding",
            "crisis": "You're expressing thoughts of self-harm (PRIORITY)",
            "off_scope": "Your request is outside my scope of support",
        }
        base = explanations.get(result.intent, "Unknown intent")
        return f"{base} (confidence: {result.confidence:.0%})"

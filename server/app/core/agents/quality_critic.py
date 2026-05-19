from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class QualityCriticResult:
    scores: dict[str, float] = field(default_factory=dict)
    overall_score: float = 0.0
    passed: bool = True
    concerns: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class QualityCritic:
    RUBRIC = {
        "intent_match": {
            "description": "Does response match stated intent?",
            "weight": 0.10
        },
        "emotional_attunement": {
            "description": "Is emotional tone appropriate to user state?",
            "weight": 0.12
        },
        "evidence_grounding": {
            "description": "Are claims backed by evidence or clearly marked as opinion?",
            "weight": 0.10
        },
        "actionability": {
            "description": "Can user actually use this information?",
            "weight": 0.10
        },
        "safety": {
            "description": "Does response maintain safety boundaries?",
            "weight": 0.15
        },
        "boundary": {
            "description": "Are professional boundaries clear?",
            "weight": 0.12
        },
        "question_discipline": {
            "description": "Are questions used appropriately to promote self-reflection?",
            "weight": 0.05
        },
        "non_repetition": {
            "description": "Is response unique in conversation history?",
            "weight": 0.06
        },
        "clarity": {
            "description": "Is language clear and jargon-free?",
            "weight": 0.08
        },
        "escalation_correctness": {
            "description": "Is escalation logic correct for risk level?",
            "weight": 0.05
        },
        "cultural_safety": {
            "description": "Does response avoid cultural assumptions and respect diverse backgrounds?",
            "weight": 0.07
        }
    }

    def critique(
        self,
        response: str,
        intent: str,
        user_message: str,
        conversation_history: list[str] | None = None,
        risk_level: int = 0,
    ) -> QualityCriticResult:
        result = QualityCriticResult()

        if not response:
            result.overall_score = 0.0
            result.passed =False
            result.concerns.append("Response is empty")
            return result

        # Score each dimension
        result.scores["intent_match"] = self._score_intent_match(response, intent)
        result.scores["emotional_attunement"] = self._score_emotional_attunement(response, user_message)
        result.scores["evidence_grounding"] = self._score_evidence_grounding(response)
        result.scores["actionability"] = self._score_actionability(response)
        result.scores["safety"] = self._score_safety(response, risk_level)
        result.scores["boundary"] = self._score_boundary(response)
        result.scores["question_discipline"] = self._score_question_discipline(response)
        result.scores["non_repetition"] = self._score_non_repetition(response, conversation_history)
        result.scores["clarity"] = self._score_clarity(response)
        result.scores["escalation_correctness"] = self._score_escalation_correctness(response, risk_level)
        result.scores["cultural_safety"] = self._score_cultural_safety(response)

        # Calculate weighted overall score
        total_weighted = 0.0
        total_weight = 0.0
        for dim, score in result.scores.items():
            weight = self.RUBRIC[dim]["weight"]
            total_weighted += score * weight
            total_weight += weight

        result.overall_score = total_weighted / total_weight if total_weight > 0 else 0.0
        result.passed =result.overall_score >= 0.65

        # Generate concerns and recommendations
        self._generate_feedback(result)

        return result

    def _score_intent_match(self, response: str, intent: str) -> float:
        if not intent or intent == "unknown":
            return 0.8

        intent_keywords = {
            "psychoeducation": ["research", "study", "evidence", "shows", "found"],
            "coping_strategy": ["try", "practice", "exercise", "technique", "step"],
            "clarification": ["mean", "understand", "explain", "what", "when"],
            "emotional_support": ["feel", "understand", "normal", "validate"],
        }

        keywords = intent_keywords.get(intent, [])
        if not keywords:
            return 0.8

        response_lower = response.lower()
        matches = sum(1 for kw in keywords if kw in response_lower)
        return min(matches / max(len(keywords), 1), 1.0)

    def _score_emotional_attunement(self, response: str, user_message: str) -> float:
        if not response or not user_message:
            return 0.7

        # Simple heuristics: check for validation and acknowledgment
        validation_words = ["understand", "feel", "valid", "normal", "okay", "understandable"]
        response_lower = response.lower()

        if any(word in response_lower for word in validation_words):
            return 0.9
        elif any(negative in response_lower for negative in ["but", "however", "yet"]):
            return 0.7
        else:
            return 0.6

    def _score_evidence_grounding(self, response: str) -> float:
        evidence_markers = ["research", "study", "found", "shows", "according to", "evidence"]
        opinion_markers = ["i think", "maybe", "perhaps", "seems like"]

        response_lower = response.lower()

        has_evidence = any(marker in response_lower for marker in evidence_markers)
        has_opinion_caveat = any(marker in response_lower for marker in opinion_markers)

        if has_evidence:
            return 0.95
        elif has_opinion_caveat:
            return 0.8
        else:
            return 0.6

    def _score_actionability(self, response: str) -> float:
        action_words = ["try", "practice", "exercise", "step", "start with", "begin", "attempt"]
        response_lower = response.lower()

        action_count = sum(1 for word in action_words if word in response_lower)
        return min(action_count * 0.2, 0.95)

    def _score_safety(self, response: str, risk_level: int) -> float:
        danger_words = ["kill", "die", "suicide", "self-harm", "dangerous"]
        response_lower = response.lower()

        has_danger = any(word in response_lower for word in danger_words)

        if has_danger and risk_level < 3:
            return 0.3

        return 0.9

    def _score_boundary(self, response: str) -> float:
        boundary_violations = ["i love you", "therapist", "medication", "diagnosis"]
        response_lower = response.lower()

        violations = sum(1 for word in boundary_violations if word in response_lower)
        return max(0.95 - violations * 0.25, 0.0)

    def _score_question_discipline(self, response: str) -> float:
        question_count = response.count("?")

        if question_count == 0:
            return 0.7
        elif question_count == 1:
            return 0.95
        elif question_count <= 3:
            return 0.85
        else:
            return 0.6

    def _score_non_repetition(self, response: str, conversation_history: list[str] | None = None) -> float:
        if not conversation_history:
            return 0.8

        response_lower = response.lower()
        repeated_sentences = 0

        for prev_message in conversation_history[-3:]:
            if response_lower in prev_message.lower():
                repeated_sentences += 1

        return max(0.95 - repeated_sentences * 0.3, 0.0)

    def _score_clarity(self, response: str) -> float:
        avg_word_length = sum(len(word) for word in response.split()) / max(len(response.split()), 1)

        if avg_word_length < 4:
            return 0.8
        elif avg_word_length < 5.5:
            return 0.95
        elif avg_word_length < 7:
            return 0.8
        else:
            return 0.6

    def _score_escalation_correctness(self, response: str, risk_level: int) -> float:
        escalation_triggers = ["crisis", "emergency", "resources", "help", "support"]
        response_lower = response.lower()

        has_escalation = any(trigger in response_lower for trigger in escalation_triggers)

        if risk_level >= 3 and has_escalation:
            return 0.95
        elif risk_level >= 3 and not has_escalation:
            return 0.4
        elif risk_level < 2 and not has_escalation:
            return 0.95
        else:
            return 0.7

    def _score_cultural_safety(self, response: str) -> float:
        response_lower = response.lower()
        assumption_markers = [
            "everyone feels", "people always", "all people", "you must",
            "you should always", "normal people", "typical person",
        ]
        violations = sum(1 for m in assumption_markers if m in response_lower)
        inclusive_markers = ["depending on your background", "may vary", "different cultures", "many people"]
        has_inclusive = any(m in response_lower for m in inclusive_markers)
        score = max(0.95 - violations * 0.2, 0.4)
        if has_inclusive:
            score = min(score + 0.05, 1.0)
        return score

    def _generate_feedback(self, result: QualityCriticResult) -> None:
        for dimension, score in result.scores.items():
            if score < 0.65:
                result.concerns.append(
                    f"{dimension}: {self.RUBRIC[dimension]['description']} (Score: {score:.2f})"
                )

                if dimension == "intent_match":
                    result.recommendations.append("Ensure response directly addresses the stated intent")
                elif dimension == "emotional_attunement":
                    result.recommendations.append("Add validation and emotional acknowledgment")
                elif dimension == "evidence_grounding":
                    result.recommendations.append("Add research evidence or clarify as opinion")
                elif dimension == "actionability":
                    result.recommendations.append("Make recommendations more specific and actionable")
                elif dimension == "safety":
                    result.recommendations.append("Review safety implications of response")
                elif dimension == "boundary":
                    result.recommendations.append("Clarify professional boundaries")
                elif dimension == "question_discipline":
                    result.recommendations.append("Consider adding a reflective question")
                elif dimension == "non_repetition":
                    result.recommendations.append("Provide new perspective or fresh angle")
                elif dimension == "clarity":
                    result.recommendations.append("Simplify language and reduce jargon")
                elif dimension == "escalation_correctness":
                    result.recommendations.append("Adjust escalation response based on risk level")
                elif dimension == "cultural_safety":
                    result.recommendations.append("Avoid universal assumptions; use inclusive language")

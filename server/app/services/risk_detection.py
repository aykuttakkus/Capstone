"""
Risk Detection Service - Independent safety layer running parallel to conversation.

This service:
1. Scans user messages and LLM responses for crisis/risk signals
2. Runs AFTER response generation (doesn't gate responses)
3. Is conservative (high false positive acceptable)
4. Returns escalation recommendation for human review
5. Does NOT force template responses or refuse conversations

Key principle: Safety detection is separate from conversation quality.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


_RISK_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3, "crisis": 4}


class RiskLevel(str, Enum):
    """Risk assessment levels with ordering support."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRISIS = "crisis"

    def __lt__(self, other: "RiskLevel") -> bool:
        return _RISK_ORDER[self.value] < _RISK_ORDER[other.value]

    def __le__(self, other: "RiskLevel") -> bool:
        return _RISK_ORDER[self.value] <= _RISK_ORDER[other.value]

    def __gt__(self, other: "RiskLevel") -> bool:
        return _RISK_ORDER[self.value] > _RISK_ORDER[other.value]

    def __ge__(self, other: "RiskLevel") -> bool:
        return _RISK_ORDER[self.value] >= _RISK_ORDER[other.value]


@dataclass(slots=True)
class RiskAssessment:
    """Result of risk detection scan."""

    risk_level: RiskLevel
    risk_indicators: list[str]  # ["suicide_mention", "self_harm", etc.]
    should_escalate: bool
    escalation_reason: Optional[str]
    confidence: float  # 0.0-1.0
    scanned_text: str  # for audit trail


class RiskDetectionService:
    """Detects crisis and safety risk signals."""

    # Explicit crisis signals — direct or paraphrased. Conservative: high false-positive acceptable.
    # VERA-MH (2026): must cover indirect disclosures, not just explicit phrases.
    CRISIS_KEYWORDS = {
        # Direct suicidality
        "suicide", "suicidal",
        "kill myself", "killing myself",
        "end my life", "ending my life",
        "end it all", "ending it all",
        "take my life", "taking my life",
        "want to die", "wanting to die",
        "wish i was dead", "wish i were dead",
        "not worth living", "life isn't worth",
        "no reason to live", "no reason to be alive",
        "don't want to be alive", "don't want to live",
        "want it all to end", "want it all to stop permanently",
        "want everything to stop",
        # Self-harm
        "harm myself", "harming myself",
        "hurt myself", "hurting myself",
        "cut myself", "cutting myself",
        "self-harm", "self harm", "self-mutilat",
        # Overdose / medication crisis
        "overdose", "took too many pills", "taken too many pills",
        "too many pills",
        # Indirect disclosures (VERA-MH persona coverage)
        "jump off", "jump from",
        "no one would miss me", "nobody would miss me",
        "nobody would care if i", "no one would care if i",
        "better off dead",
        "can't go on",
        "don't see a point",
        "planning to end",
        "planning to kill",
        "going to hurt myself",
        # Violence
        "hurt others", "hurt people", "violence",
        # Medication stopping / crisis
        "stop medication", "medication stopping", "stop my meds", "stopping my meds",
    }

    # High-risk signals — elevate to HIGH without explicit crisis language
    HIGH_KEYWORDS = {
        "feel like a burden", "i'm a burden", "i am a burden",
        "burden to everyone", "burden on everyone",
        "no way out", "don't see a way out", "see no way out",
        "trapped", "no escape",
        "life has no meaning", "life feels meaningless",
        "everything is pointless", "nothing is worth it",
        "completely hopeless", "totally hopeless",
        "no point in anything", "there's no point",
        "so exhausted i can't", "too exhausted to go on",
    }

    # Subtle distress signals - cumulative tracking needed
    DISTRESS_SIGNALS = {
        "burden", "better without me", "better off without",
        "meaningless", "pointless", "hopeless", "helpless",
        "tired of everything", "tired of life",
        "can't take it", "numb", "nothing matters",
        "why bother", "give up", "nobody cares",
        "alone", "ashamed", "embarrassed", "worthless",
        "no point",
    }

    # Medication-related signals requiring clinical escalation
    # (AMA 2026: medication discussions in mental health AI must be flagged)
    MEDICATION_CONCERN_PATTERNS = [
        ("medication", "alcohol"),
        ("medicine", "alcohol"),
        ("pill", "alcohol"),
        ("meds", "alcohol"),
        ("medication", "doubl"),          # doubling / double
        ("dosage", "doubl"),
        ("dose", "doubl"),
        ("stop", "medication"),
        ("stop", "medicine"),
        ("stop", "meds"),
        ("stop", "antidepressant"),
        ("stop", "prescription"),
        ("stop", "psychiatric"),
        ("stop taking", "medication"),
        ("stop taking", "antidepressant"),
    ]

    MEDICATION_KEYWORDS = {
        "medication", "medicine", "pill", "drug",
        "antidepressant", "antianxiety", "anti-anxiety",
        "prescription", "dose", "dosage",
        "stop taking", "started taking", "started medication",
    }

    def assess_user_message(self, message: str) -> RiskAssessment:
        """Assess user input for risk signals."""
        risk_level = RiskLevel.NONE
        indicators = []
        confidence = 0.5

        message_lower = message.lower()

        # Tier 1 — Explicit CRISIS signals (direct or paraphrased)
        for keyword in self.CRISIS_KEYWORDS:
            if keyword in message_lower:
                indicators.append(f"crisis_keyword: {keyword}")
                risk_level = RiskLevel.CRISIS
                confidence = 0.95
                break

        # Tier 2 — HIGH signals (no explicit crisis but serious ideation)
        if risk_level == RiskLevel.NONE:
            for keyword in self.HIGH_KEYWORDS:
                if keyword in message_lower:
                    indicators.append(f"high_risk_keyword: {keyword}")
                    risk_level = RiskLevel.HIGH
                    confidence = 0.85
                    break

        # Tier 3 — Subtle cumulative distress
        if risk_level == RiskLevel.NONE:
            distress_count = sum(1 for signal in self.DISTRESS_SIGNALS if signal in message_lower)
            if distress_count >= 2:
                indicators.append(f"subtle_distress: {distress_count}_signals")
                risk_level = RiskLevel.MEDIUM
                confidence = 0.7
            elif distress_count == 1:
                risk_level = RiskLevel.LOW
                confidence = 0.5

        # Tier 4 — Medication concern patterns (AMA 2026 requirement)
        for pair in self.MEDICATION_CONCERN_PATTERNS:
            if all(term in message_lower for term in pair):
                indicators.append(f"medication_concern: {'+'.join(pair)}")
                if risk_level in (RiskLevel.NONE, RiskLevel.LOW):
                    risk_level = RiskLevel.MEDIUM
                confidence = max(confidence, 0.8)
                break

        should_escalate = risk_level in (RiskLevel.CRISIS, RiskLevel.HIGH, RiskLevel.MEDIUM)

        escalation_reason = None
        if should_escalate:
            if risk_level == RiskLevel.CRISIS:
                escalation_reason = "Crisis signal detected — immediate human review recommended"
            elif risk_level == RiskLevel.HIGH:
                escalation_reason = "High-risk ideation detected — human review recommended"
            elif any("medication" in ind for ind in indicators):
                escalation_reason = "Medication-related concern — requires clinical guidance"
            else:
                escalation_reason = "Elevated distress signals detected"

        return RiskAssessment(
            risk_level=risk_level,
            risk_indicators=indicators,
            should_escalate=should_escalate,
            escalation_reason=escalation_reason,
            confidence=confidence,
            scanned_text=message,
        )

    def assess_response(self, user_message: str, ai_response: str) -> RiskAssessment:
        """
        Assess both user message and AI response for safety issues.

        Conservative approach: flag anything that looks like risk.
        """
        # First assess user message
        user_assessment = self.assess_user_message(user_message)

        # If user message is already crisis, return that
        if user_assessment.risk_level == RiskLevel.CRISIS:
            return user_assessment

        # Check if AI response appropriately addressed risk
        ai_response_lower = ai_response.lower()

        # If user showed distress, AI should validate/support (not ignore)
        if user_assessment.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM):
            # Check if AI response includes empathy/validation
            validation_keywords = {"understand", "hear", "validate", "support", "difficult", "tough", "challenging"}
            has_validation = any(keyword in ai_response_lower for keyword in validation_keywords)

            if not has_validation and len(ai_response) > 20:
                # AI didn't validate distressed user - escalate for review
                user_assessment.should_escalate = True
                user_assessment.escalation_reason = (
                    "AI response may not adequately validate user's distress - review recommended"
                )

        # Scan AI response for crisis keywords — if AI detected a crisis signal the
        # user message alone did not trigger, elevate to MEDIUM for human review.
        ai_crisis_signal = any(kw in ai_response_lower for kw in (
            "suicide", "self-harm", "self harm", "harm yourself",
            "hurt yourself", "end your life", "crisis",
        ))
        if ai_crisis_signal and user_assessment.risk_level == RiskLevel.NONE:
            user_assessment.risk_level = RiskLevel.MEDIUM
            user_assessment.risk_indicators.append("ai_response_flagged_crisis")
            user_assessment.should_escalate = True
            user_assessment.escalation_reason = (
                "AI response indicates crisis-adjacent conversation — human review recommended"
            )

        # Check if AI generated unsafe content (boundary violations)
        unsafe_content = {"diagnose", "take this medication", "stop your medication", "prescribe"}
        has_unsafe = any(keyword in ai_response_lower for keyword in unsafe_content)

        if has_unsafe:
            user_assessment.should_escalate = True
            user_assessment.escalation_reason = "AI response may contain unsafe guidance - review recommended"

        return user_assessment

    def track_cumulative_distress(self, conversation_history: list[dict]) -> dict:
        """
        Track distress patterns across multiple turns.

        Returns: {cumulative_distress_score, escalation_needed, pattern_description}
        """
        distress_turns = []
        total_score = 0

        for turn in conversation_history[-10:]:  # Last 10 turns
            if turn.get("role") != "user":
                continue

            assessment = self.assess_user_message(turn.get("content", ""))
            if assessment.risk_level != RiskLevel.NONE:
                distress_turns.append(
                    {
                        "turn": turn,
                        "risk_level": assessment.risk_level,
                        "indicators": assessment.risk_indicators,
                    }
                )
                # Scoring: escalate if pattern emerges
                if assessment.risk_level == RiskLevel.CRISIS:
                    total_score += 5
                elif assessment.risk_level == RiskLevel.HIGH:
                    total_score += 3
                elif assessment.risk_level == RiskLevel.MEDIUM:
                    total_score += 2
                elif assessment.risk_level == RiskLevel.LOW:
                    total_score += 1

        escalation_needed = total_score >= 2 or any(
            turn["risk_level"] == RiskLevel.CRISIS for turn in distress_turns
        )

        pattern_description = ""
        if escalation_needed:
            if total_score >= 5:
                pattern_description = "Escalating distress pattern detected across conversation"
            elif any(turn["risk_level"] == RiskLevel.CRISIS for turn in distress_turns):
                pattern_description = "Crisis signal detected in conversation history"
            else:
                pattern_description = f"Cumulative distress signals ({len(distress_turns)} instances)"

        return {
            "cumulative_score": total_score,
            "distress_turn_count": len(distress_turns),
            "escalation_needed": escalation_needed,
            "pattern_description": pattern_description,
            "recent_turns": distress_turns,
        }

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EscalationLevel(str, Enum):
    """Escalation severity levels."""
    NONE = "none"                    # No escalation needed
    MONITOR = "monitor"              # Monitor but don't escalate
    RECOMMEND_HUMAN = "recommend"    # Recommend human contact
    IMMEDIATE_ESCALATION = "immediate"  # Escalate immediately


@dataclass(slots=True)
class EscalationDecision:
    """Decision on whether to escalate to human support."""
    level: EscalationLevel
    reason: str
    suggested_action: str
    escalation_context: dict[str, str | int | bool]


class HumanEscalationLogic:
    """
    Formal escalation logic that determines when conversations
    should be routed to human support.
    """

    def __init__(self) -> None:
        # Risk thresholds
        self.crisis_threshold = 5
        self.high_risk_threshold = 4
        self.medium_risk_threshold = 2

    def evaluate(
        self,
        risk_level: int,
        distress_signals: list[str],
        conversation_length: int,
        quality_score: float,
        safety_concerns: list[str] | None = None,
        user_explicitly_requested: bool = False,
    ) -> EscalationDecision:
        """
        Evaluate whether conversation should be escalated to human support.

        Args:
            risk_level: Current risk level (0-5)
            distress_signals: List of detected distress categories
            conversation_length: Number of turns so far
            quality_score: Response quality score (0.0-1.0)
            safety_concerns: List of safety concerns detected
            user_explicitly_requested: User explicitly asked for human contact

        Returns:
            EscalationDecision with level, reason, action, context
        """

        safety_concerns = safety_concerns or []

        # IMMEDIATE: User requested human contact
        if user_explicitly_requested:
            return EscalationDecision(
                level=EscalationLevel.IMMEDIATE_ESCALATION,
                reason="User explicitly requested human contact",
                suggested_action="Route to human support immediately",
                escalation_context={
                    "request_type": "explicit_user_request",
                    "priority": "immediate",
                },
            )

        # IMMEDIATE: Crisis (risk level 5)
        if risk_level >= self.crisis_threshold:
            return EscalationDecision(
                level=EscalationLevel.IMMEDIATE_ESCALATION,
                reason="Crisis detected (risk level 5)",
                suggested_action="Activate crisis protocol, route to crisis resources",
                escalation_context={
                    "risk_level": risk_level,
                    "distress_signals": distress_signals,
                    "priority": "life_threatening",
                },
            )

        # IMMEDIATE: Multiple severe safety concerns
        if len(safety_concerns) >= 3:
            return EscalationDecision(
                level=EscalationLevel.IMMEDIATE_ESCALATION,
                reason=f"Multiple safety concerns detected: {', '.join(safety_concerns[:3])}",
                suggested_action="Route to clinical team for assessment",
                escalation_context={
                    "safety_concerns": safety_concerns,
                    "concern_count": len(safety_concerns),
                    "priority": "safety",
                },
            )

        # RECOMMEND: High risk with poor quality response
        if risk_level >= self.high_risk_threshold and quality_score < 0.6:
            return EscalationDecision(
                level=EscalationLevel.RECOMMEND_HUMAN,
                reason="High-risk conversation with low-quality response",
                suggested_action="Recommend user speak with counselor",
                escalation_context={
                    "risk_level": risk_level,
                    "quality_score": quality_score,
                    "reason": "response_quality",
                },
            )

        # RECOMMEND: Persistent high-risk over multiple turns
        if risk_level >= self.high_risk_threshold and conversation_length >= 5:
            return EscalationDecision(
                level=EscalationLevel.RECOMMEND_HUMAN,
                reason="High-risk user showing no improvement after 5+ turns",
                suggested_action="Gently suggest professional support",
                escalation_context={
                    "risk_level": risk_level,
                    "conversation_length": conversation_length,
                    "reason": "persistent_distress",
                },
            )

        # RECOMMEND: Critical distress signals
        critical_signals = {"hopelessness", "burden", "goodbye ideation", "helplessness"}
        detected_critical = set(distress_signals) & critical_signals
        if len(detected_critical) >= 2:
            return EscalationDecision(
                level=EscalationLevel.RECOMMEND_HUMAN,
                reason=f"Critical distress signals: {', '.join(detected_critical)}",
                suggested_action="Recommend professional mental health support",
                escalation_context={
                    "critical_signals": list(detected_critical),
                    "signal_count": len(detected_critical),
                },
            )

        # MONITOR: High risk but stable
        if risk_level >= self.high_risk_threshold:
            return EscalationDecision(
                level=EscalationLevel.MONITOR,
                reason="High-risk conversation - monitor for escalation",
                suggested_action="Continue monitoring, be ready to escalate",
                escalation_context={
                    "risk_level": risk_level,
                    "action": "continue_with_caution",
                },
            )

        # MONITOR: Multiple moderate concerns
        if len(safety_concerns) >= 1 and risk_level >= self.medium_risk_threshold:
            return EscalationDecision(
                level=EscalationLevel.MONITOR,
                reason="Medium risk with safety concerns - monitoring",
                suggested_action="Continue conversation with heightened awareness",
                escalation_context={
                    "risk_level": risk_level,
                    "safety_concern_count": len(safety_concerns),
                },
            )

        # NONE: Low risk, no concerns
        return EscalationDecision(
            level=EscalationLevel.NONE,
            reason="No escalation needed - low risk, good response quality",
            suggested_action="Continue normal conversation",
            escalation_context={
                "risk_level": risk_level,
                "quality_score": quality_score,
            },
        )

    def format_escalation_message(
        self, decision: EscalationDecision, user_name: str = "user"
    ) -> str:
        """Format escalation decision as user-facing message."""

        if decision.level == EscalationLevel.IMMEDIATE_ESCALATION:
            return f"I'm connecting you with immediate support. {decision.suggested_action}"

        elif decision.level == EscalationLevel.RECOMMEND_HUMAN:
            return f"I think it would help to talk with a counselor. {decision.suggested_action}"

        elif decision.level == EscalationLevel.MONITOR:
            return "I'm paying close attention to how you're doing. Please reach out if things get worse."

        else:
            return ""

    def get_escalation_routing(
        self, decision: EscalationDecision
    ) -> dict[str, str | list[str]]:
        """Get routing information for escalation."""

        routing = {
            "level": decision.level.value,
            "reason": decision.reason,
        }

        if decision.level == EscalationLevel.IMMEDIATE_ESCALATION:
            routing["channels"] = [
                "crisis_hotline",
                "emergency_services",
                "clinical_team",
            ]
        elif decision.level == EscalationLevel.RECOMMEND_HUMAN:
            routing["channels"] = ["counselor", "therapist", "support_resources"]
        else:
            routing["channels"] = []

        return routing

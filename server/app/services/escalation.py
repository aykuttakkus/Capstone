"""
Escalation Service - Handles human escalation when risk is detected.

This service:
1. Receives risk assessment from RiskDetectionService
2. Determines escalation action needed
3. Logs session for human review
4. Appends appropriate safety message to response (but doesn't block it)
5. Manages transition to human staff if available

Key principle: Risk detection ≠ response blocking.
A crisis-level risk still gets a supportive LLM response + escalation message.
"""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
from typing import Optional

from server.app.services.risk_detection import RiskLevel


class EscalationAction(str, Enum):
    """Escalation actions based on risk level."""

    NONE = "none"  # No escalation needed
    LOG_FOR_REVIEW = "log_for_review"  # Log session, tag for human review
    NOTIFY_SUPPORT = "notify_support"  # Active notification to support team
    CRISIS_PROTOCOL = "crisis_protocol"  # Immediate crisis response protocol


@dataclass(slots=True)
class EscalationRecord:
    """Record of an escalation event."""

    user_id: int
    session_id: str
    timestamp: datetime
    risk_level: RiskLevel
    risk_indicators: list[str]
    action: EscalationAction
    escalation_message: str
    conversation_excerpt: str  # Last user message
    notes: Optional[str]


class EscalationService:
    """Manages escalation logic and messaging."""

    # Mapping risk level → escalation action
    RISK_ACTION_MAP = {
        RiskLevel.NONE: EscalationAction.NONE,
        RiskLevel.LOW: EscalationAction.NONE,
        RiskLevel.MEDIUM: EscalationAction.LOG_FOR_REVIEW,
        RiskLevel.HIGH: EscalationAction.NOTIFY_SUPPORT,
        RiskLevel.CRISIS: EscalationAction.CRISIS_PROTOCOL,
    }

    # Crisis-level messaging
    CRISIS_MESSAGE = """
⚠️ **If you're in crisis or having thoughts of self-harm, please reach out for immediate support:**

**United States:**
- **988 Suicide & Crisis Lifeline**: Call or text **988** (available 24/7)
- **Crisis Text Line**: Text HOME to **741741**
- **Emergency Services**: Call **911**

**Other countries:**
- International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/

**You deserve support. Please reach out to someone right now.** A trained counselor is ready to listen.
This conversation has been flagged for human review, and a care specialist may reach out to you."""

    # High-risk messaging (elevated distress, needs monitoring)
    HIGH_RISK_MESSAGE = """
I want to make sure you're getting the right support. This conversation has been flagged for our care team to review, and someone may reach out to you to check in.

If you're in crisis or having thoughts of self-harm, please contact the 988 Suicide & Crisis Lifeline (call or text 988) or emergency services immediately."""

    # Medication-related messaging
    MEDICATION_MESSAGE = """
I've noted that you mentioned medication. **Please discuss any changes to your medication with your prescribing doctor, psychiatrist, or pharmacist** — they know your full medical history and can provide personalized guidance.

This is important for your safety. If you have urgent concerns, reach out to them directly."""

    # Cumulative distress messaging
    DISTRESS_MESSAGE = """
I'm noticing you've been expressing some difficult feelings across our conversation. I want to make sure you have the right support.

If you're struggling, talking with a professional therapist or counselor can really help. If things feel urgent, the 988 Suicide & Crisis Lifeline (call or text 988) is available 24/7."""

    @staticmethod
    def determine_action(risk_level: RiskLevel) -> EscalationAction:
        """Determine escalation action based on risk level."""
        return EscalationService.RISK_ACTION_MAP.get(risk_level, EscalationAction.LOG_FOR_REVIEW)

    @staticmethod
    def build_escalation_message(risk_level: RiskLevel, reason: Optional[str] = None) -> str:
        """Build appropriate escalation message based on risk level and reason."""
        if risk_level == RiskLevel.CRISIS:
            return EscalationService.CRISIS_MESSAGE

        if risk_level == RiskLevel.HIGH:
            return EscalationService.HIGH_RISK_MESSAGE

        if reason and "medication" in reason.lower():
            return EscalationService.MEDICATION_MESSAGE

        if reason and "distress" in reason.lower():
            return EscalationService.DISTRESS_MESSAGE

        return ""

    def create_escalation_record(
        self,
        user_id: int,
        session_id: str,
        risk_level: RiskLevel,
        risk_indicators: list[str],
        user_message: str,
        reason: Optional[str] = None,
    ) -> EscalationRecord:
        """Create an escalation record for logging and human review."""
        action = self.determine_action(risk_level)
        message = self.build_escalation_message(risk_level, reason)

        record = EscalationRecord(
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
            risk_level=risk_level,
            risk_indicators=risk_indicators,
            action=action,
            escalation_message=message,
            conversation_excerpt=user_message[:500],  # Last user message (truncated)
            notes=reason,
        )

        return record

    def append_escalation_to_response(self, response_text: str, escalation_message: str) -> str:
        """Append escalation message to response (doesn't block response, just augments it)."""
        if not escalation_message:
            return response_text

        return f"{response_text.strip()}\n\n{escalation_message.strip()}"

    async def log_escalation(self, db, record: EscalationRecord) -> None:
        """
        Persist escalation record to database for human review and GDPR audit trail.

        Required by:
        - GDPR Article 9 (health data processing audit trail)
        - EU AI Act August 2026 (high-risk AI automatic logging, ≥6 month retention)
        - AMA 2026 guidelines (crisis event documentation)
        """
        try:
            from server.app.models.sql.models import EscalationLog
            log_entry = EscalationLog(
                user_id=record.user_id,
                session_id=str(record.session_id),
                risk_level=record.risk_level.value,
                risk_indicators=record.risk_indicators,
                action_taken=record.action.value,
                conversation_excerpt=record.conversation_excerpt[:500] if record.conversation_excerpt else None,
                escalation_reason=record.notes,
                resolved=False,
            )
            db.add(log_entry)
            await db.commit()
        except Exception as exc:
            # Log failure must not crash the response pipeline — user still receives the response.
            # A failed log IS a compliance gap; surface it clearly for operators.
            import logging
            logging.getLogger(__name__).error(
                "COMPLIANCE ERROR: Failed to persist escalation log for user=%s risk=%s: %s",
                record.user_id,
                record.risk_level.value,
                exc,
            )

    async def notify_support_team(self, record: EscalationRecord) -> None:
        """
        Notify support team of escalation event.

        Placeholder for: email, Slack webhook, support ticket system.
        For CRISIS level, this should trigger an immediate notification.
        """
        import logging
        logging.getLogger(__name__).warning(
            "ESCALATION ALERT [%s]: user=%s session=%s indicators=%s",
            record.risk_level.value.upper(),
            record.user_id,
            record.session_id,
            ", ".join(record.risk_indicators) if record.risk_indicators else "none",
        )

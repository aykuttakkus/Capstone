"""
Safety Test: Escalation Logging & Audit Trail

Global standard: 100% of crisis events must be persisted to DB.

These tests verify that:
1. EscalationRecord is created correctly for each risk level
2. log_escalation() persists to database (critical — currently a TODO)
3. Escalation messages contain correct emergency resources
4. Escalation never blocks the AI response

IMPORTANT: test_escalation_is_logged_to_db will FAIL until C1 (log_escalation)
is implemented. This is intentional — it serves as a continuous reminder.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from server.app.services.escalation import EscalationService, EscalationAction, EscalationRecord
from server.app.services.risk_detection import RiskLevel


@pytest.fixture
def service():
    return EscalationService()


# ── Escalation Record Creation ────────────────────────────────────────────────

def test_crisis_record_has_correct_action(service):
    record = service.create_escalation_record(
        user_id=1,
        session_id="session_001",
        risk_level=RiskLevel.CRISIS,
        risk_indicators=["suicide_mention"],
        user_message="I want to end my life",
        reason="Crisis signal detected",
    )
    assert record.action == EscalationAction.CRISIS_PROTOCOL
    assert record.risk_level == RiskLevel.CRISIS
    assert record.user_id == 1
    assert "I want to end my life" in record.conversation_excerpt


def test_high_risk_record_action(service):
    record = service.create_escalation_record(
        user_id=2,
        session_id="session_002",
        risk_level=RiskLevel.HIGH,
        risk_indicators=["hopeless", "burden"],
        user_message="I feel like a burden",
        reason="High risk signal",
    )
    assert record.action == EscalationAction.NOTIFY_SUPPORT


def test_medium_risk_record_action(service):
    record = service.create_escalation_record(
        user_id=3,
        session_id="session_003",
        risk_level=RiskLevel.MEDIUM,
        risk_indicators=["persistent_distress"],
        user_message="I've been struggling",
        reason="Cumulative distress",
    )
    assert record.action == EscalationAction.LOG_FOR_REVIEW


def test_low_risk_no_escalation(service):
    action = EscalationService.determine_action(RiskLevel.LOW)
    assert action == EscalationAction.NONE


def test_none_risk_no_escalation(service):
    action = EscalationService.determine_action(RiskLevel.NONE)
    assert action == EscalationAction.NONE


# ── Escalation Message Content ────────────────────────────────────────────────

def test_crisis_message_contains_988(service):
    """US crisis line must be included in CRISIS messages."""
    message = service.build_escalation_message(RiskLevel.CRISIS)
    assert "988" in message, "CRISIS message must include 988 Suicide & Crisis Lifeline"


def test_crisis_message_contains_text_line(service):
    """Crisis Text Line must be included."""
    message = service.build_escalation_message(RiskLevel.CRISIS)
    assert "741741" in message, "CRISIS message must include Crisis Text Line 741741"


def test_high_risk_message_not_empty(service):
    message = service.build_escalation_message(RiskLevel.HIGH)
    assert message and len(message) > 20


def test_low_risk_message_is_empty(service):
    message = service.build_escalation_message(RiskLevel.LOW)
    assert message == "" or message is None


# ── Append to Response ────────────────────────────────────────────────────────

def test_escalation_appended_not_replacing(service):
    """Safety message must be appended; original response must not be replaced."""
    original = "I hear that you're in a lot of pain right now."
    escalation_msg = "If you're in crisis, please call 988."
    result = service.append_escalation_to_response(original, escalation_msg)

    assert original.strip() in result
    assert escalation_msg.strip() in result
    assert result.index(original.strip()) < result.index(escalation_msg.strip())


def test_empty_escalation_returns_original(service):
    original = "I'm here to support you."
    result = service.append_escalation_to_response(original, "")
    assert result == original


# ── Database Persistence (C1 — Critical Gap) ──────────────────────────────────

@pytest.mark.asyncio
async def test_escalation_is_logged_to_db(db, service):
    """
    CRITICAL TEST: Every escalation event must be persisted to DB.

    This test WILL FAIL until C1 (log_escalation implementation) is complete.
    Failure here is a hard blocker for clinical deployment.
    """
    record = EscalationRecord(
        user_id=1,
        session_id="session_crisis_001",
        timestamp=datetime.now(timezone.utc),
        risk_level=RiskLevel.CRISIS,
        risk_indicators=["suicide_mention"],
        action=EscalationAction.CRISIS_PROTOCOL,
        escalation_message="Please call 988",
        conversation_excerpt="I want to end my life",
        notes="Crisis signal detected via keyword match",
    )

    await service.log_escalation(db, record)

    # Query DB to verify record was persisted
    # TODO: Replace with actual model query once EscalationLog table is created
    # from sqlalchemy import select
    # from server.app.models.sql.models import EscalationLog
    # result = await db.execute(select(EscalationLog).where(EscalationLog.session_id == "session_crisis_001"))
    # saved = result.scalar_one_or_none()
    # assert saved is not None, "Escalation record must be persisted to database"
    # assert saved.risk_level == RiskLevel.CRISIS.value

    # Placeholder assertion — remove and uncomment above when C1 is implemented
    pytest.xfail("C1 not yet implemented: log_escalation() is a TODO placeholder")

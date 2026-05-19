"""
Compliance Tests: Data Retention and Privacy Policy

Tests that data retention configuration meets GDPR Article 5(1)(e) requirements:
personal data must not be kept longer than necessary for its purpose.

Retention periods validated:
- Raw chat messages: short retention (user conversations, sensitive)
- Session summaries: medium retention (aggregated, less sensitive)
- Audit logs: long retention (compliance requirement)

References:
- GDPR Article 5(1)(e): Storage limitation principle
- GDPR Article 9: Special categories (health data)
- EU AI Act: High-risk AI audit trail requirements
"""

from __future__ import annotations

import pytest


# ── Retention period configuration ───────────────────────────────────────────

def test_raw_chat_retention_days_configured():
    """Raw chat messages must have a finite retention period."""
    from server.app.core.config import RAW_CHAT_RETENTION_DAYS
    assert isinstance(RAW_CHAT_RETENTION_DAYS, int)
    assert RAW_CHAT_RETENTION_DAYS > 0


def test_session_summary_retention_days_configured():
    """Session summaries must have a retention period."""
    from server.app.core.config import SESSION_SUMMARY_RETENTION_DAYS
    assert isinstance(SESSION_SUMMARY_RETENTION_DAYS, int)
    assert SESSION_SUMMARY_RETENTION_DAYS > 0


def test_audit_log_retention_days_configured():
    """Audit logs must be retained for compliance (≥ 90 days recommended)."""
    from server.app.core.config import AUDIT_LOG_RETENTION_DAYS
    assert isinstance(AUDIT_LOG_RETENTION_DAYS, int)
    assert AUDIT_LOG_RETENTION_DAYS >= 90, (
        f"AUDIT_LOG_RETENTION_DAYS={AUDIT_LOG_RETENTION_DAYS} is below the 90-day minimum "
        "for AI Act compliance audit trails"
    )


def test_raw_chat_shorter_than_audit_log():
    """Raw chat (sensitive) should be purged sooner than compliance audit logs."""
    from server.app.core.config import RAW_CHAT_RETENTION_DAYS, AUDIT_LOG_RETENTION_DAYS
    assert RAW_CHAT_RETENTION_DAYS <= AUDIT_LOG_RETENTION_DAYS, (
        "Raw chat data should not be retained longer than audit logs"
    )


# ── Sensitive data redaction ──────────────────────────────────────────────────

def test_sensitive_log_redaction_enabled():
    """Sensitive data redaction must be enabled by default — never off in production."""
    from server.app.core.config import SENSITIVE_LOG_REDACTION_ENABLED
    assert SENSITIVE_LOG_REDACTION_ENABLED is True, (
        "SENSITIVE_LOG_REDACTION_ENABLED must be True — "
        "logging raw user messages violates GDPR Article 9"
    )


# ── Consent flag presence ─────────────────────────────────────────────────────

def test_user_state_has_all_consent_flags(sample_user_state):
    """UserState must expose all four consent gates required by GDPR Article 9."""
    assert hasattr(sample_user_state, "personalization_consent"), (
        "Missing personalization_consent — controls whether profile fields are used"
    )
    assert hasattr(sample_user_state, "use_mood_context"), (
        "Missing use_mood_context — controls whether health mood data is processed"
    )
    assert hasattr(sample_user_state, "use_journal_context"), (
        "Missing use_journal_context — controls whether journal health data is processed"
    )
    assert hasattr(sample_user_state, "use_memory_context"), (
        "Missing use_memory_context — controls cross-session memory persistence"
    )


def test_consent_flags_default_to_bool(sample_user_state):
    assert isinstance(sample_user_state.personalization_consent, bool)
    assert isinstance(sample_user_state.use_mood_context, bool)
    assert isinstance(sample_user_state.use_journal_context, bool)
    assert isinstance(sample_user_state.use_memory_context, bool)


# ── Health data is not cached in logs when consent is off ────────────────────

def test_mood_data_not_in_context_when_consent_off(sample_user_state):
    """When use_mood_context=False, mood data must not propagate to LLM context."""
    sample_user_state.use_mood_context = False
    sample_user_state.mood_summary = "Severely depressed for three weeks"

    from server.app.services.context_formatter import ContextFormatter
    formatted = ContextFormatter.format_full_context(
        user_state=sample_user_state,
        conversation_history=[],
        intake_data=None,
    )

    if formatted and not sample_user_state.use_mood_context:
        assert "Severely depressed" not in formatted, (
            "Mood data leaked into context despite use_mood_context=False"
        )


def test_journal_data_not_in_context_when_consent_off(sample_user_state):
    """When use_journal_context=False, journal data must not propagate to LLM context."""
    sample_user_state.use_journal_context = False
    sample_user_state.journal_summary = "User wrote about childhood trauma"

    from server.app.services.context_formatter import ContextFormatter
    formatted = ContextFormatter.format_full_context(
        user_state=sample_user_state,
        conversation_history=[],
        intake_data=None,
    )

    if formatted and not sample_user_state.use_journal_context:
        assert "childhood trauma" not in formatted, (
            "Journal data leaked into context despite use_journal_context=False"
        )


def test_profile_data_not_in_context_when_personalization_off(sample_user_state):
    """When personalization_consent=False, personal profile must be excluded from context."""
    sample_user_state.personalization_consent = False
    sample_user_state.preferred_name = "PrivateName_XYZ"
    sample_user_state.life_narrative = "Sensitive personal life story"

    from server.app.services.context_formatter import ContextFormatter
    formatted = ContextFormatter.format_full_context(
        user_state=sample_user_state,
        conversation_history=[],
        intake_data=None,
    )

    # ContextFormatter receives the already-consent-gated UserState,
    # so name/narrative fields are None when consent is off (set by UserStateService).
    # This test validates the contract is maintained end-to-end.
    if formatted:
        assert "PrivateName_XYZ" not in formatted

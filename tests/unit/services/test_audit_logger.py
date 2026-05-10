from __future__ import annotations

import json
from pathlib import Path

import pytest

from server.app.utils.audit_logger import ClinicalAuditLogger


pytestmark = [pytest.mark.unit]


def test_audit_logger_writes_events_when_path_is_writable(tmp_path: Path) -> None:
    logger = ClinicalAuditLogger(str(tmp_path / "logs" / "clinical_audit.json"))
    logger.log_event(1, "I have anxiety", "topic:stress_anxiety", "concerned", "normal", 12.5)

    payload = json.loads((tmp_path / "logs" / "clinical_audit.json").read_text(encoding="utf-8"))
    assert len(payload) == 1
    assert payload[0]["route"] == "topic:stress_anxiety"


def test_audit_logger_redacts_email_and_phone(tmp_path: Path) -> None:
    logger = ClinicalAuditLogger(str(tmp_path / "logs" / "clinical_audit.json"))
    logger.log_event(1, "Email me at user@example.com or call +1 (555) 123-4567", "topic:stress_anxiety", "concerned", "normal", 12.5)

    payload = json.loads((tmp_path / "logs" / "clinical_audit.json").read_text(encoding="utf-8"))
    assert payload[0]["query_preview"]
    assert "user@example.com" not in payload[0]["query_preview"]
    assert "555" not in payload[0]["query_preview"]
    assert "[REDACTED_EMAIL]" in payload[0]["query_preview"]
    assert "[REDACTED_PHONE]" in payload[0]["query_preview"]


def test_audit_logger_fails_open_when_directory_cannot_be_created(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "blocked" / "clinical_audit.json"

    def boom(self, parents=False, exist_ok=False):  # type: ignore[no-untyped-def]
        raise PermissionError("blocked")

    monkeypatch.setattr(Path, "mkdir", boom)

    logger = ClinicalAuditLogger(str(target))
    assert logger.enabled is False
    logger.log_event(1, "I have anxiety", "topic:stress_anxiety", "concerned", "normal", 12.5)

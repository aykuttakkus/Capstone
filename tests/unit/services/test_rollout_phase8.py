from __future__ import annotations

import pytest

from server.app.services.rollout import should_enable_feature


pytestmark = [pytest.mark.unit]


def test_rollout_decision_defaults_to_enabled_in_stable_mode(monkeypatch) -> None:
    monkeypatch.setenv("ROLLOUT_MODE", "stable")
    monkeypatch.setenv("ROLLOUT_TRAFFIC_PERCENT", "0")

    decision = should_enable_feature(42)

    assert decision.enabled is True
    assert decision.mode == "stable"


def test_rollout_decision_disables_when_off(monkeypatch) -> None:
    monkeypatch.setenv("ROLLOUT_MODE", "off")
    monkeypatch.setenv("ROLLOUT_TRAFFIC_PERCENT", "100")

    decision = should_enable_feature(42)

    assert decision.enabled is False
    assert decision.reason == "rollout_disabled"


def test_rollout_decision_uses_canary_bucket(monkeypatch) -> None:
    monkeypatch.setenv("ROLLOUT_MODE", "canary")
    monkeypatch.setenv("ROLLOUT_TRAFFIC_PERCENT", "50")

    decision = should_enable_feature(17)

    assert decision.mode == "canary"
    assert isinstance(decision.enabled, bool)
    assert decision.reason.startswith("bucket_") or decision.reason == "missing_user_id"

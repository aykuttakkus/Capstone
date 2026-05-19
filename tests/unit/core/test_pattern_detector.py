from __future__ import annotations

import pytest

from server.app.core.agents.pattern_detector import (
    detect_change_talk_patterns,
    detect_cognitive_distortions,
    detect_cross_session_patterns,
    detect_within_session_patterns,
)


pytestmark = [pytest.mark.unit]


def test_detect_within_session_patterns_flags_repeated_word() -> None:
    patterns = detect_within_session_patterns(
        [
            {"role": "user", "content": "Boşuna yine boşuna hissediyorum", "route": "topic:stress"},
            {"role": "assistant", "content": "Tell me more", "route": "topic:stress"},
            {"role": "user", "content": "Bu boşuna gibi geliyor", "route": "topic:stress"},
            {"role": "user", "content": "Boşuna, boşuna, boşuna", "route": "topic:stress"},
        ]
    )

    assert any("boşuna" in item for item in patterns)


def test_detect_cross_session_patterns_flags_recurring_theme() -> None:
    patterns = detect_cross_session_patterns(
        {
            "recurring_themes": [
                {"theme": "uyku güçlüğü", "count": 4, "last_seen": "2026-05-17"},
                {"theme": "iş yükü", "count": 2, "last_seen": "2026-05-17"},
            ]
        }
    )

    assert patterns == ["'uyku güçlüğü' 4 seanstır gündemde"]


def test_detect_cognitive_distortions_recognizes_all_or_nothing() -> None:
    distortions = detect_cognitive_distortions(
        [{"role": "user", "content": "Hiçbir şeyi doğru yapamıyorum, her zaman böyle."}]
    )

    assert "all_or_nothing" in distortions


def test_detect_change_talk_patterns_detects_desire_and_commitment() -> None:
    patterns = detect_change_talk_patterns("I want to try and I will start tomorrow.")

    assert "desire" in patterns
    assert "commitment" in patterns

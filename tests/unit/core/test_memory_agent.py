from __future__ import annotations

import json

import pytest

from server.app.core.agents.memory_agent import MemoryAgent
from server.app.core.generation.base import MockLLMBackend, UnavailableLLMBackend


pytestmark = [pytest.mark.unit]


def test_parse_legacy_text_migrates_to_structured_schema() -> None:
    parsed = MemoryAgent.parse("Topic: burnout. Intent: emotional_support.")

    assert parsed["v"] == 2
    assert parsed["recurring_themes"]
    assert parsed["last_session_topic"].startswith("Topic: burnout")
    assert parsed["last_session_date"]


def test_parse_json_normalizes_lists_and_trend() -> None:
    parsed = MemoryAgent.parse(
        json.dumps(
            {
                "preferred_name": "Zeynep",
                "recurring_themes": [{"theme": "iş yükü", "count": "3", "last_seen": "2026-05-17"}],
                "user_vocabulary": ["boşuna", "boşuna", "sıkışmış"],
                "mood_trend": [4, "6", 5],
            },
            ensure_ascii=False,
        )
    )

    assert parsed["preferred_name"] == "Zeynep"
    assert parsed["recurring_themes"][0]["count"] == 3
    assert parsed["user_vocabulary"] == ["boşuna", "sıkışmış"]
    assert parsed["mood_trend"] == [4, 6, 5]


def test_mood_trend_summary_reports_direction() -> None:
    summary = MemoryAgent.mood_trend_summary({"mood_trend": [4, 5, 7]})

    assert "recent: [4, 5, 7]" in summary
    assert "improving" in summary


def test_summarize_interaction_falls_back_to_json_when_llm_is_offline() -> None:
    agent = MemoryAgent(llm=UnavailableLLMBackend())
    result = agent.summarize_interaction(
        user_msg="I feel stuck with work and sleep.",
        ai_msg="Let's keep this simple and focus on sleep first.",
        current_memory="Topic: burnout. Intent: emotional_support.",
        mood_score=4,
    )

    parsed = json.loads(result)

    assert parsed["v"] == 2
    assert parsed["recurring_themes"]
    assert parsed["mood_trend"]


def test_summarize_interaction_merges_structured_llm_output() -> None:
    agent = MemoryAgent(
        llm=MockLLMBackend(
            text=json.dumps(
                {
                    "preferred_name": "Aykut",
                    "recurring_themes": [{"theme": "stress", "count": 2, "last_seen": "2026-05-17"}],
                    "mood_trend": [5, 6],
                },
                ensure_ascii=False,
            )
        )
    )

    result = agent.summarize_interaction("work is intense", "try a walk", "{}", mood_score=7)
    parsed = json.loads(result)

    assert parsed["preferred_name"] == "Aykut"
    assert parsed["mood_trend"][-1] == 7
    assert parsed["recurring_themes"][0]["theme"] == "stress"

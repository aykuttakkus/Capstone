from __future__ import annotations

import pytest


pytestmark = [pytest.mark.integration]


def test_profile_round_trip(api_client, auth_headers) -> None:
    update_response = api_client.put(
        "/api/profile/",
        headers=auth_headers,
        json={
            "preferred_name": "Aykut",
            "communication_style": "Direct_and_Practical",
            "response_length_preference": "Balanced",
            "use_mood_context": True,
            "use_journal_context": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["preferred_name"] == "Aykut"

    summary_response = api_client.get("/api/profile/summary", headers=auth_headers)
    assert summary_response.status_code == 200
    assert "profile" in summary_response.json()["context_sources"]


def test_mood_and_journal_endpoints_return_personalization_data(api_client, auth_headers) -> None:
    mood_response = api_client.post(
        "/api/mood/",
        headers=auth_headers,
        json={"mood_score": 3, "anxiety_score": 8, "sleep_quality": 4, "notes": "Poor sleep this week"},
    )
    assert mood_response.status_code == 200

    trend_response = api_client.get("/api/mood/trend", headers=auth_headers)
    assert trend_response.status_code == 200
    assert "summary" in trend_response.json()

    journal_response = api_client.post(
        "/api/journal/",
        headers=auth_headers,
        json={"title": "Week note", "content": "I feel stress and anxiety before exams.", "consent_for_chat": True},
    )
    assert journal_response.status_code == 200
    assert journal_response.json()["topics"] != []

    insight_response = api_client.get("/api/journal/insights", headers=auth_headers)
    assert insight_response.status_code == 200
    assert "entries" in insight_response.json()

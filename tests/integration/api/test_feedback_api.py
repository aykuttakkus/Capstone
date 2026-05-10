from __future__ import annotations

import pytest


pytestmark = [pytest.mark.integration]


def test_feedback_create_and_list(api_client, auth_headers) -> None:
    created = api_client.post(
        "/api/feedback/",
        headers=auth_headers,
        json={
            "session_id": None,
            "message_id": None,
            "route": "topic:stress_anxiety",
            "helpful": True,
            "comment": "Useful answer.",
        },
    )
    assert created.status_code == 201
    assert created.json()["helpful"] == "yes"

    listed = api_client.get("/api/feedback/", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

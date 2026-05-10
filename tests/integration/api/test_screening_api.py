from __future__ import annotations

import pytest


pytestmark = [pytest.mark.integration]


def test_screening_progression_updates_user_state(api_client, auth_headers) -> None:
    phq9 = api_client.post(
        "/api/screen/",
        headers=auth_headers,
        json={"test_type": "phq9", "answers": {f"q{i}": 1 for i in range(1, 10)}},
    )
    assert phq9.status_code == 200
    assert phq9.json()["scale_name"] == "PHQ-9"

    gad7 = api_client.post(
        "/api/screen/",
        headers=auth_headers,
        json={"test_type": "gad7", "answers": {f"q{i}": 1 for i in range(1, 8)}},
    )
    assert gad7.status_code == 200
    assert gad7.json()["scale_name"] == "GAD-7"

    me = api_client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json()["screening_completed"] is True
    assert me.json()["next_required_step"] == "chat"

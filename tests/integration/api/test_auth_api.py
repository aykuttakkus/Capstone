from __future__ import annotations

import pytest


pytestmark = [pytest.mark.integration]


def test_register_login_and_me_flow(api_client) -> None:
    register = api_client.post(
        "/api/auth/register",
        json={"email": "person@example.com", "password": "Password123"},
    )
    assert register.status_code == 201
    assert register.json()["next_required_step"] == "screening"

    login = api_client.post(
        "/api/auth/login",
        json={"email": "person@example.com", "password": "Password123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = api_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "person@example.com"


def test_me_requires_authentication(api_client) -> None:
    response = api_client.get("/api/auth/me")
    assert response.status_code == 401

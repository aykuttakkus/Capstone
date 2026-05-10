from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

import server.app.main as main_module
from server.app.core.database import get_db
from server.app.services.assistant import get_service


@pytest.fixture
def test_app(db_engine, db_session_factory, monkeypatch):
    async def override_get_db() -> AsyncIterator[object]:
        async with db_session_factory() as session:
            yield session

    monkeypatch.setattr(main_module, "engine", db_engine)
    main_module.app.dependency_overrides[get_db] = override_get_db
    get_service.cache_clear()
    yield main_module.app
    get_service.cache_clear()
    main_module.app.dependency_overrides.clear()


@pytest.fixture
def api_client(test_app):
    with TestClient(test_app) as client:
        yield client


@pytest.fixture
def auth_headers(api_client):
    email = "api-user@example.com"
    password = "Password123"
    register_response = api_client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    login_response = api_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

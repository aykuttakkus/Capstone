from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import select

from server.app.models.sql.models import User
from tests.factories.sessions import create_session_with_turn


pytestmark = [pytest.mark.integration]


def test_sessions_endpoints_list_detail_archive_export_and_delete(api_client, auth_headers, db_session_factory) -> None:
    async def seed() -> int:
        async with db_session_factory() as db:
            user = (await db.execute(select(User).where(User.email == "api-user@example.com"))).scalar_one()
            session = await create_session_with_turn(db, user)
            return session.id

    session_id = asyncio.run(seed())

    listing = api_client.get("/api/sessions/", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    detail = api_client.get(f"/api/sessions/{session_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 2

    archive = api_client.post(f"/api/sessions/{session_id}/archive", headers=auth_headers)
    assert archive.status_code == 200
    assert archive.json()["status"] == "archived"

    exported = api_client.get(f"/api/sessions/{session_id}/export?format=markdown", headers=auth_headers)
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/markdown")

    deleted = api_client.delete(f"/api/sessions/{session_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_sessions_list_accepts_both_with_and_without_trailing_slash(
    api_client,
    auth_headers,
    db_session_factory,
) -> None:
    async def seed() -> None:
        async with db_session_factory() as db:
            user = (await db.execute(select(User).where(User.email == "api-user@example.com"))).scalar_one()
            await create_session_with_turn(db, user, title="Trailing slash guard")

    asyncio.run(seed())

    no_slash = api_client.get("/api/sessions", headers=auth_headers, follow_redirects=False)
    with_slash = api_client.get("/api/sessions/", headers=auth_headers, follow_redirects=False)

    assert no_slash.status_code == 200
    assert with_slash.status_code == 200

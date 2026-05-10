from __future__ import annotations

import pytest

from tests.factories.sessions import create_session_with_turn
from server.app.services.session_store import (
    archive_session,
    delete_session,
    export_session_json,
    export_session_markdown,
    list_sessions,
    load_session_thread,
    search_sessions,
)


pytestmark = [pytest.mark.unit, pytest.mark.anyio]


async def test_session_store_supports_restore_search_archive_export_and_delete(
    db_session_factory,
    authenticated_user,
) -> None:
    async with db_session_factory() as db:
        session = await create_session_with_turn(db, authenticated_user)

        sessions = await list_sessions(db, authenticated_user.id)
        searched = await search_sessions(db, authenticated_user.id, query="stress")
        thread = await load_session_thread(db, authenticated_user.id, session.id)

        assert len(sessions) == 1
        assert searched[0].id == session.id
        assert len(thread.messages) == 2

        archived = await archive_session(db, authenticated_user.id, session.id)
        await db.commit()
        assert archived.status == "archived"

        thread = await load_session_thread(db, authenticated_user.id, session.id)
        exported_json = export_session_json(thread)
        exported_markdown = export_session_markdown(thread)
        assert exported_json["session"]["id"] == session.id
        assert "# Stress support" in exported_markdown

        await delete_session(db, authenticated_user.id, session.id)
        await db.commit()
        assert await list_sessions(db, authenticated_user.id) == []

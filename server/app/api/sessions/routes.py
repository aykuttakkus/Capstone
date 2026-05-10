from __future__ import annotations

import json
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.core.database import get_db
from server.app.core.security import get_current_user
from server.app.models.schemas.session import SessionListItem, SessionRead, SessionMessageRead
from server.app.models.sql.models import User
from server.app.services.session_store import (
    archive_session,
    delete_session,
    export_session_json,
    export_session_markdown,
    list_sessions,
    load_session_thread,
    search_sessions,
    summarize_session_for_debug,
)


router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("", response_model=list[SessionListItem], include_in_schema=False)
@router.get("/", response_model=list[SessionListItem])
async def session_list(
    query: str | None = Query(default=None, description="Search title, topic, or summary"),
    topic: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    safety_mode: str | None = Query(default=None),
    created_on: date | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SessionListItem]:
    if any([query, topic, status_filter, safety_mode, created_on]):
        sessions = await search_sessions(
            db,
            current_user.id,
            query=query,
            topic=topic,
            status=status_filter,
            safety_mode=safety_mode,
            created_on=created_on,
            limit=limit,
        )
    else:
        sessions = await list_sessions(db, current_user.id, limit=limit)
    return [SessionListItem.model_validate(session) for session in sessions]


@router.get("/{session_id}", response_model=SessionRead)
async def session_detail(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionRead:
    try:
        thread = await load_session_thread(db, current_user.id, session_id)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    return SessionRead(
        id=thread.session.id,
        title=thread.session.title,
        topic=thread.session.topic,
        status=thread.session.status,
        summary=thread.session.summary,
        last_safety_mode=thread.session.last_safety_mode,
        intake=_decode_json(thread.session.intake_json),
        consent=_decode_json(thread.session.consent_json),
        created_at=thread.session.created_at,
        last_message_at=thread.session.last_message_at,
        archived_at=thread.session.archived_at,
        messages=[SessionMessageRead.model_validate(message) for message in thread.messages],
    )


@router.get("/{session_id}/summary")
async def session_summary_debug(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        thread = await load_session_thread(db, current_user.id, session_id)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    return summarize_session_for_debug(thread)


def _decode_json(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


@router.post("/{session_id}/archive", response_model=SessionListItem)
async def archive_session_route(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionListItem:
    try:
        session = await archive_session(db, current_user.id, session_id)
        await db.commit()
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    return SessionListItem.model_validate(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_route(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        await delete_session(db, current_user.id, session_id)
        await db.commit()
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{session_id}/export")
async def export_session_route(
    session_id: int,
    format: str = Query(default="json", pattern="^(json|markdown)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        thread = await load_session_thread(db, current_user.id, session_id)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    if format == "markdown":
        return Response(
            content=export_session_markdown(thread),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="session-{session_id}.md"'},
        )

    return export_session_json(thread)

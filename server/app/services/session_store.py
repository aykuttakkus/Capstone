from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models.sql.models import ChatMessage, ChatSession
from server.app.services.session import build_session_summary, prune_memory_text


@dataclass(slots=True)
class SessionThread:
    session: ChatSession
    messages: list[ChatMessage]


def _serialize_json(value: object | None) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _deserialize_json(value: str | None) -> object | None:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def build_session_title(message: str, topic: str | None = None) -> str:
    if topic and topic != "general":
        return topic.replace("_", " ").title()
    cleaned = " ".join(message.split())
    return (cleaned[:48].rstrip() or "New session")


async def ensure_session(
    db: AsyncSession,
    user_id: int,
    session_id: int | None = None,
    *,
    title: str | None = None,
    topic: str | None = None,
    intake: dict | None = None,
    consent: dict | None = None,
) -> ChatSession:
    if session_id is not None:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise LookupError("Session not found.")
        if title and session.title == "New session":
            session.title = title
        if topic and not session.topic:
            session.topic = topic
        return session

    session = ChatSession(
        user_id=user_id,
        title=title or "New session",
        topic=topic,
        status="active",
        intake_json=_serialize_json(intake),
        consent_json=_serialize_json(consent),
        last_message_at=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.flush()
    return session


async def append_session_turn(
    db: AsyncSession,
    session: ChatSession,
    user_id: int,
    *,
    query: str,
    response: str,
    intent: str,
    route: str,
    safety_mode: str,
    sources: list[dict] | None = None,
    intake: dict | None = None,
) -> None:
    now = datetime.now(timezone.utc)
    user_message = ChatMessage(
        session_id=session.id,
        user_id=user_id,
        role="user",
        content=query,
        intent=intent,
        route=route,
        safety_mode=safety_mode,
    )
    assistant_message = ChatMessage(
        session_id=session.id,
        user_id=user_id,
        role="assistant",
        content=response,
        intent=intent,
        route=route,
        safety_mode=safety_mode,
        sources_json=_serialize_json(sources),
    )

    db.add_all([user_message, assistant_message])

    if not session.title or session.title == "New session":
        session.title = build_session_title(query, session.topic)

    if not session.topic and route.startswith("topic:"):
        session.topic = route.split(":", 1)[1]

    if session.summary:
        session.summary = prune_memory_text(session.summary, max_lines=5, max_chars=420)

    session.summary = build_session_summary(
        intake or {},
        response,
        topic=session.topic or route,
        intent=intent,
        safety_mode=safety_mode,
        previous_summary=session.summary,
    ).recap
    session.last_safety_mode = safety_mode
    session.last_message_at = now
    session.status = "active"
    await db.flush()


async def list_sessions(db: AsyncSession, user_id: int, limit: int = 10) -> list[ChatSession]:
    limit = max(1, min(limit, 100))
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(func.coalesce(ChatSession.last_message_at, ChatSession.created_at).desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def search_sessions(
    db: AsyncSession,
    user_id: int,
    *,
    query: str | None = None,
    topic: str | None = None,
    status: str | None = None,
    safety_mode: str | None = None,
    created_on: date | None = None,
    limit: int = 25,
) -> list[ChatSession]:
    limit = max(1, min(limit, 100))
    stmt = select(ChatSession).where(ChatSession.user_id == user_id)

    if status and status != "all":
        stmt = stmt.where(func.lower(ChatSession.status) == status.lower())

    if topic:
        pattern = f"%{topic.lower()}%"
        stmt = stmt.where(func.lower(func.coalesce(ChatSession.topic, "")).like(pattern))

    if safety_mode:
        stmt = stmt.where(func.lower(func.coalesce(ChatSession.last_safety_mode, "")).like(f"%{safety_mode.lower()}%"))

    if created_on:
        stmt = stmt.where(func.date(ChatSession.created_at) == created_on.isoformat())

    if query:
        pattern = f"%{query.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(func.coalesce(ChatSession.title, "")).like(pattern),
                func.lower(func.coalesce(ChatSession.topic, "")).like(pattern),
                func.lower(func.coalesce(ChatSession.summary, "")).like(pattern),
            )
        )

    result = await db.execute(
        stmt.order_by(func.coalesce(ChatSession.last_message_at, ChatSession.created_at).desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_latest_session(db: AsyncSession, user_id: int) -> ChatSession | None:
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(func.coalesce(ChatSession.last_message_at, ChatSession.created_at).desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def archive_session(db: AsyncSession, user_id: int, session_id: int) -> ChatSession:
    thread = await load_session_thread(db, user_id, session_id)
    thread.session.status = "archived"
    thread.session.archived_at = datetime.now(timezone.utc)
    await db.flush()
    return thread.session


async def delete_session(db: AsyncSession, user_id: int, session_id: int) -> None:
    await load_session_thread(db, user_id, session_id)
    await db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id, ChatMessage.user_id == user_id))
    await db.execute(delete(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id))
    await db.flush()


async def load_session_thread(db: AsyncSession, user_id: int, session_id: int) -> SessionThread:
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
    )
    session = session_result.scalar_one_or_none()
    if session is None:
        raise LookupError("Session not found.")

    messages_result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == user_id,
        )
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
    )
    return SessionThread(session=session, messages=list(messages_result.scalars().all()))


def summarize_session_for_debug(thread: SessionThread) -> dict[str, object]:
    return {
        "session_id": thread.session.id,
        "title": thread.session.title,
        "topic": thread.session.topic,
        "status": thread.session.status,
        "summary": prune_memory_text(thread.session.summary, max_lines=5, max_chars=420),
        "message_count": len(thread.messages),
    }


def export_session_json(thread: SessionThread) -> dict:
    session = thread.session
    return {
        "session": {
            "id": session.id,
            "title": session.title,
            "topic": session.topic,
            "status": session.status,
            "summary": session.summary,
            "last_safety_mode": session.last_safety_mode,
            "intake": _deserialize_json(session.intake_json),
            "consent": _deserialize_json(session.consent_json),
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
            "archived_at": session.archived_at.isoformat() if session.archived_at else None,
        },
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "intent": message.intent,
                "route": message.route,
                "safety_mode": message.safety_mode,
                "sources": _deserialize_json(message.sources_json),
                "created_at": message.created_at.isoformat() if message.created_at else None,
            }
            for message in thread.messages
        ],
    }


def export_session_markdown(thread: SessionThread) -> str:
    data = export_session_json(thread)
    session = data["session"]
    lines = [
        f"# {session['title']}",
        "",
        f"- Topic: {session['topic'] or 'n/a'}",
        f"- Status: {session['status']}",
        f"- Safety mode: {session['last_safety_mode'] or 'n/a'}",
        f"- Created at: {session['created_at'] or 'n/a'}",
    ]
    if session.get("summary"):
        lines.extend(["", "## Summary", "", str(session["summary"])])

    lines.extend(["", "## Messages", ""])
    for message in data["messages"]:
        lines.extend([
            f"### {message['role'].title()}",
            "",
            message["content"],
            "",
        ])

    return "\n".join(lines).strip() + "\n"

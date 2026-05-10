from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import select

import server.app.api.chat.routes as chat_routes
from server.app.models.schemas.chat import ChatResponse
from server.app.models.sql.models import Conversation, User


pytestmark = [pytest.mark.integration]


class FakeChatService:
    async def handle_message(self, message, user, db, session_id=None, new_session=False, intake=None, screening=None, history=None, personalization=None, background_tasks=None):
        db.add(
            Conversation(
                user_id=user.id,
                query=message,
                response="Grounded answer",
                safety_mode="normal",
                latency_ms=12.0,
            )
        )
        await db.commit()
        return ChatResponse(
            session_id=1,
            status="ok",
            route="topic:stress_anxiety",
            intent="psychoeducation",
            safety_mode="normal",
            summary="psychoeducation",
            answer="Grounded answer",
            follow_up=["Ask a follow-up"],
            sources=[
                {
                    "title": "Stress basics",
                    "source": "Test corpus",
                    "topic": "stress_anxiety",
                    "score": 0.98,
                    "excerpt": "Stress can disrupt sleep.",
                    "rank": 1,
                    "source_kind": "user_corpus",
                    "language": "en",
                    "confidence": 0.95,
                    "section": "Page 1",
                    "page": 1,
                    "reason_tags": ["topic_match"],
                }
            ],
            retrieval_diagnostics=[
                {
                    "rank": 1,
                    "chunk_id": "stress-001",
                    "title": "Stress basics",
                    "topic": "stress_anxiety",
                    "score": 0.98,
                    "source_kind": "user_corpus",
                    "language": "en",
                    "confidence": 0.95,
                    "topic_alignment": "exact",
                    "query_overlap": 3,
                    "reason_tags": ["topic_match"],
                }
            ],
            source_highlight="Stress basics · Page 1 · user corpus",
            personalization_applied=True,
            personalization_signals=["profile"],
            context_used={"profile": True},
        )


def test_chat_requires_authentication(api_client) -> None:
    response = api_client.post("/api/chat/", json={"message": "Hello"})
    assert response.status_code == 401


def test_chat_returns_valid_response_and_persists_history(api_client, auth_headers, monkeypatch, db_session_factory) -> None:
    monkeypatch.setattr(chat_routes, "get_service", lambda: FakeChatService())

    response = api_client.post(
        "/api/chat/",
        headers=auth_headers,
        json={"message": "Tell me about stress"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "topic:stress_anxiety"
    assert body["answer"] == "Grounded answer"
    assert body["source_highlight"] == "Stress basics · Page 1 · user corpus"
    assert body["sources"][0]["source_kind"] == "user_corpus"
    assert body["sources"][0]["language"] == "en"

    async def verify() -> None:
        async with db_session_factory() as db:
            conversations = list((await db.execute(select(Conversation))).scalars())
            assert len(conversations) == 1

    asyncio.run(verify())


def test_chat_history_returns_recent_conversations(api_client, auth_headers, db_session_factory) -> None:
    async def seed() -> None:
        async with db_session_factory() as db:
            user = (await db.execute(select(User).where(User.email == "api-user@example.com"))).scalar_one()
            db.add(
                Conversation(
                    user_id=user.id,
                    query="Earlier question",
                    response="Earlier answer",
                    safety_mode="normal",
                    latency_ms=8.0,
                )
            )
            await db.commit()

    asyncio.run(seed())

    response = api_client.get("/api/chat/history", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()[0]["query"] == "Earlier question"

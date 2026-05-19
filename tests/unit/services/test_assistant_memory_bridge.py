from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

import pytest
from sqlalchemy import select

from server.app.core.agents.memory_agent import MemoryAgent
from server.app.core.agents.response_planner import ResponsePlanner
from server.app.core.generation.base import UnavailableLLMBackend
from server.app.models.sql.models import ChatMessage, ChatSession, Memory
from server.app.services.assistant import AssistantService
from server.app.utils.privacy import encrypt_clinical_data, decrypt_clinical_data


pytestmark = [pytest.mark.unit, pytest.mark.anyio]


def _build_service() -> AssistantService:
    service = AssistantService.__new__(AssistantService)
    service.memory_agent = MemoryAgent(UnavailableLLMBackend())
    service.response_planner = ResponsePlanner()
    return service


async def test_user_memory_round_trip_keeps_full_json(db_session_factory, authenticated_user) -> None:
    service = _build_service()
    raw_memory = json.dumps(
        {
            "v": 2,
            "preferred_name": "Aykut",
            "recurring_themes": [{"theme": "stress", "count": 4, "last_seen": "2026-05-17"}],
            "user_vocabulary": ["stuck", "overloaded", "numb", "tired", "drained", "foggy", "tense"],
            "what_helped": ["walks", "journaling"],
            "key_people": ["friend", "sister"],
            "mood_trend": [4, 5, 6, 5, 7],
            "milestone_moments": ["named the pattern"],
            "active_action_plan": "take a walk after work",
            "last_session_topic": "work stress",
            "last_session_date": "2026-05-14",
        },
        ensure_ascii=False,
    )

    async with db_session_factory() as db:
        await service._update_user_memory(db, authenticated_user.id, raw_memory)
        loaded = await service._get_user_memory(db, authenticated_user.id)

        assert loaded == raw_memory
        assert len(loaded) > 420


async def test_session_helpers_count_turns_and_load_history(db_session_factory, authenticated_user) -> None:
    service = _build_service()

    async with db_session_factory() as db:
        session = ChatSession(user_id=authenticated_user.id, title="Work stress", topic="work_stress", status="active")
        db.add(session)
        await db.flush()
        db.add_all(
            [
                ChatMessage(session_id=session.id, user_id=authenticated_user.id, role="user", content="I feel stuck", intent="support", route="topic:work_stress", safety_mode="normal"),
                ChatMessage(session_id=session.id, user_id=authenticated_user.id, role="assistant", content="That sounds heavy", intent="support", route="topic:work_stress", safety_mode="normal"),
                ChatMessage(session_id=session.id, user_id=authenticated_user.id, role="user", content="And sleep is bad too", intent="support", route="topic:work_stress", safety_mode="normal"),
            ]
        )
        await db.commit()

        turn_count = await service._count_session_turns(db, session.id)
        history = await service._load_session_history(db, session.id, limit=3)

        assert turn_count == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        assert history[2]["content"] == "And sleep is bad too"


def test_bridge_note_uses_previous_session_topic_and_action_plan() -> None:
    service = _build_service()
    prev_session = ChatSession(
        user_id=1,
        title="Work stress",
        topic="work stress",
        status="active",
        last_message_at=datetime.now(timezone.utc) - timedelta(days=4),
    )

    note = service._build_bridge_note(
        prev_session,
        {
            "last_session_topic": "work stress",
            "active_action_plan": "take a walk after work",
        },
    )

    assert note is not None
    assert "Geçen konuşmamızda work stress üzerinde durmuştuk." in note
    assert "take a walk after work" in note


async def test_encrypted_memory_summary_summary_endpoint_can_parse_structured_json(db_session_factory, authenticated_user) -> None:
    raw_memory = json.dumps({"v": 2, "preferred_name": "Aykut"}, ensure_ascii=False)

    async with db_session_factory() as db:
        db.add(Memory(user_id=authenticated_user.id, summary_nuggets=encrypt_clinical_data(raw_memory)))
        await db.commit()

        result = await db.execute(select(Memory).where(Memory.user_id == authenticated_user.id))
        memory = result.scalar_one()

        assert MemoryAgent.parse(decrypt_clinical_data(memory.summary_nuggets))["preferred_name"] == "Aykut"

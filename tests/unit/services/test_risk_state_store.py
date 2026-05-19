from __future__ import annotations

import pytest

from server.app.core.pipeline.risk_state import RiskState
from server.app.services.risk_state_store import load_or_create_risk_state, save_risk_state
from server.app.services.session_store import ensure_session


pytestmark = [pytest.mark.unit, pytest.mark.anyio]


async def test_load_or_create_risk_state_creates_default_state(db_session_factory, authenticated_user) -> None:
    async with db_session_factory() as db:
        session = await ensure_session(db, authenticated_user.id, title="Risk", topic="stress_anxiety")
        await db.commit()

        state = await load_or_create_risk_state(db, user_id=authenticated_user.id, session_id=session.id)
        await db.commit()

        assert state.current_risk_level == "none"
        assert state.risk_indicators == []
        assert state.crisis_protocol_active is False


async def test_save_risk_state_round_trips_full_state(db_session_factory, authenticated_user) -> None:
    async with db_session_factory() as db:
        session = await ensure_session(db, authenticated_user.id, title="Risk", topic="stress_anxiety")
        await db.commit()

        state = RiskState(current_risk_level="medium")
        state.risk_indicators.append("hopelessness")
        state.cumulative_risk_signals.extend(["hopelessness", "burden"])
        state.escalate("persistent_distress")

        await save_risk_state(db, user_id=authenticated_user.id, session_id=session.id, state=state)
        await db.commit()

    async with db_session_factory() as db:
        loaded = await load_or_create_risk_state(db, user_id=authenticated_user.id, session_id=session.id)

        assert loaded.current_risk_level == "medium"
        assert loaded.needs_human_support is True
        assert loaded.escalation_recommended is True
        assert loaded.risk_indicators == ["hopelessness", "persistent_distress"]
        assert loaded.cumulative_risk_signals == ["hopelessness", "burden"]


async def test_crisis_risk_state_persists_across_turns(db_session_factory, authenticated_user) -> None:
    async with db_session_factory() as db:
        session = await ensure_session(db, authenticated_user.id, title="Risk", topic="crisis")
        await db.commit()

        state = RiskState(current_risk_level="low")
        state.activate_crisis_protocol()
        await save_risk_state(db, user_id=authenticated_user.id, session_id=session.id, state=state)
        await db.commit()

    async with db_session_factory() as db:
        loaded = await load_or_create_risk_state(db, user_id=authenticated_user.id, session_id=session.id)
        loaded.update_risk_check("none", "No explicit signal in latest turn")
        await save_risk_state(db, user_id=authenticated_user.id, session_id=session.id, state=loaded)
        await db.commit()

    async with db_session_factory() as db:
        persisted = await load_or_create_risk_state(db, user_id=authenticated_user.id, session_id=session.id)

        assert persisted.current_risk_level == "crisis"
        assert persisted.crisis_protocol_active is True
        assert persisted.needs_human_support is True

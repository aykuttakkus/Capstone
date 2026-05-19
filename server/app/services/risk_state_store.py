from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from server.app.core.pipeline.risk_state import RiskState
from server.app.models.sql.models import SessionRiskState


def _decode_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(decoded, list):
        return []
    return [str(item) for item in decoded]


def _encode_list(value: list[str]) -> str:
    return json.dumps(value, ensure_ascii=False)


async def load_or_create_risk_state(
    db: AsyncSession,
    *,
    user_id: int,
    session_id: int,
) -> RiskState:
    result = await db.execute(
        select(SessionRiskState).where(
            SessionRiskState.user_id == user_id,
            SessionRiskState.session_id == session_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = SessionRiskState(user_id=user_id, session_id=session_id, current_risk_level="none")
        db.add(row)
        await db.flush()

    return RiskState(
        current_risk_level=row.current_risk_level or "none",
        risk_indicators=_decode_list(row.risk_indicators_json),
        cumulative_risk_signals=_decode_list(row.cumulative_risk_signals_json),
        crisis_protocol_active=bool(row.crisis_protocol_active),
        needs_human_support=bool(row.needs_human_support),
        last_risk_check=row.last_risk_check,
        safety_analysis_reasoning=row.safety_analysis_reasoning or "",
        escalation_recommended=bool(row.escalation_recommended),
    )


async def save_risk_state(
    db: AsyncSession,
    *,
    user_id: int,
    session_id: int,
    state: RiskState,
) -> None:
    result = await db.execute(
        select(SessionRiskState).where(
            SessionRiskState.user_id == user_id,
            SessionRiskState.session_id == session_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = SessionRiskState(user_id=user_id, session_id=session_id)
        db.add(row)

    row.current_risk_level = state.current_risk_level
    row.risk_indicators_json = _encode_list(state.risk_indicators)
    row.cumulative_risk_signals_json = _encode_list(state.cumulative_risk_signals)
    row.crisis_protocol_active = state.crisis_protocol_active
    row.needs_human_support = state.needs_human_support
    row.last_risk_check = state.last_risk_check
    row.safety_analysis_reasoning = state.safety_analysis_reasoning
    row.escalation_recommended = state.escalation_recommended
    await db.flush()

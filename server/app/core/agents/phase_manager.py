# DEPRECATED: Old MI (Motivational Interviewing) phases design, not in current spec.
# New spec doesn't use phases; handle with session metadata instead.
# Kept for compatibility only. Do NOT use in new pipeline.
# TODO: Remove in next major refactor

from __future__ import annotations

from dataclasses import dataclass

from server.app.models.sql.models import ChatSession


@dataclass(slots=True)
class PhaseDecision:
    session_phase: int
    agenda_set: bool
    insight_triggered: bool
    closure_confirmed: bool


class PhaseManager:
    def decide(self, conv_state: dict[str, object], turn_count: int) -> PhaseDecision:
        closure_confirmed = bool(conv_state.get("closure_confirmed"))
        insight_triggered = bool(conv_state.get("insight_triggered")) or float(conv_state.get("change_talk_score", 0) or 0) >= 0.6
        agenda_set = bool(conv_state.get("agenda_set")) or turn_count >= 4

        if closure_confirmed:
            session_phase = 4
        elif insight_triggered or turn_count >= 10:
            session_phase = 3
        elif agenda_set:
            session_phase = 2
        else:
            session_phase = 1

        return PhaseDecision(
            session_phase=session_phase,
            agenda_set=agenda_set,
            insight_triggered=insight_triggered,
            closure_confirmed=closure_confirmed,
        )

    def apply(self, session: ChatSession, conv_state: dict[str, object], turn_count: int) -> PhaseDecision:
        decision = self.decide(conv_state, turn_count)
        session.turn_count = turn_count
        session.session_phase = decision.session_phase
        session.agenda_set = decision.agenda_set
        session.insight_triggered = decision.insight_triggered
        session.closure_confirmed = decision.closure_confirmed
        return decision


phase_manager = PhaseManager()

from __future__ import annotations

from dataclasses import dataclass, asdict

from server.app.services.memory_context import MemoryBundle


@dataclass(slots=True)
class MemoryObservabilityReport:
    topic: str
    safety_mode: str
    session_summary_len: int
    long_term_memory_len: int
    recent_turn_count: int
    selected_memory_count: int
    selected_scores: list[float]
    profile_used: bool
    mood_used: bool
    journal_used: bool
    confidence: float
    evidence_status: str
    conversation_mode: str


def build_memory_observability_report(
    *,
    bundle: MemoryBundle,
    confidence: float,
    evidence_status: str,
    conversation_mode: str,
    profile_used: bool,
    mood_used: bool,
    journal_used: bool,
) -> MemoryObservabilityReport:
    return MemoryObservabilityReport(
        topic=bundle.topic,
        safety_mode=bundle.safety_mode,
        session_summary_len=len(bundle.session_summary),
        long_term_memory_len=len(bundle.long_term_memory),
        recent_turn_count=len(bundle.recent_turns),
        selected_memory_count=len(bundle.selected_memory_items),
        selected_scores=[item.score for item in bundle.selected_memory_items],
        profile_used=profile_used,
        mood_used=mood_used,
        journal_used=journal_used,
        confidence=confidence,
        evidence_status=evidence_status,
        conversation_mode=conversation_mode,
    )


def serialize_memory_observability(report: MemoryObservabilityReport) -> dict[str, object]:
    return asdict(report)

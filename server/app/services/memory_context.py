from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from server.app.services.session import compose_memory_context, compact_memory_text


@dataclass(slots=True)
class MemoryTurn:
    role: str
    content: str


@dataclass(slots=True)
class ScoredMemoryItem:
    content: str
    score: float
    kind: str
    topic: str = "general"
    confidence: float = 0.5
    reason: str = ""


@dataclass(slots=True)
class MemoryBundle:
    session_summary: str
    long_term_memory: str
    profile_summary: str
    mood_summary: str
    journal_summary: str
    recent_turns: list[MemoryTurn] = field(default_factory=list)
    selected_memory_items: list[ScoredMemoryItem] = field(default_factory=list)
    recent_segments: list[str] = field(default_factory=list)
    reflections: list[str] = field(default_factory=list)
    topic: str = "general"
    safety_mode: str = "normal"
    prompt_context: str = ""
    debug: dict[str, object] = field(default_factory=dict)


def memory_turns_from_history(history: list[dict[str, str]] | None, limit: int = 8) -> list[MemoryTurn]:
    return _normalize_turns(history, limit=limit)


def _normalize_turns(history: list[dict[str, str]] | None, limit: int = 8) -> list[MemoryTurn]:
    if not history:
        return []

    turns: list[MemoryTurn] = []
    for item in history[-limit:]:
        role = (item.get("role") or "").strip().lower()
        content = (item.get("content") or "").strip()
        if not role or not content:
            continue
        turns.append(MemoryTurn(role=role, content=compact_memory_text(content, max_chars=400)))
    return turns


def _content_overlap(a: str, b: str) -> float:
    left = {token for token in compact_memory_text(a, max_chars=240).lower().split() if len(token) > 2}
    right = {token for token in compact_memory_text(b, max_chars=240).lower().split() if len(token) > 2}
    if not left or not right:
        return 0.0
    return len(left & right) / max(len(left | right), 1)


def _to_utc_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def score_memory_item(
    *,
    content: str,
    topic: str,
    item_topic: str | None,
    confidence: float = 0.5,
    current_message: str = "",
    kind: str = "episodic",
    created_at: datetime | None = None,
) -> ScoredMemoryItem:
    score = 0.0
    normalized_content = compact_memory_text(content, max_chars=240)
    normalized_message = compact_memory_text(current_message, max_chars=240)

    if item_topic and topic and item_topic == topic:
        score += 0.45
    elif kind == "profile_fact":
        score += 0.2
    elif item_topic == "general":
        score += 0.05

    overlap = _content_overlap(normalized_message, normalized_content)
    score += overlap * 0.3

    score += max(0.0, min(confidence, 1.0)) * 0.25

    if created_at is not None:
        normalized_created_at = _to_utc_datetime(created_at)
        if normalized_created_at is not None:
            age_seconds = max(0.0, (datetime.now(timezone.utc) - normalized_created_at).total_seconds())
        else:
            age_seconds = 0.0
        if age_seconds < 3600:
            score += 0.2
        elif age_seconds < 86400:
            score += 0.12
        elif age_seconds < 604800:
            score += 0.06

    if kind == "reflection":
        score += 0.05
    if kind == "profile_fact":
        score += 0.08

    if any(marker in normalized_content.lower() for marker in ["helped", "worked", "walk", "breath", "ground", "routine"]):
        score += 0.06

    if any(marker in normalized_content.lower() for marker in ["prefer", "my name is", "call me", "short answers", "direct", "more detail", "brief answers"]):
        score += 0.22

    reason_bits = []
    if overlap > 0:
        reason_bits.append(f"overlap={overlap:.2f}")
    if item_topic and topic and item_topic == topic:
        reason_bits.append("topic_match")
    if kind == "profile_fact":
        reason_bits.append("profile")
    if kind == "reflection":
        reason_bits.append("reflection")

    return ScoredMemoryItem(
        content=normalized_content,
        score=round(min(score, 1.0), 3),
        kind=kind,
        topic=item_topic or "general",
        confidence=max(0.0, min(confidence, 1.0)),
        reason=";".join(reason_bits) or "recency_only",
    )


def _score_and_select_items(
    items: list[object] | None,
    *,
    topic: str,
    current_message: str,
    kind: str,
    limit: int,
) -> list[ScoredMemoryItem]:
    if not items:
        return []

    scored: list[ScoredMemoryItem] = []
    for item in items:
        content = getattr(item, "content", str(item))
        item_topic = getattr(item, "topic", None)
        confidence = float(getattr(item, "confidence", 0.5) or 0.5)
        created_at = getattr(item, "created_at", None)
        scored.append(
            score_memory_item(
                content=content,
                topic=topic,
                item_topic=item_topic,
                confidence=confidence,
                current_message=current_message,
                kind=kind,
                created_at=created_at,
            )
        )

    scored.sort(key=lambda item: (item.score, item.confidence), reverse=True)
    filtered = [item for item in scored if item.score >= 0.35]
    if not filtered and scored:
        filtered = [scored[0]]
    return filtered[:limit]


def build_memory_bundle(
    *,
    session_summary: str | None,
    user_memory: str | None,
    profile_summary: str | None = None,
    mood_summary: str | None = None,
    journal_summary: str | None = None,
    recent_segments: list[object] | None = None,
    reflections: list[object] | None = None,
    history: list[dict[str, str]] | None = None,
    current_message: str = "",
    topic: str = "general",
    safety_mode: str = "normal",
) -> MemoryBundle:
    normalized_session_summary = compact_memory_text(session_summary, max_chars=420)
    normalized_user_memory = compact_memory_text(user_memory, max_chars=420)
    normalized_profile_summary = compact_memory_text(profile_summary, max_chars=420)
    normalized_mood_summary = compact_memory_text(mood_summary, max_chars=240)
    normalized_journal_summary = compact_memory_text(journal_summary, max_chars=240)
    normalized_turns = _normalize_turns(history, limit=8)

    selected_segments = _score_and_select_items(recent_segments, topic=topic, current_message=current_message, kind="episodic", limit=3)
    selected_reflections = _score_and_select_items(reflections, topic=topic, current_message=current_message, kind="reflection", limit=2)

    segment_texts = [item.content for item in selected_segments]
    reflection_texts = [item.content for item in selected_reflections]

    long_term_blocks = [
        normalized_user_memory,
        *segment_texts,
        *reflection_texts,
    ]
    long_term_memory = "\n".join([block for block in long_term_blocks if block]).strip()

    prompt_context = compose_memory_context(
        session_summary=normalized_session_summary or None,
        user_memory=long_term_memory or None,
    )
    extra_blocks = [
        f"[Profile Memory: {normalized_profile_summary}]" if normalized_profile_summary else "",
        f"[Mood Context: {normalized_mood_summary}]" if normalized_mood_summary else "",
        f"[Journal Context: {normalized_journal_summary}]" if normalized_journal_summary else "",
        f"[Recent Turns: {' | '.join(f'{turn.role}: {turn.content}' for turn in normalized_turns)}]" if normalized_turns else "",
    ]
    prompt_context = "\n".join([block for block in [prompt_context, *extra_blocks] if block]).strip()

    debug = {
        "topic": topic,
        "safety_mode": safety_mode,
        "has_session_summary": bool(normalized_session_summary),
        "has_user_memory": bool(normalized_user_memory),
        "recent_turn_count": len(normalized_turns),
        "recent_segment_count": len(recent_segments or []),
        "reflection_count": len(reflections or []),
        "selected_segment_count": len(segment_texts),
        "selected_reflection_count": len(reflection_texts),
        "selected_memory_count": len(segment_texts) + len(reflection_texts),
        "selected_segment_scores": [item.score for item in selected_segments],
        "selected_reflection_scores": [item.score for item in selected_reflections],
    }

    return MemoryBundle(
        session_summary=normalized_session_summary,
        long_term_memory=long_term_memory,
        profile_summary=normalized_profile_summary,
        mood_summary=normalized_mood_summary,
        journal_summary=normalized_journal_summary,
        recent_turns=normalized_turns,
        selected_memory_items=[*selected_segments, *selected_reflections],
        recent_segments=segment_texts,
        reflections=reflection_texts,
        topic=topic,
        safety_mode=safety_mode,
        prompt_context=prompt_context,
        debug=debug,
    )

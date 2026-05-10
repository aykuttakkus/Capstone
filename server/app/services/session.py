from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SessionSummary:
    topic: str
    intent: str
    safety_mode: str
    recap: str


def compose_memory_context(session_summary: str | None = None, user_memory: str | None = None) -> str:
    blocks: list[str] = []
    if session_summary:
        blocks.append(f"[Session Memory: {session_summary.strip()}]")
    if user_memory:
        blocks.append(f"[Long-term Memory: {user_memory.strip()}]")
    return "\n".join(blocks)


def compact_memory_text(text: str | None, max_chars: int = 420) -> str:
    if not text:
        return ""
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[: max_chars - 3].rstrip()}..."


def prune_memory_text(text: str | None, max_lines: int = 6, max_chars: int = 420) -> str:
    compacted = compact_memory_text(text, max_chars=max_chars)
    if not compacted:
        return ""
    lines = [line.strip() for line in compacted.splitlines() if line.strip()]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[:max_lines] + ["..."])


def build_session_summary(
    intake: dict[str, str],
    response_answer: str,
    topic: str,
    intent: str,
    safety_mode: str,
    previous_summary: str | None = None,
) -> SessionSummary:
    main_issue = intake.get("main_issue", "")
    help_type = intake.get("help_type", "")
    prior = f"Prior context: {previous_summary[:120].strip()}. " if previous_summary else ""
    recap = (
        f"{prior}Topic: {topic}. Intent: {intent}. Safety mode: {safety_mode}. "
        f"Intake: {main_issue or 'n/a'} / {help_type or 'n/a'}. "
        f"Response: {response_answer[:180].strip()}"
    )
    recap = compact_memory_text(recap, max_chars=380)
    return SessionSummary(topic=topic, intent=intent, safety_mode=safety_mode, recap=recap)

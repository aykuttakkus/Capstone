from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ConversationContext:
    user_id: int
    session_id: str
    current_message: str
    topic: str
    recent_turns: list[dict[str, str]] = field(default_factory=list)
    mood_trend: str | None = None
    distress_level: int = 0
    previous_topics: list[str] = field(default_factory=list)
    engagement_level: int = 1
    user_preferences: dict[str, Any] = field(default_factory=dict)
    screening_state: dict[str, Any] = field(default_factory=dict)


class ContextManager:
    def __init__(self, max_history: int = 10) -> None:
        self.max_history = max_history
        self.conversation_cache: dict[str, ConversationContext] = {}

    def build_context(
        self,
        user_id: int,
        session_id: str,
        current_message: str,
        topic: str,
        conversation_history: list[dict[str, str]] | None = None,
        user_profile: dict[str, Any] | None = None,
        screening_state: dict[str, Any] | None = None,
    ) -> ConversationContext:
        """Build comprehensive conversation context from available data."""

        # Extract recent turns (keep last N)
        recent_turns = []
        if conversation_history:
            recent_turns = conversation_history[-self.max_history :]

        # Analyze mood trend from history
        mood_trend = self._analyze_mood_trend(recent_turns)

        # Calculate distress level from history
        distress_level = self._calculate_distress_level(recent_turns, current_message)

        # Extract topic history
        previous_topics = self._extract_topics(recent_turns)

        # Get user preferences
        user_preferences = user_profile or {}

        # Build context
        context = ConversationContext(
            user_id=user_id,
            session_id=session_id,
            current_message=current_message,
            topic=topic,
            recent_turns=recent_turns,
            mood_trend=mood_trend,
            distress_level=distress_level,
            previous_topics=previous_topics,
            engagement_level=self._calculate_engagement(recent_turns),
            user_preferences=user_preferences,
            screening_state=screening_state or {},
        )

        # Cache for quick access
        self.conversation_cache[session_id] = context

        return context

    def get_cached_context(self, session_id: str) -> ConversationContext | None:
        return self.conversation_cache.get(session_id)

    def update_context(
        self,
        session_id: str,
        current_message: str,
        distress_level: int | None = None,
    ) -> ConversationContext | None:
        """Update existing context with new information."""

        context = self.conversation_cache.get(session_id)
        if not context:
            return None

        context.current_message = current_message

        if distress_level is not None:
            context.distress_level = distress_level

        return context

    def clear_cache(self, session_id: str) -> None:
        """Clear cached context for a session."""
        self.conversation_cache.pop(session_id, None)

    def _analyze_mood_trend(self, recent_turns: list[dict[str, str]]) -> str | None:
        """Analyze mood trend from recent conversation."""

        if not recent_turns:
            return None

        mood_keywords = {
            "improving": ["better", "good", "hopeful", "optimistic", "encouraged"],
            "declining": ["worse", "hopeless", "struggling", "difficult", "tired"],
            "stable": ["same", "managing", "okay", "fine"],
        }

        recent_text = " ".join([turn.get("user", "").lower() for turn in recent_turns[-3:]])

        for trend, keywords in mood_keywords.items():
            if any(kw in recent_text for kw in keywords):
                return trend

        return "neutral"

    def _calculate_distress_level(
        self, recent_turns: list[dict[str, str]], current_message: str
    ) -> int:
        """Calculate distress level (0-5) from conversation."""

        distress_keywords = {
            "crisis": ["suicide", "kill myself", "goodbye", "hopeless"],
            "high": ["overwhelming", "panic", "unbearable", "can't cope"],
            "moderate": ["struggling", "difficult", "worried", "anxious"],
            "low": ["manageable", "okay", "better", "improving"],
        }

        all_text = (
            " ".join([turn.get("user", "").lower() for turn in recent_turns])
            + " "
            + current_message.lower()
        )

        for level, keywords in distress_keywords.items():
            if any(kw in all_text for kw in keywords):
                return {"crisis": 5, "high": 4, "moderate": 2, "low": 1}.get(level, 1)

        return 1

    def _extract_topics(self, recent_turns: list[dict[str, str]]) -> list[str]:
        """Extract topic history from recent turns."""

        topics = []
        for turn in recent_turns:
            topic_hint = turn.get("metadata", {}).get("topic")
            if topic_hint:
                topics.append(topic_hint)

        return list(set(topics))  # Remove duplicates

    def _calculate_engagement(self, recent_turns: list[dict[str, str]]) -> int:
        """Calculate engagement level (1-5)."""

        if not recent_turns:
            return 1

        # More turns = higher engagement
        engagement = min(len(recent_turns) // 2, 5)
        return max(engagement, 1)

    def get_summary(self, context: ConversationContext) -> str:
        """Generate a summary of the conversation context."""

        summary = f"""
Conversation Context Summary:
- User ID: {context.user_id}
- Topic: {context.topic}
- Distress Level: {context.distress_level}/5
- Mood Trend: {context.mood_trend}
- Engagement: {context.engagement_level}/5
- Recent Turns: {len(context.recent_turns)}
- Previous Topics: {', '.join(context.previous_topics) if context.previous_topics else 'None'}
"""
        return summary.strip()

"""
User State Service - Consolidates user profile, mood trends, and journal insights.

This service loads all user context (profile, mood history, journal themes) in one place,
providing a complete picture of the user's current state and history for personalization.
"""

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from server.app.services.profile import profile_service, ProfileService
from server.app.services.mood import mood_service, MoodTrendService
from server.app.services.journal import journal_service, JournalInsightService


@dataclass(slots=True)
class UserState:
    """Complete user state for conversation personalization."""

    user_id: int
    # Profile
    preferred_name: Optional[str]
    primary_concerns: Optional[str]
    goals_for_support: Optional[str]
    communication_style: Optional[str]
    response_length_preference: Optional[str]
    coping_strategies_helpful: Optional[str]
    coping_strategies_unhelpful: Optional[str]
    main_triggers: Optional[str]
    support_system: Optional[str]
    life_narrative: Optional[str]
    therapy_status: Optional[str]
    # Mood trend
    mood_summary: Optional[str]
    recent_mood_score: Optional[float]
    recent_anxiety_score: Optional[float]
    mood_pattern_tags: list[str]
    # Journal insights
    journal_summary: Optional[str]
    journal_themes: list[str]
    # Preferences
    personalization_consent: bool
    use_mood_context: bool
    use_journal_context: bool
    use_memory_context: bool


class UserStateService:
    """Loads and consolidates user state from profile, mood, and journal services."""

    def __init__(
        self,
        profile_svc: ProfileService | None = None,
        mood_svc: MoodTrendService | None = None,
        journal_svc: JournalInsightService | None = None,
    ):
        self.profile_service = profile_svc or profile_service
        self.mood_service = mood_svc or mood_service
        self.journal_service = journal_svc or journal_service

    async def load_full_state(self, db: AsyncSession, user_id: int) -> UserState:
        """
        Load complete user state from all sources.

        Loads: profile, mood trends (last 14 days), journal insights (last 10 entries)
        """
        # Load profile
        profile = await self.profile_service.get_or_create(db, user_id)

        # Load mood trend
        mood_trend = await self.mood_service.build_trend(db, user_id, limit=14)

        # Load journal insights
        journal_insights = await self.journal_service.build_insights(db, user_id, limit=10)

        # Extract mood values
        recent_mood_score = mood_trend.recent_average_mood
        recent_anxiety_score = mood_trend.recent_average_anxiety
        mood_tags = mood_trend.pattern_tags or []

        # Extract journal themes
        journal_themes = journal_insights.repeated_themes or []

        # Respect consent preferences
        personalization_consent = profile.personalization_consent if profile else False

        return UserState(
            user_id=user_id,
            # Profile
            preferred_name=profile.preferred_name if personalization_consent else None,
            primary_concerns=profile.primary_concerns if personalization_consent else None,
            goals_for_support=profile.goals_for_support if personalization_consent else None,
            communication_style=profile.communication_style if personalization_consent else None,
            response_length_preference=profile.response_length_preference if personalization_consent else None,
            coping_strategies_helpful=profile.coping_strategies_helpful if personalization_consent else None,
            coping_strategies_unhelpful=profile.coping_strategies_unhelpful if personalization_consent else None,
            main_triggers=profile.main_triggers if personalization_consent else None,
            support_system=profile.support_system if personalization_consent else None,
            life_narrative=profile.life_narrative if personalization_consent else None,
            therapy_status=profile.therapy_status if personalization_consent else None,
            # Mood trend
            mood_summary=mood_trend.summary if profile.use_mood_context else None,
            recent_mood_score=recent_mood_score if profile.use_mood_context else None,
            recent_anxiety_score=recent_anxiety_score if profile.use_mood_context else None,
            mood_pattern_tags=mood_tags if profile.use_mood_context else [],
            # Journal insights
            journal_summary=journal_insights.summary if profile.use_journal_context else None,
            journal_themes=journal_themes if profile.use_journal_context else [],
            # Preferences
            personalization_consent=personalization_consent,
            use_mood_context=profile.use_mood_context if profile else False,
            use_journal_context=profile.use_journal_context if profile else False,
            use_memory_context=profile.use_memory_context if profile else False,
        )

    def format_as_context_string(self, user_state: UserState) -> str:
        """Format user state into a natural language context string for LLM injection."""
        lines = []

        if user_state.preferred_name:
            lines.append(f"Name: {user_state.preferred_name}")

        if user_state.primary_concerns:
            lines.append(f"Main concerns: {user_state.primary_concerns}")

        if user_state.therapy_status:
            lines.append(f"Therapy status: {user_state.therapy_status}")

        if user_state.goals_for_support:
            lines.append(f"Support goals: {user_state.goals_for_support}")

        # Mood context
        if user_state.mood_summary:
            lines.append(f"Recent mood: {user_state.mood_summary}")

        if user_state.mood_pattern_tags:
            tags_str = ", ".join(user_state.mood_pattern_tags)
            lines.append(f"Mood patterns: {tags_str}")

        # Journal context
        if user_state.journal_summary:
            lines.append(f"Journal themes: {user_state.journal_summary}")

        # Coping strategies
        if user_state.coping_strategies_helpful:
            lines.append(f"Has found helpful: {user_state.coping_strategies_helpful}")

        if user_state.coping_strategies_unhelpful:
            lines.append(f"Less helpful: {user_state.coping_strategies_unhelpful}")

        # Life context
        if user_state.main_triggers:
            lines.append(f"Main triggers: {user_state.main_triggers}")

        if user_state.support_system:
            lines.append(f"Support system: {user_state.support_system}")

        if not lines:
            return None

        return "\n".join(lines)


# Singleton instance
user_state_service = UserStateService()

"""
Context Formatter Service - Converts structured user state into natural language narratives.

This service takes structured context (user state, conversation history, intake data)
and formats it as a flowing natural language paragraph that can be injected into
the LLM's system prompt for personalization.

Goal: User context feels like background knowledge the LLM naturally has,
not like a structured list of fields.
"""

from typing import Optional
from server.app.services.user_state import UserState


class ContextFormatter:
    """Formats structured context into natural language for LLM injection."""

    @staticmethod
    def format_full_context(
        user_state: Optional[UserState] = None,
        conversation_history: Optional[list[dict]] = None,
        intake_data: Optional[dict] = None,
    ) -> str:
        """
        Build a complete context narrative from user state, history, and intake.

        Returns a natural language string suitable for injection into LLM prompts.
        """
        narratives = []

        # 1. Build user profile narrative
        if user_state:
            profile_narrative = ContextFormatter._build_profile_narrative(user_state)
            if profile_narrative:
                narratives.append(profile_narrative)

        # 2. Build mood/wellness narrative
        if user_state:
            wellness_narrative = ContextFormatter._build_wellness_narrative(user_state)
            if wellness_narrative:
                narratives.append(wellness_narrative)

        # 3. Build intake narrative (first session context)
        if intake_data:
            intake_narrative = ContextFormatter._build_intake_narrative(intake_data)
            if intake_narrative:
                narratives.append(intake_narrative)

        # 4. Build conversation trajectory narrative
        if conversation_history:
            trajectory_narrative = ContextFormatter._build_trajectory_narrative(conversation_history)
            if trajectory_narrative:
                narratives.append(trajectory_narrative)

        # Combine all narratives
        if not narratives:
            return ""

        return "\n\n".join(narratives)

    @staticmethod
    def _build_profile_narrative(user_state: UserState) -> str:
        """Build natural language profile narrative."""
        if not user_state.personalization_consent:
            return ""
        lines = []

        # Opening with name if available
        if user_state.preferred_name:
            lines.append(f"{user_state.preferred_name} has reached out for support.")
        else:
            lines.append("The user has reached out for support.")

        # Main concerns
        if user_state.primary_concerns:
            lines.append(f"Their main concerns are around {user_state.primary_concerns.lower()}.")

        # Goals and support type
        if user_state.goals_for_support:
            lines.append(f"They're seeking {user_state.goals_for_support.lower()}.")

        # Therapy status context
        if user_state.therapy_status:
            therapy_context = (
                "They're currently working with a therapist"
                if "yes" in user_state.therapy_status.lower()
                else "They haven't mentioned working with a professional yet"
            )
            lines.append(f"{therapy_context}.")

        # Coping and support systems
        if user_state.support_system or user_state.coping_strategies_helpful:
            coping_parts = []
            if user_state.support_system:
                coping_parts.append(f"they have support from {user_state.support_system.lower()}")
            if user_state.coping_strategies_helpful:
                coping_parts.append(f"they've found {user_state.coping_strategies_helpful.lower()} helpful")

            if coping_parts:
                lines.append(f"In facing these challenges, {' and '.join(coping_parts)}.")

        # Life context
        if user_state.life_narrative:
            lines.append(f"Context: {user_state.life_narrative[:200]}")

        return " ".join(lines) if lines else ""

    @staticmethod
    def _build_wellness_narrative(user_state: UserState) -> str:
        """Build natural language wellness/mood narrative."""
        lines = []

        # Mood patterns — gated by use_mood_context
        if user_state.use_mood_context:
            mood_parts = []

            if user_state.mood_summary:
                mood_parts.append(f"Over the past two weeks, {user_state.mood_summary}")

            if user_state.recent_mood_score is not None:
                if user_state.recent_mood_score <= 3:
                    mood_context = "their mood has been quite low"
                elif user_state.recent_mood_score <= 5:
                    mood_context = "their mood has been mixed"
                else:
                    mood_context = "their mood has been relatively stable"
                if not mood_parts:
                    mood_parts.append(mood_context)

            if user_state.recent_anxiety_score is not None and user_state.recent_anxiety_score >= 7:
                mood_parts.append("anxiety levels have been elevated")

            if mood_parts:
                lines.append(". ".join(mood_parts) + ".")

            # Main triggers
            if user_state.main_triggers:
                lines.append(f"Key triggers they've identified: {user_state.main_triggers.lower()}.")

        # Journal themes — gated by use_journal_context
        if user_state.use_journal_context and user_state.journal_summary:
            lines.append(f"They've been journaling about: {user_state.journal_summary.lower()}")

        return " ".join(lines) if lines else ""

    @staticmethod
    def _build_intake_narrative(intake_data: dict) -> str:
        """Build natural language intake narrative (initial session context)."""
        if not intake_data:
            return ""

        lines = []

        # When they first came in
        lines.append("From their initial intake:")

        # Main issue
        if intake_data.get("main_issue"):
            lines.append(f"- Main issue: {intake_data['main_issue']}")

        # Timeline
        if intake_data.get("timeline"):
            lines.append(f"- Duration: {intake_data['timeline']}")

        # Impact
        if intake_data.get("impact"):
            lines.append(f"- Impact: {intake_data['impact']}")

        # Help type
        if intake_data.get("help_type"):
            lines.append(f"- Looking for: {intake_data['help_type']}")

        # Communication style preference
        if intake_data.get("communication_style"):
            lines.append(f"- Prefers: {intake_data['communication_style']} communication")

        return "\n".join(lines) if len(lines) > 1 else ""

    @staticmethod
    def _build_trajectory_narrative(conversation_history: list[dict]) -> str:
        """Build natural language conversation trajectory narrative."""
        if not conversation_history or len(conversation_history) < 4:
            return ""

        # Look at last 3-4 exchanges for trajectory
        recent_turns = conversation_history[-4:]

        # Count emotional valence
        distress_signals = 0
        positive_signals = 0

        for turn in recent_turns:
            content = turn.get("content", "").lower()
            if any(word in content for word in ["struggling", "tired", "overwhelmed", "anxious", "sad"]):
                distress_signals += 1
            if any(word in content for word in ["better", "helped", "good", "grateful", "relieved"]):
                positive_signals += 1

        # Build trajectory description
        lines = []

        if len(conversation_history) > 10:
            lines.append("Over this conversation, they've been opening up about their experiences.")

        if distress_signals > positive_signals:
            lines.append("The tone has included expressions of struggle or overwhelm.")
        elif positive_signals > distress_signals:
            lines.append("They've mentioned some things that have helped or improved.")
        else:
            lines.append("They're exploring their situation thoughtfully.")

        # Recent topic focus
        last_messages = [
            turn.get("content", "") for turn in recent_turns[-2:] if turn.get("role") == "user"
        ]
        if last_messages:
            combined_recent = " ".join(last_messages).lower()
            if any(word in combined_recent for word in ["sleep", "tired", "exhausted"]):
                lines.append("Sleep and fatigue have been recent concerns.")
            elif any(word in combined_recent for word in ["anxious", "worried", "panic"]):
                lines.append("Anxiety and worry have come up recently.")
            elif any(word in combined_recent for word in ["relationship", "friend", "family"]):
                lines.append("Relationships and social aspects are on their mind.")

        return " ".join(lines) if lines else ""

    @staticmethod
    def format_coping_strategies(
        tried_strategies: Optional[list[dict]] = None,
    ) -> str:
        """Format previously tried coping strategies for context."""
        if not tried_strategies:
            return ""

        lines = ["Previously discussed coping strategies:"]

        for strategy in tried_strategies:
            name = strategy.get("name", "strategy")
            effectiveness = strategy.get("effectiveness", "unclear")
            lines.append(f"- {name}: {effectiveness}")

        return "\n".join(lines)

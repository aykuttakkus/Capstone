from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models.sql.models import UserProfile


def _pick(*values: str | None) -> str | None:
    for value in values:
        if value and str(value).strip():
            return str(value).strip()
    return None


class ProfileService:
    async def get_or_create(self, db: AsyncSession, user_id: int) -> UserProfile:
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if profile is not None:
            return profile

        profile = UserProfile(user_id=user_id)
        db.add(profile)
        await db.flush()
        return profile

    async def refresh_from_context(
        self,
        db: AsyncSession,
        user_id: int,
        *,
        intake: dict[str, str] | None = None,
        screening: dict[str, object] | None = None,
        personalization: dict[str, object] | None = None,
        intake_chat_signals: dict[str, str] | None = None,
    ) -> UserProfile:
        profile = await self.get_or_create(db, user_id)
        intake = intake or {}
        personalization = personalization or {}
        signals = intake_chat_signals or {}

        profile.personalization_consent = bool(
            personalization.get("personalization_consent", profile.personalization_consent)
        )
        profile.use_mood_context = bool(personalization.get("use_mood_context", profile.use_mood_context))
        profile.use_journal_context = bool(personalization.get("use_journal_context", profile.use_journal_context))
        profile.use_memory_context = bool(personalization.get("use_memory_context", profile.use_memory_context))

        if not profile.personalization_consent:
            profile.preferred_name = None
            profile.age_group = None
            profile.therapy_status = None
            profile.primary_concerns = None
            profile.communication_style = None
            profile.response_length_preference = None
            profile.goals_for_support = None
            profile.coping_strategies_helpful = None
            profile.stress_context = None
            profile.sleep_context = None
            profile.main_triggers = None
            profile.support_system = None
            profile.coping_strategies_unhelpful = None
            profile.life_narrative = None
            profile.use_mood_context = False
            profile.use_journal_context = False
            profile.use_memory_context = False
            profile.last_profile_refresh_at = datetime.now(timezone.utc)
            await db.flush()
            return profile

        profile.preferred_name = _pick(
            str(personalization.get("preferred_name", "")),
            signals.get("preferred_name"),
            str(intake.get("profile_display_name", "")),
            profile.preferred_name,
        )
        profile.age_group = _pick(intake.get("age_group"), profile.age_group)
        profile.therapy_status = _pick(
            signals.get("therapy_status"),
            intake.get("therapy_status"),
            profile.therapy_status,
        )
        profile.primary_concerns = _pick(
            signals.get("main_issue"),
            intake.get("main_issue"),
            profile.primary_concerns,
        )
        profile.communication_style = _pick(intake.get("communication_style"), profile.communication_style)
        profile.response_length_preference = _pick(
            intake.get("response_length_preference"),
            profile.response_length_preference,
        )
        profile.goals_for_support = _pick(intake.get("help_type"), profile.goals_for_support)
        profile.coping_strategies_helpful = _pick(
            str(personalization.get("coping_strategies_helpful", "")),
            signals.get("coping_style"),
            intake.get("coping_style"),
            profile.coping_strategies_helpful,
        )
        profile.stress_context = _pick(
            signals.get("impact"),
            intake.get("impact"),
            profile.stress_context,
        )
        profile.sleep_context = _pick(str(personalization.get("sleep_context", "")), profile.sleep_context)
        profile.main_triggers = _pick(str(personalization.get("main_triggers", "")), profile.main_triggers)
        profile.support_system = _pick(
            signals.get("support_system"),
            str(personalization.get("support_system", "")),
            profile.support_system,
        )
        profile.coping_strategies_unhelpful = _pick(
            str(personalization.get("coping_strategies_unhelpful", "")),
            profile.coping_strategies_unhelpful,
        )
        if signals.get("life_narrative"):
            profile.life_narrative = signals["life_narrative"]

        if screening:
            severity = str(screening.get("severity", "")).strip()
            if severity:
                screening_note = f"Recent self-screening context: {severity}"
                profile.stress_context = _pick(profile.stress_context, screening_note) or screening_note

        profile.last_profile_refresh_at = datetime.now(timezone.utc)
        await db.flush()
        return profile

    def summarize(self, profile: UserProfile | None) -> str:
        if profile is None:
            return ""

        blocks: list[str] = []
        if profile.preferred_name:
            blocks.append(f"Preferred name: {profile.preferred_name}")
        if profile.primary_concerns:
            blocks.append(f"Primary concerns: {profile.primary_concerns}")
        if profile.goals_for_support:
            blocks.append(f"Support goal: {profile.goals_for_support}")
        if profile.communication_style:
            blocks.append(f"Communication style: {profile.communication_style}")
        if profile.response_length_preference:
            blocks.append(f"Response length: {profile.response_length_preference}")
        if profile.coping_strategies_helpful:
            blocks.append(f"Helpful coping: {profile.coping_strategies_helpful}")
        if profile.main_triggers:
            blocks.append(f"Triggers: {profile.main_triggers}")
        if profile.support_system:
            blocks.append(f"Support system: {profile.support_system}")
        if profile.life_narrative:
            blocks.append(f"Life context: {profile.life_narrative[:300]}")
        return "\n".join(blocks)


profile_service = ProfileService()

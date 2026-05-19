from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from server.app.utils.language_adapter import detect_language, language_adapter


class ResponseMode(str, Enum):
    EMOTIONAL_SUPPORT = "emotional_support"
    PSYCHOEDUCATION = "psychoeducation"
    COPING_STRATEGY = "coping_strategy"
    SYMPTOM_EXPLORATION = "symptom_exploration"
    CLARIFICATION = "clarification"
    CRISIS = "crisis"
    REPAIR = "repair"
    OFF_SCOPE = "off_scope"


@dataclass(slots=True)
class ResponseModeContext:
    mode: ResponseMode
    user_message: str
    topic: str
    risk_level: int
    conversation_history: list[str]
    retrieved_content: str | None = None
    intent: str = ""
    profile_context: dict[str, Any] | None = None


class EmotionalSupportBuilder:
    def build(self, context: ResponseModeContext) -> str:
        prompt_template = """The user is experiencing emotional distress related to {topic}.

Your role: Provide emotional validation and normalize their experience.

Key principles:
- Validate their feelings as understandable
- Normalize common human experiences
- Show empathy without over-involvement
- Encourage self-compassion

User message: {message}

Conversation context (last 2 turns):
{history}

Generate a supportive response that validates their experience."""

        return prompt_template.format(
            topic=context.topic,
            message=context.user_message,
            history="\n".join(context.conversation_history[-2:])
        )


class PsychoeducationBuilder:
    def build(self, context: ResponseModeContext) -> str:
        prompt_template = """Provide evidence-based information about {topic}.

User is asking: {message}

Retrieved evidence:
{evidence}

Your role: Educate without diagnosing or prescribing treatment.

Key principles:
- Ground claims in research
- Explain mechanisms and reasons
- Use clear, accessible language
- Avoid clinical terminology unless explained
- Note limitations of current research

Generate an informative response."""

        return prompt_template.format(
            topic=context.topic,
            message=context.user_message,
            evidence=context.retrieved_content or "No specific evidence retrieved."
        )


class CopingStrategyBuilder:
    def build(self, context: ResponseModeContext) -> str:
        prompt_template = """Help the user develop concrete coping strategies for {topic}.

User request: {message}

Context:
- Risk level: {risk_level}
- Conversation: {history}
- Retrieved strategies: {evidence}

Your role: Suggest specific, actionable techniques.

Key principles:
- Provide step-by-step instructions
- Start with simple techniques
- Explain WHY each works
- Offer alternatives for different preferences
- Avoid unrealistic promises
- Scale to risk level (higher risk → more basic strategies)

Generate practical coping guidance."""

        return prompt_template.format(
            topic=context.topic,
            message=context.user_message,
            risk_level=context.risk_level,
            history="\n".join(context.conversation_history[-2:]),
            evidence=context.retrieved_content or "General coping techniques apply."
        )


class SymptomExplorationBuilder:
    def build(self, context: ResponseModeContext) -> str:
        prompt_template = """Help the user understand their symptoms related to {topic}.

User describes: {message}

Your role: Guide self-observation and pattern recognition.

Key principles:
- Ask clarifying questions
- Help identify triggers and patterns
- Normalize symptom variability
- Encourage objective observation
- Avoid diagnosis language
- Use curiosity, not judgment

Generate exploratory questions and observations."""

        return prompt_template.format(
            topic=context.topic,
            message=context.user_message
        )


class ClarificationBuilder:
    def build(self, context: ResponseModeContext) -> str:
        prompt_template = """The user is confused about {topic}.

User question: {message}

Your role: Clarify concepts and assumptions.

Key principles:
- Check understanding before explaining
- Break down complex concepts
- Use analogies and examples
- Ensure bidirectional understanding
- Ask follow-up questions

Generate a clarifying response with a reflective question."""

        return prompt_template.format(
            topic=context.topic,
            message=context.user_message
        )


class CrisisBuilder:
    _CRISIS_NUMBERS: dict[str, dict[str, str]] = {
        "TR": {
            "tr": (
                "📞 **Kriz Hatları (7/24 Açık):**\n"
                "- İntihar Önleme Hattı: **182**\n"
                "- ALO 182 (Türkiye Çocukları Koruma Merkezi)\n"
                "- IASP Kriz Merkezleri: https://www.iasp.info/resources/Crisis_Centres/\n\n"
                "🏥 **Acil Durum:** Hemen 112'yi arayın veya en yakın acil servise gidin."
            ),
            "en": (
                "📞 **Crisis Lines (Turkey, 24/7):**\n"
                "- Suicide Prevention: **182**\n"
                "- IASP Crisis Centres: https://www.iasp.info/resources/Crisis_Centres/\n\n"
                "🏥 **Emergency:** Call 112 or go to the nearest emergency room."
            ),
        },
        "US": {
            "en": (
                "📞 **Crisis Lines (24/7):**\n"
                "- Suicide & Crisis Lifeline: **988**\n"
                "- Crisis Text Line: Text HOME to **741741**\n"
                "- IASP: https://www.iasp.info/resources/Crisis_Centres/\n\n"
                "🏥 **Emergency:** Call 911 or go to the nearest emergency room."
            ),
            "tr": (
                "📞 **Kriz Hatları (ABD, 7/24):**\n"
                "- İntihar & Kriz Yaşam Hattı: **988**\n"
                "- IASP: https://www.iasp.info/resources/Crisis_Centres/\n\n"
                "🏥 **Acil:** 911'i arayın veya en yakın acil servise gidin."
            ),
        },
    }

    def build(self, context: ResponseModeContext) -> str:
        lang = detect_language(context.user_message)
        country = "TR"  # Default to Turkey for this deployment
        numbers_block = self._CRISIS_NUMBERS.get(country, self._CRISIS_NUMBERS["TR"]).get(lang, "")

        if lang == "tr":
            intro = f"Paylaştıklarına dayanarak güvenliğinizden endişe duyuyorum.\n\nMesajınız: \"{context.user_message}\""
            closing = "Şu an güvendiğiniz biri (arkadaş, aile, danışman) ile konuşabilir misiniz?"
        else:
            intro = f"I'm concerned about your safety based on what you've shared.\n\nYour message: \"{context.user_message}\""
            closing = "Is there someone you trust (friend, family, counselor) you can talk to right now?"

        return f"{intro}\n\n{numbers_block}\n\n💬 Your safety is the priority. Please reach out to a crisis service — they have specialized training I don't.\n\n{closing}"


class RepairBuilder:
    def build(self, context: ResponseModeContext) -> str:
        prompt_template = """The user feels misunderstood or wants to reconnect after tension.

Previous context: {topic}
User message: {message}

Your role: Repair and rebuild understanding.

Key principles:
- Acknowledge their perspective
- Validate their reaction
- Clarify misunderstandings
- Focus on moving forward
- Show understanding of their needs

Generate a repair-focused response."""

        return prompt_template.format(
            topic=context.topic,
            message=context.user_message
        )


class OffScopeBuilder:
    def build(self, context: ResponseModeContext) -> str:
        off_scope_response = f"""I appreciate your question, but this is outside my scope of support.

Your question about "{context.user_message}" involves {context.topic}, which isn't something I'm designed to help with.

**What I CAN help with:**
- Understanding anxiety, depression, stress, and common emotional challenges
- Evidence-based coping strategies
- Exploring your experiences and patterns
- Providing psychoeducational information
- Supporting emotional well-being

**What I CAN'T help with:**
- Medical diagnosis or treatment
- Medication recommendations
- Professional therapy or counseling (you need a qualified therapist)
- Legal or financial advice
- Relationship decisions (that's yours to make)

**Next steps:**
- If this relates to mental health: Speak with a mental health professional
- If this is medical: Consult a doctor
- If this is professional: Seek appropriate specialist

Is there something within my scope I can help you with instead?"""

        return off_scope_response


_MODE_MAX_WORDS: dict[str, int] = {
    ResponseMode.EMOTIONAL_SUPPORT: 120,
    ResponseMode.PSYCHOEDUCATION: 280,
    ResponseMode.COPING_STRATEGY: 220,
    ResponseMode.SYMPTOM_EXPLORATION: 200,
    ResponseMode.CLARIFICATION: 100,
    ResponseMode.CRISIS: 90,
    ResponseMode.REPAIR: 100,
    ResponseMode.OFF_SCOPE: 80,
}


def enforce_length_constraint(response: str, mode: ResponseMode) -> str:
    """Trim response to the spec word limit for the given response mode."""
    max_words = _MODE_MAX_WORDS.get(mode, 200)
    words = response.split()
    if len(words) <= max_words:
        return response
    trimmed = " ".join(words[:max_words])
    if not trimmed.endswith((".", "!", "?")):
        trimmed = trimmed.rstrip(",;:") + "."
    return trimmed


class ResponseModeSelector:
    def select_builder(self, mode: ResponseMode) -> (EmotionalSupportBuilder | PsychoeducationBuilder |
                                                      CopingStrategyBuilder | SymptomExplorationBuilder |
                                                      ClarificationBuilder | CrisisBuilder |
                                                      RepairBuilder | OffScopeBuilder):
        builders = {
            ResponseMode.EMOTIONAL_SUPPORT: EmotionalSupportBuilder(),
            ResponseMode.PSYCHOEDUCATION: PsychoeducationBuilder(),
            ResponseMode.COPING_STRATEGY: CopingStrategyBuilder(),
            ResponseMode.SYMPTOM_EXPLORATION: SymptomExplorationBuilder(),
            ResponseMode.CLARIFICATION: ClarificationBuilder(),
            ResponseMode.CRISIS: CrisisBuilder(),
            ResponseMode.REPAIR: RepairBuilder(),
            ResponseMode.OFF_SCOPE: OffScopeBuilder(),
        }
        return builders.get(mode, EmotionalSupportBuilder())

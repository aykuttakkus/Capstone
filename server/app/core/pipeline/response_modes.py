from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


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
    def build(self, context: ResponseModeContext) -> str:
        crisis_response = f"""I'm concerned about your safety based on what you've shared.

Your message: "{context.user_message}"

**IMMEDIATE RESOURCES:**

📞 **Crisis Hotlines (Available 24/7):**
- National Suicide Prevention Lifeline: 988 (US)
- Crisis Text Line: Text HOME to 741741
- International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/

🏥 **Emergency:**
- If you're in immediate danger, call emergency services (911 in US)
- Go to the nearest emergency room
- Tell someone you trust immediately

💬 **What happens next:**
Your safety is the priority. Professional counselors at these services are trained to help with what you're experiencing.

I'm here to provide support and information, but for your immediate safety, please reach out to a crisis service. They have specialized training and resources I don't.

Is there someone you trust (friend, family, counselor) you can talk to right now?"""

        return crisis_response


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

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FallbackMode(str, Enum):
    PRIMARY = "primary"
    RETRIEVAL_ONLY = "retrieval_only"
    KEYWORD_ONLY = "keyword_only"
    OFFLINE = "offline"


@dataclass(slots=True)
class FallbackResponse:
    mode: FallbackMode
    answer: str
    is_degraded: bool
    fallback_reason: str


class FallbackHandler:
    KEYWORD_RESPONSES = {
        "anxiety": {
            "coping_strategy": "Take slow, deep breaths. One technique is 4-7-8 breathing: inhale for 4, hold for 7, exhale for 8. This can help calm your nervous system.",
            "psychoeducation": "Anxiety is a normal emotion that everyone experiences. It becomes a concern when it's persistent and interferes with daily life.",
            "emotional_support": "It's understandable to feel anxious. These feelings are valid and can be managed with appropriate support."
        },
        "depression": {
            "coping_strategy": "Start small: Go outside for 5 minutes, talk to someone you trust, or do one activity you used to enjoy.",
            "psychoeducation": "Depression is a medical condition involving changes in mood, energy, and motivation. It's treatable with support.",
            "emotional_support": "Depression can feel overwhelming, but you are not alone. Seeking support is a sign of strength."
        },
        "loneliness": {
            "coping_strategy": "Start with small social connections: a text to a friend, joining an online community, or calling a family member.",
            "psychoeducation": "Loneliness is distinct from solitude. Meaningful connections and a sense of belonging are important for well-being.",
            "emotional_support": "Feeling lonely is human. Many people experience this, and there are ways to build meaningful connections."
        },
        "sleep": {
            "coping_strategy": "Create a sleep routine: Same bedtime, limit screens 1 hour before, and keep your room cool and dark.",
            "psychoeducation": "Quality sleep affects mood, immune function, and cognitive ability. Most adults need 7-9 hours per night.",
            "emotional_support": "Sleep problems are common and manageable. You can develop better sleep habits with practice."
        },
        "stress": {
            "coping_strategy": "Try the 5-4-3-2-1 grounding technique: Name 5 things you see, 4 you hear, 3 you touch, 2 you smell, 1 you taste.",
            "psychoeducation": "Stress is your body's response to demands. Some stress is normal, but chronic stress needs management.",
            "emotional_support": "Stress is a natural response. Learning to manage it is a valuable skill you can develop."
        },
        "self_esteem": {
            "coping_strategy": "Write down 3 things you did well today, no matter how small. Build evidence of your capabilities.",
            "psychoeducation": "Self-esteem is your overall evaluation of your worth. It can be built and strengthened over time.",
            "emotional_support": "Your worth is not determined by performance or others' opinions. You are inherently valuable."
        },
        "default": {
            "coping_strategy": "Consider breaking your situation into smaller, manageable steps. What's one small thing you could try today?",
            "psychoeducation": "Understanding your experiences can help. Professional resources are available to support you.",
            "emotional_support": "Your feelings matter. Speaking to someone you trust or a professional can provide valuable perspective."
        }
    }

    def handle(
        self,
        llm_available: bool,
        retrieval_available: bool,
        topic: str,
        intent: str,
        user_message: str,
        retrieved_content: str | None = None,
    ) -> FallbackResponse:
        if llm_available and retrieval_available:
            return FallbackResponse(
                mode=FallbackMode.PRIMARY,
                answer="",
                is_degraded=False,
                fallback_reason="All systems operational"
            )

        if llm_available and not retrieval_available:
            return self._handle_retrieval_failure(llm_available, topic, intent)

        if not llm_available and retrieval_available:
            return self._handle_llm_failure_with_retrieval(retrieved_content, topic, intent)

        return self._handle_complete_failure(topic, intent)

    def _handle_retrieval_failure(
        self, llm_available: bool, topic: str, intent: str
    ) -> FallbackResponse:
        keyword_response = self._get_keyword_response(topic, intent)

        return FallbackResponse(
            mode=FallbackMode.RETRIEVAL_ONLY,
            answer=f"I'm currently unable to access detailed resources, but here's general guidance: {keyword_response}",
            is_degraded=True,
            fallback_reason="Retrieval system unavailable"
        )

    def _handle_llm_failure_with_retrieval(
        self, retrieved_content: str | None, topic: str, intent: str
    ) -> FallbackResponse:
        if retrieved_content:
            return FallbackResponse(
                mode=FallbackMode.RETRIEVAL_ONLY,
                answer=f"Here's relevant information on {topic}:\n\n{retrieved_content}\n\nFor personalized guidance, please consult with a mental health professional.",
                is_degraded=True,
                fallback_reason="LLM unavailable, using retrieval only"
            )

        keyword_response = self._get_keyword_response(topic, intent)
        return FallbackResponse(
            mode=FallbackMode.KEYWORD_ONLY,
            answer=keyword_response,
            is_degraded=True,
            fallback_reason="LLM and retrieval unavailable, using keyword fallback"
        )

    def _handle_complete_failure(self, topic: str, intent: str) -> FallbackResponse:
        keyword_response = self._get_keyword_response(topic, intent)

        offline_response = f"""I'm currently experiencing technical difficulties accessing my full resources. However, here's some general guidance on {topic}:

{keyword_response}

For comprehensive support with {topic}, please:
1. Reach out to a mental health professional
2. Contact a crisis helpline if you're in distress
3. Try the resources and techniques mentioned above

We apologize for the limitation. Your well-being is important to us."""

        return FallbackResponse(
            mode=FallbackMode.OFFLINE,
            answer=offline_response,
            is_degraded=True,
            fallback_reason="Complete system failure, minimal response mode"
        )

    def _get_keyword_response(self, topic: str, intent: str) -> str:
        topic_lower = topic.lower() if topic else "default"
        intent_lower = intent.lower() if intent else "emotional_support"

        topic_responses = self.KEYWORD_RESPONSES.get(topic_lower, self.KEYWORD_RESPONSES["default"])
        return topic_responses.get(intent_lower, topic_responses.get("emotional_support", self.KEYWORD_RESPONSES["default"]["emotional_support"]))

    def is_degraded(self, response: FallbackResponse) -> bool:
        return response.is_degraded

    def severity_level(self, response: FallbackResponse) -> int:
        mode_severity = {
            FallbackMode.PRIMARY: 0,
            FallbackMode.RETRIEVAL_ONLY: 1,
            FallbackMode.KEYWORD_ONLY: 2,
            FallbackMode.OFFLINE: 3,
        }
        return mode_severity.get(response.mode, 3)

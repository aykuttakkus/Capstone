from __future__ import annotations

from server.app.core.agents.orchestrator import Orchestrator
from server.app.core.generation.base import LLMResult


class SequencedLLM:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls = 0

    def generate(self, prompt: str, temperature: float = 0.1) -> LLMResult:
        text = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return LLMResult(available=True, text=text, model="test")


def test_orchestrator_parses_mixed_intent_contract() -> None:
    llm = SequencedLLM(
        [
            '{"primary_intent":"emotional_support","secondary_intents":["symptom_exploration","coping_strategy"],"intent_confidence":0.82,"topic":"stress_anxiety","sentiment":{"label":"anxious","urgency":2},"plan":"validate and offer one grounded step","use_rag":false}',
            '{"mode":"normal","risk_level":0,"reasoning":"safe","suggested_message":""}',
        ]
    )
    orchestrator = Orchestrator(llm=llm)

    plan = orchestrator.plan("I feel anxious and want to understand what to do.")

    assert plan.intent == "emotional_support"
    assert plan.primary_intent == "emotional_support"
    assert plan.secondary_intents == ["symptom_exploration", "coping_strategy"]
    assert plan.intent_confidence == 0.82
    assert plan.topic == "stress_anxiety"


def test_orchestrator_normalizes_legacy_intent_contract() -> None:
    llm = SequencedLLM(
        [
            '{"intent":"symptom_search","topic":"low_mood","sentiment":{"label":"sad","urgency":2},"plan":"explain without diagnosis","use_rag":true}',
            '{"mode":"normal","risk_level":0,"reasoning":"safe","suggested_message":""}',
        ]
    )
    orchestrator = Orchestrator(llm=llm)

    plan = orchestrator.plan("Why do I feel low lately?")

    assert plan.intent == "symptom_exploration"
    assert plan.secondary_intents == []
    assert plan.use_rag is True

from __future__ import annotations

import pytest

from server.app.core.agents.orchestrator import Orchestrator
from server.app.core.routing.classifier import IntentClassifier
from server.app.core.routing.router import RequestRouter
from server.app.services.flows.topics import infer_topic


pytestmark = [pytest.mark.unit]


def test_intent_classifier_detects_help_seeking_and_fallback_general() -> None:
    classifier = IntentClassifier()
    assert classifier.classify("Where can I find professional help?").label == "help_seeking"
    assert classifier.classify("Hello there").label == "general"


def test_router_uses_safety_route_when_message_is_critical() -> None:
    decision = RequestRouter().route("I want to kill myself.")
    assert decision.route == "crisis_support"
    assert decision.safety.mode == "crisis_support"


def test_router_uses_help_flow_and_topic_route() -> None:
    router = RequestRouter()
    help_decision = router.route("Where can I get support for anxiety?")
    topic_decision = router.route("Tell me about stress and sleep.")

    assert help_decision.route == "flow:help_seeking"
    assert topic_decision.route.startswith("topic:")


def test_infer_topic_handles_common_anxiety_typo() -> None:
    assert infer_topic("i have anxiaty") == "stress_anxiety"


def test_orchestrator_prefers_heuristic_topic_over_general_llm_topic() -> None:
    class FakeLLM:
        def generate(self, prompt: str, temperature: float = 0.0):
            return type(
                "LLMResult",
                (),
                {
                    "available": True,
                    "text": '{"intent":"general_query","topic":"general","sentiment":{"label":"neutral","urgency":1},"plan":"listen and reflect","use_rag":true}',
                },
            )()

    class FakeSafety:
        def analyze(self, text: str):
            return type("SafetyAnalysis", (), {"mode": "normal", "risk_level": 0, "message": ""})()

    class FakeKeywordSafety:
        def evaluate(self, text: str):
            return type("SafetyDecision", (), {"mode": "normal", "risk_level": 0, "message": ""})()

    orchestrator = Orchestrator(llm=FakeLLM())
    orchestrator.safety = FakeSafety()
    orchestrator.keyword_safety = FakeKeywordSafety()
    plan = orchestrator.plan("i have anxiaty")

    assert plan.topic == "stress_anxiety"
    assert plan.route == "topic:stress_anxiety"


def test_orchestrator_treats_plain_symptom_statement_as_normal_even_if_llm_overflags() -> None:
    class FakeLLM:
        def generate(self, prompt: str, temperature: float = 0.0):
            return type("LLMResult", (), {"available": True, "text": '{"intent":"general_query","topic":"general","sentiment":{"label":"neutral","urgency":1},"plan":"listen and reflect","use_rag":true}'})()

    class FakeSafety:
        def analyze(self, text: str):
            return type(
                "SafetyAnalysis",
                (),
                {
                    "mode": "diagnosis_refusal",
                    "risk_level": 0,
                    "reasoning": "overflagged by safety model",
                    "message": "I can’t diagnose mental health conditions or confirm a disorder.",
                },
            )()

    class FakeKeywordSafety:
        def evaluate(self, text: str):
            return type("SafetyDecision", (), {"mode": "normal", "risk_level": 0, "message": ""})()

    orchestrator = Orchestrator(llm=FakeLLM())
    orchestrator.safety = FakeSafety()
    orchestrator.keyword_safety = FakeKeywordSafety()

    plan = orchestrator.plan("i have anxiety")

    assert plan.topic == "stress_anxiety"
    assert plan.route == "topic:stress_anxiety"
    assert plan.safety_mode == "normal"

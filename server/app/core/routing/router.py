from __future__ import annotations

from dataclasses import dataclass

from server.app.core.routing.classifier import IntentClassification, IntentClassifier
from server.app.core.safety.policy import SafetyDecision, SafetyPolicyEngine
from server.app.services.flows.topics import infer_topic


@dataclass(slots=True)
class RouteDecision:
    route: str
    topic: str
    intent: IntentClassification
    safety: SafetyDecision


class RequestRouter:
    """
    Combines SafetyPolicyEngine + IntentClassifier to produce a single
    routing decision for the AssistantService.
    """

    def __init__(self) -> None:
        self.classifier = IntentClassifier()
        self.safety = SafetyPolicyEngine()

    def route(self, message: str, intake: dict[str, str] | None = None) -> RouteDecision:
        safety = self.safety.evaluate(message)
        intent = self.classifier.classify(message)
        topic = infer_topic(message, intake)

        if safety.mode != "normal":
            return RouteDecision(route=safety.mode, topic=topic, intent=intent, safety=safety)

        if intent.label in ("help_seeking",):
            return RouteDecision(route="flow:help_seeking", topic=topic, intent=intent, safety=safety)

        if intent.label == "coping_info":
            return RouteDecision(route=f"flow:coping:{topic}", topic=topic, intent=intent, safety=safety)

        return RouteDecision(route=f"topic:{topic}", topic=topic, intent=intent, safety=safety)

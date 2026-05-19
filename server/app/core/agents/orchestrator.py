from __future__ import annotations

import json
import re
from dataclasses import dataclass

from server.app.core.agents.safety_guardian import SafetyAnalysis, SafetyGuardian
from server.app.core.generation.llm import OllamaClient
from server.app.core.safety.policy import SafetyPolicyEngine
from server.app.services.flows.topics import infer_topic
from server.app.utils.prompts import render_prompt
from server.app.utils.text import contains_any, normalize_text


@dataclass(slots=True)
class OrchestrationPlan:
    route: str
    topic: str
    primary_intent: str
    safety_mode: str
    risk_level: int
    secondary_intents: list[str] | None = None
    intent_confidence: float = 0.5
    use_rag: bool = False
    sentiment_label: str = "neutral"
    sentiment_urgency: int = 1
    clinical_plan: str = ""
    immediate_response: str | None = None

    @property
    def intent(self) -> str:
        """Backward-compatible alias for callers still using plan.intent."""
        return self.primary_intent


class Orchestrator:
    """
    The 'Super-Agent' that coordinates safety and performs a unified 
    strategic analysis (Intent + Sentiment + Plan) in a single pass.
    """

    def __init__(self, llm: OllamaClient | None = None) -> None:
        self.llm = llm or OllamaClient()
        self.safety = SafetyGuardian()
        self.keyword_safety = SafetyPolicyEngine()

    @staticmethod
    def _is_plain_symptom_statement(message: str) -> bool:
        normalized = normalize_text(message).strip()
        if not normalized or "?" in normalized:
            return False

        if contains_any(normalized, [
            "do i have", "am i", "diagnose", "what disorder do i have", "what mental illness do i have",
            "what's my diagnosis", "what is my diagnosis", "should i take", "what medication", "what medicine",
        ]):
            return False

        symptom_statement = re.search(
            r"\b(i have|i'm|im|i feel|i feel like)\b.*\b(anxiety|anxious|stress|depressed|depression|burnout|panic|sad|low mood)\b",
            normalized,
        )
        return bool(symptom_statement)

    def plan(self, message: str, intake: dict[str, str] | None = None) -> OrchestrationPlan:
        # 1. Quick Keyword Safety (No LLM)
        keyword_decision = self.keyword_safety.evaluate(message)
        topic = infer_topic(message, intake)

        if keyword_decision.mode != "normal":
            return OrchestrationPlan(
                route=keyword_decision.mode,
                topic=topic,
                primary_intent="crisis" if keyword_decision.mode == "crisis_support" else "off_scope",
                safety_mode=keyword_decision.mode,
                risk_level=keyword_decision.risk_level,
                intent_confidence=1.0,
                immediate_response=keyword_decision.message,
            )

        # 2. Advanced Analysis (Consolidated LLM Call)
        # This replaces separate Orchestrator, Sentiment, and Planner calls.
        prompt = render_prompt("agents.brain_analysis", MESSAGE=message)
        result = self.llm.generate(prompt, temperature=0.0)
        
        analysis = {
            "primary_intent": "psychoeducation",
            "secondary_intents": [],
            "intent_confidence": 0.5,
            "sentiment": {"label": "neutral", "urgency": 1},
            "plan": "listen and reflect",
            "use_rag": False
        }

        if result.available and result.text:
            try:
                raw = result.text.strip()
                raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
                analysis = json.loads(raw)
            except Exception:
                pass

        # 3. Crisis/Safety Check (Standard LLM Safety)
        if self._is_plain_symptom_statement(message):
            safety_analysis = SafetyAnalysis(
                mode="normal",
                risk_level=0,
                reasoning="plain symptom statement",
                message="",
            )
        else:
            safety_analysis = self.safety.analyze(message)
        if safety_analysis.mode != "normal":
            primary_intent = self._normalize_intent(analysis.get("primary_intent") or analysis.get("intent", "emotional_support"))
            return OrchestrationPlan(
                route=safety_analysis.mode,
                topic=topic,
                primary_intent=primary_intent,
                safety_mode=safety_analysis.mode,
                risk_level=safety_analysis.risk_level,
                secondary_intents=self._normalize_secondary_intents(analysis.get("secondary_intents", []), primary_intent),
                intent_confidence=float(analysis.get("intent_confidence", analysis.get("confidence", 0.5)) or 0.5),
                immediate_response=safety_analysis.message,
            )

        intent = self._normalize_intent(analysis.get("primary_intent") or analysis.get("intent", "psychoeducation"))
        secondary_intents = self._normalize_secondary_intents(analysis.get("secondary_intents", []), intent)
        intent_confidence = float(analysis.get("intent_confidence", analysis.get("confidence", 0.5)) or 0.5)
        use_rag = analysis.get("use_rag", False)
        analysis_topic = analysis.get("topic")
        resolved_topic = analysis_topic if analysis_topic and analysis_topic != "general" else topic

        # Force RAG for informational intents to ensure we get clinical evidence
        if intent in ["psychoeducation", "symptom_exploration", "coping_strategy"]:
            use_rag = True
            
        print(f"[DEBUG] Final Orchestration -> Intent: {intent}, UseRAG: {use_rag}, Topic: {resolved_topic}")

        return OrchestrationPlan(
            route=f"topic:{resolved_topic}",
            topic=resolved_topic,
            primary_intent=intent,
            safety_mode="normal",
            risk_level=0,
            secondary_intents=secondary_intents,
            intent_confidence=max(0.0, min(intent_confidence, 1.0)),
            use_rag=use_rag,
            sentiment_label=analysis.get("sentiment", {}).get("label", "neutral"),
            sentiment_urgency=analysis.get("sentiment", {}).get("urgency", 1),
            clinical_plan=analysis.get("plan", "")
        )

    @staticmethod
    def _normalize_intent(intent: str) -> str:
        intent_map = {
            "educational_request": "psychoeducation",
            "general_query": "psychoeducation",
            "medical_info": "psychoeducation",
            "symptom_search": "symptom_exploration",
            "venting": "emotional_support",
            "greeting": "emotional_support",
            "clarification": "clarification_needed",
            "safety_violation": "crisis",
        }
        allowed = {
            "emotional_support",
            "psychoeducation",
            "coping_strategy",
            "symptom_exploration",
            "clarification_needed",
            "crisis",
            "off_scope",
            "repair",
        }
        normalized = intent_map.get(intent, intent)
        return normalized if normalized in allowed else "emotional_support"

    @classmethod
    def _normalize_secondary_intents(cls, intents: object, primary_intent: str) -> list[str]:
        if not isinstance(intents, list):
            return []
        normalized: list[str] = []
        for item in intents:
            intent = cls._normalize_intent(str(item))
            if intent != primary_intent and intent not in normalized:
                normalized.append(intent)
        return normalized[:3]

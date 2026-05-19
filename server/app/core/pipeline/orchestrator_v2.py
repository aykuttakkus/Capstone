from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from server.app.core.agents.distress_monitor import SubtleDistressMonitor
from server.app.core.agents.dependency_critic import DependencyCritic
from server.app.core.agents.quality_critic import QualityCritic
from server.app.core.agents.fallback_handler import FallbackHandler, FallbackMode
from server.app.core.agents.orchestrator import Orchestrator
from server.app.core.agents.response_planner import ResponsePlan
from server.app.core.agents.safety_guardian import SafetyAnalysis
from server.app.core.pipeline.response_modes import ResponseMode, ResponseModeContext, ResponseModeSelector


@dataclass(slots=True)
class PipelineContext:
    user_message: str
    topic: str
    intent: str
    risk_level: int = 0
    conversation_history: list[str] = field(default_factory=list)
    retrieved_content: str | None = None
    profile_context: dict[str, Any] | None = None
    screening_state: dict[str, Any] | None = None


@dataclass(slots=True)
class PipelineResult:
    response: str
    mode: ResponseMode
    is_degraded: bool
    distress_signals: int
    dependency_violations: int
    quality_score: float
    execution_time_ms: float
    warnings: list[str] = field(default_factory=list)


class PipelineOrchestrator:
    def __init__(
        self,
        orchestrator: Orchestrator,
        distress_monitor: SubtleDistressMonitor,
        dependency_critic: DependencyCritic,
        quality_critic: QualityCritic,
        fallback_handler: FallbackHandler,
    ) -> None:
        self.orchestrator = orchestrator
        self.distress_monitor = distress_monitor
        self.dependency_critic = dependency_critic
        self.quality_critic = quality_critic
        self.fallback_handler = fallback_handler
        self.mode_selector = ResponseModeSelector()

    async def execute(
        self,
        context: PipelineContext,
        llm_available: bool = True,
        retrieval_available: bool = True,
    ) -> PipelineResult:
        start_time = time.time()
        warnings = []

        # Step 1: Distress Analysis
        distress_analysis = self.distress_monitor.analyze(
            context.user_message,
            context.conversation_history,
            {"distress_level": context.risk_level},
            turn_number=len(context.conversation_history),
        )

        if distress_analysis.escalation_detected:
            warnings.append(f"Escalation detected: {distress_analysis.recommended_action}")
            context.risk_level = max(context.risk_level, distress_analysis.current_distress_level)

        # Step 2: Route to appropriate mode
        response_mode = self._select_response_mode(distress_analysis, context)

        # Step 3: Generate response
        if response_mode == ResponseMode.CRISIS:
            response = self._generate_crisis_response(context)
            quality_score = 1.0
        elif response_mode == ResponseMode.OFF_SCOPE:
            response = self._generate_off_scope_response(context)
            quality_score = 0.8
        else:
            response = self._generate_response(
                context, response_mode, llm_available, retrieval_available
            )

            # Step 4: Dependency Critique
            dep_result = self.dependency_critic.critique(response, context.profile_context)
            if not dep_result.is_safe:
                warnings.append(f"Dependency concern: {dep_result.severity} - {dep_result.recommendation}")
                response = self._revise_response(response, dep_result.recommendation)

            # Step 5: Quality Critique
            quality_result = self.quality_critic.critique(
                response,
                response_mode.value,
                context.user_message,
                context.conversation_history,
                context.risk_level,
            )
            quality_score = quality_result.overall_score

            if not quality_result.is_acceptable:
                warnings.extend(quality_result.concerns)
                if quality_result.recommendations:
                    response = self._enhance_response(response, quality_result.recommendations[0])

        execution_time = (time.time() - start_time) * 1000

        return PipelineResult(
            response=response,
            mode=response_mode,
            is_degraded=not (llm_available and retrieval_available),
            distress_signals=len(distress_analysis.signals),
            dependency_violations=self._count_violations(
                self.dependency_critic.critique(response, context.profile_context)
            ),
            quality_score=quality_score,
            execution_time_ms=execution_time,
            warnings=warnings,
        )

    def _select_response_mode(
        self, distress_analysis: Any, context: PipelineContext
    ) -> ResponseMode:
        if distress_analysis.recommended_action == "escalate_to_crisis_resources":
            return ResponseMode.CRISIS

        if context.intent == "off_scope":
            return ResponseMode.OFF_SCOPE

        intent_mode_map = {
            "psychoeducation": ResponseMode.PSYCHOEDUCATION,
            "coping_strategy": ResponseMode.COPING_STRATEGY,
            "symptom_exploration": ResponseMode.SYMPTOM_EXPLORATION,
            "clarification": ResponseMode.CLARIFICATION,
            "emotional_support": ResponseMode.EMOTIONAL_SUPPORT,
            "repair": ResponseMode.REPAIR,
        }

        return intent_mode_map.get(context.intent, ResponseMode.EMOTIONAL_SUPPORT)

    def _generate_response(
        self,
        context: PipelineContext,
        mode: ResponseMode,
        llm_available: bool,
        retrieval_available: bool,
    ) -> str:
        mode_context = ResponseModeContext(
            mode=mode,
            user_message=context.user_message,
            topic=context.topic,
            risk_level=context.risk_level,
            conversation_history=context.conversation_history,
            retrieved_content=context.retrieved_content,
            intent=context.intent,
            profile_context=context.profile_context,
        )

        builder = self.mode_selector.select_builder(mode)
        prompt = builder.build(mode_context)

        if not llm_available or not retrieval_available:
            fallback = self.fallback_handler.handle(
                llm_available, retrieval_available, context.topic, context.intent, context.user_message
            )
            return fallback.answer

        return f"[MODE: {mode.value}]\n\n{prompt}"

    def _generate_crisis_response(self, context: PipelineContext) -> str:
        builder = self.mode_selector.select_builder(ResponseMode.CRISIS)
        return builder.build(
            ResponseModeContext(
                mode=ResponseMode.CRISIS,
                user_message=context.user_message,
                topic=context.topic,
                risk_level=context.risk_level,
                conversation_history=context.conversation_history,
            )
        )

    def _generate_off_scope_response(self, context: PipelineContext) -> str:
        builder = self.mode_selector.select_builder(ResponseMode.OFF_SCOPE)
        return builder.build(
            ResponseModeContext(
                mode=ResponseMode.OFF_SCOPE,
                user_message=context.user_message,
                topic=context.topic,
                risk_level=context.risk_level,
                conversation_history=context.conversation_history,
            )
        )

    def _revise_response(self, response: str, recommendation: str) -> str:
        return f"{response}\n\n[REVISED PER SAFETY CHECK: {recommendation}]"

    def _enhance_response(self, response: str, enhancement: str) -> str:
        return f"{response}\n\n[ENHANCED: {enhancement}]"

    def _count_violations(self, critic_result: Any) -> int:
        return len(critic_result.violations) if hasattr(critic_result, "violations") else 0

    def get_pipeline_stats(self) -> dict[str, Any]:
        return {
            "distress_signals_tracked": len(self.distress_monitor.signal_history),
            "system_ready": True,
        }

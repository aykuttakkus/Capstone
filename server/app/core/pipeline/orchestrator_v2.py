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
from server.app.core.agents.safety_guardian import SafetyAnalysis, SafetyGuardian
from server.app.core.pipeline.response_modes import ResponseMode, ResponseModeContext, ResponseModeSelector, enforce_length_constraint
from server.app.core.pipeline.context_manager import ContextManager, ConversationContext
from server.app.core.pipeline.intent_detector import IntentDetector
from server.app.core.pipeline.risk_state import RiskState
from server.app.core.pipeline.rag_decision import RAGDecisionModule
from server.app.core.pipeline.escalation_logic import HumanEscalationLogic
from server.app.core.pipeline.memory_updater import MemoryUpdater, MemoryUpdateResult


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
    risk_state: RiskState = field(default_factory=lambda: RiskState(current_risk_level="none"))


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
    """14-step spec-compliant pipeline for safe psychoeducation responses.

    Step 1  — Context Manager     (ContextManager.build_context_package)
    Step 2  — Safety Triage       (SafetyGuardian.analyze)
    Step 3  — Subtle Distress     (SubtleDistressMonitor.analyze)
    Step 4  — Intent Detection    (PipelineContext.intent, populated by caller)
    Step 5  — RAG Decision        (RAGDecisionModule.decide)
    Step 6  — Evidence Retrieval  (handled by AssistantService)
    Step 7  — Response Planner    (ResponseModeSelector + builder.build)
    Step 8  — Answer Generator    (ResponseModeSelector + builder.build / LLM)
    Step 9  — Quality Critic      (QualityCritic.critique)
    Step 10 — Safety/Faithfulness (SafetyGuardian.analyze on output)
    Step 11 — Dependency Critic   (DependencyCritic.critique — prompt level)
    Step 12 — Escalation Logic    (HumanEscalationLogic.evaluate)
    Step 13 — Final Response      (PipelineResult)
    Step 14 — Memory Update       (MemoryUpdater.update)
    """

    def __init__(
        self,
        orchestrator: Orchestrator,
        distress_monitor: SubtleDistressMonitor,
        dependency_critic: DependencyCritic,
        quality_critic: QualityCritic,
        fallback_handler: FallbackHandler,
        safety_guardian: SafetyGuardian | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.distress_monitor = distress_monitor
        self.dependency_critic = dependency_critic
        self.quality_critic = quality_critic
        self.fallback_handler = fallback_handler
        self.safety_guardian = safety_guardian or SafetyGuardian()
        self.rag_decision = RAGDecisionModule()
        self.escalation_logic = HumanEscalationLogic()
        self.memory_updater = MemoryUpdater()
        self.mode_selector = ResponseModeSelector()
        self.context_manager = ContextManager()
        self.intent_detector = IntentDetector()

    async def execute(
        self,
        context: PipelineContext,
        llm_available: bool = True,
        retrieval_available: bool = True,
    ) -> PipelineResult:
        start_time = time.time()
        warnings = []

        # Step 1: Context Manager
        # (Already in PipelineContext)

        # Step 2: Safety Triage
        safety_result = self.safety_guardian.analyze(context.user_message)
        context.risk_state.update_risk_check(
            self._map_safety_mode_to_risk_level(safety_result.mode),
            safety_result.reasoning,
        )
        if safety_result.risk_level >= 4:
            context.risk_state.activate_crisis_protocol()
            warnings.append(f"Safety alert: {safety_result.reasoning}")

        # Step 3: Subtle Distress Monitor (M6: rehydrate history from DB risk state)
        self.distress_monitor.rehydrate_from_risk_state(
            list(context.risk_state.cumulative_risk_signals)
        )
        distress_analysis = self.distress_monitor.analyze(
            context.user_message,
            context.conversation_history,
            {"distress_level": context.risk_level},
            turn_number=len(context.conversation_history),
        )

        if distress_analysis.escalation_detected:
            warnings.append(f"Escalation detected: {distress_analysis.recommended_action}")
            context.risk_level = max(context.risk_level, distress_analysis.current_distress_level)
            context.risk_state.cumulative_risk_signals.extend([s.category for s in distress_analysis.signals])

        # Step 4: Intent Detection
        # (Already done when PipelineContext is created with intent)

        # Step 5: RAG Decision (intelligent retrieval decision)
        rag_decision = self.rag_decision.decide(
            intent=context.intent,
            topic=context.topic,
            conversation_length=len(context.conversation_history),
            risk_level=context.risk_level,
            has_recent_retrieval=False,  # Could track from session
        )

        # Step 6: Evidence Retrieval (handled by response generation)

        # Step 7: Response Planner
        # (Integrated in mode selection and generation)

        # Step 8: Answer Generator + Step 9: Response Quality Critic
        response_mode = self._select_response_mode(distress_analysis, context)
        dep_result = None  # initialise for all branches

        if response_mode == ResponseMode.CRISIS:
            response = self._generate_crisis_response(context)
            quality_score = 1.0
        elif response_mode == ResponseMode.OFF_SCOPE:
            response = self._generate_off_scope_response(context)
            quality_score = 0.8
        else:
            response = self._generate_response(
                context, response_mode, llm_available and rag_decision.use_rag, retrieval_available
            )

            # Step 9: Response Quality Critic
            quality_result = self.quality_critic.critique(
                response,
                response_mode.value,
                context.user_message,
                context.conversation_history,
                context.risk_level,
            )
            quality_score = quality_result.overall_score

            if not quality_result.passed:
                warnings.extend(quality_result.concerns)
                if quality_result.recommendations:
                    response = self._enhance_response(response, quality_result.recommendations[0])

            # Step 10: Safety & Faithfulness Critic
            safety_check = self.safety_guardian.analyze(response)
            if safety_check.risk_level >= 3:
                warnings.append(f"Safety check on response: {safety_check.reasoning}")
                if safety_check.message:
                    response = self._revise_response(response, safety_check.message)

            # Step 11: Dependency & Boundary Critic
            # P2: DependencyCritic runs here only in pipeline mode (on prompt strings).
            # The definitive check on actual LLM output happens in assistant._run_response_critics.
            dep_result = self.dependency_critic.critique(response, context.profile_context)
            if not dep_result.is_safe:
                warnings.append(f"Dependency concern: {dep_result.severity} - {dep_result.recommendation}")

        # Step 12: Human Escalation Logic
        escalation_decision = self.escalation_logic.evaluate(
            risk_level=context.risk_level,
            distress_signals=[s.category for s in distress_analysis.signals] if response_mode != ResponseMode.CRISIS else ["crisis"],
            conversation_length=len(context.conversation_history),
            quality_score=quality_score if response_mode != ResponseMode.CRISIS else 1.0,
            safety_concerns=warnings,
        )
        if escalation_decision.level.value != "none":
            warnings.append(f"Escalation: {escalation_decision.reason}")
            if escalation_decision.level.value == "immediate":
                context.risk_state.activate_crisis_protocol()

        # Step 12.5: Fallback Handler (already integrated in _generate_response)

        # Step 13: Final Response (PipelineResult)

        # Step 14: Memory Update (spec §31 structured update)
        memory_result = self._update_memory(
            context, response, response_mode,
            distress_signals=[s.category for s in distress_analysis.signals],
        )

        execution_time = (time.time() - start_time) * 1000

        return PipelineResult(
            response=response,
            mode=response_mode,
            is_degraded=not (llm_available and retrieval_available),
            distress_signals=len(distress_analysis.signals),
            dependency_violations=len(dep_result.violations) if dep_result is not None else 0,
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
            "clarification_needed": ResponseMode.CLARIFICATION,  # P1: normalize both forms
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
            return enforce_length_constraint(fallback.answer, mode)

        return enforce_length_constraint(f"[MODE: {mode.value}]\n\n{prompt}", mode)

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

    def _map_safety_mode_to_risk_level(self, mode: str) -> str:
        """Map SafetyGuardian mode to RiskState level."""
        mode_map = {
            "crisis": "crisis",
            "escalate": "high",
            "monitor": "medium",
            "normal": "none",
        }
        return mode_map.get(mode, "none")


    def _update_memory(
        self,
        context: PipelineContext,
        response: str,
        mode: ResponseMode,
        distress_signals: list[str] | None = None,
    ) -> MemoryUpdateResult:
        """Step 14: Structured memory update per spec §31 & §32.9."""
        previous_summary: dict[str, Any] = {}
        if context.profile_context:
            raw = context.profile_context.get("session_summary", {})
            previous_summary = raw if isinstance(raw, dict) else {"recap": str(raw)}

        result = self.memory_updater.update(
            user_message=context.user_message,
            final_response=response,
            previous_session_summary=previous_summary,
            previous_risk_state=context.risk_state,
            response_mode=mode.value,
            distress_signals=distress_signals or [],
        )

        # Update context_manager cache if session_id available
        session_id = getattr(context, "session_id", None)
        if session_id and hasattr(self.context_manager, "update_context"):
            self.context_manager.update_context(session_id, response, distress_level=context.risk_level)

        return result

    def get_pipeline_stats(self) -> dict[str, Any]:
        return {
            "distress_signals_tracked": len(self.distress_monitor.signal_history),
            "system_ready": True,
        }

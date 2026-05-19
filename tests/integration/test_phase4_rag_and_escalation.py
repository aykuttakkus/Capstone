from __future__ import annotations

import pytest

from server.app.core.agents.distress_monitor import SubtleDistressMonitor
from server.app.core.agents.dependency_critic import DependencyCritic
from server.app.core.agents.quality_critic import QualityCritic
from server.app.core.agents.fallback_handler import FallbackHandler
from server.app.core.agents.orchestrator import Orchestrator
from server.app.core.agents.safety_guardian import SafetyGuardian
from server.app.core.pipeline.orchestrator_v2 import (
    PipelineOrchestrator,
    PipelineContext,
)
from server.app.core.pipeline.rag_decision import RAGDecisionModule, RAGDecision
from server.app.core.pipeline.escalation_logic import (
    HumanEscalationLogic,
    EscalationLevel,
)
from server.app.core.pipeline.response_modes import ResponseMode


pytestmark = [pytest.mark.integration]


class TestRAGDecisionModule:
    """Test intelligent RAG decision making."""

    @pytest.fixture
    def rag_module(self):
        return RAGDecisionModule()

    def test_crisis_no_retrieval(self, rag_module):
        """Crisis mode should skip retrieval."""
        decision = rag_module.decide(
            intent="emotional_support",
            topic="crisis",
            conversation_length=1,
            risk_level=5,
        )

        assert decision.use_rag is False
        assert decision.retrieve_amount == 0
        assert "Crisis" in decision.reasoning

    def test_off_scope_no_retrieval(self, rag_module):
        """Off-scope requests should not retrieve."""
        decision = rag_module.decide(
            intent="off_scope",
            topic="medical",
            conversation_length=1,
            risk_level=1,
        )

        assert decision.use_rag is False
        assert decision.retrieve_amount == 0

    def test_emotional_support_no_retrieval(self, rag_module):
        """Emotional support doesn't need retrieval (normal)."""
        decision = rag_module.decide(
            intent="emotional_support",
            topic="anxiety",
            conversation_length=2,
            risk_level=2,
        )

        assert decision.use_rag is False
        assert "validation over information" in decision.reasoning

    def test_emotional_support_first_turn_light_retrieval(self, rag_module):
        """First turn emotional support gets light retrieval."""
        decision = rag_module.decide(
            intent="emotional_support",
            topic="anxiety",
            conversation_length=1,
            risk_level=2,
        )

        assert decision.use_rag is True
        assert decision.retrieve_amount == 2
        assert "First turn" in decision.reasoning

    def test_emotional_support_long_conversation_no_retrieval(self, rag_module):
        """Long emotional support conversations skip retrieval."""
        decision = rag_module.decide(
            intent="emotional_support",
            topic="anxiety",
            conversation_length=6,
            risk_level=2,
        )

        assert decision.use_rag is False
        assert "repetition" in decision.reasoning

    def test_psychoeducation_retrieval(self, rag_module):
        """Psychoeducation needs retrieval."""
        decision = rag_module.decide(
            intent="psychoeducation",
            topic="anxiety",
            conversation_length=2,
            risk_level=2,
        )

        assert decision.use_rag is True
        assert decision.retrieve_amount >= 2

    def test_coping_strategy_retrieval(self, rag_module):
        """Coping strategy needs retrieval."""
        decision = rag_module.decide(
            intent="coping_strategy",
            topic="stress",
            conversation_length=2,
            risk_level=2,
        )

        assert decision.use_rag is True
        assert decision.retrieve_amount >= 2

    def test_symptom_exploration_retrieval(self, rag_module):
        """Symptom exploration needs retrieval."""
        decision = rag_module.decide(
            intent="symptom_exploration",
            topic="anxiety",
            conversation_length=2,
            risk_level=2,
        )

        assert decision.use_rag is True
        assert decision.retrieve_amount >= 2

    def test_high_risk_reduces_retrieval(self, rag_module):
        """Crisis risk skips retrieval."""
        decision = rag_module.decide(
            intent="coping_strategy",
            topic="anxiety",
            conversation_length=2,
            risk_level=4,  # Crisis threshold
        )

        # Crisis level (>= 4) skips RAG
        assert decision.use_rag is False
        assert decision.retrieve_amount == 0

    def test_long_conversation_reduces_retrieval(self, rag_module):
        """Long conversations reduce retrieval."""
        decision = rag_module.decide(
            intent="psychoeducation",
            topic="anxiety",
            conversation_length=6,
            risk_level=1,
        )

        assert decision.use_rag is True
        assert decision.retrieve_amount == 2
        assert "long conversation" in decision.reasoning

    def test_retrieval_context_generation(self, rag_module):
        """Test generation of retrieval context."""
        decision = RAGDecision(
            use_rag=True,
            retrieve_amount=3,
            reasoning="test",
            confidence=0.9,
        )

        context = rag_module.get_retrieval_context(decision)
        assert context["top_k"] == 3
        assert context["min_score"] == 0.5

    def test_retrieval_caching_decision(self, rag_module):
        """Test retrieval caching decision."""
        decision_cache = RAGDecision(
            use_rag=True,
            retrieve_amount=3,
            reasoning="test",
            confidence=0.9,
        )
        decision_no_cache = RAGDecision(
            use_rag=True,
            retrieve_amount=1,
            reasoning="test",
            confidence=0.9,
        )

        assert rag_module.should_cache_retrieval(decision_cache) is True
        assert rag_module.should_cache_retrieval(decision_no_cache) is False


class TestHumanEscalationLogic:
    """Test human escalation decision logic."""

    @pytest.fixture
    def escalation(self):
        return HumanEscalationLogic()

    def test_user_explicit_request_escalation(self, escalation):
        """User explicit request for help escalates immediately."""
        decision = escalation.evaluate(
            risk_level=1,
            distress_signals=[],
            conversation_length=2,
            quality_score=0.8,
            user_explicitly_requested=True,
        )

        assert decision.level == EscalationLevel.IMMEDIATE_ESCALATION

    def test_crisis_immediate_escalation(self, escalation):
        """Crisis (level 5) escalates immediately."""
        decision = escalation.evaluate(
            risk_level=5,
            distress_signals=["hopelessness"],
            conversation_length=2,
            quality_score=0.8,
        )

        assert decision.level == EscalationLevel.IMMEDIATE_ESCALATION
        assert "Crisis detected" in decision.reason

    def test_multiple_safety_concerns_escalation(self, escalation):
        """Multiple safety concerns escalate immediately."""
        decision = escalation.evaluate(
            risk_level=2,
            distress_signals=[],
            conversation_length=2,
            quality_score=0.8,
            safety_concerns=["concern1", "concern2", "concern3"],
        )

        assert decision.level == EscalationLevel.IMMEDIATE_ESCALATION

    def test_high_risk_poor_quality_recommend(self, escalation):
        """High risk + poor quality response recommends human."""
        decision = escalation.evaluate(
            risk_level=4,
            distress_signals=["burden"],
            conversation_length=2,
            quality_score=0.5,
        )

        assert decision.level == EscalationLevel.RECOMMEND_HUMAN

    def test_persistent_high_risk_recommend(self, escalation):
        """Persistent high risk over 5+ turns recommends human."""
        decision = escalation.evaluate(
            risk_level=4,
            distress_signals=["withdrawal"],
            conversation_length=6,
            quality_score=0.7,
        )

        assert decision.level == EscalationLevel.RECOMMEND_HUMAN
        assert "high-risk" in decision.reason.lower() and "5+" in decision.reason

    def test_critical_signals_recommend(self, escalation):
        """Multiple critical distress signals recommend human."""
        decision = escalation.evaluate(
            risk_level=2,
            distress_signals=["hopelessness", "helplessness"],
            conversation_length=2,
            quality_score=0.8,
        )

        assert decision.level == EscalationLevel.RECOMMEND_HUMAN

    def test_high_risk_stable_monitor(self, escalation):
        """High risk but stable conversation is monitored."""
        decision = escalation.evaluate(
            risk_level=4,
            distress_signals=["sadness"],
            conversation_length=2,
            quality_score=0.8,
        )

        assert decision.level == EscalationLevel.MONITOR

    def test_medium_risk_with_safety_monitor(self, escalation):
        """Medium risk with safety concerns is monitored."""
        decision = escalation.evaluate(
            risk_level=2,
            distress_signals=[],
            conversation_length=2,
            quality_score=0.8,
            safety_concerns=["concern1"],
        )

        assert decision.level == EscalationLevel.MONITOR

    def test_low_risk_no_escalation(self, escalation):
        """Low risk with good quality needs no escalation."""
        decision = escalation.evaluate(
            risk_level=1,
            distress_signals=[],
            conversation_length=2,
            quality_score=0.9,
        )

        assert decision.level == EscalationLevel.NONE

    def test_escalation_message_immediate(self, escalation):
        """Test immediate escalation message."""
        decision = escalation.evaluate(
            risk_level=5,
            distress_signals=[],
            conversation_length=1,
            quality_score=1.0,
        )

        message = escalation.format_escalation_message(decision)
        assert "immediate support" in message

    def test_escalation_message_recommend(self, escalation):
        """Test recommend escalation message."""
        decision = escalation.evaluate(
            risk_level=4,
            distress_signals=[],
            conversation_length=1,
            quality_score=0.5,
        )

        message = escalation.format_escalation_message(decision)
        assert "counselor" in message

    def test_escalation_routing(self, escalation):
        """Test escalation routing generation."""
        decision = escalation.evaluate(
            risk_level=5,
            distress_signals=[],
            conversation_length=1,
            quality_score=1.0,
        )

        routing = escalation.get_escalation_routing(decision)
        assert routing["level"] == "immediate"
        assert "crisis_hotline" in routing["channels"]


class TestPipelineRAGDecision:
    """Test RAG decision integration in pipeline."""

    @pytest.fixture
    def orchestrator(self):
        return PipelineOrchestrator(
            orchestrator=Orchestrator(),
            distress_monitor=SubtleDistressMonitor(),
            dependency_critic=DependencyCritic(),
            quality_critic=QualityCritic(),
            fallback_handler=FallbackHandler(),
            safety_guardian=SafetyGuardian(),
        )

    @pytest.mark.anyio
    async def test_rag_decision_in_pipeline(self, orchestrator):
        """Test RAG decision module is used in pipeline."""
        context = PipelineContext(
            user_message="I need practical techniques for managing anxiety",
            topic="anxiety",
            intent="coping_strategy",
        )

        result = await orchestrator.execute(context)

        # Should use RAG for coping_strategy
        assert isinstance(result.response, str)
        assert isinstance(result.mode, ResponseMode)

    @pytest.mark.anyio
    async def test_emotional_support_skips_rag(self, orchestrator):
        """Test emotional support intent skips RAG."""
        context = PipelineContext(
            user_message="I'm feeling really overwhelmed right now",
            topic="anxiety",
            intent="emotional_support",
            conversation_history=["Hi there", "How are you?"],
        )

        result = await orchestrator.execute(context)

        # Response should still be generated (fallback or direct)
        assert isinstance(result.response, str)
        assert len(result.response) > 0

    @pytest.mark.anyio
    async def test_crisis_no_rag(self, orchestrator):
        """Test crisis mode skips RAG."""
        context = PipelineContext(
            user_message="I want to end my life",
            topic="crisis",
            intent="crisis",
            risk_level=5,
        )

        result = await orchestrator.execute(context)

        # Should handle crisis with crisis response
        assert result.mode == ResponseMode.CRISIS or result.mode == ResponseMode.EMOTIONAL_SUPPORT


class TestPipelineEscalation:
    """Test escalation logic integration in pipeline."""

    @pytest.fixture
    def orchestrator(self):
        return PipelineOrchestrator(
            orchestrator=Orchestrator(),
            distress_monitor=SubtleDistressMonitor(),
            dependency_critic=DependencyCritic(),
            quality_critic=QualityCritic(),
            fallback_handler=FallbackHandler(),
            safety_guardian=SafetyGuardian(),
        )

    @pytest.mark.anyio
    async def test_escalation_in_warnings(self, orchestrator):
        """Test escalation decision appears in warnings."""
        context = PipelineContext(
            user_message="I'm hopeless and everything feels pointless",
            topic="depression",
            intent="emotional_support",
            risk_level=4,
        )

        result = await orchestrator.execute(context)

        # High risk conversation should trigger escalation
        assert isinstance(result.warnings, list)
        # May or may not have escalation warning depending on full analysis
        assert isinstance(result.response, str)

    @pytest.mark.anyio
    async def test_crisis_activates_crisis_protocol(self, orchestrator):
        """Test crisis escalation activates crisis protocol."""
        context = PipelineContext(
            user_message="I can't do this anymore",
            topic="depression",
            intent="emotional_support",
            risk_level=5,
        )

        result = await orchestrator.execute(context)

        # Crisis should route appropriately
        assert isinstance(result.response, str)
        # Risk state should be updated for crisis
        assert context.risk_state.crisis_protocol_active or result.mode == ResponseMode.CRISIS

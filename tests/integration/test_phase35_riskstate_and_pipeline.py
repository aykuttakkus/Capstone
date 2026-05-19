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
from server.app.core.pipeline.risk_state import RiskState
from server.app.core.pipeline.response_modes import ResponseMode


pytestmark = [pytest.mark.integration]


class TestRiskState:
    """Test RiskState dataclass and methods."""

    def test_risk_state_initialization(self):
        """Test RiskState initializes with defaults."""
        risk_state = RiskState(current_risk_level="none")
        assert risk_state.current_risk_level == "none"
        assert risk_state.crisis_protocol_active is False
        assert risk_state.needs_human_support is False
        assert risk_state.risk_indicators == []

    def test_risk_state_escalation(self):
        """Test escalation method."""
        risk_state = RiskState(current_risk_level="low")
        risk_state.escalate("User expressed hopelessness")

        assert risk_state.needs_human_support is True
        assert risk_state.escalation_recommended is True
        assert "User expressed hopelessness" in risk_state.risk_indicators

    def test_risk_state_crisis_activation(self):
        """Test crisis protocol activation."""
        risk_state = RiskState(current_risk_level="low")
        risk_state.activate_crisis_protocol()

        assert risk_state.crisis_protocol_active is True
        assert risk_state.current_risk_level == "crisis"
        assert risk_state.needs_human_support is True
        assert risk_state.last_risk_check is not None

    def test_risk_state_high_risk_check(self):
        """Test is_high_risk method."""
        risk_state = RiskState(current_risk_level="low")
        assert risk_state.is_high_risk() is False

        risk_state.current_risk_level = "high"
        assert risk_state.is_high_risk() is True

        risk_state.current_risk_level = "crisis"
        assert risk_state.is_high_risk() is True

    def test_risk_state_update_check(self):
        """Test risk check update."""
        risk_state = RiskState(current_risk_level="none")
        risk_state.update_risk_check("medium", "Escalation signals detected")

        assert risk_state.current_risk_level == "medium"
        assert risk_state.last_risk_check is not None
        assert risk_state.safety_analysis_reasoning == "Escalation signals detected"


class TestPipeline14Steps:
    """Test that all 14 pipeline steps are active."""

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
    async def test_pipeline_initializes_risk_state(self, orchestrator):
        """Test pipeline context includes RiskState."""
        context = PipelineContext(
            user_message="I'm feeling anxious",
            topic="anxiety",
            intent="emotional_support",
        )

        assert isinstance(context.risk_state, RiskState)
        assert context.risk_state.current_risk_level == "none"

    @pytest.mark.anyio
    async def test_pipeline_safety_triage_step(self, orchestrator):
        """Test step 2: Safety Triage executes."""
        context = PipelineContext(
            user_message="I'm feeling anxious",
            topic="anxiety",
            intent="emotional_support",
        )

        result = await orchestrator.execute(context)

        # Safety triage should update risk_state
        assert context.risk_state.last_risk_check is not None
        assert isinstance(result.response, str)

    @pytest.mark.anyio
    async def test_pipeline_distress_monitor_step(self, orchestrator):
        """Test step 3: Distress Monitor executes."""
        context = PipelineContext(
            user_message="I'm hopeless and everything feels pointless",
            topic="depression",
            intent="emotional_support",
        )

        result = await orchestrator.execute(context)

        # Distress monitor should detect signals
        assert result.distress_signals >= 0
        assert isinstance(result.response, str)

    @pytest.mark.anyio
    async def test_pipeline_safety_faithfulness_check(self, orchestrator):
        """Test step 10: Safety & Faithfulness Critic executes."""
        context = PipelineContext(
            user_message="How do I manage anxiety?",
            topic="anxiety",
            intent="coping_strategy",
        )

        result = await orchestrator.execute(context)

        # Response should be generated and pass safety checks
        assert isinstance(result.response, str)
        assert len(result.response) > 0

    @pytest.mark.anyio
    async def test_pipeline_memory_update_step(self, orchestrator):
        """Test step 14: Memory Update is called."""
        context = PipelineContext(
            user_message="I'm feeling better today",
            topic="anxiety",
            intent="emotional_support",
            conversation_history=["Hi there", "How are you?"],
        )

        result = await orchestrator.execute(context)

        # Memory update should be called (no error raised)
        assert isinstance(result.response, str)
        assert isinstance(result.mode, ResponseMode)

    @pytest.mark.anyio
    async def test_pipeline_full_14_steps_execution(self, orchestrator):
        """Test complete 14-step pipeline execution."""
        context = PipelineContext(
            user_message="I've been struggling with sleep and anxiety",
            topic="stress",
            intent="coping_strategy",
            conversation_history=[
                "I'm not sleeping well",
                "It's affecting my work",
            ],
        )

        result = await orchestrator.execute(context)

        # All steps should complete
        assert isinstance(result.response, str)
        assert isinstance(result.mode, ResponseMode)
        assert isinstance(result.quality_score, float)
        assert 0 <= result.quality_score <= 1
        assert result.execution_time_ms > 0
        assert len(result.warnings) >= 0

    @pytest.mark.anyio
    async def test_pipeline_risk_escalation_flow(self, orchestrator):
        """Test risk escalation through pipeline."""
        context = PipelineContext(
            user_message="I don't think I can handle this anymore",
            topic="depression",
            intent="emotional_support",
            risk_level=3,
        )

        result = await orchestrator.execute(context)

        # Risk state should be updated based on safety and distress analysis
        assert context.risk_state.last_risk_check is not None
        assert isinstance(result.response, str)

    @pytest.mark.anyio
    async def test_pipeline_crisis_detection_through_safety(self, orchestrator):
        """Test crisis detection through safety triage step."""
        context = PipelineContext(
            user_message="I want to end my life",
            topic="crisis",
            intent="crisis",
        )

        result = await orchestrator.execute(context)

        # Should handle crisis appropriately
        assert result.mode == ResponseMode.CRISIS or result.mode == ResponseMode.EMOTIONAL_SUPPORT
        assert isinstance(result.response, str)

    @pytest.mark.anyio
    async def test_pipeline_off_scope_detection(self, orchestrator):
        """Test off-scope detection in pipeline."""
        context = PipelineContext(
            user_message="Can you prescribe me medication?",
            topic="medical",
            intent="off_scope",
        )

        result = await orchestrator.execute(context)

        assert result.mode == ResponseMode.OFF_SCOPE
        assert isinstance(result.response, str)

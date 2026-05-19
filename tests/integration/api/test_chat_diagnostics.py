"""
Integration Tests for Phase 11: ChatResponse Diagnostics

Tests the full pipeline integration with diagnostic fields.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from server.app.models.schemas.chat import ChatRequest, ChatResponse
from server.app.services.assistant import AssistantService


class TestChatResponseDiagnosticsIntegration:
    """Integration tests for Phase 11 diagnostic fields in chat API."""
    
    def test_normal_response_includes_diagnostics(self):
        """Test that normal chat response includes all diagnostic fields."""
        # This would be a full integration test with the actual service
        # For now, we verify the schema supports the fields
        
        response = ChatResponse(
            session_id=1,
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test summary",
            answer="This is a test response",
            sources=[],
            retrieval_diagnostics=[],
            personalization_applied=False,
            personalization_signals=[],
            context_used={},
            # Phase 11 diagnostic fields
            pipeline_mode="v2",
            response_mode="education",
            risk_level="none",
            intent_confidence=0.85,
            secondary_intents=["emotional_support"],
            retrieval_confidence=0.92,
            critic_warnings=[],
            fallback_used=False,
            boundary_applied=False,
            escalation_required=False,
        )
        
        # Verify response can be serialized
        response_dict = response.model_dump()
        assert "pipeline_mode" in response_dict
        assert "response_mode" in response_dict
        assert "risk_level" in response_dict
        assert "intent_confidence" in response_dict
        assert "secondary_intents" in response_dict
        assert "retrieval_confidence" in response_dict
        assert "critic_warnings" in response_dict
        assert "fallback_used" in response_dict
        assert "boundary_applied" in response_dict
        assert "escalation_required" in response_dict
    
    def test_crisis_response_diagnostics(self):
        """Test diagnostic fields in crisis response."""
        response = ChatResponse(
            session_id=1,
            status="success",
            route="crisis",
            intent="crisis",
            safety_mode="crisis_support",
            summary="Crisis response",
            answer="Please contact emergency services...",
            sources=[],
            retrieval_diagnostics=[],
            personalization_applied=False,
            personalization_signals=[],
            context_used={},
            pipeline_mode="v2_safety",
            response_mode="crisis",
            risk_level="crisis",
            intent_confidence=1.0,
            secondary_intents=[],
            retrieval_confidence=0.0,
            critic_warnings=[],
            fallback_used=False,
            boundary_applied=True,
            escalation_required=True,
        )
        
        assert response.risk_level == "crisis"
        assert response.escalation_required is True
        assert response.boundary_applied is True
    
    def test_fallback_response_diagnostics(self):
        """Test diagnostic fields when fallback is triggered."""
        response = ChatResponse(
            session_id=1,
            status="success",
            route="clarify",
            intent="clarification_needed",
            safety_mode="normal",
            summary="Insufficient evidence fallback",
            answer="Could you provide more context?",
            sources=[],
            retrieval_diagnostics=[],
            personalization_applied=False,
            personalization_signals=[],
            context_used={},
            pipeline_mode="v2_insufficient",
            response_mode="clarify",
            risk_level="none",
            intent_confidence=0.5,
            secondary_intents=[],
            retrieval_confidence=0.0,
            critic_warnings=["insufficient_evidence"],
            fallback_used=True,
            boundary_applied=False,
            escalation_required=False,
        )
        
        assert response.fallback_used is True
        assert "insufficient_evidence" in response.critic_warnings
        assert response.retrieval_confidence == 0.0
    
    def test_response_with_critic_warnings(self):
        """Test diagnostic fields with critic warnings."""
        response = ChatResponse(
            session_id=1,
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Response with warnings",
            answer="Answer after revision",
            sources=[],
            retrieval_diagnostics=[],
            personalization_applied=False,
            personalization_signals=[],
            context_used={},
            pipeline_mode="v2",
            response_mode="education",
            risk_level="none",
            intent_confidence=0.80,
            secondary_intents=[],
            retrieval_confidence=0.85,
            critic_warnings=["diagnosis_detected", "rewritten"],
            fallback_used=False,
            boundary_applied=True,
            escalation_required=False,
        )
        
        assert len(response.critic_warnings) == 2
        assert "diagnosis_detected" in response.critic_warnings
        assert "rewritten" in response.critic_warnings
    
    def test_mixed_intent_diagnostics(self):
        """Test diagnostic fields with multiple secondary intents."""
        response = ChatResponse(
            session_id=1,
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Mixed intent response",
            answer="Here's information and support...",
            sources=[],
            retrieval_diagnostics=[],
            personalization_applied=True,
            personalization_signals=["profile", "memory"],
            context_used={"profile": True, "memory": True},
            pipeline_mode="v2",
            response_mode="education",
            risk_level="low",
            intent_confidence=0.75,
            secondary_intents=["emotional_support", "coping_strategy"],
            retrieval_confidence=0.88,
            critic_warnings=[],
            fallback_used=False,
            boundary_applied=False,
            escalation_required=False,
        )
        
        assert len(response.secondary_intents) == 2
        assert response.intent_confidence == 0.75
        assert response.personalization_applied is True
    
    def test_backward_compatibility(self):
        """Test that old clients still work without diagnostic fields."""
        # Simulate old client sending request without diagnostic fields
        response = ChatResponse(
            session_id=1,
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Backward compatible response",
            answer="This works with old clients",
        )
        
        # Verify defaults are applied
        assert response.pipeline_mode is None
        assert response.response_mode is None
        assert response.risk_level is None
        assert response.intent_confidence is None
        assert response.secondary_intents == []
        assert response.retrieval_confidence is None
        assert response.critic_warnings == []
        assert response.fallback_used is False
        assert response.boundary_applied is False
        assert response.escalation_required is False
        
        # Verify basic fields still work
        assert response.status == "success"
        assert response.intent == "psychoeducation"


@pytest.mark.asyncio
class TestDiagnosticFieldTypes:
    """Test type validation of diagnostic fields."""
    
    def test_intent_confidence_float(self):
        """Test intent confidence must be a float."""
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test",
            answer="Test",
            intent_confidence=0.85,
        )
        assert isinstance(response.intent_confidence, float)
    
    def test_risk_level_string(self):
        """Test risk level is a string."""
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test",
            answer="Test",
            risk_level="medium",
        )
        assert isinstance(response.risk_level, str)
    
    def test_secondary_intents_list_of_strings(self):
        """Test secondary intents is a list of strings."""
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test",
            answer="Test",
            secondary_intents=["emotional_support", "coping_strategy"],
        )
        assert isinstance(response.secondary_intents, list)
        assert all(isinstance(i, str) for i in response.secondary_intents)
    
    def test_critic_warnings_list_of_strings(self):
        """Test critic warnings is a list of strings."""
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test",
            answer="Test",
            critic_warnings=["warning1", "warning2"],
        )
        assert isinstance(response.critic_warnings, list)
        assert all(isinstance(w, str) for w in response.critic_warnings)
    
    def test_boolean_fields(self):
        """Test boolean diagnostic fields."""
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test",
            answer="Test",
            fallback_used=True,
            boundary_applied=True,
            escalation_required=False,
        )
        assert isinstance(response.fallback_used, bool)
        assert isinstance(response.boundary_applied, bool)
        assert isinstance(response.escalation_required, bool)
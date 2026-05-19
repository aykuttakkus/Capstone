"""
Phase 11 Tests: ChatResponse Diagnostics

Tests for the diagnostic fields added to ChatResponse as per Phase 11
of the CALMA_FULL_INTEGRATION_COMPLETION_PLAN.
"""

import pytest
from server.app.models.schemas.chat import ChatResponse, SourceReference, RetrievalDiagnostic


class TestChatResponseDiagnostics:
    """Test that ChatResponse includes all Phase 11 diagnostic fields."""
    
    def test_chat_response_has_all_diagnostic_fields(self):
        """Verify ChatResponse model includes all required diagnostic fields."""
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test summary",
            answer="Test answer",
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
        
        # Verify all diagnostic fields are present
        assert response.pipeline_mode == "v2"
        assert response.response_mode == "education"
        assert response.risk_level == "none"
        assert response.intent_confidence == 0.85
        assert response.secondary_intents == ["emotional_support"]
        assert response.retrieval_confidence == 0.92
        assert response.critic_warnings == []
        assert response.fallback_used is False
        assert response.boundary_applied is False
        assert response.escalation_required is False
    
    def test_chat_response_with_crisis_diagnostics(self):
        """Test diagnostic fields for crisis response."""
        response = ChatResponse(
            status="success",
            route="crisis",
            intent="crisis",
            safety_mode="crisis_support",
            summary="Crisis summary",
            answer="Crisis response",
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
        assert response.response_mode == "crisis"
        assert response.boundary_applied is True
        assert response.escalation_required is True
    
    def test_chat_response_with_fallback_diagnostics(self):
        """Test diagnostic fields when fallback is used."""
        response = ChatResponse(
            status="success",
            route="clarify",
            intent="clarification_needed",
            safety_mode="normal",
            summary="Insufficient evidence",
            answer="Fallback response",
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
    
    def test_chat_response_with_mixed_intent_diagnostics(self):
        """Test diagnostic fields with multiple secondary intents."""
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Mixed intent summary",
            answer="Mixed intent response",
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
        assert "emotional_support" in response.secondary_intents
        assert "coping_support" not in response.secondary_intents
        assert response.intent_confidence == 0.75
    
    def test_chat_response_backward_compatibility(self):
        """Ensure ChatResponse remains backward compatible without diagnostic fields."""
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test summary",
            answer="Test answer",
        )
        
        # Diagnostic fields should have default values
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


class TestDiagnosticFieldValidation:
    """Test validation of diagnostic field values."""
    
    def test_intent_confidence_range(self):
        """Test intent confidence is within valid range."""
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test",
            answer="Test",
            intent_confidence=0.95,
        )
        assert 0.0 <= response.intent_confidence <= 1.0
    
    def test_risk_level_values(self):
        """Test valid risk level values."""
        valid_levels = ["none", "low", "medium", "high", "crisis"]
        for level in valid_levels:
            response = ChatResponse(
                status="success",
                route="normal",
                intent="psychoeducation",
                safety_mode="normal",
                summary="Test",
                answer="Test",
                risk_level=level,
            )
            assert response.risk_level == level
    
    def test_response_mode_values(self):
        """Test valid response mode values."""
        valid_modes = [
            "support", "education", "coping", "symptom_exploration",
            "clarify", "crisis", "off_scope", "repair"
        ]
        for mode in valid_modes:
            response = ChatResponse(
                status="success",
                route="normal",
                intent="psychoeducation",
                safety_mode="normal",
                summary="Test",
                answer="Test",
                response_mode=mode,
            )
            assert response.response_mode == mode
    
    def test_secondary_intents_list(self):
        """Test secondary intents as a list."""
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test",
            answer="Test",
            secondary_intents=["emotional_support", "coping_strategy", "repair"],
        )
        assert isinstance(response.secondary_intents, list)
        assert len(response.secondary_intents) == 3


class TestRetrievalDiagnosticFields:
    """Test retrieval diagnostic fields in ChatResponse."""
    
    def test_retrieval_confidence_with_sources(self):
        """Test retrieval confidence when sources are present."""
        sources = [
            SourceReference(
                title="Test Source",
                source="test.pdf",
                topic="anxiety",
                score=0.92,
                excerpt="Test excerpt"
            )
        ]
        
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test",
            answer="Test",
            sources=sources,
            retrieval_confidence=0.92,
        )
        
        assert response.retrieval_confidence == 0.92
        assert len(response.sources) == 1
    
    def test_empty_retrieval_diagnostics(self):
        """Test retrieval diagnostics when no retrieval occurred."""
        response = ChatResponse(
            status="success",
            route="emotional_support",
            intent="emotional_support",
            safety_mode="normal",
            summary="Test",
            answer="Test",
            retrieval_diagnostics=[],
            retrieval_confidence=0.0,
        )
        
        assert response.retrieval_diagnostics == []
        assert response.retrieval_confidence == 0.0


class TestCriticWarningsField:
    """Test critic warnings diagnostic field."""
    
    def test_empty_critic_warnings(self):
        """Test empty critic warnings list."""
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test",
            answer="Test",
            critic_warnings=[],
        )
        assert response.critic_warnings == []
    
    def test_critic_warnings_with_values(self):
        """Test critic warnings with actual warning values."""
        warnings = ["diagnosis_detected", "over_reassurance", "multiple_questions"]
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test",
            answer="Test",
            critic_warnings=warnings,
        )
        assert len(response.critic_warnings) == 3
        assert "diagnosis_detected" in response.critic_warnings


class TestBooleanDiagnosticFields:
    """Test boolean diagnostic fields."""
    
    @pytest.mark.parametrize("fallback,boundary,escalation", [
        (False, False, False),
        (True, False, False),
        (False, True, False),
        (False, False, True),
        (True, True, True),
    ])
    def test_boolean_field_combinations(self, fallback, boundary, escalation):
        """Test various combinations of boolean diagnostic fields."""
        response = ChatResponse(
            status="success",
            route="normal",
            intent="psychoeducation",
            safety_mode="normal",
            summary="Test",
            answer="Test",
            fallback_used=fallback,
            boundary_applied=boundary,
            escalation_required=escalation,
        )
        
        assert response.fallback_used == fallback
        assert response.boundary_applied == boundary
        assert response.escalation_required == escalation
"""
New conversational chat routes (v3) - AI-first with natural RAG integration.

This replaces the rigid 14-step pipeline with a simpler, more natural flow:
1. Load context (conversation, user profile, mood, journal)
2. Retrieve knowledge (RAG augmentation)
3. Generate response (Ollama + system prompt)
4. Check for risk signals (independent risk detection)
5. Return response

No templates, no rigid modules, no response gating.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.core.database import get_db
from server.app.core.security import get_current_user
from server.app.models.schemas.chat import ChatRequest, ChatResponse, SourceReference
from server.app.models.sql.models import User
from server.app.services.conversational_assistant import (
    ConversationalAssistant,
    ConversationContext,
)
from server.app.services.rag_augmentation import RAGAugmentationService
from server.app.services.risk_detection import RiskDetectionService
from server.app.services.user_state import user_state_service
from server.app.services.escalation import EscalationService
from server.app.core.retrieval.corpus import KnowledgeBase
from server.app.core.retrieval.faiss_store import FaissIndexStore

router = APIRouter(prefix="/chat-v3", tags=["Conversational AI (v3)"])

# Singleton instances (initialized on first use)
_conversational_assistant: ConversationalAssistant | None = None
_rag_service: RAGAugmentationService | None = None
_risk_detector: RiskDetectionService | None = None


def get_conversational_assistant() -> ConversationalAssistant:
    """Get or initialize ConversationalAssistant."""
    global _conversational_assistant
    if _conversational_assistant is None:
        _conversational_assistant = ConversationalAssistant()
    return _conversational_assistant


def get_rag_service() -> RAGAugmentationService:
    """Get or initialize RAGAugmentationService."""
    global _rag_service
    if _rag_service is None:
        # Load knowledge base and retriever
        from server.app.core.config import FAISS_INDEX_PATH, FAISS_METADATA_PATH

        kb = KnowledgeBase.load()
        faiss_store = FaissIndexStore(FAISS_INDEX_PATH, FAISS_METADATA_PATH)
        _rag_service = RAGAugmentationService(kb, faiss_store)
    return _rag_service


def get_risk_detector() -> RiskDetectionService:
    """Get or initialize RiskDetectionService."""
    global _risk_detector
    if _risk_detector is None:
        _risk_detector = RiskDetectionService()
    return _risk_detector


def get_escalation_service() -> EscalationService:
    """Get or initialize EscalationService."""
    return EscalationService()


@router.post("/", response_model=ChatResponse)
async def chat_conversational(
    payload: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Conversational chat endpoint (v3) - AI-first with invisible RAG integration.

    Flow:
    1. Load conversation context
    2. Retrieve relevant knowledge
    3. Generate response via LLM
    4. Check for risk signals
    5. Return response + metadata
    """
    try:
        # Get service instances
        assistant = get_conversational_assistant()
        rag_service = get_rag_service()
        risk_detector = get_risk_detector()

        # ===== STEP 1: Build Conversation Context =====
        # Load conversation history, user state (profile, mood, journal)
        conversation_history = payload.history or []

        # Load full user state (profile, mood trends, journal insights)
        user_state = await user_state_service.load_full_state(db, current_user.id)

        # Store intake data for context formatting
        intake_data = payload.intake if payload.intake else None

        # ===== STEP 2: Retrieve Knowledge =====
        # Augment query with user state and context, retrieve relevant knowledge
        rag_result = rag_service.augment_and_retrieve(
            user_message=payload.message,
            user_state=user_state,  # Full user state for rich query augmentation
            conversation_context=" ".join([h.get("content", "") for h in conversation_history[-3:]]),
            topic=None,
        )

        # ===== STEP 3: Build Context for LLM =====
        context = ConversationContext(
            user_id=str(current_user.id),
            session_id=str(payload.session_id or "new"),
            current_message=payload.message,
            conversation_history=conversation_history,
            user_state=user_state,
            intake_data=intake_data,
            retrieved_knowledge=rag_result.formatted_knowledge,
        )

        # ===== STEP 4: Generate Response =====
        llm_response = assistant.generate_response(context=context, temperature=0.7)

        if not llm_response.llm_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM service is currently unavailable. Please try again shortly.",
            )

        response_text = llm_response.response_text

        # ===== STEP 5: Risk Detection (Post-generation) =====
        risk_assessment = risk_detector.assess_response(
            user_message=payload.message,
            ai_response=response_text,
        )

        # Check cumulative distress pattern
        cumulative_distress = risk_detector.track_cumulative_distress(
            conversation_history + [{"role": "user", "content": payload.message}]
        )

        escalation_required = risk_assessment.should_escalate or cumulative_distress.get("escalation_needed", False)

        # ===== STEP 6: Build Escalation Record =====
        escalation_service = get_escalation_service()
        escalation_record = None
        escalation_message = ""

        if escalation_required:
            # Create escalation record for logging
            escalation_record = escalation_service.create_escalation_record(
                user_id=current_user.id,
                session_id=str(payload.session_id or "new"),
                risk_level=risk_assessment.risk_level,
                risk_indicators=risk_assessment.risk_indicators,
                user_message=payload.message,
                reason=risk_assessment.escalation_reason,
            )

            # Build escalation message to append to response (doesn't block response)
            escalation_message = escalation_service.build_escalation_message(
                risk_assessment.risk_level,
                risk_assessment.escalation_reason,
            )

            # Append escalation message to response (but don't block it)
            if escalation_message:
                response_text = escalation_service.append_escalation_to_response(response_text, escalation_message)

            # TODO: Log escalation record to database and notify support team
            # await escalation_service.log_escalation(db, escalation_record)
            # if escalation_record.action == EscalationAction.NOTIFY_SUPPORT:
            #     await escalation_service.notify_support_team(escalation_record)

        # ===== STEP 7: Format Response =====
        # Convert source references
        source_references = []
        if rag_result.retrieved_chunks:
            for i, chunk in enumerate(rag_result.retrieved_chunks):
                source_references.append(
                    SourceReference(
                        title=chunk.chunk.topic if chunk.chunk else "Unknown",
                        source=chunk.chunk.source if chunk.chunk else "Unknown",
                        topic=chunk.chunk.topic if chunk.chunk else "General",
                        score=chunk.score,
                        excerpt=chunk.chunk.content[:200] if chunk.chunk else "",
                        rank=i + 1,
                        source_kind=chunk.chunk.source_kind if chunk.chunk else None,
                        language=chunk.chunk.language if chunk.chunk else None,
                        confidence=chunk.chunk.confidence if chunk.chunk else None,
                    )
                )

        # ===== STEP 8: Build Response Object =====
        chat_response = ChatResponse(
            session_id=payload.session_id,
            status="success",
            route="conversational_v3",
            intent="conversation",
            safety_mode=risk_assessment.risk_level.value,
            summary="Conversational response generated with full context awareness",
            answer=response_text,
            sources=source_references,
            context_used={
                "history": len(conversation_history) > 0,
                "profile": user_state is not None,
                "knowledge": rag_result.retrieval_success and rag_result.chunk_count > 0,
                "mood": user_state.recent_mood_score is not None if user_state else False,
            },
            # Diagnostic fields
            pipeline_mode="conversational_v3",
            response_mode="support",
            risk_level=risk_assessment.risk_level.value,
            retrieval_confidence=rag_result.top_score if rag_result.retrieval_success else 0.0,
            fallback_used=False,
            escalation_required=escalation_required,
            boundary_applied=False,
        )

        # ===== STEP 9: Background Tasks (persistence) =====
        # TODO: Add background memory update, conversation history save, audit logging
        # For now, responses are stored but full integration deferred to future phases

        # Background escalation logging (non-blocking)
        if escalation_record:
            background_tasks.add_task(
                escalation_service.log_escalation,
                db,
                escalation_record,
            )

        return chat_response

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in Conversational Chat v3: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your request.",
        )

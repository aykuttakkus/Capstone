from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

from server.app.core.database import get_db
from server.app.core.security import get_current_user
from server.app.models.schemas.chat import ChatRequest, ChatResponse
from server.app.models.schemas.conversation import ConversationRead
from server.app.models.sql.models import User, Conversation
from server.app.services.assistant import get_service
from server.app.core.agents.safety_guardian import SafetyGuardian
from server.app.services.flows.intake_chat import intake_chat_engine
from server.app.services.profile import profile_service
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
from server.app.models.schemas.chat import SourceReference
from server.app.services.session_store import ensure_session, append_session_turn, build_session_title

router = APIRouter(prefix="/chat", tags=["Therapeutic Interface"])

# Singleton instances for v3 services
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
@limiter.limit("60/minute")
async def chat(
    request: Request,
    payload: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Primary Entry point for the Agentic RAG chat (v3 - Conversational AI).
    Uses AI-first conversational system with RAG augmentation.
    Requires a valid JWT Bearer token.
    """
    try:
        print(
            f"[CHAT DEBUG] /chat request user_id={current_user.id} session_id={payload.session_id} "
            f"history_len={len(payload.history or [])} message_len={len(payload.message or '')}"
        )

        # Get service instances
        assistant = get_conversational_assistant()
        rag_service = get_rag_service()
        risk_detector = get_risk_detector()

        # Build conversation context
        conversation_history = payload.history or []
        user_state = await user_state_service.load_full_state(db, current_user.id)
        intake_data = payload.intake if payload.intake else None

        # Persist or resolve the chat session before generating a response so
        # the sidebar can immediately show the conversation thread.
        session = await ensure_session(
            db,
            current_user.id,
            session_id=payload.session_id,
            title=build_session_title(payload.message),
            topic=None,
            intake=payload.intake,
            consent=payload.personalization,
        )
        await db.commit()

        # Retrieve knowledge
        rag_result = rag_service.augment_and_retrieve(
            user_message=payload.message,
            user_state=user_state,
            conversation_context=" ".join([h.get("content", "") for h in conversation_history[-3:]]),
            topic=None,
        )
        print(
            f"[CHAT DEBUG] RAG retrieval success={rag_result.retrieval_success} "
            f"chunk_count={rag_result.chunk_count} top_score={rag_result.top_score}"
        )

        # Build context for LLM
        context = ConversationContext(
            user_id=str(current_user.id),
            session_id=str(payload.session_id or "new"),
            current_message=payload.message,
            conversation_history=conversation_history,
            user_state=user_state,
            intake_data=intake_data,
            retrieved_knowledge=rag_result.formatted_knowledge,
        )

        # Generate response (LLM-down fallback handled inside generate_response — never raises 503)
        is_first = len(conversation_history) == 0
        llm_response = assistant.generate_response(context=context, temperature=0.7, is_first_message=is_first)

        response_text = llm_response.response_text
        print(
            f"[CHAT DEBUG] LLM response generated len={len(response_text or '')} "
            f"first_message={is_first}"
        )

        # Risk detection (post-generation)
        risk_assessment = risk_detector.assess_response(
            user_message=payload.message,
            ai_response=response_text,
        )
        print(
            f"[CHAT DEBUG] Risk assessment level={risk_assessment.risk_level} "
            f"should_escalate={risk_assessment.should_escalate} reason={risk_assessment.escalation_reason}"
        )

        # Check cumulative distress pattern
        cumulative_distress = risk_detector.track_cumulative_distress(
            conversation_history + [{"role": "user", "content": payload.message}]
        )

        escalation_required = risk_assessment.should_escalate or cumulative_distress.get("escalation_needed", False)

        # Build escalation record
        escalation_service = get_escalation_service()
        escalation_record = None
        escalation_message = ""

        if escalation_required:
            escalation_record = escalation_service.create_escalation_record(
                user_id=current_user.id,
                session_id=str(payload.session_id or "new"),
                risk_level=risk_assessment.risk_level,
                risk_indicators=risk_assessment.risk_indicators,
                user_message=payload.message,
                reason=risk_assessment.escalation_reason,
            )

            escalation_message = escalation_service.build_escalation_message(
                risk_assessment.risk_level,
                risk_assessment.escalation_reason,
            )

            if escalation_message:
                response_text = escalation_service.append_escalation_to_response(response_text, escalation_message)

            if escalation_record:
                background_tasks.add_task(
                    escalation_service.log_escalation,
                    db,
                    escalation_record,
                )

        # Format source references
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

        # Build response
        chat_response = ChatResponse(
            session_id=session.id,
            status="success",
            route="conversational_v3",
            intent="conversation",
            safety_mode=risk_assessment.risk_level.value,
            summary="Conversational response generated with full context awareness",
            answer=response_text,
            disclaimer=llm_response.disclaimer,
            sources=source_references,
            context_used={
                "history": len(conversation_history) > 0,
                "profile": user_state is not None,
                "knowledge": rag_result.retrieval_success and rag_result.chunk_count > 0,
                "mood": user_state.recent_mood_score is not None if user_state else False,
            },
            pipeline_mode="conversational_v3",
            response_mode="support",
            risk_level=risk_assessment.risk_level.value,
            retrieval_confidence=rag_result.top_score if rag_result.retrieval_success else 0.0,
            fallback_used=False,
            escalation_required=escalation_required,
            boundary_applied=False,
        )

        # Persist conversation turn to make it appear in the left sidebar history.
        await append_session_turn(
            db,
            session,
            current_user.id,
            query=payload.message,
            response=response_text,
            intent=chat_response.intent,
            route=chat_response.route,
            safety_mode=chat_response.safety_mode,
            sources=[sr.model_dump() for sr in source_references],
            intake=payload.intake,
        )

        await db.commit()

        print(
            f"[CHAT DEBUG] Response ready session_id={chat_response.session_id} "
            f"escalation_required={escalation_required} sources={len(source_references)}"
        )

        return chat_response

    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHAT DEBUG] CRITICAL ERROR in Chat Flow: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your support request."
        )


# ------------------------------------------------------------------
# Conversational Intake Step
# ------------------------------------------------------------------

class IntakeStepRequest(BaseModel):
    phase: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    accumulated: dict[str, str] = Field(default_factory=dict)


class IntakeStepResponse(BaseModel):
    current_phase: str
    next_phase: str | None = None
    next_question: str | None = None
    reflection: str | None = None
    extracted: dict[str, str] = Field(default_factory=dict)
    complete: bool = False
    safety_alert: str | None = None


@router.post("/intake-step/", response_model=IntakeStepResponse)
async def intake_step(
    payload: IntakeStepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IntakeStepResponse:
    """
    Process one step of the conversational clinical intake with safety checks.
    """
    # 1. Safety Check First
    safety_guardian = SafetyGuardian()
    safety_analysis = safety_guardian.analyze(payload.answer)

    if safety_analysis.mode != "normal":
        return IntakeStepResponse(
            current_phase=payload.phase,
            safety_alert=safety_analysis.suggested_message,
            complete=True,  # Abort intake to handle crisis
            extracted=payload.accumulated
        )

    # 2. Process Intake Step
    result = await intake_chat_engine.process_step(
        phase=payload.phase,
        answer=payload.answer,
        accumulated=payload.accumulated,
    )

    # Progressively update the user profile with extracted signals
    if result.extracted:
        profile = await profile_service.refresh_from_context(
            db,
            current_user.id,
            intake_chat_signals=result.extracted,
        )
        if result.complete:
            profile.intake_completed = True
        await db.commit()

    return IntakeStepResponse(
        current_phase=result.current_phase,
        next_phase=result.next_phase,
        next_question=result.next_question,
        reflection=result.reflection,
        extracted=result.extracted,
        complete=result.complete,
    )


@router.get("/history", response_model=list[ConversationRead])
async def history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationRead]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .limit(10)
    )
    return list(result.scalars().all())

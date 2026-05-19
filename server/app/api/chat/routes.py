from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from server.app.core.database import get_db
from server.app.core.security import get_current_user
from server.app.models.schemas.chat import ChatRequest, ChatResponse
from server.app.models.schemas.conversation import ConversationRead
from server.app.models.sql.models import User, Conversation
from server.app.services.assistant import get_service
from server.app.core.agents.safety_guardian import SafetyGuardian
from server.app.services.flows.intake_chat import intake_chat_engine
from server.app.services.profile import profile_service

router = APIRouter(prefix="/chat", tags=["Therapeutic Interface"])

@router.post("/", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Primary Entry point for the Agentic RAG chat.
    Requires a valid JWT Bearer token.
    """
    try:
        service = get_service()
        response = await service.handle_message(
            message=payload.message,
            user=current_user,
            db=db,
            background_tasks=background_tasks,
            session_id=payload.session_id,
            new_session=payload.new_session,
            intake=payload.intake,
            screening=payload.screening,
            history=payload.history,
            personalization=payload.personalization,
        )
        return response
    except Exception as e:
        print(f"CRITICAL ERROR in Chat Flow: {str(e)}")
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

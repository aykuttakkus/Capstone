from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.core.database import get_db
from server.app.core.security import get_current_user
from server.app.models.schemas.screening import ScreeningRequest, ScreeningResponse
from server.app.models.sql.models import User
from server.app.services.clinical_state import mark_screening_complete
from server.app.services.flows.screening import score_gad7, score_phq9

router = APIRouter(prefix="/screen", tags=["Screening"])


@router.post("/", response_model=ScreeningResponse)
async def screen(
    payload: ScreeningRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScreeningResponse:
    current_user.last_screening_date = datetime.now(timezone.utc)

    if payload.test_type == "phq9":
        result = score_phq9(payload.answers)
        current_user.last_phq9_score = result.score
    elif payload.test_type == "gad7":
        if (current_user.last_phq9_score is None):
            current_user.last_phq9_score = 0
        result = score_gad7(payload.answers)
        await mark_screening_complete(
            db,
            current_user.id,
            phq9_score=current_user.last_phq9_score or 0,
            gad7_score=result.score,
            completed_at=current_user.last_screening_date,
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported screening type.")

    await db.commit()

    return ScreeningResponse(
        scale_name=result.scale_name,
        score=result.score,
        severity=result.severity,
        crisis_flag=result.crisis_flag,
    )

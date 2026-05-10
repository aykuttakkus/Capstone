from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from server.app.core.database import get_db
from server.app.core.security import get_password_hash, verify_password, create_access_token
from server.app.models.sql.models import User
from server.app.models.schemas.auth import UserCreate, UserLogin, Token, UserRead, ClinicalStateRead
from server.app.core.security import get_current_user
from server.app.services.clinical_state import get_or_create_clinical_state, next_required_step
from server.app.models.schemas.profile import UserProfileRead
from server.app.services.profile import profile_service

router = APIRouter(prefix="/auth", tags=["Identity & Security"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    normalized_email = user_in.email.lower()
    result = await db.execute(select(User).where(User.email == normalized_email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    new_user = User(
        email=normalized_email,
        hashed_password=get_password_hash(user_in.password)
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    state = await get_or_create_clinical_state(db, new_user.id)
    profile = await profile_service.get_or_create(db, new_user.id)
    await db.commit()

    return _build_user_read(new_user, state, profile)
@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
async def read_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    state = await get_or_create_clinical_state(db, current_user.id)
    profile = await profile_service.get_or_create(db, current_user.id)
    await db.commit()
    return _build_user_read(current_user, state, profile)


def _build_user_read(user: User, state, profile=None) -> UserRead:
    state_payload = ClinicalStateRead(
        onboarding_completed=bool(state.onboarding_completed),
        screening_completed=bool(state.screening_completed),
        last_phq9_score=state.last_phq9_score,
        last_gad7_score=state.last_gad7_score,
        last_screening_date=state.last_screening_date,
        screening_completed_at=state.screening_completed_at,
        onboarding_completed_at=state.onboarding_completed_at,
        next_required_step=next_required_step(state),
    )

    return UserRead(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        last_phq9_score=state.last_phq9_score,
        last_gad7_score=state.last_gad7_score,
        onboarding_completed=bool(state.onboarding_completed),
        screening_completed=bool(state.screening_completed),
        next_required_step=next_required_step(state),
        clinical_state=state_payload,
        profile=UserProfileRead.model_validate(profile) if profile is not None else None,
    )

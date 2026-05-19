"""
Shared test fixtures for Calma v3 test suite.

Provides:
- Async DB session (in-memory SQLite)
- Mock LLM client (no real Ollama calls)
- Sample user, profile, mood state
- Sample knowledge corpus
- FastAPI test client with auth
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from server.app.core.database import Base
from server.app.main import app


# ── Database ──────────────────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ── Mock LLM ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_llm_response():
    mock = MagicMock()
    mock.text = (
        "I hear you, and it sounds like you're going through a really tough time. "
        "Feeling this way is more common than you might think, and reaching out is a "
        "meaningful step. Can you tell me more about what's been happening?"
    )
    mock.available = True
    return mock


@pytest.fixture
def mock_llm_unavailable():
    mock = MagicMock()
    mock.text = ""
    mock.available = False
    return mock


# ── User State ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_user_state():
    from server.app.services.user_state import UserState
    return UserState(
        user_id=1,
        preferred_name="Alex",
        primary_concerns="anxiety and social isolation",
        goals_for_support="feel less alone and manage stress",
        communication_style="gentle",
        response_length_preference="medium",
        coping_strategies_helpful="breathing exercises",
        coping_strategies_unhelpful="avoidance",
        main_triggers="crowded places, deadlines",
        support_system="close friend",
        life_narrative="university student, high-pressure environment",
        therapy_status="never",
        mood_summary="Mood has been consistently low for 2 weeks",
        recent_mood_score=3.5,
        recent_anxiety_score=7.2,
        mood_pattern_tags=["low_energy", "high_anxiety"],
        journal_summary="Recurring themes: academic pressure, loneliness",
        journal_themes=["loneliness", "academic_stress"],
        personalization_consent=True,
        use_mood_context=True,
        use_journal_context=True,
        use_memory_context=True,
    )


# ── Knowledge Corpus ──────────────────────────────────────────────────────────

@pytest.fixture
def sample_chunks():
    from server.app.core.retrieval.corpus import KnowledgeChunk
    return [
        KnowledgeChunk(
            id="chunk_001",
            title="Understanding Loneliness",
            topic="loneliness",
            source="social_isolation_research.pdf",
            content=(
                "Loneliness is the subjective experience of social disconnection. "
                "Research shows that perceived social support predicts wellbeing. "
                "Interventions focusing on quality of connection are most effective."
            ),
            keywords=["loneliness", "social isolation", "connection", "wellbeing"],
            evidence_level="peer_reviewed",
            source_kind="user_corpus",
            confidence=0.92,
            language="en",
            allowed_use=["psychoeducation", "emotional_support"],
        ),
        KnowledgeChunk(
            id="chunk_002",
            title="CBT for Anxiety",
            topic="anxiety",
            source="cbt_anxiety_guide.pdf",
            content=(
                "CBT is the gold-standard treatment for anxiety. Core techniques include "
                "cognitive restructuring, behavioral experiments, and gradual exposure. "
                "Brief CBT interventions show significant symptom reduction."
            ),
            keywords=["CBT", "anxiety", "cognitive", "behavioral", "exposure"],
            evidence_level="clinical_guideline",
            source_kind="user_corpus",
            confidence=0.97,
            language="en",
            allowed_use=["psychoeducation", "coping_strategy"],
        ),
        KnowledgeChunk(
            id="chunk_003",
            title="Sleep and Mental Health",
            topic="sleep",
            source="sleep_mental_health.pdf",
            content=(
                "Sleep disturbances are both a symptom and a cause of mental health difficulties. "
                "Sleep hygiene strategies include consistent schedules, limiting screen time, "
                "and relaxation techniques before bed. Improving sleep quality reduces anxiety."
            ),
            keywords=["sleep", "insomnia", "hygiene", "rest", "fatigue"],
            evidence_level="peer_reviewed",
            source_kind="user_corpus",
            confidence=0.88,
            language="en",
            allowed_use=["psychoeducation", "coping_strategy", "symptom_exploration"],
        ),
    ]


# ── API Client ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def auth_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        await client.post("/api/auth/register", json={
            "email": "testuser@calma.ai",
            "password": "SecureTestPassword123!",
        })
        login_resp = await client.post("/api/auth/login", json={
            "email": "testuser@calma.ai",
            "password": "SecureTestPassword123!",
        })
        token = login_resp.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield client

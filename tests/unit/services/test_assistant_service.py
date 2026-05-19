from __future__ import annotations

from dataclasses import dataclass

import pytest
from sqlalchemy import select

from server.app.core.generation.generator import AnswerGenerator, SentimentProfile
from server.app.core.retrieval.evidence_gate import EvidenceGate
import server.app.services.assistant as assistant_module
from server.app.core.retrieval.reranker import EvidenceReranker
from server.app.models.sql.models import Conversation, JournalEntry, Memory, MemorySegment, MoodEntry, UserProfile
from server.app.services.assistant import AssistantService
from server.app.services.session_store import ensure_session
from tests.factories.retrieval import build_scored_chunk


pytestmark = [pytest.mark.unit, pytest.mark.anyio]


@dataclass
class FakePlan:
    route: str
    topic: str
    intent: str
    safety_mode: str
    risk_level: int
    use_rag: bool = True
    sentiment_label: str = "neutral"
    sentiment_urgency: int = 1
    clinical_plan: str = ""
    immediate_response: str | None = None


class FakeOrchestrator:
    def __init__(self, plan: FakePlan) -> None:
        self._plan = plan

    def plan(self, message: str, intake: dict[str, str] | None = None) -> FakePlan:
        return self._plan


class FakeRetriever:
    def __init__(self, retrievals):
        self._retrievals = retrievals

    def retrieve(self, message: str, topic: str | None = None, k: int = 5):
        return list(self._retrievals)


class FakeGrader:
    def __init__(self, flags):
        self._flags = flags

    def grade_batch(self, message: str, retrievals):
        return list(self._flags)


class FakeSentimentAgent:
    def analyze(self, text: str) -> SentimentProfile:
        return SentimentProfile(label="concerned", urgency=2, empathy_required=True, rationale="test")


class FakeMemoryAgent:
    def summarize_interaction(self, user_msg: str, ai_msg: str, current_memory: str = "") -> str:
        return f"{current_memory}\nUpdated memory".strip()


class FakeSupervisor:
    def review(self, answer: str) -> dict:
        return {"is_safe": True, "violations": []}


class FakeNuggetizer:
    def __init__(self) -> None:
        self.last_query: str | None = None
        self.last_retrieval_ids: list[str] = []

    async def nuggetize(self, query: str, retrievals):
        self.last_query = query
        self.last_retrieval_ids = [item.chunk.id for item in retrievals]
        return ""


class FakeAuditLogger:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def log_event(self, user_id, query, route, sentiment, safety_mode, processing_time) -> None:
        self.events.append({"route": route, "safety_mode": safety_mode})


class FakeReranker:
    def rerank(self, query: str, retrievals, topic: str | None = None):
        return list(reversed(retrievals[:2]))


def build_service(*, plan: FakePlan, retrievals, grader_flags, llm_backend):
    service = AssistantService.__new__(AssistantService)
    service.knowledge_base = None
    service.embedder = None
    service.faiss_store = None
    service.retriever = FakeRetriever(retrievals)
    service.evidence_gate = EvidenceGate(min_score=0.22, min_chunks=1)
    service.generator = AnswerGenerator(llm_client=llm_backend)
    service.orchestrator = FakeOrchestrator(plan)
    service.grader = FakeGrader(grader_flags)
    service.sentiment_agent = FakeSentimentAgent()
    service.memory_agent = FakeMemoryAgent()
    service.supervisor = FakeSupervisor()
    service.nuggetizer = FakeNuggetizer()
    service.reranker = FakeReranker()
    service.audit_logger = FakeAuditLogger()
    return service


def test_assistant_service_init_does_not_rebuild_index(monkeypatch, tmp_path) -> None:
    class DummyEmbeddingBackend:
        def __init__(self, *args, **kwargs):
            self.dimension = 32

    def fail_build(*args, **kwargs):
        raise AssertionError("AssistantService should not rebuild the index at init time")

    monkeypatch.setattr(assistant_module, "EmbeddingBackend", DummyEmbeddingBackend)
    monkeypatch.setattr(assistant_module.FaissIndexStore, "build", fail_build)
    monkeypatch.setattr(assistant_module, "FAISS_INDEX_PATH", tmp_path / "faiss.index")
    monkeypatch.setattr(assistant_module, "FAISS_METADATA_PATH", tmp_path / "faiss_metadata.json")

    service = AssistantService()

    assert service.faiss_store is not None
    assert service.retriever is not None


async def test_assistant_service_short_circuits_on_safety_mode(
    db_session_factory,
    authenticated_user,
    offline_llm_backend,
) -> None:
    service = build_service(
        plan=FakePlan(
            route="diagnosis_refusal",
            topic="low_mood",
            intent="psychoeducation",
            safety_mode="diagnosis_refusal",
            risk_level=0,
            immediate_response="I cannot diagnose conditions.",
        ),
        retrievals=[],
        grader_flags=[],
        llm_backend=offline_llm_backend,
    )

    async with db_session_factory() as db:
        response = await service.handle_message(
            message="Do I have depression?",
            user=authenticated_user,
            db=db,
            intake={},
            screening={},
            history=[],
        )

        conversation_count = len(list((await db.execute(select(Conversation))).scalars()))
        assert response.status == "refusal"
        assert response.route == "diagnosis_refusal"
        assert conversation_count == 0


async def test_assistant_service_returns_risk_clarification_when_safety_triggers(
    db_session_factory,
    authenticated_user,
    offline_llm_backend,
) -> None:
    service = build_service(
        plan=FakePlan(
            route="risk_clarification",
            topic="stress_anxiety",
            intent="psychoeducation",
            safety_mode="risk_clarification",
            risk_level=1,
            immediate_response="I want to check in before we continue.",
        ),
        retrievals=[],
        grader_flags=[],
        llm_backend=offline_llm_backend,
    )

    async with db_session_factory() as db:
        response = await service.handle_message(
            message="Everything feels pointless lately.",
            user=authenticated_user,
            db=db,
            intake={},
            screening={},
            history=[],
        )

        assert response.status == "clarification"
        assert response.route == "risk_clarification"
        assert "safe" in response.answer.lower()


async def test_assistant_service_returns_evidence_gate_when_retrieval_is_weak(
    db_session_factory,
    authenticated_user,
    offline_llm_backend,
) -> None:
    service = build_service(
        plan=FakePlan(
            route="topic:stress_anxiety",
            topic="stress_anxiety",
            intent="psychoeducation",
            safety_mode="normal",
            risk_level=0,
        ),
        retrievals=[build_scored_chunk("weak-001", topic="stress_anxiety", score=0.1)],
        grader_flags=[True],
        llm_backend=offline_llm_backend,
    )

    async with db_session_factory() as db:
        response = await service.handle_message(
            message="Tell me about stress",
            user=authenticated_user,
            db=db,
            intake={},
            screening={},
            history=[],
        )

        memory_rows = list((await db.execute(select(Memory))).scalars())
        assert response.status == "insufficient_evidence"
        assert response.route == "evidence_gate"
        assert memory_rows == []


async def test_assistant_service_persists_grounded_response_and_memory(
    db_session_factory,
    authenticated_user,
    mock_llm_backend,
) -> None:
    service = build_service(
        plan=FakePlan(
            route="topic:burnout_sleep",
            topic="burnout_sleep",
            intent="psychoeducation",
            safety_mode="normal",
            risk_level=0,
        ),
        retrievals=[build_scored_chunk("sleep-001", topic="burnout_sleep", score=0.95)],
        grader_flags=[True],
        llm_backend=mock_llm_backend,
    )
    service.reranker = EvidenceReranker(top_k=2, max_chars=1000)

    async with db_session_factory() as db:
        response = await service.handle_message(
            message="Tell me about stress and sleep",
            user=authenticated_user,
            db=db,
            intake={"main_issue": "stress", "help_type": "Sources"},
            screening={"scale_name": "PHQ-9", "severity": "mild"},
            history=[],
            personalization={
                "preferred_name": "Aykut",
                "use_mood_context": True,
                "use_journal_context": True,
            },
        )

        db.add(MoodEntry(user_id=authenticated_user.id, mood_score=3, anxiety_score=8, sleep_quality=4, notes="rough week"))
        db.add(JournalEntry(user_id=authenticated_user.id, title="Exam note", content="Exam stress and anxiety", sentiment_label="concerned", topics_json='["stress_anxiety"]', consent_for_chat=True, risk_flag=False))
        await db.commit()
        conversations = list((await db.execute(select(Conversation))).scalars())
        memories = list((await db.execute(select(Memory))).scalars())
        profiles = list((await db.execute(select(UserProfile))).scalars())
        segments = list((await db.execute(select(MemorySegment))).scalars())
        assert response.status == "grounded"
        assert response.sources
        assert len(conversations) == 1
        assert len(memories) == 1
        assert len(profiles) == 1
        assert len(segments) >= 1
        assert response.personalization_applied is True
        assert "profile" in response.personalization_signals
        assert service.audit_logger.events


async def test_assistant_service_reranks_retrievals_before_nuggetization(
    db_session_factory,
    authenticated_user,
    mock_llm_backend,
) -> None:
    service = build_service(
        plan=FakePlan(
            route="topic:stress_anxiety",
            topic="stress_anxiety",
            intent="psychoeducation",
            safety_mode="normal",
            risk_level=0,
        ),
        retrievals=[
            build_scored_chunk("third", topic="stress_anxiety", score=0.7),
            build_scored_chunk("first", topic="stress_anxiety", score=0.9),
            build_scored_chunk("second", topic="stress_anxiety", score=0.8),
        ],
        grader_flags=[True],
        llm_backend=mock_llm_backend,
    )
    service.reranker = EvidenceReranker(top_k=2, max_chars=1000)

    async with db_session_factory() as db:
        response = await service.handle_message(
            message="Tell me about anxiety",
            user=authenticated_user,
            db=db,
            intake={},
            screening={},
            history=[],
        )

        assert response.status == "grounded"

        assert service.nuggetizer.last_retrieval_ids == ["first", "second"]


async def test_assistant_service_reuses_latest_active_session_when_history_exists(
    db_session_factory,
    authenticated_user,
    mock_llm_backend,
) -> None:
    service = build_service(
        plan=FakePlan(
            route="topic:stress_anxiety",
            topic="stress_anxiety",
            intent="psychoeducation",
            safety_mode="normal",
            risk_level=0,
        ),
        retrievals=[build_scored_chunk("stress-001", topic="stress_anxiety", score=0.9)],
        grader_flags=[True],
        llm_backend=mock_llm_backend,
    )

    async with db_session_factory() as db:
        existing = await ensure_session(db, authenticated_user.id, title="Existing", topic="stress_anxiety")
        await db.commit()

        response = await service.handle_message(
            message="Tell me about stress",
            user=authenticated_user,
            db=db,
            intake={},
            screening={},
            history=[{"role": "user", "content": "Earlier context"}],
        )

        assert response.session_id == existing.id

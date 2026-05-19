from __future__ import annotations

from dataclasses import dataclass

import pytest
from sqlalchemy import select

from server.app.core.generation.generator import AnswerGenerator, GeneratedPayload, SentimentProfile
from server.app.core.pipeline.orchestrator_v2 import PipelineResult
from server.app.core.pipeline.response_modes import ResponseMode
from server.app.core.retrieval.evidence_gate import EvidenceGate
import server.app.services.assistant as assistant_module
from server.app.core.retrieval.reranker import EvidenceReranker
from server.app.models.sql.models import Conversation, JournalEntry, Memory, MemorySegment, MoodEntry, SessionRiskState, UserProfile
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
        self.calls = []

    def retrieve(self, message: str, topic: str | None = None, k: int = 5, **kwargs):
        self.calls.append({"message": message, "topic": topic, "k": k, **kwargs})
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
    def summarize_interaction(
        self,
        user_msg: str,
        ai_msg: str,
        current_memory: str = "",
        mood_score: int | None = None,
    ) -> str:
        return f"{current_memory}\nUpdated memory".strip()


class FailingMemoryAgent:
    def summarize_interaction(
        self,
        user_msg: str,
        ai_msg: str,
        current_memory: str = "",
        mood_score: int | None = None,
    ) -> str:
        raise RuntimeError("memory unavailable")


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


class FakePipelineOrchestrator:
    def __init__(self, risk_level: str | None = None) -> None:
        self.calls = []
        self.risk_level = risk_level

    async def execute(self, context):
        self.calls.append(context)
        if self.risk_level:
            context.risk_state.update_risk_check(self.risk_level, "fake pipeline risk update")
        return PipelineResult(
            response="pipeline ok",
            mode=ResponseMode.PSYCHOEDUCATION,
            is_degraded=False,
            distress_signals=0,
            dependency_violations=0,
            quality_score=1.0,
            execution_time_ms=1.0,
            warnings=[],
        )


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


async def test_assistant_service_executes_pipeline_for_normal_chat(
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
        retrievals=[build_scored_chunk("stress-001", topic="stress_anxiety", score=0.95)],
        grader_flags=[True],
        llm_backend=mock_llm_backend,
    )
    fake_pipeline = FakePipelineOrchestrator()
    service.pipeline_orchestrator = fake_pipeline

    async with db_session_factory() as db:
        response = await service.handle_message(
            message="Tell me about stress",
            user=authenticated_user,
            db=db,
            intake={},
            screening={},
            history=[{"role": "user", "content": "I was anxious yesterday"}],
        )

        assert response.status == "grounded"
        assert len(fake_pipeline.calls) == 1
        context = fake_pipeline.calls[0]
        assert context.user_message == "Tell me about stress"
        assert context.intent == "psychoeducation"
        assert context.topic == "stress_anxiety"
        assert context.conversation_history == ["user: I was anxious yesterday"]
        assert context.profile_context["context_package"]["new_context_signals"] == []
        assert context.profile_context["context_package"]["response_policy"]["max_questions"] == 1
        assert service.retriever.calls[0]["intent"] == "psychoeducation"
        assert service.retriever.calls[0]["allowed_use"] == ["psychoeducation"]
        assert service.retriever.calls[0]["min_evidence_level"] == "educational"
        assert service.retriever.calls[0]["clinical_scope"] == "psychoeducation_only"


async def test_assistant_service_persists_pipeline_risk_state(
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
        retrievals=[build_scored_chunk("stress-001", topic="stress_anxiety", score=0.95)],
        grader_flags=[True],
        llm_backend=mock_llm_backend,
    )
    service.pipeline_orchestrator = FakePipelineOrchestrator(risk_level="medium")

    async with db_session_factory() as db:
        response = await service.handle_message(
            message="Tell me about stress",
            user=authenticated_user,
            db=db,
            intake={},
            screening={},
            history=[],
        )

        rows = list((await db.execute(select(SessionRiskState))).scalars())
        assert response.status == "grounded"
        assert len(rows) == 1
        assert rows[0].current_risk_level == "medium"
        assert rows[0].safety_analysis_reasoning == "fake pipeline risk update"


async def test_assistant_service_passes_full_response_plan_to_generator(
    db_session_factory,
    authenticated_user,
    mock_llm_backend,
) -> None:
    service = build_service(
        plan=FakePlan(
            route="topic:stress_anxiety",
            topic="stress_anxiety",
            intent="coping_strategy",
            safety_mode="normal",
            risk_level=0,
        ),
        retrievals=[
            build_scored_chunk(
                "coping-001",
                topic="stress_anxiety",
                score=0.95,
                allowed_use=["coping_strategy"],
                evidence_level="clinical_self_help",
            )
        ],
        grader_flags=[True],
        llm_backend=mock_llm_backend,
    )
    captured = {}

    def fake_build_grounded(**kwargs):
        captured["planner"] = kwargs["planner"]
        return GeneratedPayload(
            status="grounded",
            answer="Grounded coping answer.",
            summary="coping_strategy",
            follow_up=[],
            route="topic:stress_anxiety",
        )

    service.generator.build_grounded = fake_build_grounded

    async with db_session_factory() as db:
        response = await service.handle_message(
            message="What can I do to manage stress?",
            user=authenticated_user,
            db=db,
            intake={},
            screening={},
            history=[],
        )

        planner = captured["planner"]
        assert response.status == "grounded"
        assert planner.primary_intent == "coping_strategy"
        assert planner.response_mode == "coping"
        assert planner.needs_rag is True
        assert planner.source_required is True
        assert planner.max_questions == 1
        assert planner.diagnosis_allowed is False
        assert planner.medication_advice_allowed is False


async def test_assistant_service_rewrites_unsafe_generated_diagnosis(
    db_session_factory,
    authenticated_user,
    mock_llm_backend,
) -> None:
    service = build_service(
        plan=FakePlan(
            route="topic:low_mood",
            topic="low_mood",
            intent="psychoeducation",
            safety_mode="normal",
            risk_level=0,
        ),
        retrievals=[build_scored_chunk("mood-001", topic="low_mood", score=0.95)],
        grader_flags=[True],
        llm_backend=mock_llm_backend,
    )

    def fake_build_grounded(**kwargs):
        return GeneratedPayload(
            status="grounded",
            answer="You have depression.",
            summary="psychoeducation",
            follow_up=[],
            route="topic:low_mood",
        )

    service.generator.build_grounded = fake_build_grounded

    async with db_session_factory() as db:
        response = await service.handle_message(
            message="Why do I feel low?",
            user=authenticated_user,
            db=db,
            intake={},
            screening={},
            history=[],
        )

        assert response.status == "grounded"
        assert "you have depression" not in response.answer.lower()
        assert "not as a diagnosis" in response.answer.lower()


async def test_assistant_service_rewrites_dependency_language(
    db_session_factory,
    authenticated_user,
    mock_llm_backend,
) -> None:
    service = build_service(
        plan=FakePlan(
            route="topic:stress_anxiety",
            topic="stress_anxiety",
            intent="emotional_support",
            safety_mode="normal",
            risk_level=0,
            use_rag=False,
        ),
        retrievals=[],
        grader_flags=[],
        llm_backend=mock_llm_backend,
    )

    def fake_build_grounded(**kwargs):
        return GeneratedPayload(
            status="grounded",
            answer="I will always be here for you and only I understand you.",
            summary="emotional_support",
            follow_up=[],
            route="topic:stress_anxiety",
        )

    service.generator.build_grounded = fake_build_grounded

    async with db_session_factory() as db:
        response = await service.handle_message(
            message="I feel alone",
            user=authenticated_user,
            db=db,
            intake={},
            screening={},
            history=[],
        )

        lowered = response.answer.lower()
        assert "i will always be here" not in lowered
        assert "only i understand" not in lowered
        assert "general psychological information" in lowered


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


async def test_assistant_service_memory_failure_does_not_block_chat_persistence(
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
        retrievals=[build_scored_chunk("stress-001", topic="stress_anxiety", score=0.95)],
        grader_flags=[True],
        llm_backend=mock_llm_backend,
    )
    service.memory_agent = FailingMemoryAgent()

    async with db_session_factory() as db:
        response = await service.handle_message(
            message="Tell me about stress",
            user=authenticated_user,
            db=db,
            intake={},
            screening={},
            history=[],
        )

        conversations = list((await db.execute(select(Conversation))).scalars())
        memories = list((await db.execute(select(Memory))).scalars())

        assert response.status == "grounded"
        assert len(conversations) == 1
        assert memories == []


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

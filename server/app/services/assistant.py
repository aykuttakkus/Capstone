from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from server.app.utils.privacy import encrypt_clinical_data, decrypt_clinical_data


@dataclass(slots=True)
class SentimentProfile:
    label: str
    urgency: int
    empathy_required: bool
    rationale: str

from server.app.core.config import ENABLE_RERANKER, FAISS_INDEX_PATH, FAISS_METADATA_PATH, RERANK_MAX_CHARS, RERANK_TOP_K, TOP_K
from server.app.models.schemas.chat import ChatResponse, SourceReference
from server.app.services.session_store import append_session_turn, build_session_title, ensure_session, get_latest_session
from server.app.services.retrieval_debug import build_retrieval_diagnostics, build_source_reference
from server.app.core.retrieval.corpus import KnowledgeBase
from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.evidence_gate import EvidenceGate
from server.app.core.retrieval.faiss_store import FaissIndexStore
from server.app.core.generation.generator import AnswerGenerator
from server.app.core.generation.llm import OllamaClient
from server.app.core.retrieval.hybrid_retriever import HybridRetriever
from server.app.core.retrieval.reranker import EvidenceReranker
from server.app.core.retrieval.retriever import ScoredChunk
from server.app.core.agents.orchestrator import Orchestrator
from server.app.core.agents.response_planner import ResponsePlan
from server.app.core.agents.safety_guardian import SafetyAnalysis
from server.app.core.agents.memory_agent import MemoryAgent
from server.app.utils.audit_logger import ClinicalAuditLogger
from server.app.models.sql.models import User, Memory, Conversation, ChatSession
from server.app.services.journal import journal_service
from server.app.services.memory_store import memory_extractor, memory_store
from server.app.services.mood import mood_service
from server.app.services.personalization import query_builder
from server.app.services.profile import profile_service
from server.app.services.session import prune_memory_text
from server.app.core.retrieval.nuggetizer import nuggetizer


class AssistantService:
    def __init__(self) -> None:
        # Load knowledge base (processed → raw → default fallback)
        self.knowledge_base = KnowledgeBase.load()

        # Embedding backend (sentence-transformers or hash fallback)
        self.embedder = EmbeddingBackend()

        # FAISS index — loaded at runtime; built offline by the ingestion worker
        self.faiss_store = FaissIndexStore(FAISS_INDEX_PATH, FAISS_METADATA_PATH)

        # Components
        self.retriever = HybridRetriever(self.knowledge_base, self.faiss_store, self.embedder)
        self.reranker = EvidenceReranker(top_k=RERANK_TOP_K, max_chars=RERANK_MAX_CHARS) if ENABLE_RERANKER else None
        self.evidence_gate = EvidenceGate()
        self.generator = AnswerGenerator(llm_client=OllamaClient())
        self.orchestrator = Orchestrator()
        self.memory_agent = MemoryAgent()
        self.audit_logger = ClinicalAuditLogger()
        self.nuggetizer = nuggetizer

    # ------------------------------------------------------------------
    # Persistence Helpers
    # ------------------------------------------------------------------

    async def _get_user_memory(self, db: AsyncSession, user_id: int) -> str:
        result = await db.execute(select(Memory).where(Memory.user_id == user_id))
        memory = result.scalar_one_or_none()
        if not memory or not memory.summary_nuggets:
            return ""
        return prune_memory_text(decrypt_clinical_data(memory.summary_nuggets), max_lines=6, max_chars=420)

    async def _update_user_memory(self, db: AsyncSession, user_id: int, new_summary: str):
        result = await db.execute(select(Memory).where(Memory.user_id == user_id))
        memory = result.scalar_one_or_none()
        encrypted_summary = encrypt_clinical_data(prune_memory_text(new_summary, max_lines=6, max_chars=420))
        
        if not memory:
            memory = Memory(user_id=user_id, summary_nuggets=encrypted_summary)
            db.add(memory)
        else:
            memory.summary_nuggets = encrypted_summary
        await db.commit()

    async def _persist_conversation(self, db: AsyncSession, user_id: int, query: str, response: str, safety_mode: str, latency: float):
        conv = Conversation(
            user_id=user_id,
            query=query,
            response=response,
            safety_mode=safety_mode,
            latency_ms=latency
        )
        db.add(conv)
        await db.commit()

    async def _persist_session_turn(
        self,
        db: AsyncSession,
        session: ChatSession,
        user_id: int,
        query: str,
        response: str,
        intent: str,
        route: str,
        safety_mode: str,
        intake: dict[str, str] | None,
        sources: list[dict] | None,
    ) -> None:
        await append_session_turn(
            db,
            session,
            user_id,
            query=query,
            response=response,
            intent=intent,
            route=route,
            safety_mode=safety_mode,
            sources=sources,
            intake=intake,
        )
        await db.commit()

    def _source_models(self, query: str, retrievals: list[ScoredChunk], topic: str | None = None) -> list[SourceReference]:
        return [
            build_source_reference(query, item, rank=rank, query_topic=topic)
            for rank, item in enumerate(retrievals, start=1)
        ]

    def _retrieval_diagnostics(self, query: str, retrievals: list[ScoredChunk], topic: str | None = None):
        return build_retrieval_diagnostics(query, retrievals, query_topic=topic)

    def _source_highlight(self, sources: list[SourceReference]) -> str | None:
        if not sources:
            return None
        top = sources[0]
        parts = [top.title]
        if top.section:
            parts.append(top.section)
        if top.source_kind:
            parts.append(top.source_kind.replace("_", " "))
        return " · ".join(parts)

    # ------------------------------------------------------------------
    # Main Entry Point
    # ------------------------------------------------------------------

    async def handle_message(
        self,
        message: str,
        user: User,
        db: AsyncSession,
        background_tasks: BackgroundTasks | None = None,
        session_id: int | None = None,
        new_session: bool = False,
        intake: dict[str, str] | None = None,
        screening: dict[str, str | int | bool] | None = None,
        history: list[dict[str, str]] | None = None,
        personalization: dict[str, object] | None = None,
    ) -> ChatResponse:
        import time
        start_time = time.time()
        
        # Load persistent memory
        user_memory = await self._get_user_memory(db, user.id)
        personalization = personalization or {}

        # 1. Agentic Orchestration - Force ignoring intake to prevent bias as requested
        print(f"[DEBUG] {time.time() - start_time:.2f}s: Starting Orchestrator (Intake Ignored)")
        plan = self.orchestrator.plan(message, intake=None) 
        print(f"[DEBUG] {time.time() - start_time:.2f}s: Orchestrator finished. Intent: {plan.intent}")

        resolved_session_id = session_id
        if resolved_session_id is None and history and not new_session:
            latest_session = await get_latest_session(db, user.id)
            if latest_session is not None and latest_session.status == "active":
                resolved_session_id = latest_session.id

        session = await ensure_session(
            db,
            user.id,
            session_id=resolved_session_id,
            title=build_session_title(message, plan.topic),
            topic=plan.topic,
            intake=intake,
            consent=None,
        )
        await db.commit()

        print(f"[DEBUG] {time.time() - start_time:.2f}s: Session & Profile loading")
        profile = await profile_service.refresh_from_context(
            db,
            user.id,
            intake=intake,
            screening=screening,
            personalization=personalization,
        )
        recent_segments = await memory_store.recent_segments(db, user_id=user.id, topic=plan.topic, limit=5)
        reflections = await memory_store.reflections(db, user_id=user.id, limit=3)
        mood_trend = await mood_service.build_trend(db, user.id) if profile.use_mood_context else None
        journal_insights = await journal_service.build_insights(db, user.id) if profile.use_journal_context else None

        memory_context = user_memory
        if profile.use_memory_context and recent_segments:
            memory_context = "\n".join([user_memory, *[segment.content for segment in recent_segments[:3]]]).strip()
        if reflections:
            memory_context = "\n".join([memory_context, *[reflection.content for reflection in reflections[:2]]]).strip()

        # 2. Safety Intercept
        if plan.safety_mode != "normal":
            print(f"[DEBUG] {time.time() - start_time:.2f}s: Safety violation detected")
            safety_decision = SafetyAnalysis(
                mode=plan.safety_mode,
                risk_level=plan.risk_level,
                reasoning="Agentic analysis",
                message=plan.immediate_response or ""
            )
            payload = self.generator.build_special(
                safety=safety_decision, topic=plan.topic, intent_label=plan.intent
            )
            await self._persist_session_turn(
                db,
                session,
                user.id,
                message,
                payload.answer,
                plan.intent,
                payload.route,
                plan.safety_mode,
                intake,
                [],
            )
            return ChatResponse(
                session_id=session.id,
                status=payload.status,
                route=payload.route,
                intent=plan.intent,
                safety_mode=plan.safety_mode,
                summary=payload.summary,
                answer=payload.answer,
                follow_up=payload.follow_up,
                sources=[],
                retrieval_diagnostics=[],
                personalization_applied=False,
                personalization_signals=[],
                context_used={"profile": False, "screening": False, "mood_trend": False, "journal": False, "memory": False},
            )

        # 3. Retrieval (Conditional)
        # Re-use sentiment from consolidated plan
        sentiment = SentimentProfile(
            label=plan.sentiment_label, 
            urgency=plan.sentiment_urgency,
            empathy_required=True,
            rationale="Consolidated brain analysis"
        )
        retrievals = []
        clinical_nugget = ""
        
        if plan.use_rag:
            print(f"[DEBUG] {time.time() - start_time:.2f}s: Starting RAG Retrieval")
            personalized_query = query_builder.build(
                message=message,
                topic=plan.topic,
                profile=profile,
                screening=screening,
                memory_segments=recent_segments if profile.use_memory_context else [],
                reflections=reflections,
                sentiment=sentiment,
            )
            retrievals = self.retriever.retrieve(personalized_query.retrieval_query, topic=plan.topic, k=TOP_K)
            print(f"[DEBUG] {time.time() - start_time:.2f}s: Retrieval finished. Found {len(retrievals)} chunks")

            if self.reranker is not None:
                reranked_retrievals = self.reranker.rerank(personalized_query.retrieval_query, retrievals, topic=plan.topic)
                if reranked_retrievals:
                    retrievals = reranked_retrievals
                print(f"[DEBUG] {time.time() - start_time:.2f}s: Reranking finished. Using {len(retrievals)} chunks")

            # 4. Corrective RAG (CRAG) - Simplified (Grader removed to fix timeout)
            if retrievals:
                print(f"[DEBUG] {time.time() - start_time:.2f}s: Starting Nuggetizer")
                clinical_nugget = await self.nuggetizer.nuggetize(personalized_query.retrieval_query, retrievals)
                print(f"[DEBUG] {time.time() - start_time:.2f}s: Nuggetizer finished")

        profile_snapshot = profile_service.summarize(profile) if profile.personalization_consent else ""
        mood_summary = mood_trend.summary if mood_trend and mood_trend.summary else ""
        journal_summary = journal_insights.summary if journal_insights and journal_insights.summary else ""
        personalization_signals: list[str] = []
        if profile_snapshot:
            personalization_signals.append("profile")
        if mood_summary:
            personalization_signals.append("mood_trend")
        if journal_summary:
            personalization_signals.append("journal")
        if memory_context:
            personalization_signals.append("memory")
        personalization_applied = bool(personalization_signals)
        
        # 4. Map Plan to Response Planner
        planner = ResponsePlan(
            intent=plan.intent,
            topic=plan.topic,
            risk_mode=plan.safety_mode,
            knowledge_need=plan.use_rag,
            memory_need=profile.use_memory_context,
            tone_plan=plan.clinical_plan,
            support_goal="therapeutic dialogue",
            recommended_structure="mirroring + nugget + socratic question",
            source_mode="grounded" if plan.use_rag else "empathetic",
            personalization_signals=[]
        )

        # 5. Evidence Gate (Skip if RAG is not needed for this intent)
        if plan.use_rag and not self.evidence_gate.has_enough_evidence(retrievals, topic=plan.topic):
            payload = self.generator.build_insufficient(
                topic=plan.topic, intent_label=plan.intent
            )
            await self._persist_session_turn(
                db,
                session,
                user.id,
                message,
                payload.answer,
                plan.intent,
                payload.route,
                plan.safety_mode,
                intake,
                [source.model_dump() for source in self._source_models(message, retrievals, plan.topic)],
            )
            return ChatResponse(
                session_id=session.id,
                status=payload.status,
                route=payload.route,
                intent=plan.intent,
                safety_mode=plan.safety_mode,
                summary=payload.summary,
                answer=payload.answer,
                follow_up=payload.follow_up,
                sources=self._source_models(message, retrievals, plan.topic),
                retrieval_diagnostics=self._retrieval_diagnostics(message, retrievals, plan.topic),
                source_highlight=self._source_highlight(self._source_models(message, retrievals, plan.topic)),
                personalization_applied=personalization_applied,
                personalization_signals=personalization_signals,
                context_used={
                    "profile": bool(profile_snapshot),
                    "screening": bool(screening),
                    "mood_trend": bool(mood_summary),
                    "journal": bool(journal_summary),
                    "memory": bool(memory_context),
                },
                care_plan_hint="Shift toward general psychoeducation or add more personal context.",
            )

        # 7. Generation
        print(f"[DEBUG] {time.time() - start_time:.2f}s: Starting Final Generator")
        payload = self.generator.build_grounded(
            message=message,
            topic=plan.topic,
            retrievals=retrievals,
            intent_label=plan.intent,
            clinical_nugget=clinical_nugget,
            screening=screening,
            sentiment=sentiment,
            session_memory=session.summary,
            memory=memory_context,
            planner=planner,
            profile_snapshot=profile_snapshot,
            mood_summary=mood_summary,
            journal_summary=journal_summary,
        )
        print(f"[DEBUG] {time.time() - start_time:.2f}s: Generation complete")

        # 8. Persistence (Memory & History) - Backgrounded to fix 504 timeout
        latency = (time.time() - start_time) * 1000
        
        if background_tasks is not None:
            background_tasks.add_task(
                self._background_interaction_tasks,
                db=db,
                user=user,
                message=message,
                answer=payload.answer,
                user_memory=user_memory,
                session=session,
                topic=plan.topic,
                intent=plan.intent,
                route=payload.route,
                safety_mode=plan.safety_mode,
                sentiment_label=sentiment.label,
                latency=latency,
                intake=intake,
                sources=[source.model_dump() for source in self._source_models(message, retrievals, plan.topic)]
            )
        else:
            await self._background_interaction_tasks(
                db=db,
                user=user,
                message=message,
                answer=payload.answer,
                user_memory=user_memory,
                session=session,
                topic=plan.topic,
                intent=plan.intent,
                route=payload.route,
                safety_mode=plan.safety_mode,
                sentiment_label=sentiment.label,
                latency=latency,
                intake=intake,
                sources=[source.model_dump() for source in self._source_models(message, retrievals, plan.topic)],
            )

        return ChatResponse(
            session_id=session.id,
            status=payload.status,
            route=payload.route,
            intent=plan.intent,
            safety_mode=plan.safety_mode,
            summary=payload.summary,
            answer=payload.answer,
            follow_up=payload.follow_up,
            clinical_nugget=clinical_nugget,
            sources=self._source_models(message, retrievals, plan.topic),
            retrieval_diagnostics=self._retrieval_diagnostics(message, retrievals, plan.topic),
            source_highlight=self._source_highlight(self._source_models(message, retrievals, plan.topic)),
            personalization_applied=personalization_applied,
            personalization_signals=personalization_signals,
            context_used={
                "profile": bool(profile_snapshot),
                "screening": bool(screening),
                "mood_trend": bool(mood_summary),
                "journal": bool(journal_summary),
                "memory": bool(memory_context),
            }
        )

    async def _background_interaction_tasks(
        self,
        db: AsyncSession,
        user: User,
        message: str,
        answer: str,
        user_memory: str,
        session: ChatSession,
        topic: str,
        intent: str,
        route: str,
        safety_mode: str,
        sentiment_label: str,
        latency: float,
        intake: dict[str, str] | None,
        sources: list[dict],
    ):
        # 1. Update Persistent Memory
        updated_memory = self.memory_agent.summarize_interaction(message, answer, user_memory)
        await self._update_user_memory(db, user.id, updated_memory)
        
        # 2. Extract specific segments
        extracted_memory = memory_extractor.extract(message, answer, current_memory=user_memory)
        await memory_store.add_segments(
            db,
            user_id=user.id,
            session_id=session.id,
            topic=topic,
            extracted=extracted_memory,
        )

        # 3. Persist turns and logs
        await self._persist_conversation(db, user.id, message, answer, safety_mode, latency)
        await self._persist_session_turn(
            db,
            session,
            user.id,
            message,
            answer,
            intent,
            route,
            safety_mode,
            intake,
            sources,
        )
        self.audit_logger.log_event(user.id, message, route, sentiment_label, safety_mode, latency)


@lru_cache(maxsize=1)
def get_service() -> AssistantService:
    return AssistantService()

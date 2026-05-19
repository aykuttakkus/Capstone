from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any
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
from server.app.core.retrieval.safety_router import select_retrieval_scope
from server.app.core.agents.orchestrator import Orchestrator
from server.app.core.agents.response_planner import ResponsePlan
from server.app.core.agents.safety_guardian import SafetyAnalysis, SafetyGuardian
from server.app.core.agents.memory_agent import MemoryAgent
from server.app.core.agents.distress_monitor import SubtleDistressMonitor
from server.app.core.agents.dependency_critic import DependencyCritic
from server.app.core.agents.faithfulness_critic import FaithfulnessCritic
from server.app.core.agents.quality_critic import QualityCritic
from server.app.core.agents.fallback_handler import FallbackHandler
from server.app.core.pipeline.orchestrator_v2 import PipelineOrchestrator, PipelineContext
from server.app.core.pipeline.context_manager import ContextManager
from server.app.core.pipeline.intent_detector import IntentDetector
from server.app.core.pipeline.risk_state import RiskState
from server.app.core.pipeline.rag_decision import RAGDecisionModule
from server.app.core.pipeline.escalation_logic import HumanEscalationLogic
from server.app.utils.audit_logger import ClinicalAuditLogger
from server.app.models.sql.models import User, Memory, Conversation, ChatSession
from server.app.services.journal import journal_service
from server.app.services.memory_store import memory_extractor, memory_store
from server.app.services.mood import mood_service
from server.app.services.personalization import query_builder
from server.app.services.profile import profile_service
from server.app.services.risk_state_store import load_or_create_risk_state, save_risk_state
from server.app.services.session import prune_memory_text
from server.app.core.retrieval.nuggetizer import nuggetizer
from server.app.utils.language_adapter import detect_language, language_adapter


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

        # Phase 1: Critical safety and quality modules
        self.distress_monitor = SubtleDistressMonitor()
        self.dependency_critic = DependencyCritic()
        self.faithfulness_critic = FaithfulnessCritic()
        self.quality_critic = QualityCritic()
        self.fallback_handler = FallbackHandler()
        self.safety_guardian = SafetyGuardian()

        # Phase 2: Pipeline orchestration (14-step execution)
        self.pipeline_orchestrator = PipelineOrchestrator(
            orchestrator=self.orchestrator,
            distress_monitor=self.distress_monitor,
            dependency_critic=self.dependency_critic,
            quality_critic=self.quality_critic,
            fallback_handler=self.fallback_handler,
            safety_guardian=self.safety_guardian,
        )

        # Phase 3: Context and Intent processing
        self.context_manager = self.pipeline_orchestrator.context_manager
        self.intent_detector = self.pipeline_orchestrator.intent_detector

    def _ensure_pipeline_orchestrator(self) -> PipelineOrchestrator:
        """Return the active pipeline, creating it for test-constructed services."""
        pipeline = getattr(self, "pipeline_orchestrator", None)
        if pipeline is not None:
            return pipeline

        pipeline = PipelineOrchestrator(
            orchestrator=getattr(self, "orchestrator", None) or Orchestrator(),
            distress_monitor=getattr(self, "distress_monitor", None) or SubtleDistressMonitor(),
            dependency_critic=getattr(self, "dependency_critic", None) or DependencyCritic(),
            quality_critic=getattr(self, "quality_critic", None) or QualityCritic(),
            fallback_handler=getattr(self, "fallback_handler", None) or FallbackHandler(),
            safety_guardian=getattr(self, "safety_guardian", None) or SafetyGuardian(),
        )
        self.pipeline_orchestrator = pipeline
        self.context_manager = pipeline.context_manager
        self.intent_detector = pipeline.intent_detector
        return pipeline

    def _ensure_quality_critic(self) -> QualityCritic:
        critic = getattr(self, "quality_critic", None)
        if critic is None:
            critic = QualityCritic()
            self.quality_critic = critic
        return critic

    def _ensure_dependency_critic(self) -> DependencyCritic:
        critic = getattr(self, "dependency_critic", None)
        if critic is None:
            critic = DependencyCritic()
            self.dependency_critic = critic
        return critic

    def _ensure_faithfulness_critic(self) -> FaithfulnessCritic:
        critic = getattr(self, "faithfulness_critic", None)
        if critic is None:
            critic = FaithfulnessCritic()
            self.faithfulness_critic = critic
        return critic

    def _build_pipeline_context(
        self,
        *,
        message: str,
        session: ChatSession,
        plan: Any,
        memory_context: str,
        profile_snapshot: str = "",
        mood_summary: str = "",
        journal_summary: str = "",
        screening: dict[str, str | int | bool] | None = None,
        history: list[dict[str, str]] | None = None,
        risk_state: RiskState | None = None,
    ) -> PipelineContext:
        context_manager = getattr(self, "context_manager", None) or ContextManager(max_history=8)
        self.context_manager = context_manager
        context_package = context_manager.build_context_package(
            current_user_message=message,
            recent_conversation=history or [],
            session_summary=session.summary or {},
            user_state={
                "topic": plan.topic,
                "primary_intent": self._normalize_pipeline_intent(plan.intent),
                "secondary_intents": getattr(plan, "secondary_intents", None) or [],
                "intent_confidence": getattr(plan, "intent_confidence", 0.5),
                "safety_mode": plan.safety_mode,
            },
            risk_state=risk_state,
            response_policy=None,
            max_turns=8,
        )
        conversation_history = [
            f"{turn['role']}: {turn['content']}" for turn in context_package.recent_conversation
        ]
        profile_context = {
            "session_summary": context_package.session_summary,
            "memory": memory_context,
            "profile": profile_snapshot,
            "mood_summary": mood_summary,
            "journal_summary": journal_summary,
            "context_package": {
                "response_policy": context_package.response_policy,
                "resolved_references": context_package.resolved_references,
                "new_context_signals": context_package.new_context_signals,
                "possible_contradictions": context_package.possible_contradictions,
                "previously_suggested_strategies": context_package.previously_suggested_strategies,
            },
        }

        return PipelineContext(
            user_message=message,
            topic=plan.topic,
            intent=self._normalize_pipeline_intent(plan.intent),
            risk_level=plan.risk_level,
            conversation_history=conversation_history,
            profile_context=profile_context,
            screening_state=screening or {},
            risk_state=context_package.risk_state,
        )

    @staticmethod
    def _normalize_pipeline_intent(intent: str) -> str:
        intent_map = {
            "educational_request": "psychoeducation",
            "general_query": "psychoeducation",
            "medical_info": "psychoeducation",
            "symptom_search": "symptom_exploration",
            "venting": "emotional_support",
            "clarification": "clarification",
            "clarification_needed": "clarification",   # P1: normalize both forms
            "safety_violation": "crisis",
        }
        return intent_map.get(intent, intent or "emotional_support")

    @staticmethod
    def _risk_level_name(risk_level: int, safety_mode: str) -> str:
        if safety_mode in {"crisis", "crisis_support"} or risk_level >= 4:
            return "crisis"
        if safety_mode != "normal" or risk_level >= 3:
            return "high"
        if risk_level == 2:
            return "medium"
        if risk_level == 1:
            return "low"
        return "none"

    @staticmethod
    def _response_mode_for_intent(intent: str, safety_mode: str) -> str:
        if safety_mode in {"crisis", "crisis_support"}:
            return "crisis"
        if safety_mode in {"off_domain", "prompt_injection_blocked"}:
            return "off_scope"
        return {
            "emotional_support": "support",
            "psychoeducation": "education",
            "coping_strategy": "coping",
            "symptom_exploration": "symptom_exploration",
            "clarification_needed": "clarify",
            "crisis": "crisis",
            "off_scope": "off_scope",
            "repair": "repair",
        }.get(intent, "support")

    def _run_response_critics(
        self,
        *,
        answer: str,
        user_message: str,
        conversation_history: list[str],
        retrievals: list[ScoredChunk],
        planner: ResponsePlan,
        profile_context: dict[str, Any],
    ) -> tuple[str, list[str], bool]:
        warnings: list[str] = []
        fallback_used = False

        quality_result = self._ensure_quality_critic().critique(
            answer,
            planner.primary_intent,
            user_message,
            conversation_history,
            3 if planner.escalation_required else 0,
        )
        if not quality_result.passed:
            warnings.extend([f"quality:{concern}" for concern in quality_result.concerns])

        faithfulness_result = self._ensure_faithfulness_critic().critique(
            answer,
            retrievals,
            planner,
            planner.retrieval_confidence,
        )
        if not faithfulness_result.passed:
            warnings.extend([f"faithfulness:{item}" for item in faithfulness_result.unsupported_claims])
            warnings.extend([f"faithfulness:{item}" for item in faithfulness_result.source_misuse])
            answer = self._safe_critic_fallback(planner, user_message)
            fallback_used = True

        dependency_result = self._ensure_dependency_critic().critique(answer, profile_context)
        if not dependency_result.is_safe:
            warnings.extend([f"dependency:{item}" for item in dependency_result.violations])
            answer = self._safe_critic_fallback(planner, user_message)
            fallback_used = True

        second_faithfulness = self._ensure_faithfulness_critic().critique(
            answer,
            retrievals,
            planner,
            planner.retrieval_confidence,
        )
        if fallback_used and not second_faithfulness.passed:
            warnings.append("critic:fallback_failed_second_pass")
            answer = (
                "I want to stay within safe, general psychological information here. "
                "I cannot diagnose, give medication advice, or make strong claims without reliable support. "
                "A qualified professional can help if this is affecting your safety or daily life."
            )

        return answer, warnings, fallback_used

    def _safe_critic_fallback(self, planner: ResponsePlan, user_message: str) -> str:
        if planner.response_mode == "crisis" or planner.escalation_required:
            return (
                "This sounds important and safety comes first. If there is any immediate danger, contact local emergency services now or reach out to someone nearby who can help. "
                "I can offer general support here, but urgent or high-risk situations need real-time human support."
            )
        if planner.response_mode == "coping":
            return (
                "I can keep this general and safe: try one small grounding step, such as slowing your breathing and naming what you can see around you. "
                "This is not a diagnosis or treatment plan, but it may help you steady the moment."
            )
        if planner.response_mode == "education":
            return (
                "I can share this only as general psychoeducation, not as a diagnosis. "
                "When reliable sources are limited, it is safer to use cautious language and speak with a qualified professional for personal evaluation."
            )
        return (
            "I hear that this matters. I can support you with general psychological information, but I should avoid diagnosis, medication advice, or unsupported certainty. "
            "A small next step is to name what feels most urgent right now."
        )

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

        # H4: Language detection for bilingual (TR/EN) adaptation
        detected_lang = detect_language(message)
        _lang_note = language_adapter.adapt_system_note(detected_lang)

        # H1: Enrich plan with IntentDetector for secondary intents + confidence
        _intent_detector = getattr(self, "intent_detector", None)
        if _intent_detector is not None:
            _intent_result = _intent_detector.detect(
                message=message,
                topic=plan.topic,
                context={"risk_level": plan.risk_level, "safety_mode": plan.safety_mode},
            )
            if not plan.secondary_intents:
                plan.secondary_intents = _intent_result.secondary_intents
            if plan.intent_confidence == 0.5:
                plan.intent_confidence = _intent_result.confidence

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
        risk_state = await load_or_create_risk_state(db, user_id=user.id, session_id=session.id)

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

        profile_snapshot = profile_service.summarize(profile) if profile.personalization_consent else ""
        mood_summary = mood_trend.summary if mood_trend and mood_trend.summary else ""
        journal_summary = journal_insights.summary if journal_insights and journal_insights.summary else ""

        pipeline_context = self._build_pipeline_context(
            message=message,
            session=session,
            plan=plan,
            memory_context=memory_context,
            profile_snapshot=profile_snapshot,
            mood_summary=mood_summary,
            journal_summary=journal_summary,
            screening=screening,
            history=history,
            risk_state=risk_state,
        )
        _pipeline_result = await self._ensure_pipeline_orchestrator().execute(pipeline_context)
        await save_risk_state(db, user_id=user.id, session_id=session.id, state=pipeline_context.risk_state)
        await db.commit()
        if _pipeline_result.warnings:
            print(f"[DEBUG] Pipeline warnings: {_pipeline_result.warnings}")

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
                # Phase 11: Diagnostic fields for safety intercept
                pipeline_mode="v2_safety",
                response_mode="crisis" if plan.safety_mode in {"crisis", "crisis_support"} else "off_scope",
                risk_level="crisis" if plan.safety_mode in {"crisis", "crisis_support"} else "high",
                intent_confidence=1.0,
                secondary_intents=[],
                retrieval_confidence=0.0,
                critic_warnings=[],
                fallback_used=False,
                boundary_applied=True,
                escalation_required=plan.safety_mode in {"crisis", "crisis_support"},
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
        normalized_intent = self._normalize_pipeline_intent(plan.intent)
        retrieval_scope = select_retrieval_scope(
            intent=normalized_intent,
            risk_level=pipeline_context.risk_state.current_risk_level,
            safety_mode=plan.safety_mode,
        )
        
        if plan.use_rag and retrieval_scope.use_rag:
            print(f"[DEBUG] {time.time() - start_time:.2f}s: Starting RAG Retrieval")
            personalized_query = query_builder.build(
                message=message,
                topic=plan.topic,
                profile=profile,
                screening=screening,
                memory_segments=recent_segments if profile.use_memory_context else [],
                reflections=reflections,
                sentiment=sentiment,
                # Spec §13: context-aware query enrichment
                session_summary=session.summary if isinstance(session.summary, dict) else {},
                primary_intent=normalized_intent,
                secondary_intents=getattr(plan, "secondary_intents", None) or [],
                risk_level=pipeline_context.risk_state.current_risk_level,
            )
            retrievals = self.retriever.retrieve(
                personalized_query.retrieval_query,
                topic=plan.topic,
                k=TOP_K,
                intent=normalized_intent,
                risk_level=retrieval_scope.risk_level,
                allowed_use=retrieval_scope.allowed_use,
                min_evidence_level=retrieval_scope.min_evidence_level,
                clinical_scope=retrieval_scope.clinical_scope,
            )
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
            knowledge_need=plan.use_rag and retrieval_scope.use_rag,
            memory_need=profile.use_memory_context,
            tone_plan=plan.clinical_plan,
            support_goal="bounded psychoeducation support",
            recommended_structure="mirroring + nugget + socratic question",
            source_mode="grounded" if plan.use_rag else "empathetic",
            personalization_signals=personalization_signals,
            risk_level=pipeline_context.risk_state.current_risk_level,
            risk_confidence=0.9 if pipeline_context.risk_state.is_high_risk() else 0.5,
            subtle_distress=bool(_pipeline_result.distress_signals),
            primary_intent=normalized_intent,
            secondary_intents=getattr(plan, "secondary_intents", None) or [],
            intent_confidence=float(getattr(plan, "intent_confidence", 0.5) or 0.5),
            needs_rag=plan.use_rag and retrieval_scope.use_rag,
            retrieval_confidence=self.evidence_gate.gate_score(retrievals),
            response_mode=self._response_mode_for_intent(normalized_intent, plan.safety_mode),
            tone="safety-focused" if pipeline_context.risk_state.is_high_risk() else "warm",
            ask_question=normalized_intent not in {"crisis", "off_scope"},
            max_questions=1,
            diagnosis_allowed=False,
            medication_advice_allowed=False,
            source_required=plan.use_rag and retrieval_scope.use_rag,
            boundary_required=True,
            escalation_required=pipeline_context.risk_state.is_high_risk(),
        )

        # 5. Evidence Gate (Skip if RAG is not needed for this intent)
        if plan.use_rag and retrieval_scope.use_rag and not self.evidence_gate.has_enough_evidence(
            retrievals,
            topic=plan.topic,
            intent=normalized_intent,
            risk_level=retrieval_scope.risk_level,
            allowed_use=retrieval_scope.allowed_use,
            min_evidence_level=retrieval_scope.min_evidence_level,
            clinical_scope=retrieval_scope.clinical_scope,
        ):
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
                # Phase 11: Diagnostic fields for insufficient evidence
                pipeline_mode="v2_insufficient",
                response_mode="clarify",
                risk_level=pipeline_context.risk_state.current_risk_level,
                intent_confidence=planner.intent_confidence if hasattr(planner, 'intent_confidence') else 0.5,
                secondary_intents=planner.secondary_intents if hasattr(planner, 'secondary_intents') else [],
                retrieval_confidence=0.0,
                critic_warnings=["insufficient_evidence"],
                fallback_used=True,
                boundary_applied=False,
                escalation_required=False,
            )

        # H4: Append language instruction to profile_snapshot for LLM context
        if _lang_note:
            profile_snapshot = f"{profile_snapshot}\n{_lang_note}".strip() if profile_snapshot else _lang_note

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
        revised_answer, critic_warnings, critic_fallback_used = self._run_response_critics(
            answer=payload.answer,
            user_message=message,
            conversation_history=pipeline_context.conversation_history,
            retrievals=retrievals,
            planner=planner,
            profile_context=planner.__dict__ if hasattr(planner, "__dict__") else {},
        )
        if revised_answer != payload.answer:
            payload.answer = revised_answer
        if critic_warnings:
            print(f"[DEBUG] Critic warnings: {critic_warnings}")

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
                sources=[source.model_dump() for source in self._source_models(message, retrievals, plan.topic)],
                mood_score=mood_trend.latest_score if mood_trend and hasattr(mood_trend, "latest_score") else None,
                memory_enabled=profile.personalization_consent and profile.use_memory_context,
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
                mood_score=mood_trend.latest_score if mood_trend and hasattr(mood_trend, "latest_score") else None,
                memory_enabled=profile.personalization_consent and profile.use_memory_context,
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
            },
            # Phase 11: Diagnostic fields
            pipeline_mode="v2",
            response_mode=planner.response_mode,
            risk_level=pipeline_context.risk_state.current_risk_level,
            intent_confidence=planner.intent_confidence,
            secondary_intents=planner.secondary_intents,
            retrieval_confidence=planner.retrieval_confidence,
            critic_warnings=critic_warnings if critic_warnings else [],
            fallback_used=critic_fallback_used,
            boundary_applied=plan.safety_mode != "normal",
            escalation_required=pipeline_context.risk_state.escalation_recommended,
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
        mood_score: int | None = None,
        memory_enabled: bool = True,
    ):
        if not memory_enabled:
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
            return

        try:
            # 1. Update Persistent Memory
            updated_memory = self.memory_agent.summarize_interaction(message, answer, user_memory, mood_score=mood_score)
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
        except Exception as exc:
            print(f"[WARN] Memory update skipped: {exc}")

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

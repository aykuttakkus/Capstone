"""
DEPRECATED: This module implements the rigid 14-step pipeline system (v2.1).

This has been superseded by the new conversational AI system (v3) in:
  - /app/services/conversational_assistant.py
  - /app/services/rag_augmentation.py
  - /app/services/risk_detection.py
  - /app/services/escalation.py
  - /app/api/chat/routes_v3.py

The new system offers:
  ✅ Natural dialogue flow (no rigid modules)
  ✅ Full context awareness (conversation history + user state + RAG)
  ✅ No template responses (LLM always generates)
  ✅ Decoupled safety (risk detection doesn't gate responses)
  ✅ Invisible RAG (knowledge naturally integrated)

See `/docs/calma_new_system.md` for the original spec, which this module attempted to implement.
The new system (v3) abandons rigid modularity in favor of conversational AI.

To use the new system, access `/api/chat-v3/` instead of `/api/chat/`.

DEPRECATION TIMELINE:
  - Phase 5 (current): New system in parallel, old system still available
  - Phase 6 (future): Migrate `/api/chat/` to new system, archive old routes
  - Phase 7 (future): Remove old pipeline code completely

DO NOT build new features on this module. All new work should use the v3 system.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from server.app.core.agents.distress_monitor import SubtleDistressMonitor
from server.app.core.agents.dependency_critic import DependencyCritic
from server.app.core.agents.quality_critic import QualityCritic
from server.app.core.agents.fallback_handler import FallbackHandler, FallbackMode
from server.app.core.agents.orchestrator import Orchestrator
from server.app.core.agents.response_planner import ResponsePlan
from server.app.core.agents.safety_guardian import SafetyAnalysis, SafetyGuardian
from server.app.core.generation.llm import OllamaClient
from server.app.core.pipeline.response_modes import ResponseMode, ResponseModeContext, ResponseModeSelector, enforce_length_constraint
from server.app.core.pipeline.context_manager import ContextManager, ConversationContext
from server.app.core.pipeline.intent_detector import IntentDetector
from server.app.core.pipeline.risk_state import RiskState
from server.app.core.pipeline.rag_decision import RAGDecisionModule
from server.app.core.pipeline.escalation_logic import HumanEscalationLogic
from server.app.core.pipeline.memory_updater import MemoryUpdater, MemoryUpdateResult
from server.app.rag_v2.rag_engine import RAGEngine


@dataclass(slots=True)
class PipelineContext:
    user_message: str
    topic: str
    intent: str
    risk_level: int = 0
    conversation_history: list[str] = field(default_factory=list)
    conversation_log: list[dict[str, Any]] = field(default_factory=list)  # Enhanced conversation tracking
    retrieved_content: str | None = None
    profile_context: dict[str, Any] | None = None
    screening_state: dict[str, Any] | None = None
    risk_state: RiskState = field(default_factory=lambda: RiskState(current_risk_level="none"))
    session_id: str | None = None
    session_summary: dict[str, Any] = field(default_factory=dict)  # Persistent session summary
    previous_responses: list[str] = field(default_factory=list)  # For coherence


@dataclass(slots=True)
class PipelineResult:
    response: str
    mode: ResponseMode
    is_degraded: bool
    distress_signals: int
    dependency_violations: int
    quality_score: float
    execution_time_ms: float
    warnings: list[str] = field(default_factory=list)


class PipelineOrchestrator:
    """14-step spec-compliant pipeline for safe psychoeducation responses.

    Step 1  — Context Manager     (ContextManager.build_context_package)
    Step 2  — Safety Triage       (SafetyGuardian.analyze)
    Step 3  — Subtle Distress     (SubtleDistressMonitor.analyze)
    Step 4  — Intent Detection    (PipelineContext.intent, populated by caller)
    Step 5  — RAG Decision        (RAGDecisionModule.decide)
    Step 6  — Evidence Retrieval  (handled by AssistantService)
    Step 7  — Response Planner    (ResponseModeSelector + builder.build)
    Step 8  — Answer Generator    (ResponseModeSelector + builder.build / LLM)
    Step 9  — Quality Critic      (QualityCritic.critique)
    Step 10 — Safety/Faithfulness (SafetyGuardian.analyze on output)
    Step 11 — Dependency Critic   (DependencyCritic.critique — prompt level)
    Step 12 — Escalation Logic    (HumanEscalationLogic.evaluate)
    Step 13 — Final Response      (PipelineResult)
    Step 14 — Memory Update       (MemoryUpdater.update)
    """

    def __init__(
        self,
        orchestrator: Orchestrator,
        distress_monitor: SubtleDistressMonitor,
        dependency_critic: DependencyCritic,
        quality_critic: QualityCritic,
        fallback_handler: FallbackHandler,
        safety_guardian: SafetyGuardian | None = None,
        rag_engine: RAGEngine | None = None,
        llm_client: OllamaClient | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.distress_monitor = distress_monitor
        self.dependency_critic = dependency_critic
        self.quality_critic = quality_critic
        self.fallback_handler = fallback_handler
        self.safety_guardian = safety_guardian or SafetyGuardian()
        self.rag_decision = RAGDecisionModule()
        self.escalation_logic = HumanEscalationLogic()
        self.memory_updater = MemoryUpdater()
        self.mode_selector = ResponseModeSelector()
        self.context_manager = ContextManager()
        self.intent_detector = IntentDetector()
        self.rag_engine = rag_engine or RAGEngine()
        self.llm_client = llm_client or OllamaClient()
        self.session_conversations: dict[str, list[dict[str, Any]]] = {}  # Session-based conversation storage
        self.session_summaries: dict[str, dict[str, Any]] = {}  # Session-based summary storage
        self.session_responses: dict[str, list[str]] = {}  # Session-based response history

    async def execute(
        self,
        context: PipelineContext,
        llm_available: bool = True,
        retrieval_available: bool = True,
    ) -> PipelineResult:
        start_time = time.time()
        warnings = []

        # Step 1: Context Manager - Enhanced with session tracking
        session_id = context.session_id or "default_session"
        
        # Retrieve previous conversation data for this session
        previous_conversation = self.session_conversations.get(session_id, [])
        previous_summary = self.session_summaries.get(session_id, {})
        previous_responses = self.session_responses.get(session_id, [])
        
        # Build enhanced context package
        context_package = self.context_manager.build_context_package(
            current_user_message=context.user_message,
            recent_conversation=previous_conversation + [
                {"role": "user", "content": context.user_message, "intent": context.intent}
            ],
            session_summary=previous_summary,
            user_state=context.profile_context,
            risk_state=context.risk_state,
            max_turns=8,
            include_summaries=True,
            include_key_entities=True,
            include_risk_evolution=True,
            previous_responses=previous_responses,
        )
        
        # Update context with enhanced information
        context.session_summary = context_package.session_summary
        context.conversation_log = context_package.recent_conversation
        context.previous_responses = previous_responses

        # Step 2: Safety Triage
        safety_result = self.safety_guardian.analyze(context.user_message)
        context.risk_state.update_risk_check(
            self._map_safety_mode_to_risk_level(safety_result.mode),
            safety_result.reasoning,
        )
        if safety_result.risk_level >= 4:
            context.risk_state.activate_crisis_protocol()
            warnings.append(f"Safety alert: {safety_result.reasoning}")

        # Step 3: Subtle Distress Monitor (M6: rehydrate history from DB risk state)
        self.distress_monitor.rehydrate_from_risk_state(
            list(context.risk_state.cumulative_risk_signals)
        )
        distress_analysis = self.distress_monitor.analyze(
            context.user_message,
            context.conversation_history,
            {"distress_level": context.risk_level},
            turn_number=len(context.conversation_history),
        )

        if distress_analysis.escalation_detected:
            warnings.append(f"Escalation detected: {distress_analysis.recommended_action}")
            context.risk_level = max(context.risk_level, distress_analysis.current_distress_level)
            context.risk_state.cumulative_risk_signals.extend([s.category for s in distress_analysis.signals])

        # Step 4: Intent Detection
        # (Already done when PipelineContext is created with intent)

        # Step 5: RAG Decision (intelligent retrieval decision)
        rag_decision = self.rag_decision.decide(
            intent=context.intent,
            topic=context.topic,
            conversation_length=len(context.conversation_history),
            risk_level=context.risk_level,
            has_recent_retrieval=False,  # Could track from session
        )

        # Step 6: Evidence Retrieval (FAISS-based RAG)
        if rag_decision.use_rag and retrieval_available:
            try:
                rag_response = self.rag_engine.answer(
                    query=context.user_message,
                    top_k=rag_decision.retrieve_amount or 3,
                )
                if rag_response.retrieved_chunks:
                    context.retrieved_content = rag_response.context
                    # Log retrieval info for debugging
                    print(f"[RAG] Retrieved {len(rag_response.retrieved_chunks)} chunks from indexes: {rag_response.sources}")
            except Exception as e:
                print(f"[RAG] Retrieval failed: {e}")
                # Continue without retrieval - fallback to non-RAG response
                rag_decision.use_rag = False

        # Step 7: Response Planner
        # (Integrated in mode selection and generation)

        # Step 8: Answer Generator + Step 9: Response Quality Critic
        response_mode = self._select_response_mode(distress_analysis, context)
        dep_result = None  # initialise for all branches

        if response_mode == ResponseMode.CRISIS:
            response = self._generate_crisis_response(context)
            quality_score = 1.0
        elif response_mode == ResponseMode.OFF_SCOPE:
            response = self._generate_off_scope_response(context)
            quality_score = 0.8
        else:
            response = self._generate_response(
                context, response_mode, llm_available and rag_decision.use_rag, retrieval_available
            )

            # Step 9: Response Quality Critic
            quality_result = self.quality_critic.critique(
                response,
                response_mode.value,
                context.user_message,
                context.conversation_history,
                context.risk_level,
            )
            quality_score = quality_result.overall_score

            if not quality_result.passed:
                warnings.extend(quality_result.concerns)
                if quality_result.recommendations:
                    response = self._enhance_response(response, quality_result.recommendations[0])

            # Step 10: Safety & Faithfulness Critic
            safety_check = self.safety_guardian.analyze(response)
            if safety_check.risk_level >= 3:
                warnings.append(f"Safety check on response: {safety_check.reasoning}")
                if safety_check.message:
                    response = self._revise_response(response, safety_check.message)

            # Step 11: Dependency & Boundary Critic
            # P2: DependencyCritic runs here only in pipeline mode (on prompt strings).
            # The definitive check on actual LLM output happens in assistant._run_response_critics.
            dep_result = self.dependency_critic.critique(response, context.profile_context)
            if not dep_result.is_safe:
                warnings.append(f"Dependency concern: {dep_result.severity} - {dep_result.recommendation}")

        # Step 12: Human Escalation Logic
        escalation_decision = self.escalation_logic.evaluate(
            risk_level=context.risk_level,
            distress_signals=[s.category for s in distress_analysis.signals] if response_mode != ResponseMode.CRISIS else ["crisis"],
            conversation_length=len(context.conversation_history),
            quality_score=quality_score if response_mode != ResponseMode.CRISIS else 1.0,
            safety_concerns=warnings,
        )
        if escalation_decision.level.value != "none":
            warnings.append(f"Escalation: {escalation_decision.reason}")
            if escalation_decision.level.value == "immediate":
                context.risk_state.activate_crisis_protocol()

        # Step 12.5: Fallback Handler (already integrated in _generate_response)

        # Step 13: Final Response (PipelineResult)

        # Step 14: Memory Update (spec §31 structured update) - Enhanced with session persistence
        memory_result = self._update_memory(
            context, response, response_mode,
            distress_signals=[s.category for s in distress_analysis.signals],
        )
        
        # Update session storage for context persistence across turns
        if session_id:
            # Add current turn to conversation history
            current_turn = {
                "role": "assistant",
                "content": response,
                "mode": response_mode.value,
                "intent": context.intent,
                "risk_level": context.risk_level,
                "quality_score": quality_score if response_mode != ResponseMode.CRISIS else 1.0,
            }
            
            # Update conversation log
            if session_id not in self.session_conversations:
                self.session_conversations[session_id] = []
            self.session_conversations[session_id].append({
                "role": "user",
                "content": context.user_message,
                "intent": context.intent,
            })
            self.session_conversations[session_id].append(current_turn)
            
            # Sliding window: Son 8 turu tut (Global standart: 4-8 turn)
            if len(self.session_conversations[session_id]) > 16:  # 8 kullanıcı + 8 AI mesajı
                self.session_conversations[session_id] = self.session_conversations[session_id][-16:]
            
            # Update session summary with latest information
            if session_id not in self.session_summaries:
                self.session_summaries[session_id] = {}
            
            self.session_summaries[session_id].update({
                "last_turn": len(self.session_conversations[session_id]) // 2,
                "last_risk_level": context.risk_level,
                "last_intent": context.intent,
                "last_topic": context.topic,
                "main_topics": context.session_summary.get("main_topics", []),
                "key_entities": context.session_summary.get("key_entities", []),
                "risk_evolution": context.session_summary.get("risk_evolution", {}),
                "updated_at": time.time(),
            })
            
            # GLOBAL BEST PRACTICE 2: Session Persistence + Sliding Window
            if session_id not in self.session_responses:
                self.session_responses[session_id] = []
            self.session_responses[session_id].append(response)
            
            # Sliding window: Son 8 yanıtı tut (OpenAI/LangChain standardı)
            if len(self.session_responses[session_id]) > 8:
                self.session_responses[session_id] = self.session_responses[session_id][-8:]
            
            # Keep only last 5 responses
            if len(self.session_responses[session_id]) > 5:
                self.session_responses[session_id] = self.session_responses[session_id][-5:]

        execution_time = (time.time() - start_time) * 1000

        return PipelineResult(
            response=response,
            mode=response_mode,
            is_degraded=not (llm_available and retrieval_available),
            distress_signals=len(distress_analysis.signals),
            dependency_violations=len(dep_result.violations) if dep_result is not None else 0,
            quality_score=quality_score,
            execution_time_ms=execution_time,
            warnings=warnings,
        )

    def _select_response_mode(
        self, distress_analysis: Any, context: PipelineContext
    ) -> ResponseMode:
        if distress_analysis.recommended_action == "escalate_to_crisis_resources":
            return ResponseMode.CRISIS

        if context.intent == "off_scope":
            return ResponseMode.OFF_SCOPE

        intent_mode_map = {
            "psychoeducation": ResponseMode.PSYCHOEDUCATION,
            "coping_strategy": ResponseMode.COPING_STRATEGY,
            "symptom_exploration": ResponseMode.SYMPTOM_EXPLORATION,
            "clarification": ResponseMode.CLARIFICATION,
            "clarification_needed": ResponseMode.CLARIFICATION,  # P1: normalize both forms
            "emotional_support": ResponseMode.EMOTIONAL_SUPPORT,
            "repair": ResponseMode.REPAIR,
        }

        return intent_mode_map.get(context.intent, ResponseMode.EMOTIONAL_SUPPORT)

    def _generate_response(
        self,
        context: PipelineContext,
        mode: ResponseMode,
        llm_available: bool,
        retrieval_available: bool,
    ) -> str:
        # ============================================
        # YENİ: HER ZAMAN LLM KULLAN
        # ============================================
        print(f"[DEBUG] _generate_response called with intent: {context.intent}")
        print(f"[DEBUG] retrieved_content length: {len(context.retrieved_content) if context.retrieved_content else 0}")
        
        # Eski fallback kodunu devre dışı bırak
        # if context.intent in ["emotional_support", "clarification"] and not context.retrieved_content:
        #     ... (fallback kodu devre dışı)
        
        # Build coherence context from previous responses
        coherence_context = ""
        if context.previous_responses:
            coherence_context = "\n\n[Previous Response Summary]:\n"
            for i, prev_resp in enumerate(context.previous_responses[-3:], 1):
                # Extract key points from previous response (first 200 chars)
                summary = prev_resp[:200].replace("[MODE:", "").replace("]", "")
                coherence_context += f"{i}. {summary}...\n"
        
        # Build enhanced conversation history with context
        enhanced_history = context.conversation_history.copy()
        
        # Add key entities and topics from session summary if available
        if context.session_summary:
            if "key_entities" in context.session_summary:
                entities = context.session_summary["key_entities"]
                if entities:
                    entity_summary = "[Key Topics in Conversation]: " + ", ".join(
                        [e.get("type", "") for e in entities[:5]]
                    )
                    enhanced_history.append(entity_summary)
            
            if "main_topics" in context.session_summary:
                topics = context.session_summary["main_topics"]
                if topics:
                    topic_summary = "[Main Topics]: " + ", ".join(topics[:3])
                    enhanced_history.append(topic_summary)
        
        mode_context = ResponseModeContext(
            mode=mode,
            user_message=context.user_message,
            topic=context.topic,
            risk_level=context.risk_level,
            conversation_history=enhanced_history,
            retrieved_content=context.retrieved_content,
            intent=context.intent,
            profile_context=context.profile_context,
        )

        # ============================================
        # YENİ: QWEN LLM İLE DİNAMİK YANIT ÜRETİMİ
        # ============================================
        
        print(f"[DEBUG] Starting LLM generation for intent: {context.intent}")
        print(f"[DEBUG] Retrieved content length: {len(context.retrieved_content) if context.retrieved_content else 0}")
        
        # LLM için zengin prompt oluştur
        llm_prompt = self._build_llm_prompt(context, mode, coherence_context)
        print(f"[DEBUG] LLM Prompt built, length: {len(llm_prompt)}")
        
        # Qwen LLM'den yanıt al
        try:
            print("[DEBUG] Calling OllamaClient.generate()...")
            llm_result = self.llm_client.generate(prompt=llm_prompt, temperature=0.7)
            print(f"[DEBUG] LLM result available: {llm_result.available}")
            print(f"[DEBUG] LLM result text length: {len(llm_result.text) if llm_result.text else 0}")
            
            if llm_result.available and llm_result.text:
                # LLM yanıtını kullan - DOĞRUDAN, MÜDAHALE ETME
                response = llm_result.text.strip()
                print(f"[DEBUG] Using LLM response: {response[:100]}...")
                
                # LLM'e güven, müdahale etme
                return enforce_length_constraint(response, mode)
            else:
                # LLM çalışmadı, fallback kullan
                print("[WARNING] LLM not available, using fallback")
                return self._generate_contextual_response(context, mode)
                
        except Exception as e:
            print(f"[ERROR] LLM generation failed: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_contextual_response(context, mode)
    
    def _build_llm_prompt(self, context: PipelineContext, mode: ResponseMode, coherence_context: str) -> str:
        """Qwen LLM için zengin, bağlamsal prompt oluştur - Global Best Practices: Sliding Window + Session Persistence"""
        
        # GLOBAL BEST PRACTICE 1: Sliding Window (Son 6 mesajı tut - token limit için)
        # OpenAI, LangChain, Anthropic hepsi son N mesaj yaklaşımını kullanır
        session_id = context.session_id or "default_session"
        MAX_HISTORY_TURNS = 6  # Global standart: 4-8 turn
        
        # Session'dan konuşma geçmişini al (Kullanıcı + AI mesajları)
        session_conv = self.session_conversations.get(session_id, [])
        session_responses = self.session_responses.get(session_id, [])
        
        # Konuşma geçmişini formatla (Kullanıcı-AI çiftleri)
        history_lines = []
        
        # Önceki mesajları ekle (Sliding window: son MAX_HISTORY_TURNS tur)
        start_idx = max(0, len(session_conv) - MAX_HISTORY_TURNS)
        
        for i in range(start_idx, len(session_conv)):
            user_msg = session_conv[i].get("content", "") if i < len(session_conv) else ""
            ai_msg = session_responses[i] if i < len(session_responses) else ""
            
            if user_msg:
                history_lines.append(f"Kullanıcı: {user_msg}")
            if ai_msg:
                # AI yanıtını kısalt (token tasarrufu)
                ai_short = ai_msg[:200] + "..." if len(ai_msg) > 200 else ai_msg
                history_lines.append(f"Sen: {ai_short}")
        
        # Şu anki kullanıcı mesajını da ekle
        history_lines.append(f"Kullanıcı: {context.user_message}")
        
        history_text = "\n\n".join(history_lines) if history_lines else "(Yeni konuşma)"
        
        # FAISS'ten gelen bilgileri al
        knowledge_text = ""
        if context.retrieved_content:
            # Klinik/soğuk ifadeleri temizle
            knowledge_text = self._clean_knowledge(context.retrieved_content)
        
        # BASİT VE ETKİLİ PROMPT - LLM'e özgürlük ver
        # RAG sadece bilgi kaynağı, LLM doğal konuşsun
        
        prompt = f"""Sen empati dolu, samimi bir sohbet arkadaşısın. Doğal bir insan gibi konuş.

KONUŞMA GEÇMİŞİ:
{history_text if history_text else "(Yeni konuşma başlıyor)"}

ŞU ANKİ MESAJ:
Kullanıcı: {context.user_message}

YARDIMCI BİLGİLER (Kaynaklardan):
{knowledge_text if knowledge_text else "Genel destek konuşması yap"}

GÖREV:
- Doğal, samimi bir şekilde yanıt ver
- Konuşmayı kesme, devam ettir
- Kullanıcı "evet" derse, hemen bilgiyi paylaş (tekrar sorma)
- Soğuk, klinik ifadeler kullanma
- Gerekirse bilgiyi doğrudan ver, "paylaşabilirim" demekle yetinme

Yanıtın:"""
        
        return prompt
    
    def _clean_knowledge(self, knowledge: str) -> str:
        """FAISS'ten gelen bilgilerden klinik/soğuk ifadeleri temizle"""
        cold_phrases = [
            "i'm really sorry",
            "unable to provide",
            "one-on-one counseling",
            "personalized advice",
            "i'm not a therapist",
            "i cannot diagnose",
            "professional help",
            "mental health professional",
            "seek professional",
            "consult a professional",
            "if you feel that your feelings persist",
            "reach out to a mental health professional",
        ]
        
        cleaned = knowledge
        for phrase in cold_phrases:
            cleaned = cleaned.replace(phrase, "")
            cleaned = cleaned.replace(phrase.title(), "")
        
        # Fazla boşlukları temizle
        cleaned = " ".join(cleaned.split())
        
        return cleaned[:800]  # LLM token limit için kısalt
    
    def _contains_clinical_language(self, response: str) -> bool:
        """Check if response contains cold/clinical language that pushes user away"""
        cold_phrases = [
            "unable to provide",
            "one-on-one counseling",
            "personalized advice",
            "i'm not a therapist",
            "i cannot diagnose",
            "professional help",
            "mental health professional",
            "seek professional",
            "consult a professional",
        ]
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in cold_phrases)
    
    def _add_warm_framing(self, context: PipelineContext, original_response: str) -> str:
        """Add warm, empathetic framing around clinical responses"""
        
        # Extract the actual useful content (remove the cold disclaimers)
        lines = original_response.split('\n')
        useful_lines = []
        
        for line in lines:
            line_lower = line.lower()
            # Skip cold disclaimer lines
            if any(phrase in line_lower for phrase in [
                "i'm really sorry",
                "unable to provide",
                "one-on-one counseling",
                "personalized advice",
                "i'm not a therapist",
                "i cannot",
                "please consult",
                "seek professional",
            ]):
                continue
            useful_lines.append(line)
        
        # Get useful content
        useful_content = ' '.join(useful_lines).strip()
        
        # Create warm opening based on topic
        user_msg = context.user_message.lower()
        
        if "lonely" in user_msg or "alone" in user_msg:
            warm_opening = "I hear you. Feeling lonely, especially when you're surrounded by people, is one of the most painful experiences. That disconnect you described—the feeling that nobody understands—it's real, and it matters."
        elif "anxious" in user_msg or "worried" in user_msg:
            warm_opening = "Thank you for trusting me with that. Anxiety can feel overwhelming, and those racing thoughts can be exhausting. What you're feeling is valid."
        elif "sad" in user_msg or "depressed" in user_msg:
            warm_opening = "I appreciate you sharing that with me. Sadness can feel heavy and isolating. It's okay to not be okay right now."
        elif "understand" in user_msg and "nobody" in user_msg:
            warm_opening = "Feeling like nobody understands you can be incredibly isolating. That pain is real, and it makes sense that you'd want to talk about it."
        else:
            warm_opening = "Thank you for sharing that with me. What you're going through sounds really difficult, and I want you to know that your feelings are valid."
        
        # Combine warm opening with useful content (if any)
        if useful_content and len(useful_content) > 20:
            # Clean up the content - remove repetitive professional referrals at the end
            cleaned_content = self._clean_clinical_endings(useful_content)
            if cleaned_content:
                warm_response = f"{warm_opening}\n\n{cleaned_content}\n\nI'm here to listen and talk through this with you. What feels most important right now?"
            else:
                warm_response = f"{warm_opening}\n\nI'm here to listen and talk through this with you. Would you like to tell me more about what you're experiencing?"
        else:
            warm_response = f"{warm_opening}\n\nI'm here to listen and talk through this with you. Would you like to tell me more about what you're experiencing?"
        
        return warm_response
    
    def _clean_clinical_endings(self, content: str) -> str:
        """Remove clinical/professional referral endings from content"""
        endings_to_remove = [
            "if you feel that your feelings persist or worsen, it might be helpful to reach out to a mental health professional.",
            "please consult with a mental health professional.",
            "seek professional help if needed.",
            "consider reaching out to a therapist.",
            "you may want to speak with a professional.",
        ]
        
        content_lower = content.lower()
        for ending in endings_to_remove:
            idx = content_lower.find(ending)
            if idx != -1:
                content = content[:idx].strip()
                content_lower = content.lower()
        
        return content.strip()
    
    def _generate_contextual_response(self, context: PipelineContext, mode: ResponseMode) -> str:
        """Generate a contextual response based on user's specific message"""
        
        user_msg = context.user_message.lower()
        topic = context.topic.lower()
        
        # TOPIC-SPECIFIC EMPATHETIC RESPONSES
        # These actually address what the user said, not generic templates
        
        if "lonely" in user_msg or "alone" in user_msg or topic == "loneliness":
            if "around people" in user_msg or "surrounded" in user_msg:
                response = "Feeling lonely even when you're with others can be especially painful. It's like there's a wall between you and everyone else. That disconnect you're feeling is real, and it matters."
            else:
                response = "Loneliness can feel really heavy, like you're carrying something invisible that others can't see. Thank you for sharing this with me—it takes courage to talk about."
        
        elif "understand" in user_msg and ("nobody" in user_msg or "no one" in user_msg):
            response = "Feeling like nobody understands you is incredibly isolating. It's painful when it seems like others can't see what you're going through. Your feelings are valid, and they matter."
        
        elif "anxious" in user_msg or "anxiety" in user_msg or "worried" in user_msg:
            if "heart" in user_msg or "chest" in user_msg or "physical" in user_msg:
                response = "Those physical sensations—the racing heart, the tightness—are your body's way of sounding an alarm. Anxiety manifests in very real physical ways, and what you're experiencing is valid."
            else:
                response = "Anxiety can feel overwhelming, like your mind won't quiet down. It's exhausting to carry that weight. What you're feeling is more common than you might think, and it doesn't mean you're weak."
        
        elif "sad" in user_msg or "depressed" in user_msg or "hopeless" in user_msg:
            if "hopeless" in user_msg or "pointless" in user_msg:
                response = "When everything feels pointless, it's hard to find the energy to keep going. That heaviness you're describing is real, and it's okay to feel it. You don't have to carry this alone."
            else:
                response = "Sadness can feel like a weight that won't lift. It's okay to not be okay right now. Your feelings are valid, and they don't define your worth."
        
        elif "tired" in user_msg or "exhausted" in user_msg or "burnout" in user_msg:
            response = "Being emotionally exhausted is just as real as physical exhaustion. When you're running on empty, everything feels harder. It's okay to acknowledge that you're depleted."
        
        elif "can't cope" in user_msg or "can't handle" in user_msg or "overwhelmed" in user_msg:
            response = "Feeling like you can't cope doesn't mean you're failing—it means you're human, and you're carrying a lot right now. What you're feeling makes sense given what you're going through."
        
        elif "okay" in user_msg or "fine" in user_msg:
            if len(user_msg) < 20:  # Short responses like "I'm okay"
                response = "Sometimes 'okay' is what we say when the real answer feels too heavy to share. If you're not really okay, that's okay too. I'm here to listen."
            else:
                response = "I hear you. Sometimes we say we're okay even when we're not. Whatever you're feeling is valid."
        
        else:
            # Default empathetic response that actually acknowledges the person
            response = "Thank you for sharing that with me. What you're going through sounds really difficult, and I want you to know that your feelings are valid. I'm here to listen."
        
        # Add gentle follow-up question or statement based on conversation progress
        if len(context.conversation_history) <= 2:  # Early in conversation
            response += " Would you like to tell me more about what you're experiencing?"
        elif len(context.conversation_history) > 4:  # Deeper into conversation
            response += " What feels most important for you to talk about right now?"
        
        # Add retrieved content ONLY if it adds value and is not educational when user needs support
        if context.retrieved_content and mode != ResponseMode.EMOTIONAL_SUPPORT:
            response += f"\n\nI found some information that might help: {context.retrieved_content[:200]}..."
        
        return enforce_length_constraint(response, mode)

    def _generate_crisis_response(self, context: PipelineContext) -> str:
        builder = self.mode_selector.select_builder(ResponseMode.CRISIS)
        return builder.build(
            ResponseModeContext(
                mode=ResponseMode.CRISIS,
                user_message=context.user_message,
                topic=context.topic,
                risk_level=context.risk_level,
                conversation_history=context.conversation_history,
            )
        )

    def _generate_off_scope_response(self, context: PipelineContext) -> str:
        builder = self.mode_selector.select_builder(ResponseMode.OFF_SCOPE)
        return builder.build(
            ResponseModeContext(
                mode=ResponseMode.OFF_SCOPE,
                user_message=context.user_message,
                topic=context.topic,
                risk_level=context.risk_level,
                conversation_history=context.conversation_history,
            )
        )

    def _revise_response(self, response: str, recommendation: str) -> str:
        return f"{response}\n\n[REVISED PER SAFETY CHECK: {recommendation}]"

    def _enhance_response(self, response: str, enhancement: str) -> str:
        return f"{response}\n\n[ENHANCED: {enhancement}]"

    def _count_violations(self, critic_result: Any) -> int:
        return len(critic_result.violations) if hasattr(critic_result, "violations") else 0

    def _map_safety_mode_to_risk_level(self, mode: str) -> str:
        """Map SafetyGuardian mode to RiskState level."""
        mode_map = {
            "crisis": "crisis",
            "escalate": "high",
            "monitor": "medium",
            "normal": "none",
        }
        return mode_map.get(mode, "none")


    def _update_memory(
        self,
        context: PipelineContext,
        response: str,
        mode: ResponseMode,
        distress_signals: list[str] | None = None,
    ) -> MemoryUpdateResult:
        """Step 14: Structured memory update per spec §31 & §32.9."""
        previous_summary: dict[str, Any] = {}
        if context.profile_context:
            raw = context.profile_context.get("session_summary", {})
            previous_summary = raw if isinstance(raw, dict) else {"recap": str(raw)}

        result = self.memory_updater.update(
            user_message=context.user_message,
            final_response=response,
            previous_session_summary=previous_summary,
            previous_risk_state=context.risk_state,
            response_mode=mode.value,
            distress_signals=distress_signals or [],
        )

        # Update context_manager cache if session_id available
        session_id = getattr(context, "session_id", None)
        if session_id and hasattr(self.context_manager, "update_context"):
            self.context_manager.update_context(session_id, response, distress_level=context.risk_level)

        return result

    def get_pipeline_stats(self) -> dict[str, Any]:
        return {
            "distress_signals_tracked": len(self.distress_monitor.signal_history),
            "system_ready": True,
        }

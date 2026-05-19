# Calma Full Integration Completion Plan

## 1. Purpose

This document converts the gap analysis against `docs/calma_new_system.md` into a fully actionable implementation plan.

The goal is to move Calma from an advanced prototype into a final capstone-ready, safety-aware, context-aware, evidence-grounded psychological psychoeducation system.

The final system must guarantee that every chat response passes through the complete safety and RAG pipeline:

```text
User Message
-> Context Manager
-> Safety Triage
-> Subtle Distress Monitor
-> Intent Detection
-> RAG Decision
-> Evidence Retrieval
-> Response Planner
-> Answer Generator
-> Response Quality Critic
-> Safety & Faithfulness Critic
-> Dependency & Boundary Critic
-> Fallback Handler if needed
-> Final Response
-> Memory Update
```

This plan is implementation-oriented. Each phase includes target files, required changes, acceptance criteria, and tests.

---

## 2. Current State Summary

The repository already contains many required modules:

```text
server/app/core/pipeline/orchestrator_v2.py
server/app/core/pipeline/context_manager.py
server/app/core/pipeline/intent_detector.py
server/app/core/pipeline/rag_decision.py
server/app/core/pipeline/risk_state.py
server/app/core/agents/distress_monitor.py
server/app/core/agents/quality_critic.py
server/app/core/agents/dependency_critic.py
server/app/core/agents/fallback_handler.py
server/app/core/agents/safety_guardian.py
server/app/services/assistant.py
server/app/core/retrieval/*
server/app/config/prompts.yaml
```

However, the production chat endpoint currently does not execute the complete pipeline.

The main chat route calls:

```text
/api/chat/
-> AssistantService.handle_message()
-> Orchestrator.plan()
-> Safety intercept
-> Conditional RAG
-> Evidence gate
-> Answer generation
-> Background memory update
```

The key problem is not absence of modules. The key problem is incomplete integration.

---

## 3. Final Integration Goals

The final implementation must satisfy these claims:

1. Every normal chat response goes through the unified pipeline.
2. Crisis and high-risk messages stop normal RAG generation.
3. Subtle distress is tracked cumulatively across session turns.
4. Risk state is stored separately from normal session summary.
5. Intent detection supports primary intent, secondary intents, and confidence.
6. RAG is used only when appropriate and is controlled by intent, risk, topic, metadata, confidence, and source quality.
7. Every factual psychoeducation answer is internally traceable to retrieved sources.
8. Every generated answer is checked by quality, safety/faithfulness, and dependency/boundary critics before returning to the user.
9. Memory updates are privacy-aware, minimal, structured, and do not overwrite risk casually.
10. Prompts position Calma as a psychoeducation support system, not as a therapist or clinical provider.

---

## 4. Phase 1 - Make PipelineOrchestrator The Primary Chat Path

### Target Files

```text
server/app/services/assistant.py
server/app/core/pipeline/orchestrator_v2.py
server/app/models/schemas/chat.py
tests/unit/services/test_assistant_service.py
tests/integration/api/test_chat_api.py
tests/integration/test_pipeline_integration.py
```

### Required Changes

Refactor `AssistantService.handle_message()` so the active chat path builds a rich `PipelineContext` and calls:

```python
pipeline_result = await self.pipeline_orchestrator.execute(context)
```

The current `Orchestrator.plan()` may remain as a helper, but it must not bypass the complete pipeline.

The active flow should become:

```text
handle_message()
-> ensure/load session
-> load recent conversation turns
-> load session summary
-> load profile/mood/journal/memory context
-> build context package
-> execute PipelineOrchestrator
-> persist final answer
-> update structured memory
-> return ChatResponse
```

### Required Implementation Details

Add a private method:

```python
async def _build_pipeline_context(...) -> PipelineContext:
    ...
```

This method must include:

```text
current user message
last 5-8 conversation turns
session summary
profile context
screening state
mood trend if consented
journal summary if consented
memory segments if consented
persisted risk state
```

The existing `history` payload must not be blindly trusted. Prefer persisted session messages when `session_id` is present.

### Acceptance Criteria

- `AssistantService.handle_message()` calls `PipelineOrchestrator.execute()` for normal chat.
- No normal chat response bypasses safety, distress monitor, RAG decision, critics, and memory update.
- Existing API response schema remains backward-compatible.
- Crisis responses return before normal RAG generation.

### Tests

Add or update tests:

```text
tests/unit/services/test_assistant_service.py
- assert pipeline_orchestrator.execute is called for normal messages
- assert crisis messages do not call normal generation
- assert response warnings are surfaced in diagnostics or logs

tests/integration/api/test_chat_api.py
- normal psychoeducation request returns answer + route + sources when RAG is used
- emotional support request can return no sources
- crisis message returns crisis mode and no RAG sources
```

---

## 5. Phase 2 - Persist Risk State Separately

### Target Files

```text
server/app/models/sql/models.py
server/app/services/session_store.py
server/app/services/risk_state_store.py
server/app/core/pipeline/risk_state.py
tests/unit/services/test_risk_state_store.py
tests/integration/api/test_chat_api.py
```

### Required Changes

Create a dedicated SQL model:

```python
class SessionRiskState(Base):
    __tablename__ = "session_risk_states"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    current_risk_level = Column(String, nullable=False, default="none")
    risk_indicators_json = Column(Text, nullable=True)
    cumulative_risk_signals_json = Column(Text, nullable=True)
    crisis_protocol_active = Column(Boolean, nullable=False, default=False)
    needs_human_support = Column(Boolean, nullable=False, default=False)
    last_risk_check = Column(DateTime(timezone=True), nullable=True)
    safety_analysis_reasoning = Column(Text, nullable=True)
    escalation_recommended = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

Create service:

```text
server/app/services/risk_state_store.py
```

with:

```python
async def load_or_create_risk_state(db, user_id: int, session_id: int) -> RiskState
async def save_risk_state(db, user_id: int, session_id: int, state: RiskState) -> None
```

### Risk State Rules

- Risk state must never be embedded only inside `ChatSession.summary`.
- Crisis state must persist until clearly resolved.
- A later normal message must not automatically downgrade risk.
- Downgrading from `high` or `crisis` must require explicit safety resolution logic.

### Acceptance Criteria

- Risk state survives across multiple API calls in the same session.
- Repeated subtle distress raises cumulative risk sensitivity.
- Crisis protocol activation persists in `session_risk_states`.

### Tests

```text
test_risk_state_persists_across_turns
test_crisis_state_not_overwritten_by_normal_message
test_subtle_distress_accumulates_across_turns
test_risk_state_saved_after_pipeline_execution
```

---

## 6. Phase 3 - Upgrade Context Manager To The Spec Contract

### Target Files

```text
server/app/core/pipeline/context_manager.py
server/app/services/session_store.py
server/app/models/schemas/conversation.py
tests/integration/test_pipeline_integration.py
```

### Required Changes

Replace the current minimal context object with a structured context package:

```python
@dataclass(slots=True)
class ContextPackage:
    current_user_message: str
    recent_conversation: list[dict]
    session_summary: dict
    user_state: dict
    risk_state: RiskState
    response_policy: dict
    resolved_references: list[str]
    new_context_signals: list[str]
    possible_contradictions: list[str]
```

The context manager must:

- Use only the last 5-8 conversation turns by default.
- Keep current message as highest priority.
- Include persisted risk state separately.
- Detect contradictions such as “that is better now” after previous distress.
- Track previously suggested coping strategies.
- Avoid forcing old memory into every answer.

### Acceptance Criteria

- Context package follows `docs/calma_new_system.md`.
- Current message overrides old memory.
- Recent conversation is bounded.
- Risk state remains separate.

### Tests

```text
test_context_package_limits_recent_turns
test_current_message_overrides_old_summary
test_context_includes_risk_state
test_context_tracks_previously_suggested_strategy
```

---

## 7. Phase 4 - Replace Intent Model With Mixed Intent Contract

### Target Files

```text
server/app/core/pipeline/intent_detector.py
server/app/core/agents/orchestrator.py
server/app/config/prompts.yaml
tests/integration/test_pipeline_integration.py
```

### Required Output

Intent detection must return:

```python
@dataclass(slots=True)
class IntentResult:
    primary_intent: str
    secondary_intents: list[str]
    confidence: float
    rationale: str
```

Allowed intents:

```text
emotional_support
psychoeducation
coping_strategy
symptom_exploration
clarification_needed
crisis
off_scope
repair
```

### Required Changes

Current prompt uses:

```text
educational_request, symptom_search, emotional_support, venting, greeting, general_query, medical_info, clarification
```

Replace it with the final taxonomy from `calma_new_system.md`.

Map old names only as compatibility aliases during migration:

```text
educational_request -> psychoeducation
symptom_search -> symptom_exploration
venting -> emotional_support
medical_info -> psychoeducation or medication boundary depending on safety
clarification -> clarification_needed
```

### Acceptance Criteria

- Mixed intent is represented.
- Low-confidence intent leads to safer language and optional single clarifying question.
- Repair intent is detected.
- Off-scope intent does not use normal RAG.

### Tests

```text
test_mixed_intent_emotional_support_plus_symptom_exploration
test_repair_intent
test_clarification_needed_intent
test_off_scope_intent
test_low_confidence_intent_uses_fallback_policy
```

---

## 8. Phase 5 - Make RAG Decision And Retrieval Fully Metadata-Aware

### Target Files

```text
server/app/core/retrieval/corpus.py
server/app/core/retrieval/hybrid_retriever.py
server/app/core/retrieval/faiss_store.py
server/app/core/retrieval/qdrant_store.py
server/app/core/retrieval/evidence_gate.py
server/app/core/pipeline/rag_decision.py
scripts/ingest_pdfs.py
scripts/build_index.py
data/knowledge_base_taxonomy.json
tests/unit/core/test_retrieval_filters.py
tests/unit/core/test_evidence_gate.py
tests/integration/retrieval/test_retrieval_pipeline.py
```

### Required Metadata Fields

Extend `KnowledgeChunk`:

```python
allowed_use: list[str]
not_allowed: list[str]
risk_level: str
content_type: str
evidence_level: str
clinical_scope: str
requires_disclaimer: bool
source_date: str | None
last_reviewed: str | None
review_required: bool
```

Allowed values:

```text
content_type:
psychoeducation
coping_step
crisis_instruction
medication_boundary
methodology
screening_information

evidence_level:
clinical_guideline
peer_reviewed
clinical_self_help
educational
low_confidence

clinical_scope:
psychoeducation_only
crisis_support_only
medication_boundary_only
methodology_only
```

### Required Retrieval Filters

Retrieval must accept:

```python
retrieve(
    query: str,
    topic: str | None,
    intent: str,
    risk_level: str,
    allowed_use: list[str] | None,
    exclude_not_allowed: list[str] | None,
    min_evidence_level: str | None,
    freshness_required: bool = False,
)
```

### Risk-Aware Retrieval Rules

```text
intent = crisis:
  Do not use normal psychoeducation retrieval.
  Use crisis protocol or isolated crisis content only.

risk_level = high:
  Avoid long explanatory retrieval.
  Prefer safety/support resources.

intent = psychoeducation:
  Use explanation-safe chunks.

intent = coping_strategy:
  Use coping_step or clinical_self_help chunks.

intent = emotional_support:
  Use no retrieval unless planner requests a short psychoeducational nugget.

medication-related request:
  Use medication_boundary only.
  Never retrieve medication instruction chunks.
```

### Evidence Gate Upgrade

`EvidenceGate` must evaluate:

```text
minimum score
topic match
allowed use
evidence level
source confidence
freshness if required
clinical scope
not_allowed constraints
```

If evidence is weak:

```text
No reliable retrieval -> no strong claim.
```

### Acceptance Criteria

- Crisis content cannot appear in normal psychoeducation responses unless risk is present.
- Low-confidence chunks cannot support strong factual claims.
- Medication requests are routed to boundary responses.
- Retrieved sources include metadata in diagnostics.

### Tests

```text
test_psychoeducation_retrieves_only_allowed_explanation_chunks
test_coping_strategy_retrieves_coping_chunks
test_crisis_does_not_retrieve_normal_psychoeducation
test_medication_request_uses_boundary_only
test_low_confidence_source_blocks_strong_claim
test_source_freshness_filter
```

---

## 9. Phase 6 - Add Safety-Aware Source Separation

### Target Files

```text
server/app/core/retrieval/index_store.py
server/app/core/retrieval/faiss_store.py
server/app/core/retrieval/qdrant_store.py
server/app/core/retrieval/hybrid_retriever.py
scripts/build_index.py
docs/RAG_INTEGRATION_ANALYSIS.md
tests/integration/retrieval/test_retrieval_pipeline.py
```

### Required Index Strategy

Preferred:

```text
Qdrant collections:
- calma_psychoeducation
- calma_coping
- calma_crisis_safety
- calma_medication_boundary
- calma_methodology
```

Fallback if FAISS-only:

```text
data/store/faiss_psychoeducation.index
data/store/faiss_coping.index
data/store/faiss_crisis_safety.index
data/store/faiss_medication_boundary.index
data/store/faiss_methodology.index
```

### Router Rules

Create:

```text
server/app/core/retrieval/safety_router.py
```

with:

```python
def select_retrieval_scope(intent: str, risk_level: str, safety_mode: str) -> RetrievalScope:
    ...
```

### Acceptance Criteria

- Crisis safety chunks are isolated from normal retrieval.
- Normal psychoeducation cannot accidentally retrieve crisis-instruction chunks.
- Safety routing decisions appear in retrieval diagnostics.

---

## 10. Phase 7 - Implement Response Planner Contract

### Target Files

```text
server/app/core/agents/response_planner.py
server/app/core/pipeline/response_modes.py
server/app/core/pipeline/orchestrator_v2.py
tests/unit/core/test_response_planner.py
```

### Required Planner Output

```python
@dataclass(slots=True)
class ResponsePlan:
    risk_level: str
    risk_confidence: float
    subtle_distress: bool
    primary_intent: str
    secondary_intents: list[str]
    intent_confidence: float
    needs_rag: bool
    retrieval_confidence: float
    response_mode: str
    tone: str
    ask_question: bool
    max_questions: int
    diagnosis_allowed: bool
    medication_advice_allowed: bool
    source_required: bool
    boundary_required: bool
    escalation_required: bool
```

### Planner Rules

```text
crisis -> crisis mode
psychoeducation -> education mode
coping_strategy -> coping mode
emotional_support -> support mode
symptom_exploration -> symptom exploration mode
clarification_needed -> brief support + one question
repair -> acknowledge correction + answer directly
off_scope -> scope boundary
```

### Acceptance Criteria

- Planner controls response mode, tone, length, source need, question count, and boundary requirement.
- Generator follows planner rather than relying only on prompt style.

---

## 11. Phase 8 - Run Critics Before Returning Any Generated Answer

### Target Files

```text
server/app/core/agents/quality_critic.py
server/app/core/agents/safety_guardian.py
server/app/core/agents/dependency_critic.py
server/app/core/agents/faithfulness_critic.py
server/app/core/pipeline/orchestrator_v2.py
tests/unit/core/test_quality_critic.py
tests/unit/core/test_faithfulness_critic.py
tests/unit/core/test_dependency_critic.py
```

### Required New Module

Create:

```text
server/app/core/agents/faithfulness_critic.py
```

Input:

```python
draft_response: str
retrieved_chunks: list[ScoredChunk]
response_plan: ResponsePlan
retrieval_confidence: float
```

Output:

```python
passed: bool
unsupported_claims: list[str]
source_misuse: list[str]
rewrite_required: bool
rewrite_instructions: list[str]
```

### Required Critic Chain

```text
draft answer
-> quality critic
-> safety critic
-> faithfulness critic
-> dependency/boundary critic
-> rewrite if needed
-> repeat critic once
-> fallback if still failing
```

### Critical Failures

Rewrite or fallback must be triggered if response:

- diagnoses the user
- gives medication advice
- misses crisis signs
- discourages professional help
- gives absolute reassurance
- uses unsupported factual claims
- uses crisis content outside crisis context
- creates AI dependency
- asks more than one question unless explicitly allowed by policy

### Acceptance Criteria

- No generated answer returns without critic pass.
- If critic fails twice, fallback response is returned.
- Critic decisions are logged in diagnostics.

### Tests

```text
test_diagnosis_claim_is_rewritten
test_medication_advice_is_blocked
test_unsupported_claim_removed
test_dependency_language_replaced
test_multiple_questions_reduced_to_one
test_critic_failure_uses_fallback
```

---

## 12. Phase 9 - Fix System Positioning And Prompt Boundaries

### Target Files

```text
server/app/config/prompts.yaml
server/app/core/generation/generator.py
docs/technical/GOVERNANCE_CONTRACT.md
README.md
client/src/App.jsx
client/src/config.js
```

### Current Risk

Some prompts currently position the assistant as:

```text
You are a PhD Clinical Psychologist.
```

This conflicts with the required system boundary.

### Required Replacement

Use:

```text
You are Calma, a psychological psychoeducation and information-support assistant.
You are not a therapist, psychologist, psychiatrist, doctor, diagnostic tool, treatment provider, or emergency service.
You provide general psychological information, source-grounded psychoeducation, and supportive guidance.
You do not diagnose, treat, prescribe, manage medication, or replace professional care.
```

### Required Prompt Rules

Generation prompts must include:

```text
- Answer in the user's language when possible.
- Be warm, clear, and bounded.
- Do not claim to be a clinician.
- Do not provide diagnosis.
- Do not provide medication advice.
- Do not over-reassure.
- Do not create dependency.
- Ask at most one question.
- Help first, then optionally ask one useful question.
- In crisis, stay short and direct.
```

### Acceptance Criteria

- No active prompt claims the system is a psychologist, therapist, doctor, or treatment provider.
- UI and README describe Calma as psychoeducation support.
- Crisis and medication boundaries are explicit.

### Tests

```text
test_prompts_do_not_claim_clinician_identity
test_generation_prompt_contains_boundary_rules
test_response_does_not_present_as_therapist
```

---

## 13. Phase 10 - Structured Privacy-Aware Memory Update

### Target Files

```text
server/app/models/sql/models.py
server/app/services/session_store.py
server/app/services/memory_store.py
server/app/core/agents/memory_agent.py
server/app/utils/privacy.py
tests/unit/services/test_privacy_phase6.py
tests/unit/services/test_memory_context.py
```

### Required Structured Summary

Session summary should be stored as compact JSON:

```json
{
  "main_concern": "",
  "emotional_state": "",
  "triggers": [],
  "coping_tried": [],
  "coping_effectiveness": {},
  "user_goal": "",
  "last_response_mode": "",
  "important_new_information": []
}
```

Risk state must remain separate and must not be stored only inside this summary.

### Memory Rules

- Store only important information.
- Do not store unnecessary personal details.
- Do not store trauma details verbatim.
- Do not store identity-sensitive details unless necessary.
- Do not treat temporary emotions as permanent traits.
- Track coping strategies already suggested.
- Track strategies the user says did not help.
- Prefer minimal, summarized, non-identifying memory.

### Required Implementation

Create:

```python
class MemoryUpdateResult:
    updated_session_summary: dict
    updated_risk_state: RiskState
    memory_update_notes: list[str]
```

Memory update must run after final response, not before critics.

### Acceptance Criteria

- Memory update failure does not block chat response.
- Sensitive content is summarized minimally.
- Coping strategy repetition can be avoided using stored strategy history.

---

## 14. Phase 11 - Upgrade ChatResponse Diagnostics

### Target Files

```text
server/app/models/schemas/chat.py
server/app/services/retrieval_debug.py
client/src/App.jsx
tests/integration/api/test_chat_api.py
```

### Required Diagnostic Fields

Add optional fields:

```python
pipeline_mode: str | None
response_mode: str | None
risk_level: str | None
intent_confidence: float | None
secondary_intents: list[str]
retrieval_confidence: float | None
critic_warnings: list[str]
fallback_used: bool
boundary_applied: bool
escalation_required: bool
```

These can remain hidden from normal UI but should be available for evaluation and demo/debug mode.

### Acceptance Criteria

- API remains backward-compatible.
- Evaluation scripts can inspect safety, intent, retrieval, and critic behavior.

---

## 15. Phase 12 - Evaluation Dataset And Final Test Suite

### Target Files

```text
tests/eval/golden_dataset.json
tests/eval/run_eval.py
tests/eval/eval_results_schema.json
docs/RETRIEVAL_EVALUATION.md
docs/TEST_RESULTS.md
```

### Required Dataset Categories

The final dataset must include:

```text
normal psychoeducation questions
emotional support messages
coping strategy requests
symptom exploration messages
ambiguous messages
mixed intent messages
repair requests
explicit crisis messages
subtle distress messages
cumulative subtle risk conversations
medication-related messages
abuse or immediate danger messages
hallucination traps
low-retrieval / no-retrieval cases
off-scope messages
cultural sensitivity cases
over-reassurance traps
dependency-inducing scenarios
```

Each test case:

```json
{
  "id": "",
  "user_message": "",
  "conversation_context": [],
  "expected_primary_intent": "",
  "expected_secondary_intents": [],
  "expected_risk_level": "",
  "expected_response_mode": "",
  "must_include": [],
  "must_not_include": [],
  "expected_rag_used": true,
  "expected_escalation": false
}
```

### Required Metrics

```text
RAG:
- retrieval precision
- context relevance
- faithfulness
- hallucination rate
- retrieval failure handling
- source freshness compliance

Safety:
- crisis detection recall
- subtle distress detection
- cumulative risk tracking
- medication boundary compliance
- diagnosis refusal compliance
- professional escalation correctness
- unsafe response rate

Conversation:
- intent match
- mixed intent handling
- empathy score
- clarity score
- question overload score
- repair success rate

Context:
- session summary accuracy
- context carryover accuracy
- coping repetition rate
- risk persistence
- privacy-aware memory compliance
```

### Acceptance Criteria

- Evaluation script outputs machine-readable JSON.
- Final report includes pass/fail per category.
- All critical safety cases must pass before final demo.

---

## 16. Final Implementation Order

Recommended order:

```text
1. Prompt boundary fix
2. Persistent risk state store
3. Context package upgrade
4. Mixed intent contract
5. PipelineOrchestrator as primary chat path
6. Metadata-aware RAG fields
7. Safety-aware retrieval routing
8. Response planner contract
9. Critic chain before response
10. Structured memory updater
11. API diagnostics
12. Evaluation dataset and final test report
```

This order reduces safety risk early and prevents later RAG/generation work from being built on an unsafe identity or incomplete risk model.

---

## 17. Definition Of Done

The system can be considered fully integrated when all of the following are true:

```text
[ ] /api/chat/ uses the full pipeline for every normal chat response.
[ ] Crisis messages stop normal generation and RAG.
[ ] Risk state persists separately from session summary.
[ ] Subtle distress accumulates across turns.
[ ] Intent output includes primary, secondary, and confidence.
[ ] RAG decision uses intent + risk + session summary.
[ ] Retrieval filters by topic, intent, risk, allowed use, evidence level, and freshness where available.
[ ] Crisis content is isolated from normal psychoeducation retrieval.
[ ] Response planner controls mode, tone, source requirement, boundary, escalation, and max questions.
[ ] Quality critic runs before final response.
[ ] Safety and faithfulness critic runs before final response.
[ ] Dependency and boundary critic runs before final response.
[ ] Failed critic results trigger rewrite or fallback.
[ ] Memory update is structured, minimal, and privacy-aware.
[ ] Active prompts do not claim clinician identity.
[ ] Final evaluation dataset covers safety, RAG, conversation, context, and memory.
[ ] Critical safety tests pass.
[ ] Final documentation states the system is psychoeducation support, not diagnosis, therapy, medication advice, or emergency service.
```

---

## 18. Final Capstone Claim After Completion

After this plan is implemented, the project can safely claim:

```text
Calma is a safety-aware, context-aware, source-grounded psychological psychoeducation system. It does not diagnose, treat, prescribe medication, provide therapy, or replace professional care. Each response passes through context management, explicit and subtle safety analysis, mixed intent detection, risk-aware RAG decisioning, metadata-filtered evidence retrieval, response planning, answer generation, quality validation, safety and faithfulness validation, dependency and boundary validation, fallback handling, and privacy-aware memory update.
```

Turkish version:

```text
Calma, psikolojik bilgilendirme amacıyla geliştirilmiş güvenlik odaklı, bağlama duyarlı ve kaynak temelli bir psiko-eğitim sistemidir. Tanı koymaz, tedavi sunmaz, ilaç önermez, terapi yapmaz ve profesyonel desteğin yerine geçmez. Her cevap; bağlam yönetimi, açık ve dolaylı güvenlik analizi, karma niyet tespiti, risk duyarlı RAG kararı, metadata filtreli kaynak getirme, cevap planlama, cevap üretimi, kalite doğrulama, güvenlik ve kaynak sadakati doğrulama, bağımlılık ve sınır doğrulama, fallback yönetimi ve gizlilik duyarlı memory update adımlarından geçer.
```

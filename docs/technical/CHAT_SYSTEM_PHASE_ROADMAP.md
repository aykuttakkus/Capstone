# Chat System Phase Roadmap

**Base document:** `docs/technical/CHAT_SYSTEM_REVISION_PLAN.md`  
**System:** Calma — Psychoeducational Mental Health Assistant  
**Purpose:** Provide a professional, implementation-ready roadmap for evolving the current chat stack without rewriting it from scratch.

---

## 1. Executive Summary

Calma already has the right major subsystems: safety policy, orchestration, retrieval, generation, memory, and persistence. The current gap is not missing infrastructure, but the way those pieces are composed.

Today the assistant behaves too much like a gated RAG pipeline. The target behavior is different:

- understand user intent like a normal assistant,
- respond naturally first,
- enrich the response with evidence when available,
- downgrade confidence when evidence is weak,
- stop only when safety requires it.

This roadmap keeps the current codebase intact and introduces the changes in phases so each step remains testable, reversible, and reviewable.

---

## 2. Current System Diagnosis

### What already works

- `server/app/services/assistant.py` owns end-to-end chat orchestration.
- `server/app/core/agents/orchestrator.py` performs intent, topic, and safety planning.
- `server/app/core/generation/generator.py` produces the final user-facing answer.
- `server/app/core/retrieval/hybrid_retriever.py` and the FAISS/Qdrant layer provide evidence search.
- `server/app/core/retrieval/evidence_gate.py` prevents weak evidence from being presented as grounded fact.
- `server/app/core/routing/continuity_router.py` handles cross-session continuity and episodic memory use.
- `server/app/services/flows/topics.py` gives the system a first-pass topic map.
- `server/app/config/prompts.yaml` centralizes the behavioral contract.

### Where the current flow is too rigid

- `use_rag` is too binary for real conversations.
- Weak retrieval can collapse the response instead of simply lowering certainty.
- The assistant does not yet separate “natural answer” from “evidence support.”
- Topic inference is too narrow for everyday phrasing like `finals exam stress`.
- The current corpus/chunking pipeline is adequate for broad psychoeducation, but not yet optimized for action-oriented self-help.

### Target operating model

The assistant should operate as:

1. a conversational AI,
2. with evidence-grounded augmentation,
3. with explicit uncertainty handling,
4. with strict safety short-circuits.

---

## 3. Architecture Principles

| Principle | Meaning in practice |
|---|---|
| Extend, do not replace | Keep the current stack and revise the control flow around it |
| Safety first | Crisis, diagnosis, medication, and prompt injection remain hard stops |
| Answer first | The user gets a coherent answer even if retrieval is weak |
| Evidence second | Sources support the answer, they do not dictate whether an answer exists |
| Low evidence = lower confidence | Weak corpus support should downgrade certainty, not usefulness |
| Actionability matters | For self-help use cases, retrieval must surface practical steps, not only explanations |
| Bilingual parity | TR and EN must remain behaviorally consistent |

---

## 4. System Boundaries

### In scope

- Chat understanding and routing.
- Natural answer generation.
- Evidence augmentation.
- Confidence and uncertainty calibration.
- Chunking and corpus refinement for self-help.
- Safety preservation.
- Test and evaluation updates.

### Out of scope

- Replacing Ollama or the LLM backend.
- Rewriting the entire backend stack.
- Introducing a new front-end architecture.
- Changing the product from psychoeducational assistant to therapist replacement.

---

## 5. Desired End-State

The final system should support these behaviors:

- `I have finals exam stress` -> normal empathetic response, plus coping guidance if relevant chunks exist.
- `I feel off lately` -> empathy plus a clarifying response, not a forced retrieval-driven answer.
- `What can I do right now to calm down?` -> immediate self-help steps, grounded in sources when possible.
- `Do I have depression?` -> diagnosis refusal plus general explanation.
- `This is too much and I want to disappear` -> safety route.

The core requirement is not just factual correctness. It is conversational reliability under uncertainty.

---

## 6. Phase Model

Each phase below has:

- objective,
- files to revise,
- implementation tasks,
- risks,
- exit criteria.

The phases are ordered by dependency. Do not advance a phase until the previous phase passes its exit criteria.

---

## 7. Phase 0 - Contracts, Schemas, and Planning Surface

### Objective

Create the internal data contract needed for a richer chat flow, without changing user-visible behavior yet.

### Task Breakdown

1. Extend `ChatResponse` with the new confidence, evidence, and guard fields.
2. Expand `OrchestrationPlan` so routing can return confidence, evidence need, and clarification need.
3. Extend `ResponsePlan` so generation can choose answer style, support style, and uncertainty style.
4. Add prompt placeholders for draft answering, evidence augmentation, and uncertainty fallback.
5. Update retrieval diagnostics so source support can be explained consistently.
6. Add contract tests for serialization and default values.

### Files to revise

| File | Change |
|---|---|
| `server/app/models/schemas/chat.py` | Extend response schema |
| `server/app/core/agents/orchestrator.py` | Expand orchestration plan shape |
| `server/app/core/agents/response_planner.py` | Add richer output planning fields |
| `server/app/config/prompts.yaml` | Add prompt templates for the future flow |
| `server/app/services/retrieval_debug.py` | Prepare support/confidence diagnostics |

### Implementation details

#### `ChatResponse`

Add fields for:

- `confidence`
- `evidence_status`
- `conversation_mode`
- `draft_summary`
- `supporting_chunks`
- `hallucination_guard`

#### `OrchestrationPlan`

Add fields for:

- `conversation_mode`
- `confidence`
- `retrieval_need`
- `should_clarify`
- `evidence_need`

#### `ResponsePlan`

Add fields for:

- `answer_style`
- `support_style`
- `follow_up_style`
- `uncertainty_style`

### Risks

- Schema changes can ripple through endpoints and tests.
- Hidden coupling may exist in response serialization or UI assumptions.

### Exit criteria

- Existing API behavior still works.
- New fields are available and serializable.
- No safety regression is introduced.

---

## 8. Phase 1 - Conversation Understanding and Routing

### Objective

Make the system understand ordinary language before retrieval begins.

### Task Breakdown

1. Broaden `topics.py` to recognize common mental-health phrasing and exam-related stress language.
2. Revise `agents.brain_analysis` so it returns intent, topic, sentiment, urgency, evidence need, and clarification need.
3. Refine `continuity_router.py` so it only handles continuation, ambiguity, and episodic memory gating.
4. Add `conversation_mode` selection logic in the orchestrator.
5. Add ambiguous-input fallbacks for vague distress, mixed intent, and general chat.
6. Add routing regression tests for natural-language inputs in TR and EN.

### Files to revise

| File | Change |
|---|---|
| `server/app/core/agents/orchestrator.py` | Upgrade analysis and plan extraction |
| `server/app/services/flows/topics.py` | Expand topic recognition |
| `server/app/core/routing/continuity_router.py` | Keep continuity logic focused on session carryover |
| `server/app/services/assistant.py` | Pass richer routing output downstream |
| `server/app/config/prompts.yaml` | Revise `agents.brain_analysis` prompt |

### Implementation details

#### Orchestrator improvements

The orchestrator should detect:

- intent,
- topic,
- sentiment,
- urgency,
- clarification need,
- evidence need,
- safety mode,
- confidence.

It should no longer reduce its decision to only `use_rag`.

#### Topic system improvements

Expand `topics.py` to recognize broader phrasing for:

- stress,
- anxiety,
- finals/exam pressure,
- panic,
- low mood,
- burnout,
- sleep,
- self-esteem,
- grief,
- loneliness,
- social pressure,
- help-seeking.

#### Continuity router role

Keep it limited to:

- new topic vs continuation,
- episodic memory gating,
- soft check-in behavior when ambiguous.

Do not let it compete with semantic intent understanding.

### Risks

- Over-classification into the wrong topic if keyword patterns are still too narrow.
- Ambiguous messages may still need a clarifying fallback.

### Exit criteria

- The system classifies everyday mental-health language correctly.
- Continuity routing no longer drives the whole chat logic.
- The assistant can tell when to ask a clarifying question.

---

## 9. Phase 2 - Natural Answer First, Evidence Second

### Objective

Convert response generation into a two-step composition flow instead of a single evidence-bound answer step.

### Task Breakdown

1. Split generation into a draft step and a final composition step.
2. Define the draft payload fields needed by the final composer.
3. Update prompts so the draft is conversational and retrieval-independent.
4. Update prompts so the final composer can insert evidence naturally without exposing internal labels.
5. Add fallback composition for cases where retrieval is weak or absent.
6. Add generation tests for natural answers with and without evidence.

### Files to revise

| File | Change |
|---|---|
| `server/app/core/generation/generator.py` | Split answer generation into draft and final composition |
| `server/app/core/agents/response_planner.py` | Map plans to answer composition strategy |
| `server/app/config/prompts.yaml` | Add draft and compose prompts |
| `server/app/services/assistant.py` | Orchestrate draft -> retrieval -> final answer |

### Implementation details

#### Draft stage

The draft should contain:

- direct answer,
- key claims,
- confidence estimate,
- safety sensitivity,
- likely follow-up needs.

The draft must remain conversational and not expose internal routing or retrieval labels.

#### Final stage

The final composer should:

- preserve the draft’s natural tone,
- inject evidence only when it supports the claim,
- keep the response coherent when evidence is partial,
- drop unsupported certainty.

### Prompt expectations

The prompts should explicitly require:

- natural language,
- short answers when appropriate,
- one clarifying question at most,
- no raw source labels in the user-facing text,
- no fabricated certainty.

### Risks

- The model can become too verbose if the output contract is not constrained.
- The final composer may over-edit and lose the conversational voice.

### Exit criteria

- The assistant produces a usable answer even when no chunk is retrieved.
- The answer reads like a human assistant, not a retrieval report.
- The system can still stay concise.

---

## 10. Phase 3 - Retrieval as Evidence Augmentation

### Objective

Turn retrieval into a support layer for claims and self-help steps.

### Task Breakdown

1. Update the retriever so it can search against draft claims as well as the user message.
2. Introduce support labels for retrieved chunks.
3. Separate retrieval into direct support, coping guidance, and background context buckets.
4. Update source diagnostics so the final response can show why a source was selected.
5. Adjust evidence gating so weak evidence downgrades certainty instead of blocking the answer.
6. Add retrieval tests for supported, partially supported, and unsupported queries.

### Files to revise

| File | Change |
|---|---|
| `server/app/core/retrieval/hybrid_retriever.py` | Allow retrieval against draft claims and user message |
| `server/app/core/retrieval/evidence_gate.py` | Change from hard gate to graded evidence assessor |
| `server/app/services/retrieval_debug.py` | Add support-label diagnostics |
| `server/app/models/schemas/chat.py` | Return evidence-support metadata |

### Implementation details

#### Retrieval strategy

Use three retrieval buckets:

- direct support,
- related coping guidance,
- background educational context.

#### Support labels

Each chunk should be tagged internally as one of:

- `supports`,
- `partially_supports`,
- `background_only`,
- `not_used`.

#### Retrieval query sources

The retriever should consider:

- the raw user message,
- the draft claims,
- the current topic,
- the conversation mode.

### Risks

- If the retriever only follows the exact user wording, it will miss helpful self-help chunks.
- If it follows the draft too aggressively, it can drift away from user intent.

### Exit criteria

- The response can be grounded without becoming rigid.
- Partial support is represented honestly.
- The system can distinguish direct support from background-only context.

---

## 11. Phase 4 - Uncertainty and Hallucination Control

### Objective

Prevent overconfident unsupported claims while preserving answer usefulness.

### Task Breakdown

1. Define the supported evidence states and their composition rules.
2. Add guard metadata for blocked and downgraded claims.
3. Update the generator so unsupported claims are softened or removed.
4. Update the orchestrator so confidence and clarification signals affect final behavior.
5. Add user-facing fallback language for thin corpus coverage.
6. Add golden-set tests for unsupported-claim leakage and uncertainty wording.

### Files to revise

| File | Change |
|---|---|
| `server/app/core/generation/generator.py` | Add uncertainty-aware composition |
| `server/app/core/agents/orchestrator.py` | Add confidence and clarification control |
| `server/app/core/retrieval/evidence_gate.py` | Produce evidence strength, not only pass/fail |
| `server/app/models/schemas/chat.py` | Add `evidence_status` and guard metadata |
| `server/app/config/prompts.yaml` | Add fallback language for unsupported claims |

### Evidence states

| State | Meaning |
|---|---|
| `well_supported` | Corpus directly supports the answer |
| `partially_supported` | Corpus supports part of the answer |
| `weakly_supported` | Corpus is related but not specific enough |
| `unsupported` | Corpus does not support the claim confidently |

### Required fallback behavior

- Keep the answer if it is still useful in general terms.
- Explicitly say when the corpus is thin on the exact point.
- Offer a safer adjacent explanation or action step.
- Never invent citations.
- Never upgrade weak support into certainty.

### Risks

- If uncertainty language is too frequent, the assistant will feel hesitant.
- If it is too rare, the model may overstate unsupported claims.

### Exit criteria

- The assistant is honest about confidence.
- Unsupported claims are downgraded, not invented.
- The experience remains helpful and not defensive.

---

## 12. Phase 5 - Chunking and Corpus Revamp

### Objective

Make the PDF corpus better suited for grounded self-help, not only broad psychoeducation.

### Task Breakdown

1. Update the chunker to preserve headings, worksheets, and self-help steps as meaningful units.
2. Extend corpus metadata with topic, subtopic, action type, audience, risk level, and page tracking.
3. Revise ingestion history so schema versioning and chunking versioning are recorded.
4. Improve metadata classification so source PDFs are tagged by actionability, not only topic.
5. Enforce corpus procurement rules for source quality, provenance, and license safety.
6. Validate that the corpus contains enough support for coping, grounding, help-seeking, and psychoeducation.

### Files to revise

| File | Change |
|---|---|
| `server/app/core/retrieval/ingestion/chunker.py` | Improve splitting for long sections and worksheets |
| `server/app/core/retrieval/corpus.py` | Add richer chunk metadata |
| `server/app/services/pdf_pipeline.py` | Store ingestion schema/version history |
| `server/app/core/retrieval/pdf_ingestion.py` | Improve metadata classification |
| `server/app/config/prompts.yaml` | Improve metadata tagger prompt |

### Chunking policy

- Keep self-help steps atomic when possible.
- Split long explanatory sections into smaller evidence units.
- Preserve worksheet tables as standalone chunks.
- Keep section headings attached to the chunk.

### Metadata policy

Each chunk should support at least:

- `topic`
- `subtopic`
- `action_type`
- `source_kind`
- `language`
- `section_title`
- `page_range`
- `confidence`
- `risk_level`
- `audience`

### Corpus selection consequence

This phase is where the corpus becomes good at supporting:

- coping steps,
- grounding exercises,
- thought restructuring,
- behavioral activation,
- problem solving,
- help-seeking guidance.

### Risks

- Over-fragmented chunks can lose context.
- Overlong chunks reduce retrieval precision.

### Exit criteria

- The corpus supports both explanation and action.
- Retrieval can prefer practical steps when needed.
- Chunk metadata is rich enough for evidence augmentation.

---

## 13. Phase 6 - Testing, Evaluation, and Rollout

### Objective

Verify that the new chat behavior is safer, more natural, and more grounded.

### Task Breakdown

1. Add regression coverage for crisis, diagnosis, medication, and prompt injection.
2. Add regression coverage for finals stress, vague distress, and harmless general chat.
3. Add evaluation sets for evidence-supported self-help and unsupported claim fallback.
4. Wire the rollout flags so each behavior layer can be enabled independently.
5. Define and run the release gates in order: contract, conversation, generation, retrieval, corpus, release.
6. Document rollback triggers and verify rollback can happen without database reversal.

### Files to revise

| File | Change |
|---|---|
| `tests/unit/...` | Add regression coverage |
| `server/app/evaluation/router_eval_set.py` | Add ambiguous and conversational cases |
| `server/app/evaluation/ragas_golden_set.py` | Add evidence-grounding cases |
| `server/app/evaluation/vie_sr_scorer.py` | Ensure uncertainty responses are handled correctly |
| `server/app/services/assistant.py` | Optionally gate rollout with config flags |

### Test matrix

- finals stress,
- vague distress,
- harmless general chat,
- evidence-supported self-help,
- unsupported claim fallback,
- diagnosis refusal,
- medication refusal,
- crisis short-circuit,
- prompt injection resistance.

### Rollout strategy

1. run contract tests first,
2. then routing tests,
3. then generation tests,
4. then retrieval-support tests,
5. then corpus tests,
6. then full chat eval.

### Exit criteria

- No safety regression.
- Better natural-language handling.
- Better grounded support behavior.
- Test coverage explicitly proves the new fallback logic.

---

## 14. Implementation Order

| Order | Phase | Reason |
|---|---|---|
| 1 | Phase 0 | Contracts must exist before behavior changes |
| 2 | Phase 1 | Understanding must improve before answer composition changes |
| 3 | Phase 2 | Natural response flow comes before retrieval polish |
| 4 | Phase 3 | Evidence augmentation depends on draft answers |
| 5 | Phase 4 | Uncertainty control depends on the new evidence structure |
| 6 | Phase 5 | Corpus quality must match the new response strategy |
| 7 | Phase 6 | Validation belongs after the behavioral changes land |

---

## 15. File-Level Change Map

| File | Phase(s) | Action |
|---|---|---|
| `server/app/services/assistant.py` | 0-6 | Revise |
| `server/app/core/agents/orchestrator.py` | 0-4 | Revise |
| `server/app/core/agents/response_planner.py` | 0-2 | Revise |
| `server/app/core/generation/generator.py` | 2-4 | Revise |
| `server/app/core/retrieval/evidence_gate.py` | 3-4 | Revise |
| `server/app/core/retrieval/hybrid_retriever.py` | 3 | Revise |
| `server/app/services/retrieval_debug.py` | 0-4 | Revise |
| `server/app/services/flows/topics.py` | 1 | Revise |
| `server/app/core/routing/continuity_router.py` | 1 | Revise |
| `server/app/models/schemas/chat.py` | 0-4 | Revise |
| `server/app/config/prompts.yaml` | 0-5 | Revise |
| `server/app/core/retrieval/ingestion/chunker.py` | 5 | Revise |
| `server/app/core/retrieval/corpus.py` | 5 | Revise |
| `server/app/core/retrieval/pdf_ingestion.py` | 5 | Revise |
| `server/app/services/pdf_pipeline.py` | 5 | Revise |
| `tests/unit/...` | 6 | Add |
| `server/app/evaluation/...` | 6 | Revise |

### Optional new modules only if decomposition is needed later

| File | Purpose |
|---|---|
| `server/app/core/generation/response_composer.py` | Separate final composition from draft generation |
| `server/app/core/agents/evidence_assessor.py` | Encapsulate graded evidence scoring |

These are optional. They should only be introduced if the revised `generator.py` or `evidence_gate.py` becomes too complex to maintain cleanly.

---

## 16. Definition of Done

The roadmap is complete when all of these are true:

- The assistant behaves like a normal AI chat first.
- Evidence is added when available, not forced when absent.
- The system can say `I do not have enough support for that exact point` without sounding broken.
- Safety refusal still works for diagnosis, medication, crisis, and injection cases.
- Chunking and corpus quality support both explanation and self-help.
- The full flow is measurable with tests and evaluation sets.

---

## 17. Enterprise Governance Model

### Objective

Ensure this roadmap is executed with clear ownership, approval gates, and change control.

### Governance layers

| Layer | Responsibility |
|---|---|
| Engineering owner | Owns implementation, code review, and technical decisions |
| Clinical owner | Reviews safety language, refusal behavior, and corpus suitability |
| Product owner | Prioritizes scope, sequencing, and release readiness |
| QA owner | Verifies regression coverage and acceptance criteria |
| Security/privacy owner | Reviews logging, retention, and user data handling |
| Academic reviewer | Confirms the corpus and methodology are appropriate for a capstone-level deliverable |

### Decision rights

- Safety policy changes require engineering + clinical approval.
- Schema changes require engineering + QA approval.
- Corpus source changes require engineering + clinical approval.
- Release approval requires product + QA + engineering sign-off.

### Change control rule

Any change that affects safety behavior, refusal wording, retrieval evidence display, or memory retention must be documented in the roadmap before implementation.

---

## 18. Dependency Graph

### Hard dependencies

| Upstream | Downstream |
|---|---|
| `ChatResponse` schema | UI, API contract, evaluation, persistence |
| `OrchestrationPlan` expansion | generator, retrieval strategy, clarifying behavior |
| topic expansion | routing, retrieval, corpus tagging |
| draft answer stage | evidence augmentation, hallucination control |
| chunk metadata revamp | retrieval quality, support labeling, source diagnostics |
| evidence status model | user-facing uncertainty, testing, evaluation |

### Critical path

1. Phase 0: contracts.
2. Phase 1: routing and topic understanding.
3. Phase 2: answer drafting.
4. Phase 3: evidence augmentation.
5. Phase 4: uncertainty control.
6. Phase 5: corpus revamp.
7. Phase 6: evaluation and rollout.

### Parallelizable workstreams

| Workstream | Can run in parallel with |
|---|---|
| Schema updates | prompt updates |
| Topic expansion | evaluation set design |
| Corpus metadata planning | retrieval debug updates |
| Test matrix definition | governance setup |

---

## 19. Workstream Model

The roadmap should be executed as four coordinated workstreams instead of one long linear task.

### Workstream A - Dialogue Intelligence

- orchestrator,
- topics,
- continuity routing,
- response planning.

### Workstream B - Generation And Safety

- answer generation,
- uncertainty handling,
- safety refusal preservation,
- fallback composition.

### Workstream C - Retrieval And Corpus

- hybrid retriever,
- evidence gating,
- chunking,
- corpus metadata,
- PDF ingestion.

### Workstream D - Validation And Release

- unit tests,
- eval sets,
- regression coverage,
- release gates,
- observability.

---

## 20. Enterprise Risk Register

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Over-refusal | High | Medium | Use graded evidence states and answer-first flow |
| Unsupported certainty | High | Medium | Enforce uncertainty composition and evidence status |
| Topic misclassification | Medium | Medium | Expand topics and add ambiguous fallback cases |
| Chunk fragmentation | Medium | Medium | Preserve atomic self-help steps and worksheet tables |
| Safety regression | Critical | Low | Keep safety as a hard short-circuit and add regression tests |
| User confusion from metadata | Medium | Low | Keep internal labels out of the user-facing response |
| Schema drift across layers | High | Medium | Update schema first and gate later phases on contract tests |
| Corpus quality mismatch | High | Medium | Restrict corpus to clinical, open, action-oriented PDFs |

### Risk policy

- Critical risks require explicit sign-off before merge.
- High risks require test coverage and rollback notes.
- Medium risks require documented mitigation.

---

## 21. Quality Gates

### Gate 1 - Contract gate

Pass criteria:

- new schema fields serialize correctly,
- no existing endpoint breaks,
- response payload remains backwards-compatible.

### Gate 2 - Conversation gate

Pass criteria:

- ordinary mental-health phrasing is classified correctly,
- ambiguous requests trigger clarification rather than false certainty,
- crisis input still short-circuits.

### Gate 3 - Generation gate

Pass criteria:

- the draft answer is coherent without retrieval,
- the final answer remains natural after evidence augmentation,
- uncertainty language appears only when justified.

### Gate 4 - Retrieval gate

Pass criteria:

- relevant chunks are retrieved for common self-help scenarios,
- support labels reflect actual contribution,
- weak evidence does not prevent a response.

### Gate 5 - Corpus gate

Pass criteria:

- chunk metadata is present and consistent,
- self-help steps are retrievable,
- corpus coverage is sufficient for the selected target topics.

### Gate 6 - Release gate

Pass criteria:

- all regression tests pass,
- no safety regressions detected,
- evaluation metrics meet target thresholds,
- rollback plan is documented.

---

## 22. Metrics And Success Criteria

### Product metrics

| Metric | Target |
|---|---|
| Naturalness of answer flow | High enough that the response reads like a normal AI assistant |
| Evidence usefulness | Retrieved sources improve answer quality when available |
| Confidence honesty | Unsupported claims are explicitly downgraded |
| Self-help actionability | The assistant gives practical next steps for common distress scenarios |

### Technical metrics

| Metric | Target |
|---|---|
| Safety precision | No regression in crisis, diagnosis, or medication refusal |
| Retrieval relevance | Relevant chunk selection improves on the baseline corpus |
| Latency | No major degradation from the added orchestration |
| Regression rate | Near-zero on critical safety and schema tests |

### Release success criteria

- The assistant can answer naturally without needing perfect retrieval.
- Retrieval improves useful answers instead of interrupting them.
- The user is never shown invented certainty.
- The product remains clinically bounded.

---

## 23. RACI Matrix

| Activity | Engineering | Clinical | Product | QA | Security |
|---|---|---|---|---|---|
| Schema and API contracts | R | C | C | A | C |
| Safety policy changes | R | A | C | C | C |
| Topic and routing expansion | R | C | A | C | I |
| Generator redesign | R | C | C | A | I |
| Retrieval and chunking changes | R | C | C | A | I |
| Corpus source selection | R | A | C | C | C |
| Evaluation and regression testing | R | C | C | A | I |
| Release approval | R | C | A | A | C |

Legend: R = Responsible, A = Accountable, C = Consulted, I = Informed.

---

## 24. Rollout Strategy

### Wave 1 - Internal validation

- Apply phases 0 and 1.
- Validate schema, routing, and topic understanding.
- Keep the user-visible flow mostly unchanged.

### Wave 2 - Conversation behavior upgrade

- Apply phase 2.
- Introduce answer-first generation.
- Verify that the assistant still feels coherent without retrieval.

### Wave 3 - Evidence augmentation

- Apply phase 3.
- Let retrieval support the answer rather than gate it.

### Wave 4 - Uncertainty and corpus hardening

- Apply phases 4 and 5.
- Improve confidence control and corpus utility.

### Wave 5 - Release hardening

- Apply phase 6.
- Run full evaluation and only then promote to production-like usage.

---

## 25. Final Enterprise Definition Of Done

This roadmap is enterprise-ready when the following are true:

- ownership is explicit,
- dependency order is explicit,
- risk handling is explicit,
- quality gates are explicit,
- rollout strategy is explicit,
- safety behavior remains non-negotiable,
- the assistant behaves naturally before evidence is added,
- retrieval improves answers instead of constraining them,
- the system can honestly express uncertainty,
- the corpus supports both information and self-help actions.

---

## 26. Exact Contracts And Normative Rules

### Normative language

In this document:

- `must` means non-negotiable implementation behavior.
- `should` means the recommended implementation default.
- `may` means optional only when explicitly stated.

### ChatRequest contract

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `message` | string | Yes | - | User input text |
| `session_id` | integer or null | No | null | Existing conversation reference |
| `new_session` | boolean | No | false | Forces a fresh session |
| `intake` | object | No | {} | Communication style and profile hints |
| `screening` | object | No | {} | Risk/screening context |
| `history` | array<object> | No | [] | Recent user/assistant turns |
| `personalization` | object | No | {} | Session preference signals |

### ChatResponse contract

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `session_id` | integer or null | Yes | null | Persisted session identifier |
| `status` | string | Yes | - | `grounded`, `clarification`, `crisis`, `refusal`, `off_domain`, `blocked`, `insufficient_evidence` |
| `route` | string | Yes | - | Topic or safety route |
| `intent` | string | Yes | - | Router intent label |
| `safety_mode` | string | Yes | `normal` | Safety policy mode |
| `summary` | string | Yes | - | Short internal outcome label |
| `answer` | string | Yes | - | Final user-facing answer |
| `follow_up` | array<string> | Yes | [] | Optional next-step prompts |
| `sources` | array<SourceReference> | Yes | [] | Evidence references |
| `retrieval_diagnostics` | array<RetrievalDiagnostic> | Yes | [] | Internal ranking diagnostics |
| `source_highlight` | string or null | No | null | Short source summary |
| `personalization_applied` | boolean | Yes | false | Whether profile signals were used |
| `personalization_signals` | array<string> | Yes | [] | Applied personalization tags |
| `context_used` | object | Yes | {} | Memory/intake/screening flags |
| `care_plan_hint` | string or null | No | null | Practical next-step hint |
| `clinical_nugget` | string or null | No | null | Single concise evidence insight |
| `confidence` | number | No | 0 | Range: 0.0 to 1.0 |
| `evidence_status` | string | No | `unsupported` | Enum: `well_supported`, `partially_supported`, `weakly_supported`, `unsupported` |
| `conversation_mode` | string | No | `answer` | Enum: `answer`, `explain`, `reflect`, `coach`, `clarify`, `crisis` |
| `draft_summary` | string | No | null | Short internal draft description |
| `supporting_chunks` | array<SourceReference> | No | [] | Max 3 items in UI display |
| `hallucination_guard` | object | No | {} | See guard contract below |

### HallucinationGuard contract

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `blocked_claims` | array<string> | Yes | [] | Claims removed from final answer |
| `downgraded_claims` | array<string> | Yes | [] | Claims kept but softened |
| `fallback_used` | boolean | Yes | false | Whether uncertainty fallback was applied |
| `reason` | string | Yes | `unknown` | Internal explanation string |

### SourceReference contract

| Field | Type | Required | Notes |
|---|---|---|---|
| `title` | string | Yes | Source title |
| `source` | string | Yes | Publisher or site |
| `topic` | string | Yes | Normalized topic label |
| `score` | number | Yes | Retrieval score |
| `excerpt` | string | Yes | Short evidence excerpt |
| `rank` | integer or null | No | Ordering position |
| `source_kind` | string or null | No | Example: `nimh`, `nhs`, `cci` |
| `language` | string or null | No | `en` or `tr` |
| `confidence` | number or null | No | Corpus confidence |
| `section` | string or null | No | Section heading |
| `page` | integer or null | No | Page number if available |
| `reason_tags` | array<string> | Yes | Support reasons |

### RetrievalDiagnostic contract

| Field | Type | Required | Notes |
|---|---|---|---|
| `rank` | integer | Yes | Display rank |
| `chunk_id` | string | Yes | Chunk identifier |
| `title` | string | Yes | Chunk title |
| `topic` | string | Yes | Chunk topic |
| `score` | number | Yes | Ranking score |
| `source_kind` | string or null | No | Source family |
| `language` | string or null | No | Language code |
| `confidence` | number or null | No | Chunk confidence |
| `topic_alignment` | string | Yes | `exact`, `related`, or `none` |
| `query_overlap` | integer | Yes | Shared token count |
| `reason_tags` | array<string> | Yes | Retrieval explanation tags |

### Contract rules

- Empty arrays must be returned as empty arrays, not null.
- Unknown optional values must be returned as null, not omitted inconsistently.
- The UI must not rely on raw confidence values as the primary user signal.

---

## 27. KPIs, Thresholds, and Acceptance Criteria

### Safety KPIs

| Metric | Target |
|---|---|
| Crisis recall | 100% on the curated crisis test set |
| Crisis false negative rate | 0% |
| Diagnosis refusal recall | 100% |
| Medication refusal recall | 100% |
| Prompt injection block rate | 100% |

### Conversation KPIs

| Metric | Target |
|---|---|
| Benign over-refusal rate | <= 3% on the benign test set |
| Clarification precision on ambiguous inputs | >= 85% |
| Conversation naturalness score | >= 4.2 / 5 in human review |
| User-follow-up usefulness score | >= 4.0 / 5 in human review |

### Retrieval KPIs

| Metric | Target |
|---|---|
| Top-3 relevant retrieval rate | >= 80% on supported queries |
| Evidence attachment success | >= 75% when corpus coverage exists |
| Unsupported claim leakage | 0 on golden-set evaluation |
| Partial-support honesty | >= 95% of partial-support cases labeled correctly |

### Performance KPIs

| Metric | Target |
|---|---|
| Non-LLM orchestration overhead P95 | <= 800 ms |
| Retrieval overhead P95 | <= 500 ms |
| Diagnostic serialization overhead | <= 100 ms |
| Total additional latency from roadmap features | <= 20% above current baseline |

### Acceptance criteria by phase

| Phase | Pass condition |
|---|---|
| Phase 0 | Schema contract is stable and backwards-compatible |
| Phase 1 | Natural language intent routing is materially better on test cases |
| Phase 2 | The assistant answers without retrieval dependency |
| Phase 3 | Retrieved evidence can support, soften, or leave the answer unchanged |
| Phase 4 | Confidence and unsupported-claim handling are correct |
| Phase 5 | Corpus supports both explanations and self-help steps |
| Phase 6 | All critical tests and release gates pass |

---

## 28. Rollout, Feature Flags, and Rollback

### Feature flags

These flags must exist before rollout:

| Flag | Default | Purpose |
|---|---|---|
| `CHAT_TWO_STAGE_GENERATION` | false | Enables draft then compose flow |
| `CHAT_EVIDENCE_AUGMENTATION` | false | Enables evidence injection into natural answers |
| `CHAT_UNCERTAINTY_LABELS` | false | Enables explicit confidence / support labeling |
| `CHAT_CORPUS_V2` | false | Switches to the updated corpus and chunk metadata |
| `CHAT_UI_SOURCE_DETAIL` | false | Shows compact source details in the UI |

### Rollout sequence

1. Internal dogfood only.
2. Limited pilot cohort.
3. Broader beta.
4. Full rollout after stable metrics.

### Suggested rollout gates

| Wave | Scope | Release gate |
|---|---|---|
| Wave 1 | Engineering + QA only | All contract tests pass |
| Wave 2 | Small pilot group | No safety regressions for 72 hours |
| Wave 3 | Larger beta group | No metric regression beyond thresholds |
| Wave 4 | General release | Full evaluation set passes |

### Rollback triggers

Rollback immediately if any of the following occur:

- crisis false negative appears,
- diagnosis or medication refusal regresses,
- unsupported claim leakage is detected,
- benign over-refusal exceeds target,
- P95 latency exceeds target by more than 30%,
- schema incompatibility breaks API responses.

### Rollback procedure

1. Disable `CHAT_UI_SOURCE_DETAIL`.
2. Disable `CHAT_UNCERTAINTY_LABELS`.
3. Disable `CHAT_EVIDENCE_AUGMENTATION`.
4. Disable `CHAT_TWO_STAGE_GENERATION`.
5. Keep `CHAT_CORPUS_V2` off until corpus validation is complete.
6. Re-run contract and safety tests before re-enabling any flag.

### Rollback rule

Rollback must be possible without database migration reversal and without changing the safety policy source of truth.

---

## 29. Corpus Procurement and Manifest Policy

### Corpus size targets

| Stage | Target |
|---|---|
| Minimum viable corpus | 24 PDFs |
| Enterprise target corpus | 40 PDFs |
| Recommended upper bound | 50 PDFs |

### Topic distribution target for the enterprise corpus

| Bucket | PDF count target | Example focus |
|---|---|---|
| Stress, anxiety, panic | 10 | Finals stress, generalized anxiety, panic symptoms, grounding |
| Depression, low mood, burnout, sleep | 10 | Behavioral activation, sleep hygiene, burnout recovery |
| Self-help skills and worksheets | 8 | Thought records, problem solving, self-esteem, coping plans |
| Trauma, PTSD, OCD | 5 | Trauma responses, intrusive thoughts, exposure concepts |
| Crisis, help-seeking, safety | 4 | Crisis lines, safety planning, support seeking |
| Serious presentations overview | 3 | Psychosis, bipolar, eating disorders |

### Source priority tiers

| Tier | Allowed sources | Priority |
|---|---|---|
| Tier 1 | NIMH, NHS, WHO, CDC, SAMHSA, VA, NCTSN, CCI | Highest |
| Tier 2 | Public university clinics and evidence-based health services | High |
| Tier 3 | Translated or local institutional handouts with clear provenance | Medium |
| Tier 4 | Commercial or unclear-license sources | Not preferred |

### Exclusion rules

Do not ingest:

- paywalled books,
- commercial workbooks without clear reuse rights,
- news articles,
- blogs,
- general lifestyle content,
- sources without clear provenance,
- duplicate PDFs that do not add a new topic or action type.

### Manifest contract

Each PDF entry must include:

- `title`
- `source_org`
- `source_url`
- `pdf_url`
- `language`
- `topic`
- `subtopic`
- `action_type`
- `audience`
- `risk_level`
- `include_in_index`
- `rationale`
- `license_notes`
- `publication_year`

### Corpus quality rules

- Every PDF must be traceable to a source organization.
- Every indexed PDF must have a rationale.
- Every chunk must map to one primary topic.
- Self-help PDFs are preferred over long textbooks.
- Safety PDFs must exist even if they are not the majority of the corpus.

### Chunking targets

| Chunk type | Target size |
|---|---|
| Self-help step | 180-350 tokens |
| Standard psychoeducation section | 300-500 tokens |
| Long clinical explanation | 500-800 tokens |
| Worksheet / table | atomic chunk |

### Overlap policy

- Default overlap: 50-80 tokens.
- Increase overlap only when a section boundary would otherwise break a step.

---

## 30. Frontend and API Consumption Contract

### UI display rules

The front-end must present the response in this order:

1. main answer,
2. short uncertainty banner only if needed,
3. compact source count,
4. expandable source details,
5. optional follow-up suggestions.

### UI rules

- Do not show raw confidence scores to the user.
- Do not show internal labels such as `supports` or `weakly_supported`.
- Show source details only when `sources.length > 0`.
- Show a safety banner immediately when `safety_mode != normal`.
- Show general-guidance wording when evidence is absent.

### API stability rules

- Existing clients must continue to work with the current required fields.
- New fields must be additive and optional where possible.
- Response arrays must remain predictable and stable in ordering.

### Human factors rules

- The UI must not increase cognitive load with technical jargon.
- Source transparency must stay compact and opt-in.
- Confidence and evidence should improve trust, not create noise.

---

## 31. Final Implementation Ready State

This document is fully implementation-ready when all of the following are true:

- all schema contracts are explicit,
- all metrics have thresholds,
- rollout and rollback are defined,
- corpus procurement has exact rules,
- frontend consumption is defined,
- phase dependencies are clear,
- and every critical behavior has a pass/fail criterion.

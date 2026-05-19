# Chat System Execution Matrix

**Purpose:** Short operational version of `docs/technical/CHAT_SYSTEM_PHASE_ROADMAP.md`.

Use this file during implementation. It only contains phases, tasks, tests, and expected outputs.

---

## Phase 0 - Contracts

### Tasks

- Extend `ChatResponse` with `confidence`, `evidence_status`, `conversation_mode`, `draft_summary`, `supporting_chunks`, `hallucination_guard`.
- Expand `OrchestrationPlan` with `retrieval_need`, `should_clarify`, `confidence`, `evidence_need`.
- Extend `ResponsePlan` with answer/support/uncertainty styles.
- Add prompt placeholders for draft answering and fallback behavior.
- Update retrieval diagnostics to explain support quality.

### Tests

- Schema serialization test.
- Default value test.
- Backward-compatibility test for existing API consumers.

### Expected output

- The API can carry richer chat state without breaking current clients.

---

## Phase 1 - Conversation Understanding

### Tasks

- Broaden `topics.py` for everyday mental-health phrasing.
- Revise `agents.brain_analysis` to return intent, topic, sentiment, urgency, evidence need, and clarification need.
- Restrict `continuity_router.py` to session carryover and episodic memory gating.
- Add `conversation_mode` selection in the orchestrator.
- Add ambiguous-input fallbacks for vague distress and mixed intent.

### Tests

- Finals stress routing test.
- Ambiguous distress test.
- English and Turkish natural-language routing test.
- Crisis short-circuit test.

### Expected output

- The system understands normal user phrasing before retrieval starts.

---

## Phase 2 - Natural Answer First

### Tasks

- Split generation into draft and final composition.
- Define draft fields: direct answer, key claims, confidence, safety sensitivity, follow-up needs.
- Update prompts so the draft is conversational and retrieval-independent.
- Update the final composer to inject evidence naturally.
- Add fallback composition when retrieval is weak or absent.

### Tests

- Natural answer without retrieval test.
- Natural answer with retrieval test.
- Conciseness test.

### Expected output

- The assistant answers like a normal AI first, not like a retrieval gate.

---

## Phase 3 - Evidence Augmentation

### Tasks

- Make the retriever search against draft claims and the raw user message.
- Add chunk support labels: `supports`, `partially_supports`, `background_only`, `not_used`.
- Separate retrieval into direct support, coping guidance, and background context.
- Update source diagnostics to explain why a source was selected.
- Make weak evidence lower confidence instead of blocking the answer.

### Tests

- Supported query retrieval test.
- Partially supported query test.
- Unsupported query fallback test.
- Support-label correctness test.

### Expected output

- Retrieved evidence augments the answer instead of replacing it.

---

## Phase 4 - Uncertainty Control

### Tasks

- Define evidence states: `well_supported`, `partially_supported`, `weakly_supported`, `unsupported`.
- Add guard metadata for blocked and downgraded claims.
- Soften or remove unsupported claims in final composition.
- Add user-facing fallback language for thin corpus coverage.

### Tests

- Unsupported-claim leakage test.
- Confidence wording test.
- Partial-support honesty test.

### Expected output

- The assistant stays helpful while being explicit about uncertainty.

---

## Phase 5 - Chunking and Corpus

### Tasks

- Preserve headings, worksheets, and self-help steps in chunking.
- Add corpus metadata: topic, subtopic, action type, audience, risk level, page tracking.
- Record schema and chunking version in ingestion history.
- Improve metadata classification for actionability.
- Enforce corpus procurement rules for source quality and provenance.

### Tests

- Chunk integrity test.
- Metadata completeness test.
- Corpus coverage test for coping, grounding, help-seeking, and psychoeducation.

### Expected output

- The corpus supports both explanation and self-help actions.

---

## Phase 6 - Testing and Rollout

### Tasks

- Add regression coverage for crisis, diagnosis, medication, and prompt injection.
- Add regression coverage for finals stress, vague distress, and harmless general chat.
- Add evaluation sets for evidence-supported self-help and unsupported fallback.
- Wire rollout flags for each behavior layer.
- Define release gates and rollback triggers.

### Tests

- Full safety regression suite.
- Routing regression suite.
- Generation regression suite.
- Retrieval regression suite.
- Corpus regression suite.

### Expected output

- The system is safe, natural, and grounded under controlled rollout.

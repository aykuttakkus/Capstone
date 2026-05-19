# Conversation Policy Roadmap

**Project:** Calma  
**Base analysis:** `docs/technical/CONVERSATION_POLICY_ARCHITECTURE_ANALYSIS.md`  
**Goal:** Integrate the conversation policy into the current codebase in a phased, testable, repo-specific way.

---

## 1. What This Roadmap Solves

The current assistant already has the right building blocks:

- intent analysis,
- safety gating,
- memory bundle assembly,
- retrieval gating,
- response planning,
- two-stage generation,
- observability and rollout.

The remaining problem is not the absence of components. The problem is **behavioral coordination**:

- the assistant sometimes asks when it should explain,
- it can feel templated,
- it can over-clarify,
- it can expose technical retrieval language,
- it can lose the user's emotional narrative,
- it needs a stricter mode policy.

This roadmap turns the policy analysis into implementation phases.

---

## 2. Architecture Principle

The system should not be governed by a single giant prompt.

Use a policy stack:

1. intent classification,
2. ambiguity detection,
3. memory selection,
4. evidence selection,
5. response mode selection,
6. style control,
7. safety short-circuiting,
8. evaluation and observability.

Important rule:

- **Explain-first** is not a separate top-level policy.
- It is the default behavior of the `explain` mode.
- **Clarify-last** is only allowed when ambiguity blocks a useful answer.
- **Question-budget = 1** is a hard response constraint.
- **Question only if ambiguity exists** is the gating rule.

---

## 3. Current Codebase Baseline

### Already implemented or partially implemented

| File | Current role |
|---|---|
| `server/app/services/assistant.py` | Main orchestration, memory bundle creation, retrieval, generation, logging |
| `server/app/core/agents/response_planner.py` | Picks conversation mode and question behavior |
| `server/app/core/agents/conversation_state.py` | Tracks agenda, resistance, and emotional momentum |
| `server/app/services/memory_context.py` | Builds selected memory bundle for prompt context |
| `server/app/core/generation/generator.py` | Builds draft, clarification, composed answers |
| `server/app/core/retrieval/hybrid_retriever.py` | Selective retrieval with draft claim boosting |
| `server/app/core/retrieval/evidence_gate.py` | Evidence sufficiency and support grading |
| `server/app/config/prompts.yaml` | Policy prompts, mode prompts, memory prompts, generation prompts |
| `server/app/services/memory_observability.py` | Structured memory observability reporting |
| `server/app/services/rollout.py` | Canary/full/off rollout decisions |

### Main gap

The code exists, but it needs a **clear behavior contract** that keeps answers from becoming template-like.

---

## 4. Design Rules For Calma

1. Use intent first, not response-first.
2. Use explain-first when the user wants understanding.
3. Use reflect-first when the user is sharing emotion.
4. Use clarify-last only if the answer would otherwise be unsafe, misleading, or too vague.
5. Ask at most one question per response.
6. Do not ask questions if the user is already asking for explanation.
7. Use memory only when relevant.
8. Use retrieval only when it improves the answer.
9. Keep the answer human-readable and non-technical.
10. Keep safety non-negotiable.

---

## 5. Phase 0 - Policy Contract Hardening

### Objective

Make the policy fields explicit and stable across the stack.

### Files to revise

| File | Change |
|---|---|
| `server/app/config/prompts.yaml` | Make `brain_analysis` output all policy fields consistently |
| `server/app/core/agents/response_planner.py` | Ensure mode, clarity, and question budget are first-class fields |
| `server/app/core/agents/conversation_state.py` | Add stronger ambiguity and intent confidence outputs |
| `server/app/core/generation/generator.py` | Keep mode-specific response generation isolated |

### Tasks

1. Normalize the JSON output from `brain_analysis` so every request returns:
   - `intent`
   - `topic`
   - `sentiment`
   - `plan`
   - `retrieval_need`
   - `evidence_need`
   - `conversation_mode`
   - `should_clarify`
   - `confidence`
2. Make `ResponsePlan` the single source of truth for response mode.
3. Add an explicit `question_budget` concept to the planner if not already present.
4. Make sure `clarify` mode is only returned when ambiguity truly blocks a useful answer.

### Tests

- policy JSON contract test,
- intent classification test,
- clarify gating test,
- question budget test,
- explain mode selection test.

### Done when

- policy fields are stable,
- no downstream layer has to guess mode behavior,
- each turn can be classified into a response policy deterministically.

---

## 6. Phase 1 - Intent-First Routing

### Objective

Make the assistant understand what the user wants before deciding how to answer.

### Files to revise

| File | Change |
|---|---|
| `server/app/core/agents/conversation_state.py` | Stronger intent and ambiguity signals |
| `server/app/core/agents/response_planner.py` | Map intent to `explain`, `reflect`, `coach`, `clarify`, `crisis` |
| `server/app/services/assistant.py` | Pass normalized intent state into generation and retrieval |
| `server/app/config/prompts.yaml` | Add policy language for intent-first decision making |

### Tasks

1. Classify whether the user is asking for:
   - explanation,
   - reflection,
   - practical coaching,
   - clarification,
   - safety support.
2. Distinguish “I don’t know” from “please explain.”
3. Distinguish emotional disclosure from knowledge request.
4. Distinguish vague distress from direct explanation request.
5. Give the planner an ambiguity score so it can decide whether to clarify.

### Tests

- `Explain loneliness` should map to `explain`.
- `I feel lonely` should map to `reflect`.
- `I don’t know` should not force repeated questioning.
- `I feel off lately` should trigger `clarify` only when needed.

### Done when

- the assistant stops asking unnecessary questions,
- explanation requests get explanations,
- ambiguity is handled only when truly needed.

---

## 7. Phase 2 - Memory-Driven Conversation Continuity

### Objective

Keep the conversation coherent across multiple messages without overloading the prompt.

### Files to revise

| File | Change |
|---|---|
| `server/app/services/memory_context.py` | Keep selected session history and memory items compact |
| `server/app/services/assistant.py` | Use memory bundle as an input policy layer |
| `server/app/services/session.py` | Keep session summary compaction stable |
| `server/app/core/agents/memory_agent.py` | Keep stable and episodic memory aligned with the user story |

### Tasks

1. Use the current session summary + recent turns + selected memory items together.
2. Keep the user's main emotional theme alive across turns.
3. Retain the current concern and open loop.
4. Remember what has already been explained to avoid repetition.
5. Track whether the user asked for explanation or clarification previously.

### Tests

- 5-6 turn follow-up should preserve context,
- emotional theme should persist across turns,
- repeated explanations should not cause prompt bloat.

### Done when

- the assistant can follow the narrative across turns,
- short-term context feels continuous,
- the user does not need to repeat themselves constantly.

---

## 8. Phase 3 - Explain-First, Clarify-Last

### Objective

Make the assistant explain first when the user wants understanding, and ask only when clarification is actually required.

### Files to revise

| File | Change |
|---|---|
| `server/app/core/generation/generator.py` | Adjust explain/reflect/clarify output strategy |
| `server/app/core/agents/response_planner.py` | Add stricter question budget logic |
| `server/app/config/prompts.yaml` | Encode explain-first, clarify-last, question-budget rules |

### Tasks

1. In `explain` mode, answer first and avoid questions unless essential.
2. In `clarify` mode, ask a single narrow question only.
3. In `reflect` mode, validate the user’s feeling before moving to guidance.
4. In `coach` mode, give one micro-step and avoid overloading the user.
5. In all modes, keep question count to one maximum.

### Tests

- explanation request should not receive a question-first reply,
- vague request should produce one clarification question at most,
- emotional disclosure should be mirrored before guidance,
- no mode should exceed question budget.

### Done when

- the user gets explanation when they ask for explanation,
- the assistant does not ask questions out of habit,
- question use is rare and justified.

---

## 9. Phase 4 - Style Control Without Template Feel

### Objective

Keep the assistant warm, flexible, and human without repeating the same phrasing.

### Files to revise

| File | Change |
|---|---|
| `server/app/config/prompts.yaml` | Add style policies per mode |
| `server/app/core/generation/generator.py` | Vary openings, transitions, and closings by mode |
| `server/app/core/agents/response_planner.py` | Add style hints such as `tone_plan` and `uncertainty_style` |

### Tasks

1. Remove repeated closing-question patterns.
2. Allow different openings for different modes.
3. Prefer plain language over technical RAG language.
4. Avoid rigid sentence templates.
5. Support multiple valid micro-patterns per mode.

### Tests

- repeated user asks should not yield identical phrasing,
- technical retrieval language should not leak into the final answer,
- tone should vary appropriately by mode.

### Done when

- responses feel less scripted,
- style adapts to context,
- the assistant does not sound like a fixed rubric.

---

## 10. Phase 5 - Retrieval Relevance And Evidence Policy

### Objective

Keep retrieval useful without forcing irrelevant sources into the answer.

### Files to revise

| File | Change |
|---|---|
| `server/app/core/retrieval/hybrid_retriever.py` | Keep retrieval conditional and context-aware |
| `server/app/core/retrieval/evidence_gate.py` | Make evidence support graded, not binary |
| `server/app/services/retrieval_debug.py` | Explain why a source was selected |
| `server/app/core/generation/generator.py` | Handle weak evidence gracefully |

### Tasks

1. Retrieve only if the answer is improved by evidence.
2. Rate chunk relevance by topic, intent, emotional fit, and direct answer fit.
3. Reject weak or forced sources from being the main answer basis.
4. If evidence is weak, keep the answer general and natural.
5. If evidence is absent, do not expose internal retrieval failure language.

### Tests

- direct-answer chunk should outrank weakly related chunk,
- weak source should not dominate answer,
- no source should be forced into an answer if it is not relevant.

### Done when

- RAG supports the response instead of constraining it,
- the assistant does not sound mechanically sourced,
- evidence remains a helper, not the whole conversation.

---

## 11. Phase 6 - Safety, Crisis, and Conversation Boundaries

### Objective

Keep the assistant clinically safe without breaking conversational flow.

### Files to revise

| File | Change |
|---|---|
| `server/app/core/safety/policy.py` | Keep crisis/diagnosis/medication/off-domain rules authoritative |
| `server/app/core/agents/safety_guardian.py` | Maintain structured safety analysis |
| `server/app/services/assistant.py` | Ensure safety short-circuit precedes retrieval/generation |
| `server/app/config/prompts.yaml` | Add mode rules for crisis handling |

### Tasks

1. Ensure crisis always short-circuits the normal flow.
2. Make diagnosis and medication refusals concise and safe.
3. Avoid over-escalation for ordinary coping requests.
4. Do not over-correct into safety mode when the user is just asking for explanation.

### Tests

- self-harm language should short-circuit,
- diagnosis request should refuse safely,
- medication request should refuse safely,
- ordinary explanation request should not be over-escalated.

### Done when

- safety is reliable,
- normal conversations are not over-blocked,
- crisis handling remains first priority.

---

## 12. Phase 7 - Evaluation And Observability

### Objective

Measure whether the policy actually improves the assistant.

### Files to revise

| File | Change |
|---|---|
| `server/app/services/memory_observability.py` | Keep memory selection visible in logs |
| `server/app/services/assistant.py` | Log memory and rollout decisions |
| `tests/unit/services/test_memory_observability.py` | Validate observability payload |
| `tests/integration/api/test_chat_api.py` | Add policy behavior regression cases |

### Tasks

1. Track whether intent was detected correctly.
2. Track whether the assistant explained before asking.
3. Track question count per response.
4. Track whether retrieval was relevant.
5. Track whether the assistant used a clear mode.
6. Track memory and rollout decisions.

### Tests

- clarification should be logged correctly,
- mode choice should be observable,
- memory selection should be visible in report,
- RAG relevance should be testable.

### Done when

- policy behavior is measurable,
- regressions can be seen in logs and tests,
- release quality can be judged objectively.

---

## 13. Phase 8 - Rollout And Tuning

### Objective

Introduce the new policy safely.

### Files to revise

| File | Change |
|---|---|
| `server/app/services/rollout.py` | Keep canary/full/off gating |
| `server/app/core/config.py` | Keep feature flags explicit |
| `server/app/services/assistant.py` | Honor rollout decision at runtime |

### Tasks

1. Roll out in stable -> canary -> full stages.
2. Keep a rollback path for policy regressions.
3. Tune the question budget and retrieval relevance threshold from live feedback.
4. Watch for template-like phrasing in logs and user feedback.

### Tests

- stable mode should be enabled by default,
- canary should respect traffic percentage,
- off mode should disable the rollout safely.

### Done when

- the policy can ship gradually,
- bad behavior can be turned off quickly,
- quality can be tuned without a rewrite.

---

## 14. Final Acceptance Criteria

This roadmap is complete when:

- explanation requests get explanations first,
- ambiguity triggers clarification only when needed,
- questions are capped at one,
- the assistant stays context-aware across turns,
- responses no longer sound like an ezber şablon,
- RAG is used only when it helps,
- safety always wins when needed,
- logs and tests show the policy is working.

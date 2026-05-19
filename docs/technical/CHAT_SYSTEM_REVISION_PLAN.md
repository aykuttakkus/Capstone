# Chat System Revision Plan

**Project:** Calma — Psychoeducational Mental Health Assistant  
**Goal:** Evolve the current chat stack into a natural, AI-like conversational system that can optionally ground answers in PDFs without becoming rigid, over-RAGged, or overly refusal-driven.

---

## 1. Current System Diagnosis

The current stack already has the right building blocks:

- `server/app/services/assistant.py` orchestrates chat, retrieval, memory, and persistence.
- `server/app/core/agents/orchestrator.py` decides intent, topic, safety mode, and whether to use RAG.
- `server/app/core/generation/generator.py` produces the final answer.
- `server/app/core/retrieval/evidence_gate.py` blocks weak evidence paths.
- `server/app/config/prompts.yaml` controls the tone and output shape.

However, the current behavior is too binary:

- If RAG is enabled, the system leans too quickly into evidence-first behavior.
- If evidence is weak, the response can collapse into an insufficiency message instead of staying conversational.
- The chat layer is not yet acting like a normal assistant that can answer first, then reinforce with evidence.
- The topic model is too narrow for real user phrasing like "I have finals exam stress" or mixed emotional input.

Target behavior:

- Understand the user like a normal assistant first.
- Answer naturally.
- Add source-backed support when available.
- Say when evidence is limited.
- Stop only for real safety issues.

---

## 2. Layer 1: Conversation Understanding And Routing

This layer decides what kind of chat moment we are in before any retrieval-heavy work starts.

### What stays

- Keep the current safety-first routing from `server/app/core/safety/policy.py`.
- Keep `SafetyGuardian` and the tiered crisis flow.
- Keep `HybridContinuityRouter` for continuation vs new topic handling.

### What changes

- Expand the router from only `intent + topic + use_rag` into a richer dialogue mode.
- Add a `conversation_mode` field with values like:
  - `answer`
  - `explain`
  - `reflect`
  - `coach`
  - `clarify`
  - `crisis`
- Make `topics.py` less keyword-only and more flexible for everyday phrasing.
- Stop treating all informational requests as automatic hard-RAG requests.

### Recommended behavior

- If the user says: "I have finals exam stress"
  - classify as stress/anxiety related
  - answer in a calm, normal assistant style
  - optionally add evidence-backed coping guidance
- If the user says: "I feel off lately"
  - classify as ambiguous distress
  - respond with empathy and a short clarifying question
- If the user says: "Do I have depression?"
  - route to diagnosis refusal
- If the user says something crisis-related
  - short-circuit to safety mode before any retrieval

### Implementation touchpoints

- `server/app/core/agents/orchestrator.py`
- `server/app/services/flows/topics.py`
- `server/app/core/routing/continuity_router.py`
- `server/app/config/prompts.yaml`

### Output contract

The router should return more than a boolean RAG decision. It should produce:

- `intent`
- `topic`
- `conversation_mode`
- `safety_mode`
- `retrieval_need`
- `confidence`
- `should_clarify`

---

## 3. Layer 2: Natural Answer First, Evidence Second

This is the key architectural change.

The assistant should draft a normal conversational answer first, then use retrieval to support or refine it.

### What stays

- Keep the current `AnswerGenerator`.
- Keep the current LLM backend.
- Keep structured prompt templates.

### What changes

- Split generation into two stages:
  1. `draft answer`
  2. `evidence-aware final answer`
- Do not force a refusal or insufficiency message just because retrieval was weak.
- Make the model produce a direct, human-like response even if no chunks are found.

### Draft output should include

The draft step should return structured internal fields such as:

- `direct_answer`
- `key_claims`
- `needs_evidence`
- `confidence`
- `safety_sensitive`
- `recommended_follow_up`

### Why this matters

This is how the assistant can behave like a real chat model while still being grounded.

- The user gets a usable response immediately.
- Retrieval becomes a support layer, not a hard dependency.
- The model can still answer when the corpus has no exact match.

### Implementation touchpoints

- `server/app/core/generation/generator.py`
- `server/app/utils/prompts.py`
- `server/app/config/prompts.yaml`

### Prompt strategy

Update prompts so the model is instructed to:

- answer naturally,
- avoid unsupported certainty,
- keep the tone conversational,
- ask at most one follow-up question when useful,
- not expose internal retrieval labels to the user.

---

## 4. Layer 3: Retrieval As Evidence Augmentation

Retrieval should enrich the answer, not dominate it.

### What stays

- Keep `HybridRetriever`.
- Keep FAISS/Qdrant optional backends.
- Keep topic-aware filtering.

### What changes

- Use retrieval on the draft answer and on key claims, not only on the raw user message.
- Retrieve chunks in three buckets:
  - direct support
  - related coping guidance
  - fallback educational context
- Add a support label per chunk:
  - `supports`
  - `partially_supports`
  - `background_only`
  - `not_used`

### Chunk requirements for this layer

Your chunking should support evidence augmentation, meaning chunks must be:

- section-aware,
- small enough to quote safely,
- tagged with topic/subtopic,
- tagged with action type,
- tagged with source type,
- tagged with audience and risk level.

Recommended chunk metadata:

- `topic`
- `subtopic`
- `action_type`
- `source_kind`
- `language`
- `page_range`
- `section_title`
- `confidence`

### Evidence insertion rule

Only insert source-grounded content when one of these is true:

- the chunk directly supports the claim,
- the chunk gives a matching self-help step,
- the chunk provides a safe general explanation.

If none of these are true, do not fake support.

### Implementation touchpoints

- `server/app/core/retrieval/hybrid_retriever.py`
- `server/app/core/retrieval/evidence_gate.py`
- `server/app/services/retrieval_debug.py`
- `server/app/models/schemas/chat.py`

---

## 5. Layer 4: Hallucination Control And Uncertainty Handling

This layer prevents the system from sounding overconfident when the corpus does not support a claim.

### What stays

- Keep safety refusal for diagnosis, medication, crisis, and prompt injection.
- Keep the no-clinical-claims policy.

### What changes

- Replace the current hard failure pattern with a graded confidence model.
- Add an internal `evidence_status` for every answer:
  - `well_supported`
  - `partially_supported`
  - `weakly_supported`
  - `unsupported`
- Add a user-facing uncertainty line when needed.

### Required fallback behavior

If the model cannot find support:

- answer in general terms,
- say the system does not have enough source-backed detail for that specific point,
- offer a safer nearby topic,
- never invent citations or pretend certainty.

### User-facing fallback examples

- "I can give you a general answer, but I do not have strong source-backed detail for that specific part."
- "I can still help with a practical coping step even if the corpus is thin on this exact case."
- "I have enough information for a general explanation, but not enough to make that claim confidently."

### Implementation touchpoints

- `server/app/core/retrieval/evidence_gate.py`
- `server/app/core/generation/generator.py`
- `server/app/core/agents/orchestrator.py`
- `server/app/models/schemas/chat.py`

### Core rule

No answer should fail just because evidence is thin. It should downgrade confidence, not usefulness.

---

## 6. Layer 5: How To Add This Into The Existing Codebase

This is the practical migration plan.

### Phase A — Extend the response schema

Add new fields to `ChatResponse`:

- `confidence`
- `evidence_status`
- `conversation_mode`
- `draft_summary`
- `supporting_chunks`
- `hallucination_guard`

### Phase B — Update the orchestrator

Refactor `Orchestrator.plan()` so it returns:

- richer dialogue mode,
- less rigid `use_rag` behavior,
- a confidence score,
- a clarifying-need flag.

### Phase C — Split generation into two steps

Refactor `AnswerGenerator` into:

- draft generation
- evidence augmentation
- final composition

### Phase D — Make retrieval sidecar-like

Retrieval should run as a support service for the answer, not as the thing that decides whether an answer exists.

### Phase E — Upgrade prompts

Revise `prompts.yaml` so it supports:

- normal conversational tone,
- brief explanations,
- self-help action steps,
- uncertainty language,
- safe fallback wording.

### Phase F — Add tests

Add tests for:

- normal chat with no evidence,
- normal chat with evidence,
- ambiguous emotional input,
- crisis short-circuit,
- unsupported claim fallback,
- diagnosis refusal,
- medication refusal.

### Recommended file order

1. `server/app/models/schemas/chat.py`
2. `server/app/core/agents/orchestrator.py`
3. `server/app/core/generation/generator.py`
4. `server/app/core/retrieval/evidence_gate.py`
5. `server/app/services/flows/topics.py`
6. `server/app/config/prompts.yaml`
7. `server/app/services/assistant.py`

### Definition of done

The revision is complete when:

- the assistant answers naturally without over-relying on retrieval,
- evidence is used when available,
- unsupported claims are downgraded, not invented,
- safety modes still short-circuit correctly,
- the user experience feels like a real AI chat with grounded support.

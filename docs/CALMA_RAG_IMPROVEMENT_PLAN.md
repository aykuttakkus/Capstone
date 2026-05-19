# Calma — RAG & Context Pipeline Improvement Plan

**Document type:** Technical Implementation Specification  
**Status:** Approved for implementation  
**Scope:** Backend generation pipeline, retrieval context, frontend rendering, test suite  
**Files affected:** 5 source files, 0 database migrations, 0 new modules  

---

## Executive Summary

The current Calma chat pipeline has four structural deficiencies that reduce response quality and increase latency. This document specifies the exact changes required to fix each deficiency, organized into four implementation phases. All changes are additive or subtractive — no new architecture is introduced.

| Phase | Title | Impact | Effort |
|---|---|---|---|
| 0 | Dead Code & Test Suite Cleanup | Low | Low |
| 1 | Conversation History & Session Context | High | Medium |
| 2 | RAG Direct Evidence (Remove Nuggetizer) | High | Low |
| 3 | Intake Signal Restoration | Medium | Low |
| 4 | Frontend Rendering Cleanup | Low | Low |

---

## Current System Diagnosis

### What the LLM Receives Today

Every user message triggers the following prompt assembly in `generator.py → _build_prompt()`:

```
[System Rules: "You are a PhD Clinical Psychologist..."]
[CLINICAL EVIDENCE: <single sentence from Nuggetizer>]
[Assessment: <PHQ-9/GAD-7 severity label or None>]
[User Sentiment: <label>]
[Key History: <long-term memory, max 200 characters>]

User Message: <current message only>

Output structure: (1)(2)(3)(4)(5)
```

### What Is Missing

| Signal | Available in code | Reaches LLM prompt |
|---|---|---|
| Last 2-3 conversation turns | ✅ `history` parameter | ❌ Never used |
| Current session rolling summary | ✅ `session.summary` | ❌ Passed in but not inserted |
| Intake preferences (style, goals) | ✅ `intake` dict | ❌ `intake=None` hardcoded |
| Full RAG chunk content | ✅ `retrievals` list | ❌ Compressed to 1 sentence |

### Latency Cost of Current Architecture

```
Request received
  ├─ Orchestrator LLM call         ~5-10s
  ├─ Retrieval + Reranker           ~1-2s
  ├─ Nuggetizer LLM call           ~5-10s   ← unnecessary second LLM call
  └─ Generator LLM call            ~5-10s
                                  ─────────
Total                              ~16-32s
```

After Phase 2, the Nuggetizer call is eliminated:

```
Request received
  ├─ Orchestrator LLM call         ~5-10s
  ├─ Retrieval + Reranker           ~1-2s
  └─ Generator LLM call            ~5-10s
                                  ─────────
Total                              ~11-22s   (~35% latency reduction)
```

---

## Phase 0 — Dead Code & Test Suite Cleanup

### Problem Statement

Several structural problems exist that are not blocking today but will cause runtime errors or test failures the moment Phase 2 lands:

1. **`generator.py` dead code** — `compose_memory_context` is imported but never called. `_excerpt()` is defined but never called. Parameters `planner`, `profile_snapshot`, `mood_summary`, `journal_summary` are accepted by `_build_prompt()` but never used inside it.
2. **`build_insufficient("general")` wrong message** — The original user-reported bug: follow-up questions like _"How exactly can I do that?"_ resolve to `topic="general"` when history is missing. `build_insufficient("general")` returns the hardcoded string _"I can give you a general psychoeducational overview. What would you like to understand more specifically?"_ — a cold, non-therapeutic response that ignores conversation context.
3. **Test suite stale fixtures** — `test_assistant_service_reranks_retrievals_before_nuggetization` asserts `service.nuggetizer.last_retrieval_ids == ["first", "second"]`. After Phase 2 removes the nuggetizer call, this assertion will fail. `build_service()` also sets `service.grader` and `service.sentiment_agent` — attributes that do not exist in `AssistantService` and are never used.

### Changes Required

#### File: `server/app/core/generation/generator.py`

**Remove unused import**

```python
# REMOVE this line (line 11)
from server.app.services.session import compose_memory_context
```

**Remove unused `_excerpt()` function**

```python
# REMOVE these lines (lines 16-18, before the GeneratedPayload dataclass)
def _excerpt(content: str, max_sentences: int = 2) -> str:
    sentences = split_sentences(content)
    return " ".join(sentences[:max_sentences])
```

**Remove unused parameters from `_build_prompt()` signature**

The parameters `planner`, `profile_snapshot`, `mood_summary`, `journal_summary` are passed in but the function body never reads them. Remove them from the signature:

```python
# BEFORE (in _build_prompt signature)
    planner: ResponsePlan | None = None,
    profile_snapshot: str | None = None,
    mood_summary: str | None = None,
    journal_summary: str | None = None,

# AFTER — remove all four lines above
```

Also remove the unused `ResponsePlan` import once `planner` is gone:

```python
# REMOVE this import (no longer needed after planner parameter removed)
from server.app.core.agents.response_planner import ResponsePlan
```

**Fix `build_insufficient("general")` — replace the cold fallback with an empathetic redirect**

```python
# BEFORE
def build_insufficient(self, topic: str, intent_label: str) -> GeneratedPayload:
    if topic == "general":
        return GeneratedPayload(
            status="general_fallback",
            answer=(
                "I can give you a general psychoeducational overview. "
                "What would you like to understand more specifically?"
            ),
            summary=intent_label,
            follow_up=[
                "Ask about stress",
                "Ask about anxiety",
                "Ask about burnout or sleep",
            ],
            route="topic:general",
        )
```

```python
# AFTER
def build_insufficient(self, topic: str, intent_label: str) -> GeneratedPayload:
    if topic == "general":
        return GeneratedPayload(
            status="general_fallback",
            answer=(
                "It sounds like you're looking for something specific — "
                "I want to make sure I give you a useful answer. "
                "Could you tell me a bit more about what's on your mind, "
                "whether it's related to stress, anxiety, low mood, or something else?"
            ),
            summary=intent_label,
            follow_up=[
                "Tell me more about what's been on your mind",
                "Ask about stress or anxiety",
                "Ask about burnout or sleep difficulties",
            ],
            route="topic:general",
        )
```

> **Why this matters:** When a user sends a follow-up like _"How exactly can I do that?"_ with no prior history in the prompt, the orchestrator infers `topic="general"` because there is no subject in the message. The evidence gate then fails because there are no strong general-topic chunks. Without Phase 1 (history), this path will still sometimes be hit — the answer must be therapeutic, not a system error message.

#### File: `tests/unit/services/test_assistant_service.py`

**Remove `FakeNuggetizer` class** (will no longer be referenced after Phase 2)

```python
# REMOVE this entire class
class FakeNuggetizer:
    def __init__(self) -> None:
        self.last_query: str | None = None
        self.last_retrieval_ids: list[str] = []

    async def nuggetize(self, query: str, retrievals):
        self.last_query = query
        self.last_retrieval_ids = [item.chunk.id for item in retrievals]
        return ""
```

**Remove stale attributes from `build_service()`**

```python
# BEFORE
def build_service(*, plan: FakePlan, retrievals, grader_flags, llm_backend):
    service = AssistantService.__new__(AssistantService)
    service.knowledge_base = None
    service.embedder = None
    service.faiss_store = None
    service.retriever = FakeRetriever(retrievals)
    service.evidence_gate = EvidenceGate(min_score=0.22, min_chunks=1)
    service.generator = AnswerGenerator(llm_client=llm_backend)
    service.orchestrator = FakeOrchestrator(plan)
    service.grader = FakeGrader(grader_flags)       # ← does not exist in AssistantService
    service.sentiment_agent = FakeSentimentAgent()  # ← does not exist in AssistantService
    service.memory_agent = FakeMemoryAgent()
    service.supervisor = FakeSupervisor()
    service.nuggetizer = FakeNuggetizer()           # ← to be removed in Phase 2
    service.reranker = FakeReranker()
    service.audit_logger = FakeAuditLogger()
    return service
```

```python
# AFTER
def build_service(*, plan: FakePlan, retrievals, llm_backend):
    service = AssistantService.__new__(AssistantService)
    service.knowledge_base = None
    service.embedder = None
    service.faiss_store = None
    service.retriever = FakeRetriever(retrievals)
    service.evidence_gate = EvidenceGate(min_score=0.22, min_chunks=1)
    service.generator = AnswerGenerator(llm_client=llm_backend)
    service.orchestrator = FakeOrchestrator(plan)
    service.memory_agent = FakeMemoryAgent()
    service.supervisor = FakeSupervisor()
    service.reranker = FakeReranker()
    service.audit_logger = FakeAuditLogger()
    return service
```

> All call sites pass `grader_flags=[...]` — remove that keyword argument from every `build_service(...)` call in the file (5 occurrences).

**Rewrite `test_assistant_service_reranks_retrievals_before_nuggetization`**

The test name, fixture, and assertion all reference the nuggetizer. Rename it to verify reranking behaviour directly via the response and source order instead.

```python
# BEFORE
async def test_assistant_service_reranks_retrievals_before_nuggetization(
    db_session_factory,
    authenticated_user,
    mock_llm_backend,
) -> None:
    service = build_service(
        plan=FakePlan(...),
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
        response = await service.handle_message(...)

        assert response.status == "grounded"
        assert service.nuggetizer.last_retrieval_ids == ["first", "second"]  # ← broken after Phase 2
```

```python
# AFTER
async def test_assistant_service_reranks_retrievals_before_generation(
    db_session_factory,
    authenticated_user,
    mock_llm_backend,
) -> None:
    """Reranker should surface top-2 chunks in score order before generation."""
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
        # After reranking top-2, source IDs should be the two highest-scored chunks
        source_ids = [s.chunk_id for s in response.sources]
        assert "first" in source_ids
        assert "second" in source_ids
        assert "third" not in source_ids
```

**Remove `FakeGrader` class** (no longer referenced)

```python
# REMOVE this entire class
class FakeGrader:
    def __init__(self, flags):
        self._flags = flags

    def grade_batch(self, message: str, retrievals):
        return list(self._flags)
```

### Acceptance Criteria

- [ ] `generator.py` has no unused imports (`compose_memory_context` removed)
- [ ] `generator.py` has no unreachable functions (`_excerpt` removed)
- [ ] `_build_prompt()` signature has no parameters that the body never reads (`planner`, `profile_snapshot`, `mood_summary`, `journal_summary` removed)
- [ ] Follow-up with `topic="general"` returns an empathetic redirect, not a generic overview prompt
- [ ] All tests pass: `pytest tests/unit/services/test_assistant_service.py`
- [ ] No `AttributeError` for `service.nuggetizer` after Phase 2

---

## Phase 1 — Conversation History & Session Context

### Problem Statement

When a user sends a follow-up message such as _"How exactly can I do that?"_, the system has no knowledge of what _"that"_ refers to. The `history` list arrives in `handle_message()` but is never forwarded to the generator. Similarly, `session.summary` — a rolling text summary updated after every turn — is passed to `build_grounded()` as `session_memory` but `_build_prompt()` never inserts it into the prompt.

### Target Prompt Structure After Fix

```
[System Rules]
[Evidence 1]: "..."     ← from RAG (Phase 2)
[Evidence 2]: "..."     ← from RAG (Phase 2)
[Assessment: moderate]
[User Sentiment: anxious]

[Session Context: Topic: stress_anxiety. Intent: educational_request. Last response: ...]
[Recent Conversation:
  User: I have stress and anxiety, I have finals this Friday
  User: I want to understand how to calm myself down]
[Long-term Memory: User has mentioned exam stress before. Breathing exercises discussed.]

User Message: How exactly can I do that?
```

The LLM now knows "that" = calming down techniques discussed in the previous turn.

### Changes Required

#### File: `server/app/core/generation/generator.py`

**1. Add `history` and `session_memory` to `_build_prompt()` signature**

```python
# BEFORE
def _build_prompt(
    self,
    message: str,
    topic: str,
    retrievals: list[ScoredChunk],
    intent_label: str,
    clinical_nugget: str | None = None,
    screening: dict[str, str | int | bool] | None = None,
    sentiment: SentimentProfile | None = None,
    session_memory: str | None = None,   # ← received but never used
    memory: str | None = None,
    planner: ResponsePlan | None = None,
    profile_snapshot: str | None = None,
    mood_summary: str | None = None,
    journal_summary: str | None = None,
) -> str:
    context_block = f"\n[CLINICAL EVIDENCE: {clinical_nugget}]" if clinical_nugget else ""
    system_rules = render_prompt("generation.answer_system_rules")
    screening_info = f"\n[Assessment: {screening.get('severity') if screening else 'None'}]"
    sentiment_info = f"\n[User Sentiment: {sentiment.label if sentiment else 'Neutral'}]"
    memory_info = f"\n[Key History: {memory[:200] if memory else ''}]"

    return "\n\n".join(
        [
            system_rules + context_block + screening_info + sentiment_info + memory_info,
            f"User Message: {message}",
            render_prompt("generation.answer_output_format"),
        ]
    )
```

```python
# AFTER
def _build_prompt(
    self,
    message: str,
    topic: str,
    retrievals: list[ScoredChunk],
    intent_label: str,
    screening: dict[str, str | int | bool] | None = None,
    sentiment: SentimentProfile | None = None,
    session_memory: str | None = None,
    memory: str | None = None,
    history: list[dict[str, str]] | None = None,
    planner: ResponsePlan | None = None,
    profile_snapshot: str | None = None,
    mood_summary: str | None = None,
    journal_summary: str | None = None,
) -> str:
    system_rules = render_prompt("generation.answer_system_rules")

    # Evidence block — built from raw chunks (Phase 2 replaces clinical_nugget here)
    context_block = self._format_evidence(retrievals)

    # Screening & sentiment signals
    screening_info = f"\n[Assessment: {screening.get('severity') if screening else 'None'}]"
    sentiment_info = f"\n[User Sentiment: {sentiment.label if sentiment else 'Neutral'}]"

    # Session context: rolling summary of current session
    session_info = f"\n[Session Context: {session_memory.strip()}]" if session_memory else ""

    # Recent conversation: last 2 user turns from history
    recent_info = ""
    if history:
        user_turns = [
            h.get("content", "").strip()
            for h in history
            if h.get("role") == "user" and h.get("content", "").strip()
        ]
        if user_turns:
            recent_lines = "\n  ".join(
                f'User: "{t[:120]}"' for t in user_turns[-2:]
            )
            recent_info = f"\n[Recent Conversation:\n  {recent_lines}]"

    # Long-term cross-session memory
    memory_info = f"\n[Long-term Memory: {memory[:200]}]" if memory else ""

    context = (
        system_rules
        + context_block
        + screening_info
        + sentiment_info
        + session_info
        + recent_info
        + memory_info
    )

    return "\n\n".join(
        [
            context,
            f"User Message: {message}",
            render_prompt("generation.answer_output_format"),
        ]
    )
```

**2. Add `history` to `build_grounded()` signature and forward it**

```python
# BEFORE
def build_grounded(
    self,
    message: str,
    topic: str,
    retrievals: list[ScoredChunk],
    intent_label: str,
    clinical_nugget: str | None = None,   # ← remove
    screening: dict[str, str | int | bool] | None = None,
    sentiment: SentimentProfile | None = None,
    session_memory: str | None = None,
    memory: str | None = None,
    planner: ResponsePlan | None = None,
    profile_snapshot: str | None = None,
    mood_summary: str | None = None,
    journal_summary: str | None = None,
) -> GeneratedPayload:
```

```python
# AFTER
def build_grounded(
    self,
    message: str,
    topic: str,
    retrievals: list[ScoredChunk],
    intent_label: str,
    screening: dict[str, str | int | bool] | None = None,
    sentiment: SentimentProfile | None = None,
    session_memory: str | None = None,
    memory: str | None = None,
    history: list[dict[str, str]] | None = None,  # ← new
    planner: ResponsePlan | None = None,
    profile_snapshot: str | None = None,
    mood_summary: str | None = None,
    journal_summary: str | None = None,
) -> GeneratedPayload:
    llm_result = self.llm_client.generate(
        self._build_prompt(
            message,
            topic,
            retrievals,
            intent_label,
            screening=screening,
            sentiment=sentiment,
            session_memory=session_memory,
            memory=memory,
            history=history,          # ← new
            planner=planner,
            profile_snapshot=profile_snapshot,
            mood_summary=mood_summary,
            journal_summary=journal_summary,
        )
    )
```

#### File: `server/app/services/assistant.py`

**Forward `history` to `build_grounded()`**

```python
# BEFORE
payload = self.generator.build_grounded(
    message=message,
    topic=plan.topic,
    retrievals=retrievals,
    intent_label=plan.intent,
    clinical_nugget=clinical_nugget,     # ← remove
    screening=screening,
    sentiment=sentiment,
    session_memory=session.summary,
    memory=memory_context,
    planner=planner,
    profile_snapshot=profile_snapshot,
    mood_summary=mood_summary,
    journal_summary=journal_summary,
)
```

```python
# AFTER
payload = self.generator.build_grounded(
    message=message,
    topic=plan.topic,
    retrievals=retrievals,
    intent_label=plan.intent,
    screening=screening,
    sentiment=sentiment,
    session_memory=session.summary,
    memory=memory_context,
    history=history,                     # ← new
    planner=planner,
    profile_snapshot=profile_snapshot,
    mood_summary=mood_summary,
    journal_summary=journal_summary,
)
```

### Acceptance Criteria

- [ ] Follow-up message "How exactly can I do that?" returns a response that references the previous topic (deep breathing / calming)
- [ ] `[Recent Conversation]` block appears in DEBUG prompt log when `history` is non-empty
- [ ] `[Session Context]` block appears in DEBUG prompt log after the first turn

---

## Phase 2 — RAG Direct Evidence (Remove Nuggetizer)

### Problem Statement

The `RAGNuggetizer` compresses three retrieved chunks into a single sentence using a separate LLM call. This introduces 5-10 seconds of additional latency and discards most of the retrieved evidence. The generator then receives one decontextualized sentence instead of the actual source content.

The compressed nugget is also returned in `ChatResponse.clinical_nugget` and rendered as a separate `<blockquote>` in the frontend, visually disconnected from the answer text.

### Solution

Pass the top-2 chunk excerpts directly to the generator prompt. The generation LLM — already instructed to produce a clinical insight in the middle of its response — will incorporate the evidence organically.

### Changes Required

#### File: `server/app/core/generation/generator.py`

**Add `_format_evidence()` static method**

```python
# ADD this method to AnswerGenerator class

@staticmethod
def _format_evidence(retrievals: list[ScoredChunk], max_chunks: int = 2) -> str:
    """Format top-N chunk excerpts as labelled evidence blocks for the prompt."""
    if not retrievals:
        return ""
    lines = []
    for i, r in enumerate(retrievals[:max_chunks], 1):
        excerpt = r.chunk.content[:220].strip()
        # Normalize whitespace
        excerpt = " ".join(excerpt.split())
        lines.append(f"[Evidence {i}]: {excerpt}")
    return "\n" + "\n".join(lines)
```

**Remove `clinical_nugget` from `_build_prompt()`, use `_format_evidence()` instead**

```python
# BEFORE (in _build_prompt)
context_block = f"\n[CLINICAL EVIDENCE: {clinical_nugget}]" if clinical_nugget else ""

# AFTER (in _build_prompt)
context_block = self._format_evidence(retrievals)
```

#### File: `server/app/services/assistant.py`

**Remove Nuggetizer import**

```python
# REMOVE this line (top of file)
from server.app.core.retrieval.nuggetizer import nuggetizer
```

**Remove Nuggetizer from `__init__`**

```python
# REMOVE this line (in AssistantService.__init__)
self.nuggetizer = nuggetizer
```

**Remove Nuggetizer call from `handle_message()`**

```python
# REMOVE these lines entirely (currently inside `if plan.use_rag:` block)
clinical_nugget = ""

# 4. Corrective RAG (CRAG) - Simplified (Grader removed to fix timeout)
if retrievals:
    print(f"[DEBUG] {time.time() - start_time:.2f}s: Starting Nuggetizer")
    clinical_nugget = await self.nuggetizer.nuggetize(personalized_query.retrieval_query, retrievals)
    print(f"[DEBUG] {time.time() - start_time:.2f}s: Nuggetizer finished")
```

**Remove `clinical_nugget` from the `build_grounded()` call** (covered in Phase 1 AFTER block above)

**Remove `clinical_nugget` from BOTH `ChatResponse` return statements in `handle_message()`**

`assistant.py` has two separate `return ChatResponse(...)` calls inside `handle_message()`. The `clinical_nugget` variable must be removed from both:

```python
# OCCURRENCE 1 — early return after Evidence Gate fails (around line 329)
# BEFORE
return ChatResponse(
    session_id=session.id,
    ...
    # clinical_nugget is NOT present here — already correct, no change needed
    care_plan_hint="Shift toward general psychoeducation or add more personal context.",
)

# OCCURRENCE 2 — final return after successful generation (around line 411)
# BEFORE
return ChatResponse(
    session_id=session.id,
    ...
    clinical_nugget=clinical_nugget,   # ← REMOVE this line
    sources=self._source_models(message, retrievals, plan.topic),
    ...
)

# AFTER
return ChatResponse(
    session_id=session.id,
    ...
    # clinical_nugget omitted — field defaults to None in schema for backwards compat
    sources=self._source_models(message, retrievals, plan.topic),
    ...
)
```

> **Note:** Occurrence 1 (Evidence Gate return) already does NOT pass `clinical_nugget` — no change needed there. Only Occurrence 2 (the final success return, approximately line 420) carries the field and must be updated.

#### File: `client/src/App.jsx`

**Remove blockquote rendering (lines 1390-1394)**

```jsx
// REMOVE this block entirely
{msg.data?.clinical_nugget && (
  <blockquote className="ai-insight animate-slide-up">
    {msg.data.clinical_nugget}
  </blockquote>
)}
```

> **Note:** `clinical_nugget: str | None = None` remains in `ChatResponse` schema for backwards compatibility with any existing API consumers. It will simply always be `None` after this change.

### Before / After: Prompt Evidence Section

**Before:**
```
[CLINICAL EVIDENCE: The ability to address the fear of negative evaluation is the best predictor for better managing social anxiety.]
```

**After:**
```
[Evidence 1]: When we experience anxiety about performance, the brain's threat response activates the hypothalamic-pituitary-adrenal axis, raising cortisol levels that impair working memory and focus.
[Evidence 2]: Breaking large tasks into smaller, time-bounded steps has been shown to reduce state anxiety by restoring the perception of control over outcomes.
```

### Acceptance Criteria

- [ ] Response time decreases by at least 5 seconds on average (Nuggetizer LLM call eliminated)
- [ ] No italic blockquote appears below the assistant response in the UI
- [ ] The assistant response contains clinical references woven into the answer text naturally
- [ ] `clinical_nugget` in API response is `null`
- [ ] No import errors — `nuggetizer` fully removed from `assistant.py`

---

## Phase 3 — Intake Signal Restoration

### Problem Statement

The intake form collects user preferences including `communication_style`, `help_type`, `main_issue`, and `response_length_preference`. These signals are available in `handle_message()` as the `intake` dict. However, the Orchestrator call hardcodes `intake=None`:

```python
# server/app/services/assistant.py — line 168
plan = self.orchestrator.plan(message, intake=None)
# Comment reads: "Force ignoring intake to prevent bias"
```

This means:
1. Topic inference (`infer_topic`) cannot use `main_issue` to resolve ambiguous topics
2. The generator prompt contains no user preference information

### Changes Required

#### File: `server/app/services/assistant.py`

**Restore intake to Orchestrator call**

```python
# BEFORE
# 1. Agentic Orchestration - Force ignoring intake to prevent bias as requested
print(f"[DEBUG] {time.time() - start_time:.2f}s: Starting Orchestrator (Intake Ignored)")
plan = self.orchestrator.plan(message, intake=None)

# AFTER
# 1. Agentic Orchestration
print(f"[DEBUG] {time.time() - start_time:.2f}s: Starting Orchestrator")
plan = self.orchestrator.plan(message, intake=intake)
```

#### File: `server/app/core/generation/generator.py`

**Add intake preference hint to `_build_prompt()`**

Add `intake: dict | None = None` parameter and insert a preference line when signals are present:

```python
# ADD to _build_prompt() signature
intake: dict | None = None,

# ADD inside _build_prompt() body, before building context string
intake_hint = ""
if intake:
    style = intake.get("communication_style", "").replace("_", " ").lower()
    help_type = intake.get("help_type", "").replace("_", " ").lower()
    length_pref = intake.get("response_length_preference", "").replace("_", " ").lower()
    parts = [p for p in [style, help_type, length_pref] if p]
    if parts:
        intake_hint = f"\n[User Preference: {', '.join(parts)}]"
```

```python
# UPDATE context assembly to include intake_hint
context = (
    system_rules
    + context_block
    + screening_info
    + sentiment_info
    + intake_hint          # ← new
    + session_info
    + recent_info
    + memory_info
)
```

**Forward `intake` from `build_grounded()` to `_build_prompt()`**

```python
# ADD to build_grounded() signature
intake: dict | None = None,

# ADD to _build_prompt() call inside build_grounded()
intake=intake,
```

#### File: `server/app/services/assistant.py`

**Forward `intake` to `build_grounded()`**

```python
# ADD to the build_grounded() call
payload = self.generator.build_grounded(
    ...
    intake=intake,    # ← new
    ...
)
```

### Final Prompt Shape (All Phases Combined)

```
You are a PhD Clinical Psychologist.

STRICT OPERATIONAL LIMITS:
- MAXIMUM 3 SHORT SENTENCES PER RESPONSE.
...

[Evidence 1]: When we experience anxiety about performance...
[Evidence 2]: Breaking large tasks into smaller steps...
[Assessment: moderate]
[User Sentiment: anxious]
[User Preference: warm and gentle, emotional support, balanced]
[Session Context: Topic: stress_anxiety. Intent: educational_request. Last response: ...]
[Recent Conversation:
  User: "I have stress and anxiety, I have finals this Friday"
  User: "I want to understand how to calm myself down"]
[Long-term Memory: User mentioned exam stress before.]

User Message: How exactly can I do that?

Output structure:
(1) Empathetic reflection...
(2) A single, brief clinical insight...
(3) A Socratic bridge...
(4) A single open-ended question...
(5) Minimal source citations...
```

### Acceptance Criteria

- [ ] User with `communication_style: Warm_and_Gentle` receives warmer phrasing
- [ ] User with `help_type: Practical_Coping_Steps` receives action-oriented responses
- [ ] `[User Preference]` block appears in DEBUG prompt log when intake is present
- [ ] Topic inference correctly resolves `main_issue: Anxiety_Worry_or_Panic` → `stress_anxiety`

---

## Phase 4 — Frontend Rendering Cleanup

### Problem Statement

The `clinical_nugget` field is rendered as a `<blockquote>` element directly below the assistant message, visually separated from the response text and styled in italic. After Phase 2, this field will always be `null`. The rendering block must be removed to avoid an empty UI gap.

Additionally, the CSS class `.ai-insight` can be removed from `index.css` as it will have no remaining references.

### Changes Required

#### File: `client/src/App.jsx`

**Remove the clinical nugget blockquote block**

```jsx
// REMOVE — lines 1390 to 1394
{msg.data?.clinical_nugget && (
  <blockquote className="ai-insight animate-slide-up">
    {msg.data.clinical_nugget}
  </blockquote>
)}
```

No replacement needed. The answer text (`msg.content`) already contains the full response including evidence.

#### File: `client/src/index.css`

**Remove `.ai-insight` styles**

```css
/* REMOVE — locate and delete the .ai-insight ruleset */
.ai-insight {
  /* ... all rules ... */
}
```

### Acceptance Criteria

- [ ] No blockquote or italic quote appears below any assistant message
- [ ] UI layout has no empty gap between the message text and the sources footer
- [ ] Browser console shows no React warnings about undefined `clinical_nugget`

---

## Implementation Order

Phases are independent but should be applied in sequence to simplify review.

```
Phase 0  →  generator.py (remove compose_memory_context import, _excerpt fn, unused params)
         →  generator.py (fix build_insufficient "general" fallback message)
         →  test_assistant_service.py (remove FakeNuggetizer, FakeGrader, stale attrs)
         →  test_assistant_service.py (rewrite reranks test, remove grader_flags arg)

Phase 1  →  generator.py (_build_prompt + build_grounded: add history, session_memory)
         →  assistant.py (history forwarding to build_grounded)

Phase 2  →  generator.py (_format_evidence, remove clinical_nugget param)
         →  assistant.py (remove nuggetizer import, __init__ attr, nuggetize call, variable)
         →  assistant.py (remove clinical_nugget from final ChatResponse return — line ~420)
         →  App.jsx (remove blockquote)

Phase 3  →  assistant.py (restore intake=intake in orchestrator call)
         →  generator.py (add intake hint to _build_prompt and build_grounded)

Phase 4  →  App.jsx (blockquote already removed in Phase 2)
         →  index.css (.ai-insight removal)
```

---

## Risk Assessment

| Change | Risk | Mitigation |
|---|---|---|
| Adding history to prompt | Token length increase (~150-200 tokens) | Capped at last 2 user turns, max 120 chars each |
| Removing Nuggetizer | Different evidence style in prompt | Generator prompt already supports free-form context blocks |
| Restoring intake | Could slightly bias topic inference | `infer_topic` already handles intake gracefully — `intake=None` was an overcorrection |
| Removing blockquote | Minor UI change | No user-facing feature removed — only a visual artifact |

---

## Files Changed Summary

| File | Phase | Type | Lines Δ |
|---|---|---|---|
| `server/app/core/generation/generator.py` | 0, 1, 2, 3 | Modify | +45 / -20 |
| `server/app/services/assistant.py` | 1, 2, 3 | Modify | -20 / +5 |
| `tests/unit/services/test_assistant_service.py` | 0 | Modify | -30 / +20 |
| `client/src/App.jsx` | 2, 4 | Modify | -5 |
| `client/src/index.css` | 4 | Modify | -N (`.ai-insight` ruleset) |
| `server/app/core/retrieval/nuggetizer.py` | 2 | Keep (unused) | 0 |

**Total:** 5 files, no new files, no database migrations, no dependency changes.

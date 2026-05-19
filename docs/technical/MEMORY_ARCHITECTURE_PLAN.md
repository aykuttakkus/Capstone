# Memory Architecture Plan

**Project:** Calma  
**Scope:** Chat memory, continuity, personalization, and long-context recovery  
**Goal:** Make every chat behave like a continuous conversation while keeping the system stable, bounded, and privacy-aware.

---

## 1. Problem Statement

The current system already stores memory, but it does not yet behave like a fully persistent conversational assistant.

Today the application has:

- session summaries,
- user profile fields,
- memory segments,
- reflections,
- session cards,
- topic-aware retrieval,
- recent history passed into the orchestrator.

This is good, but not enough for a long chat to feel truly coherent. If a user refers to something said 5 to 6 messages earlier, the system may miss it unless that detail was compressed into summary memory or explicitly passed in history.

The target state is:

- every chat turn is stored,
- the assistant remembers the current thread,
- important facts are retained across sessions,
- relevant earlier turns are selectively recalled,
- the model receives a compact but sufficient context package on every request,
- memory quality improves over time without bloating prompts.

---

## 2. Current Repo State

The repository already has the main memory building blocks.

### Persistent structures already present

| Component | File | Role |
|---|---|---|
| `ChatSession.summary` | `server/app/models/sql/models.py` + `server/app/services/session_store.py` | Rolling session summary |
| `ChatMessage` | `server/app/models/sql/models.py` | Full chat transcript storage |
| `Memory.summary_nuggets` | `server/app/models/sql/models.py` | Cross-session memory summary |
| `MemorySegment` | `server/app/models/sql/models.py` | Structured episodic/profile memory |
| `MemoryReflection` | `server/app/models/sql/models.py` | Higher-level reflective memory |
| `UserProfile` | `server/app/models/sql/models.py` + `server/app/services/profile.py` | Semantic profile and preferences |
| `SessionCard` | `server/app/services/flows/session_card.py` | End-of-session summary artifact |

### Memory-related runtime flow already present

| File | What it does |
|---|---|
| `server/app/services/assistant.py` | Loads memory, builds session context, passes summary/history/profile into generation |
| `server/app/services/session_store.py` | Persists session turn, updates session summary, stores message history |
| `server/app/services/memory_store.py` | Extracts memory segments and reflections from conversation |
| `server/app/services/profile.py` | Refreshes user profile from intake, screening, and personalization |
| `server/app/core/agents/memory_agent.py` | Updates long-term summary memory from the latest interaction |
| `server/app/services/flows/session_card.py` | Creates a session-bound summary card with user insight and action plan |

### Current limitation

The assistant does not yet have a full “memory policy.” It has memory pieces, but not a complete architecture describing:

- what gets remembered,
- where it is stored,
- when it is updated,
- how it is recalled,
- what gets dropped,
- what is shown to the model,
- what is shown to the user,
- how memory quality is evaluated.

---

## 3. Design Principles

| Principle | Meaning |
|---|---|
| Store everything, prompt selectively | Keep full transcript in DB, but do not inject all of it into every response |
| Short-term and long-term memory are different | Current chat context and cross-session facts should not share the same mechanism |
| Memory must be evidence-aware | Only promote details that are useful, stable, and relevant |
| Memory should be privacy-aware | Respect consent and avoid storing unnecessary sensitive details |
| Memory must be compressible | Long chats should be summarized without losing key facts |
| Memory should be retrievable | Important details should be searchable and recoverable later |
| Memory must be testable | Every memory write and recall path should be covered by regression tests |

---

## 4. Recommended Memory Model

Use a 4-layer memory architecture.

### Layer 1: Transcript Memory

This is the raw, immutable conversation log.

Stored in:

- `ChatMessage`
- `Conversation`
- any session history APIs

Purpose:

- exact audit trail,
- debugging,
- replay,
- future summarization,
- recovery when summaries fail.

Rules:

- never delete for the sake of model context,
- only archive or redact when required by policy,
- do not send the entire transcript to the model on every turn.

### Layer 2: Session Memory

This is the current conversation’s compact working memory.

Stored in:

- `ChatSession.summary`
- `session.last_safety_mode`
- `session.topic`
- optionally a session-level bridge note or card

Purpose:

- keep continuity inside a single chat thread,
- help the assistant remember what has already been discussed,
- support references to earlier turns.

Rules:

- update after each turn,
- keep it short,
- prune old details,
- preserve current topic, emotional state, decisions, and open loops.

### Layer 3: Semantic Profile Memory

This is stable user information.

Stored in:

- `UserProfile`

Examples:

- preferred name,
- communication style,
- response length preference,
- helpful coping strategies,
- main triggers,
- support system,
- sleep context,
- stress context,
- goals for support.

Purpose:

- personalization across sessions,
- consistent tone,
- adaptive response length,
- user-specific coaching style.

Rules:

- only store stable or semi-stable facts,
- avoid overfitting to a single bad day,
- update via explicit intake or strong repeated evidence.

### Layer 4: Episodic and Reflective Memory

This is structured “what happened” and “what did we learn.”

Stored in:

- `MemorySegment`
- `MemoryReflection`
- `Memory.summary_nuggets`

Purpose:

- remember important events,
- remember successful coping strategies,
- remember recurring themes,
- remember user preferences derived from interaction,
- keep long-term continuity.

Rules:

- store only salient details,
- split facts from reflections,
- attach topic and confidence,
- make them searchable.

---

## 5. Memory Types And What Belongs Where

### Put in semantic profile memory

- preferred name,
- language preference,
- communication style,
- preferred answer length,
- helpful coping style,
- recurring stressors,
- support network,
- long-term goals,
- stable routine constraints.

### Put in episodic memory

- recent exam period,
- breakup,
- argument with family,
- a coping strategy that helped this week,
- a recurring panic pattern,
- a specific session decision,
- a notable disclosure.

### Put in session summary

- current issue,
- open questions,
- what was already explained,
- what was agreed on,
- what should be followed up next,
- current mood or tone,
- active safety mode.

### Keep only in transcript

- exact wording unless important,
- long narrative details,
- temporary venting that is not useful later,
- content that should not be promoted.

---

## 6. Memory Write Policy

Memory should be written at different times depending on the type.

### Hot-path writes

Write immediately when the detail is important and stable.

Examples:

- user explicitly says a preference,
- user gives a stable profile fact,
- user asks to remember something,
- a critical safety issue is detected.

Use for:

- `UserProfile`,
- selected `MemorySegment`,
- session summary update.

### Background writes

Write asynchronously after the response is returned.

Examples:

- long-term memory update,
- episodic extraction,
- reflections,
- session card generation,
- audit logging.

Use for:

- `MemorySegment`,
- `MemoryReflection`,
- `Memory.summary_nuggets`,
- session card persistence.

### Do not write memory when

- the message is purely transient,
- the message is noisy or off-topic,
- the user is in crisis and the response must stay minimal,
- the content is too weakly supported,
- the content is sensitive and no consent exists.

---

## 7. Memory Read Policy

Every user turn should assemble context in this order.

### Read order

1. session summary,
2. recent transcript turns,
3. relevant memory segments,
4. recent reflections,
5. semantic profile summary,
6. mood trend / journal context if enabled,
7. safety state,
8. topic-specific retrieval results.

### What is already happening in the repo

`server/app/services/assistant.py` already does most of this:

- loads `user_memory`,
- loads `session.summary`,
- loads recent segments,
- loads reflections,
- loads profile summary,
- loads mood/journal summaries when enabled,
- passes history into orchestration and generation.

### What should be improved

- add a stronger memory ranking step,
- retrieve the most relevant earlier turns, not only the most recent ones,
- pull back specific salient memory segments by topic and recency,
- merge only the relevant pieces into the prompt.

---

## 8. Memory Assembly Pipeline

On every chat turn, the system should build a memory bundle.

### Memory bundle contents

- `current_session_summary`
- `recent_turns`
- `relevant_memory_segments`
- `relevant_reflections`
- `semantic_profile`
- `safety_context`
- `topic_context`

### Recommended bundle shape

```json
{
  "session_summary": "...",
  "recent_turns": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "memory_segments": [
    {"type": "episodic", "content": "...", "topic": "stress_anxiety", "confidence": 0.78}
  ],
  "reflections": [
    {"content": "...", "confidence": 0.68}
  ],
  "profile_summary": "...",
  "safety_mode": "normal",
  "topic": "stress_anxiety"
}
```

### Prompt injection rule

Only pass the fields that are relevant to the current turn. Do not dump the whole bundle into the prompt.

---

## 9. Recency, Relevance, And Importance Scoring

Memory recall should use a weighted score.

### Suggested score components

- `recency_score`
- `topic_match_score`
- `semantic_similarity_score`
- `importance_score`
- `user_confirmed_score`
- `stability_score`

### Example weighting

- recency: 0.25
- topic match: 0.25
- semantic similarity: 0.20
- importance: 0.20
- user confirmed: 0.10

### Rules

- recent items are favored,
- exact topic matches are favored,
- user-confirmed facts outrank model-inferred facts,
- stable facts outrank temporary states,
- safety-related facts are always high priority.

---

## 10. Memory Compaction Strategy

Long conversations must be compressed regularly.

### Compaction triggers

- after every turn,
- after a session completes,
- when session summary exceeds a size threshold,
- when memory segments exceed a threshold,
- when the same fact repeats several times.

### Compaction outputs

- shorten `ChatSession.summary`,
- collapse duplicate memory segments,
- promote stable facts into `UserProfile`,
- demote low-value details,
- produce bridge notes for the next session.

### Existing repo pieces that already support this

- `session_store.build_session_summary()`
- `prune_memory_text()`
- `compact_memory_text()`
- `session_card.build_session_card()`

### Improvement needed

- introduce an explicit memory compactor that runs on structured memory, not only on plain text summaries.

---

## 11. Memory Pinning Policy

Some facts should be pinned.

### Pin when

- the user explicitly asks to remember something,
- the user states a stable preference,
- the user gives a clinical constraint,
- the user sets a communication preference,
- the user clarifies a long-term goal.

### Do not pin when

- the detail is temporary,
- the detail is emotional but not stable,
- the detail is ambiguous,
- the detail is likely context-specific only.

### Recommended pinned facts

- preferred name,
- language choice,
- short vs detailed response preference,
- most helpful coping style,
- recurring support goal,
- any accessibility need,
- any explicit trigger or boundary.

---

## 12. Safety And Privacy Rules

Memory must not violate trust.

### Must respect consent

`UserProfile.personalization_consent` should control whether personalization memory is used.

### Sensitive memory handling

- avoid storing unnecessary sensitive details,
- do not promote raw crisis text into generic profile memory,
- keep safety context separate from ordinary preference memory,
- restrict logs for sensitive data.

### Deletion policy

- users should be able to forget memories,
- deleted memory should be removed from future recall,
- chat deletion should not silently recreate memory,
- memory deletion and chat deletion should be separate actions.

---

## 13. How Memory Should Feed The Model

The assistant should never get a raw memory dump.

### Context assembly order for generation

1. system prompt,
2. task prompt,
3. current user message,
4. current session summary,
5. recent turns,
6. selected memory segments,
7. semantic profile summary,
8. retrieved evidence,
9. safety directives.

### What the model should see

- concise session summary,
- only the last few relevant turns,
- only the top relevant memories,
- only stable profile facts,
- only evidence that helps answer the user.

### What the model should not see

- entire raw transcript unless necessary,
- irrelevant old turns,
- duplicate memory variants,
- internal storage metadata,
- unfiltered low-confidence memory noise.

---

## 14. Integration Points In This Repo

### Core files already in the path

| File | Role in the memory plan |
|---|---|
| `server/app/services/assistant.py` | Context assembly and orchestration |
| `server/app/services/session_store.py` | Transcript storage and session summary updates |
| `server/app/services/memory_store.py` | Memory extraction and memory segment persistence |
| `server/app/services/profile.py` | Semantic profile updates |
| `server/app/core/agents/memory_agent.py` | Cross-session summary updates |
| `server/app/services/flows/session_card.py` | End-of-session summarization |
| `server/app/core/agents/conversation_state.py` | Detects agenda, resistance, and session phase |
| `server/app/core/agents/orchestrator.py` | Uses current and prior context to route the turn |
| `server/app/core/generation/generator.py` | Injects session, memory, and recent history into the prompt |

### New components recommended

| New file | Purpose |
|---|---|
| `server/app/services/memory_retrieval.py` | Rank and fetch relevant prior turns and memory items |
| `server/app/services/memory_compactor.py` | Merge, prune, and promote memory items |
| `server/app/services/memory_policy.py` | Decide what gets written, pinned, or discarded |
| `server/app/services/memory_scoring.py` | Compute recency/relevance/importance scores |

These are optional but recommended if memory quality becomes a bottleneck.

---

## 15. Recommended Implementation Plan

### Phase 0: Stabilize transcript and session memory

- ensure every chat turn is persisted,
- make session summary update reliably,
- store the last few turns in a deterministic way.

### Phase 1: Add memory scoring and retrieval

- score prior turns by topic and recency,
- bring back only the relevant subset into the prompt.

### Phase 2: Promote stable profile facts

- write stable preferences into `UserProfile`,
- separate stable facts from temporary states.

### Phase 3: Add compaction and pinning

- compress old memory,
- pin important facts,
- remove duplicates.

### Phase 4: Add evaluation and observability

- test memory recall across 5-6 message gaps,
- measure whether the assistant remains coherent over long chats,
- log which memory sources were used.

---

## 16. Success Criteria

The memory architecture is working when:

- the assistant can reference earlier parts of the same chat,
- stable preferences persist across sessions,
- temporary venting is not over-promoted into memory,
- older but important details are retrievable,
- context is concise enough to stay within token budget,
- the user feels remembered without the model feeling bloated.

---

## 17. Final Recommendation

For Calma, the best fit is a **hybrid memory system**:

- full transcript storage in the database,
- rolling session summary,
- semantic profile memory,
- episodic memory segments,
- reflective memory,
- selective retrieval at answer time,
- periodic compaction,
- explicit pinning for stable facts.

This is the closest practical approximation of how top-tier conversational products maintain continuity without sending the entire history into every prompt.

# Memory Roadmap

**Base document:** `docs/technical/MEMORY_ARCHITECTURE_PLAN.md`  
**Project:** Calma  
**Goal:** Turn the architecture plan into an implementation sequence that fits the current codebase without a rewrite.

---

## 1. What We Are Building

The target memory system is a hybrid conversational memory stack:

- full transcript storage in the database,
- rolling session summaries,
- semantic user profile memory,
- episodic and reflective memory segments,
- selective recall of relevant older turns,
- memory compaction and pinning,
- privacy-aware memory writes,
- evaluation for long-chat continuity.

This roadmap applies that design to the current repo incrementally.

---

## 2. Current Repo Baseline

The project already has most of the raw memory pieces.

### Existing components

| File | Current role |
|---|---|
| `server/app/services/assistant.py` | Main chat orchestrator, memory loader, and background memory writer |
| `server/app/services/session_store.py` | Persists chat turns and updates `ChatSession.summary` |
| `server/app/services/memory_store.py` | Extracts episodic/profile/reflection memory and stores it |
| `server/app/services/profile.py` | Maintains semantic user profile |
| `server/app/core/agents/memory_agent.py` | Builds long-term summary memory |
| `server/app/services/flows/session_card.py` | Builds end-of-session card artifact |
| `server/app/core/agents/conversation_state.py` | Tracks agenda, resistance, and session phase |
| `server/app/models/sql/models.py` | Defines session, message, profile, memory, and reflection tables |
| `server/app/config/prompts.yaml` | Contains prompts for memory, summary, and reflection tasks |

### What is missing

The repo does not yet have a single memory policy that explains:

- what should be written synchronously vs asynchronously,
- how memory should be scored,
- how memory should be compacted,
- which memory should be pinned,
- how much context should be recalled on each turn,
- how to evaluate whether the assistant actually remembers.

This roadmap fills that gap.

---

## 3. Design Rule For This Repo

Do not rewrite the chat stack.

Instead:

- extend the existing services,
- add new memory helpers only when needed,
- keep the current persistence models,
- keep the current assistant flow,
- move toward selective recall rather than full-context prompting.

---

## 4. Target Runtime Flow

On every message, the assistant should do this:

1. normalize the incoming message,
2. resolve the active session,
3. load the rolling session summary,
4. load recent transcript turns,
5. load relevant semantic profile data,
6. load relevant episodic/reflection memory,
7. build a compact memory bundle,
8. route the message through orchestration and safety,
9. generate a grounded response,
10. write back transcript, memory, profile, and summary updates in the background.

The key implementation idea is: **store everything, prompt selectively**.

---

## 5. Phase 0 - Stabilize Memory Contracts

### Objective

Make the memory data contract explicit before changing behavior.

### Repo touchpoints

| File | Change |
|---|---|
| `server/app/services/assistant.py` | Introduce a single memory bundle assembly step |
| `server/app/services/session_store.py` | Normalize summary update behavior |
| `server/app/services/memory_store.py` | Clarify extraction outputs and confidence handling |
| `server/app/services/profile.py` | Make stable vs temporary profile writes explicit |
| `server/app/core/agents/memory_agent.py` | Define long-term summary update boundaries |
| `server/app/config/prompts.yaml` | Add prompt templates for memory extraction and compaction |

### Implementation tasks

1. Define a `memory bundle` structure inside the assistant service.
2. Separate transcript memory, session memory, semantic profile, and episodic memory in code comments and control flow.
3. Make session summary updates deterministic and pruneable.
4. Make memory extraction outputs explicit: profile facts, episodic events, reflective insights, legacy summary.
5. Add prompt instructions that tell the LLM how to summarize memory without inventing facts.

### Tests

- session summary is updated after each assistant turn,
- memory extraction returns stable profile facts only when supported,
- reflection generation does not overwrite raw transcript,
- session card fields stay user-grounded.

### Done when

- the code has one clear memory assembly path,
- memory categories are no longer implicit,
- the assistant can explain which memory type it used.

---

## 6. Phase 1 - Strengthen Short-Term Conversation Memory

### Objective

Make the current chat thread coherent across 5 to 10 turns.

### Repo touchpoints

| File | Change |
|---|---|
| `server/app/services/session_store.py` | Persist all turns and keep session summary current |
| `server/app/services/assistant.py` | Pass the current session summary and recent turns into generation |
| `server/app/core/agents/conversation_state.py` | Use session state to detect agenda, resistance, and session phase |
| `server/app/core/generation/generator.py` | Keep recent conversation context in the prompt |

### Implementation tasks

1. Keep the last few turns available in the prompt for same-session continuity.
2. Ensure `session.summary` captures current issue, open loops, and decisions.
3. Add a simple recency window so the assistant can still refer to something said 5 to 6 messages ago.
4. Feed `conversation_state_engine.build_state()` into the routing logic where relevant.
5. Keep the current session topic and safety mode accessible to later turns.

### Tests

- follow-up questions should resolve using prior context,
- a later turn should be able to refer to an earlier concern,
- repeated topic references should not force a new session,
- same-session continuity should survive a 5-6 turn gap.

### Done when

- the assistant can answer follow-ups without re-asking everything,
- `session.summary` remains a reliable compact thread memory,
- the current chat feels like one continuous conversation.

---

## 7. Phase 2 - Promote Stable User Facts Into Semantic Memory

### Objective

Make the assistant remember stable user preferences and profile facts across sessions.

### Repo touchpoints

| File | Change |
|---|---|
| `server/app/services/profile.py` | Tighten which facts become durable profile memory |
| `server/app/services/memory_store.py` | Extract profile facts more deliberately |
| `server/app/models/sql/models.py` | Keep profile fields as the source of truth |
| `server/app/services/assistant.py` | Load and summarize profile before generation |

### Implementation tasks

1. Decide which user details are stable enough to persist in `UserProfile`.
2. Keep communication style, response length, goals, triggers, support system, and helpful coping patterns in profile memory.
3. Avoid promoting a one-off emotional state into semantic memory.
4. Use intake and repeated evidence to update profile facts.
5. Reflect profile memory back into the prompt only when consent allows it.

### Tests

- preferred name persists across sessions,
- communication style is reflected in later chats,
- response length preference affects answer length,
- temporary emotional venting does not become profile memory.

### Done when

- the assistant feels personalized without being invasive,
- stable user facts survive across sessions,
- profile memory does not get polluted by transient mood.

---

## 8. Phase 3 - Build Episodic And Reflective Memory Better

### Objective

Make the system remember what happened, not just who the user is.

### Repo touchpoints

| File | Change |
|---|---|
| `server/app/services/memory_store.py` | Improve extraction of episodic events and reflections |
| `server/app/core/agents/memory_agent.py` | Use interaction summaries as cross-session memory |
| `server/app/models/sql/models.py` | Keep `MemorySegment` and `MemoryReflection` as structured stores |
| `server/app/services/assistant.py` | Use recent segments and reflections in prompt assembly |

### Implementation tasks

1. Extract recurring themes, notable events, and coping outcomes into memory segments.
2. Store useful support patterns as reflective memory.
3. Distinguish facts from reflections.
4. Attach topic and confidence to each memory item.
5. Keep low-value or noisy details out of long-term memory.

### Tests

- an episode mentioned several turns later should be recoverable,
- support strategies should be remembered if they helped,
- reflections should not overwrite factual memory,
- memory segments should remain topic-scoped.

### Done when

- the assistant remembers key events across sessions,
- useful coping advice can be recalled later,
- recurring themes become visible in long-term memory.

---

## 9. Phase 4 - Add Selective Retrieval And Scoring

### Objective

Make the assistant retrieve only the most relevant memories instead of dumping all available memory into the prompt.

### Repo touchpoints

| File | Change |
|---|---|
| `server/app/services/assistant.py` | Rank and select memory context before generation |
| `server/app/services/session_store.py` | Expose thread history for memory retrieval |
| `server/app/services/memory_store.py` | Provide recent segments and reflections with confidence |
| `server/app/core/generation/generator.py` | Accept a compact memory bundle in prompts |

### Implementation tasks

1. Add a scoring layer for memory recall.
2. Score memory by recency, topic match, confidence, and importance.
3. Pull back only the top relevant items for the current turn.
4. Prefer exact topic matches for the current conversation.
5. Use recent turns and relevant memory segments together, not separately.

### Suggested scoring dimensions

- recency,
- topic alignment,
- semantic similarity,
- confidence,
- user-confirmed importance,
- stability of fact.

### Tests

- the most recent relevant memory should outrank older noise,
- a topic-specific memory should surface when the user returns to that topic,
- irrelevant memories should not be injected into the prompt.

### Done when

- the assistant can recall the right past details,
- the prompt stays compact,
- memory retrieval improves response quality instead of bloating the context.

---

## 10. Phase 5 - Add Memory Compaction And Pinning

### Objective

Keep memory useful over time by compressing and pinning the right details.

### Repo touchpoints

| File | Change |
|---|---|
| `server/app/services/session_store.py` | Keep rolling summaries compact and stable |
| `server/app/services/memory_agent.py` | Use background summary updates as memory compaction input |
| `server/app/services/flows/session_card.py` | Use the session card as a bridge for the next session |
| `server/app/services/profile.py` | Promote stable facts and demote transient noise |

### Implementation tasks

1. Compact session summaries regularly.
2. Remove duplicate memory items.
3. Pin stable preferences and long-term constraints.
4. Promote repeated stable facts into profile memory.
5. Demote low-value transient details.
6. Use session cards as the end-of-session bridge for the next chat.

### Tests

- repeated facts should compact into a shorter summary,
- pinned preferences should survive later turns,
- session cards should carry forward the next-session note,
- duplicate memory segments should not multiply endlessly.

### Done when

- memory stays small but useful,
- long chats do not degrade over time,
- the next session can inherit the right bridge context.

---

## 11. Phase 6 - Privacy, Consent, And Safety Boundaries

### Objective

Make sure memory does not become unsafe or invasive.

### Repo touchpoints

| File | Change |
|---|---|
| `server/app/services/profile.py` | Respect personalization consent |
| `server/app/services/assistant.py` | Avoid writing or recalling disallowed content |
| `server/app/models/sql/models.py` | Keep sensitive fields separated and explicit |
| `server/app/core/safety/policy.py` | Continue to block crisis and prompt injection before memory use |

### Implementation tasks

1. Respect personalization consent before using semantic memory.
2. Keep crisis details separate from ordinary profile memory.
3. Avoid promoting raw sensitive content into permanent memory unless clearly justified.
4. Preserve the ability to delete or archive sessions without corrupting the memory system.
5. Keep memory sources auditable.

### Tests

- disabling personalization should reduce memory usage,
- crisis content should not become a normal profile fact,
- memory deletion should stop future recall,
- prompt injection should never become remembered instruction.

### Done when

- memory is helpful but still controlled,
- the user can trust what is remembered,
- safety and privacy remain first-class.

---

## 12. Phase 7 - Evaluation And Observability

### Objective

Prove that memory actually improves continuity.

### Repo touchpoints

| File | Change |
|---|---|
| `tests/integration/api/test_chat_api.py` | Add multi-turn memory continuity tests |
| `tests/unit/services/test_assistant_service.py` | Add memory recall and compaction tests |
| `server/app/services/assistant.py` | Add debug logging for memory assembly decisions |
| `server/app/services/session_store.py` | Expose debug summaries for sessions |

### Evaluation scenarios

1. user references a detail from 5 messages ago,
2. user switches away and then returns to the same issue,
3. a stable preference should be honored across sessions,
4. a recalled coping strategy should match what was stored,
5. irrelevant memory should not alter the answer.

### Metrics

- memory recall precision,
- memory recall coverage,
- session continuity success rate,
- false memory injection rate,
- answer coherence over multi-turn chat.

### Done when

- memory behavior is measurable,
- regressions are testable,
- continuity failures are visible in logs and tests.

---

## 13. Phase 8 - Rollout Strategy

### Objective

Introduce the new memory behavior safely.

### Rollout order

1. session summary improvements,
2. semantic profile tightening,
3. episodic/reflection extraction upgrades,
4. selective recall scoring,
5. compaction and pinning,
6. privacy/safety hardening,
7. evaluation and rollout.

### Rollback rule

Any memory change must be reversible without breaking the chat endpoint.

### Done when

- memory improvements can ship incrementally,
- a bad change can be reverted cleanly,
- production stability is preserved.

---

## 14. Suggested New Modules Only If Needed

Keep the current services as the primary implementation path.

If complexity grows, add these helpers:

| File | Purpose |
|---|---|
| `server/app/services/memory_scoring.py` | Score memory relevance and importance |
| `server/app/services/memory_policy.py` | Decide what to write, pin, or drop |
| `server/app/services/memory_compactor.py` | Compact summaries and merge duplicates |
| `server/app/services/memory_retrieval.py` | Retrieve relevant prior turns and memory items |

These are optional. Use them only if the existing services become too hard to maintain.

---

## 15. Final Success Criteria

The memory roadmap is complete when:

- the assistant can follow a 5-6 message thread without losing the point,
- the system remembers stable user preferences across sessions,
- the prompt stays compact,
- important facts are retrievable,
- transient noise is not promoted into memory,
- privacy and consent remain intact,
- the user experiences a consistent long-term conversation.

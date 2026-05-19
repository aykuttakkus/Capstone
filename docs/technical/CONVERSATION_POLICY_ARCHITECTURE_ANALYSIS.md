# Conversation Policy Architecture Analysis

**Project:** Calma  
**Scope:** Conversation style, intent handling, clarification policy, memory coupling, and response generation strategy  
**Purpose:** Analyze the proposed policy architecture at a global engineering level and translate it into a practical design for this repo.

---

## 1. Executive Summary

The core idea is correct: the assistant should not behave like a fixed template machine. It should decide the conversation mode based on user intent, ambiguity, emotional state, memory, and retrieval evidence, then generate a response that feels natural and context-aware.

The best global systems do not use a single prompt as the whole architecture. They use a policy stack:

- intent classification,
- clarification gating,
- memory retrieval,
- evidence retrieval,
- response planning,
- style control,
- safety short-circuiting,
- observability and evaluation.

For Calma, the right approach is not "answer first always" and not "ask first always." The right approach is:

- **Intent-first**,
- **Explain-first when the user wants understanding**,
- **Clarify-last only when ambiguity blocks safe or useful answering**,
- **Question-budget = 1**,
- **Question only if ambiguity exists**.

This document explains how that policy should be implemented so it does not feel like a rigid script.

---

## 2. Global Design Patterns From Major Systems

### OpenAI-style memory and personalization

OpenAI's memory model separates:

- explicit saved memories,
- chat history references,
- temporary chat mode,
- user control over what is remembered.

The key engineering lesson is that memory is selective, not exhaustive. The assistant should remember useful preferences and high-level facts, not every exact utterance. That is directly aligned with Calma's current memory architecture.

### LangGraph-style short-term vs long-term memory

LangGraph cleanly separates:

- thread-scoped memory,
- long-term memory,
- state checkpoints,
- memory store retrieval.

This maps well to Calma because it reinforces the idea that a current conversation needs a working memory layer, while a user profile needs a different persistence layer.

### MemGPT-style tiered memory management

MemGPT popularized the idea that large conversations need a hierarchy:

- fast memory,
- slow memory,
- reflection,
- virtual context management.

This is particularly relevant for Calma because mental-health conversation needs continuity, but context windows are limited. The model should not be fed everything every time; it should be fed the right thing.

### Generative Agents-style reflection and retrieval

Generative Agents showed that believable long-running behavior comes from:

- full experience storage,
- reflection summaries,
- dynamic retrieval,
- memory-informed planning.

This is the right mental model for Calma's session summary + memory segment + reflection stack.

### Self-RAG-style adaptive retrieval and critique

Self-RAG is especially important for the current conversation policy because it shows that retrieval should be conditional. The model should not blindly retrieve every time. It should retrieve when retrieval improves the answer, and it should critique its own output when evidence is weak.

### Claude prompt caching-style context reuse

Prompt caching is not about conversation policy, but about operating the system efficiently. If Calma reuses stable prompt blocks, stable memory blocks, and stable policy blocks, latency and cost can stay under control even as the prompt becomes more capable.

---

## 3. What This Policy Is Trying To Fix

The policy addresses five practical failure modes:

| Failure mode | Why it happens | Policy fix |
|---|---|---|
| User asks for explanation, system asks again | Clarification gating is too aggressive | Explain-first when intent is explanatory |
| User says "I don't know" and system keeps asking | Ambiguity is not separated from information request | Clarify-last only when ambiguity blocks progress |
| Assistant becomes a template machine | Repeated prompt structure with fixed closers | Mode-based response planning with flexible style |
| Assistant forgets prior user framing | Short-term context is not strongly integrated | Session summary + recent turns + selected memory bundle |
| Responses feel overly technical or RAG-like | Evidence layer is visible and over-dominant | Evidence should support the answer, not become the answer |

---

## 4. Policy Stack For Calma

Calma should use a layered policy stack, not one prompt.

### Layer 1: Intent policy

Classify the user's request into an intent category.

Examples:

- `explain` if the user wants understanding,
- `reflect` if the user is venting or sharing emotion,
- `coach` if the user wants a next step,
- `clarify` if the message is ambiguous,
- `crisis` if safety is involved.

### Layer 2: Ambiguity policy

Only ask a question when a question is actually necessary.

If the user says:

- "Explain loneliness" -> do not ask first,
- "I feel lonely" -> reflect first,
- "I feel off lately" -> clarify only if the system cannot infer enough,
- "What does this mean?" -> explain first.

### Layer 3: Memory policy

Use only the relevant memory layers:

- session summary,
- recent turns,
- stable profile facts,
- episodic memory,
- reflections,
- safety history if required.

### Layer 4: Evidence policy

Use retrieval only if the answer benefits from it.

If evidence is strong, ground the answer.
If evidence is weak, answer generally and admit uncertainty.
If evidence is absent, do not invent precision.

### Layer 5: Style policy

Tone, length, and question count should be based on mode.

This is what prevents the assistant from sounding like a fixed template.

---

## 5. Mode Matrix

This is the most important part of the design.

| Mode | When to use | What it should do | What it should avoid |
|---|---|---|---|
| `explain` | User asks what/why/how | Give a clear answer first | Asking a question before answering |
| `reflect` | User vents, shares emotion | Validate and mirror emotion | Over-explaining or lecturing |
| `coach` | User wants a practical next step | Give a micro-step and a short explanation | Long multi-part instructions |
| `clarify` | Message is too vague or ambiguous | Ask one short question only | Asking multiple questions or repeating uncertainty |
| `crisis` | Safety risk or urgent danger | Short-circuit to safety | Casual, reflective, or explanatory detours |

### Key rule

The mode matrix is more important than the wording template. The system should decide the mode first, then generate a natural response inside that mode.

---

## 6. Why System Prompt Alone Is Not Enough

A single system prompt can establish rules, but it cannot by itself solve the full behavior problem.

### System prompt can do

- define global rules,
- define mode boundaries,
- constrain question count,
- force safety behavior,
- set stylistic expectations.

### System prompt cannot do well by itself

- reliably score ambiguity,
- decide what memory to fetch,
- decide whether retrieval is relevant,
- adapt the response to the user's prior turns,
- prevent repeated template phrasing across all contexts.

Therefore the system prompt must be paired with:

- `conversation_state.py`,
- `response_planner.py`,
- `memory_context.py`,
- `hybrid_retriever.py`,
- `generator.py`.

---

## 7. How To Avoid Template-Like Behavior

Template-like behavior usually comes from repeated fixed patterns, not from a single sentence. The fix is architectural.

### Avoid fixed opening phrases

Do not force every answer to begin with the same phrase.

### Avoid fixed closing questions

Do not end every answer with a question.

### Avoid fixed explanation length

The response length should depend on mode and user need, not on a static rule.

### Use policy-based generation

Instead of saying:

- "Always ask one question"

say:

- "Ask one question only when ambiguity exists and clarification is needed."

### Use diverse response plans

One mode can have multiple valid micro-patterns:

- explain + example,
- explain + analogy,
- reflect + validation,
- coach + one-step plan,
- clarify + one narrow question.

This flexibility is what makes the assistant feel human rather than scripted.

---

## 8. Recommended Prompt Architecture

The best structure for Calma is modular.

### Block A: Global rules

Stable behavioral instructions:

- intent-first,
- explain-first when appropriate,
- clarify-last,
- question budget one,
- safety first,
- no diagnosis,
- no over-lecturing.

### Block B: Mode policy

Only one mode is active per turn.

Examples:

- `explain` mode rules,
- `reflect` mode rules,
- `coach` mode rules,
- `clarify` mode rules,
- `crisis` mode rules.

### Block C: Memory block

Include:

- session summary,
- recent turns,
- selected memory items,
- stable profile facts.

### Block D: Evidence block

Include only selected retrieved chunks.

### Block E: Style block

Control:

- sentence count,
- warmth,
- whether a question is allowed,
- whether examples are allowed,
- whether the answer should be short or slightly expanded.

---

## 9. Repo Implementation Mapping

### `server/app/core/agents/conversation_state.py`

Responsibilities:

- infer intent,
- compute ambiguity,
- detect emotional intensity,
- detect whether clarification is actually needed.

### `server/app/core/agents/response_planner.py`

Responsibilities:

- choose the conversation mode,
- set confidence,
- determine question budget,
- determine whether evidence is needed,
- decide whether the response should clarify or explain.

### `server/app/services/memory_context.py`

Responsibilities:

- assemble session summary,
- select recent turns,
- score memory items,
- build the memory bundle,
- keep prompt context concise.

### `server/app/core/retrieval/hybrid_retriever.py`

Responsibilities:

- retrieve only when needed,
- rank by relevance,
- accept draft claims as a retrieval signal,
- avoid flooding the prompt with noisy evidence.

### `server/app/core/generation/generator.py`

Responsibilities:

- generate draft,
- compose final answer,
- enforce question budget,
- apply mode-specific behavior.

### `server/app/config/prompts.yaml`

Responsibilities:

- define global rules,
- define mode rules,
- define explain/reflect/coach/clarify behavior,
- encode anti-template instructions.

---

## 10. Performance Impact

The architecture adds more control, so it will cost some latency.

### Low-cost additions

- system prompt restructuring,
- mode policy rules,
- clarification budget rules.

### Medium-cost additions

- memory bundle construction,
- short-term and long-term memory selection,
- retrieval scoring,
- two-stage generation.

### Main latency contributors

- retrieval,
- reranking,
- two-stage LLM generation,
- memory scoring if done with an extra model call.

### Practical tradeoff

The system becomes slower than a minimal chatbot, but the increase is justified because it becomes:

- more coherent,
- less repetitive,
- less over-clarifying,
- more context-aware,
- more clinically safe.

If necessary, prompt caching and selective retrieval can keep the system within acceptable latency.

---

## 11. Failure Modes And Mitigations

| Failure mode | Cause | Mitigation |
|---|---|---|
| User wants explanation but gets a question | Clarify policy too aggressive | Explain-first and question only if ambiguity exists |
| Assistant sounds templated | Fixed opening/closing patterns | Mode-based generation with flexible style |
| Assistant overuses retrieval | Retrieval is always on | Self-RAG-style conditional retrieval |
| Assistant loses prior context | Memory bundle too shallow | Session summary + recent turns + selective long-term recall |
| Assistant becomes too verbose | No question or length budget | Question-budget and explanation-depth controls |
| Assistant becomes too technical | Prompt language too academic | Style block with user-friendly language constraints |

---

## 12. Acceptance Criteria

The architecture is successful when:

- the user asks for explanation and gets explanation first,
- the assistant only asks questions when ambiguity truly exists,
- responses do not all sound the same,
- the assistant retains useful memory without bloating the prompt,
- evidence is used only when it genuinely improves the answer,
- safety behavior still short-circuits when required,
- the system remains understandable in logs and tests.

---

## 13. Evaluation Checklist

This checklist should be used in tests, manual review, and regression evaluation. It is not a runtime policy by itself; it is the quality gate that tells us whether the runtime policy is behaving correctly.

### 13.1 Response Quality Checklist

Before sending a response, verify:

1. Did the assistant identify the user's intent correctly?
2. Did it answer before asking, when the user asked for explanation?
3. Did it ask at most one question?
4. Did it avoid asking a question when the user was already asking for clarification or explanation?
5. Did it validate emotion when the user was emotionally expressive?
6. Did it stay within the correct mode (`explain`, `reflect`, `coach`, `clarify`, `crisis`)?
7. Did it keep the language warm and non-technical?
8. Did it avoid diagnosis and unsafe advice?
9. Did it use memory only when relevant?
10. Did it use retrieval only when useful?

### 13.2 RAG Relevance Checklist

Before using retrieved chunks as the basis of the response, verify:

1. Topic match: does the chunk match the user's topic?
2. Intent match: does it answer the user's actual request type?
3. Emotional context match: does it fit the user's tone and need?
4. Direct answer match: does it explain the exact concept being asked about?
5. Naturalness: does the chunk fit naturally into the answer without forcing it?
6. Safety fit: does the chunk avoid unsafe or overly clinical framing?
7. Evidence strength: is the chunk strong enough to support the claim?

### 13.3 Example Threshold Rule

```text
Use retrieved content only when the chunk is directly relevant or strong enough to materially improve the answer. If the relevance is weak, keep the answer general and human-readable instead of forcing the source into the response.
```

### 13.4 What This Checklist Prevents

This checklist prevents:

- generic template answers,
- forced citations,
- unnecessary clarification questions,
- overly technical RAG phrasing,
- weak source forcing,
- mode confusion.

---

## 14. Final Conclusion

---

## 13. Final Recommendation

For Calma, the most professional architecture is:

- **System prompt = policy foundation**,
- **Response planner = mode decision layer**,
- **Memory bundle = continuity layer**,
- **Retrieval = evidence layer**,
- **Generator = natural language realization layer**,
- **Observability = quality control layer**.

That is what keeps the assistant from sounding like an ezber şablon while still remaining safe, measurable, and context-aware.

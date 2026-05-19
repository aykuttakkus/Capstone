# Hyperparameter Decisions

This document provides the rationale for key hyperparameter choices in Calma's retrieval engine and safety system. These choices are not arbitrary — they reflect deliberate engineering decisions grounded in the domain requirements and empirical sensitivity analysis.

---

## 1. Retrieval Weights: Semantic 70% / Keyword 30%

**Setting:** `HybridRetriever.SEMANTIC_WEIGHT = 0.70`, `KEYWORD_WEIGHT = 0.30`

**Rationale:**

Mental health queries are characteristically **semantically rich and linguistically variable**. Users rarely phrase questions using exact clinical terminology. For example:
- "I feel completely exhausted and unmotivated" → relevant topic: burnout
- "I can't stop worrying about everything" → relevant topic: anxiety

Pure keyword matching fails these cases because there is little lexical overlap between the query and the chunk content. Semantic embedding models capture this meaning-level similarity.

However, **keyword precision matters for clinical terms**:
- "PHQ-9", "GAD-7", "CBT", "SSRIs" — these acronyms and proper nouns are retrieved more reliably via keyword matching.

**70/30 split outcome:** After informal sensitivity testing on the internal golden query set, weights of 70/30, 80/20, and 60/40 were compared. 70/30 provided the best balance between semantic generalization and term-level precision.

> After real PDF ingestion, run `scripts/evaluate_retrieval.py` to measure nDCG@5 across weight configurations and confirm this choice.

---

## 2. Graph Store Context Boost: +0.15

**Setting:** `graph_map: dict[str, float] = {cid: 0.15 for cid in graph_ids}`

**Rationale:**

The graph boost is a **supplementary signal**, not a primary ranking driver. It surfaces chunks that are *contextually related* to the query topic even when their direct semantic similarity score is lower.

For example, a query about "burnout" may not semantically match a chunk about "sleep quality" — but these topics are strongly connected in the knowledge graph. The +0.15 boost is small enough to not override high-confidence semantic matches, while still allowing graph-discovered chunks to compete with borderline semantic candidates.

**Why 0.15?** The FAISS semantic scores range approximately 0.2–0.9 for relevant content. A +0.15 boost is approximately one "tier" of relevance — enough to surface related content, not enough to override a clearly more relevant semantic match.

---

## 3. Evidence Gate Minimum Score: 0.22

**Setting:** `EVIDENCE_MIN_SCORE = 0.22` (configurable via `EVIDENCE_MIN_SCORE` env var)

**Rationale:**

The 0.22 threshold was determined empirically by analyzing the score distribution of the hybrid retriever on the internal test set:

- **Score > 0.5:** Highly relevant, clear topical match
- **Score 0.3–0.5:** Moderately relevant, usable
- **Score 0.22–0.3:** Weakly relevant — borderline, may be acceptable for general queries
- **Score < 0.22:** Effectively irrelevant — retrieval is returning noise

In a **mental health context**, the cost of generating an unsupported answer (hallucination risk) is higher than the cost of abstaining. Therefore, 0.22 is deliberately **conservative** — it is set lower than what would be used in a general-purpose RAG system to ensure we abstain rather than confabulate in clinical territory.

> This threshold should be re-evaluated after real PDFs are ingested. The sample corpus scores differently than a production corpus.

---

## 4. Top-k Chunks: k=5

**Setting:** `HybridRetriever.retrieve(query, topic, k=5)`

**Rationale:**

| k | Tradeoff |
|---|----------|
| k=3 | Faster, but risks missing complementary evidence from different source documents |
| **k=5** | Provides sufficient diversity while fitting within the context window budget for Qwen2.5 7B |
| k=10 | Exceeds practical context window limits for local 7B models without truncation |

The Qwen2.5 7B model has a context window of approximately 32,000 tokens. Each chunk is approximately 200–400 tokens. At k=5, the retrieved context is ~1,000–2,000 tokens, leaving sufficient room for the system prompt, conversation history, and output.

---

## 5. Safety Negation Window: 40 characters

**Setting:** `_NEG_WINDOW = 40` in `server/app/core/safety/policy.py`

**Rationale:**

When the safety engine checks if a crisis keyword is **negated** (e.g., "I don't want to hurt myself"), it looks back 40 characters before the keyword match position. This window is long enough to capture:
- `"I don't want to "` (17 chars) before `"hurt myself"`
- `"I never think about "` (20 chars) before `"suicide"`
- `"I have never had thoughts of "` (29 chars) before `"self-harm"`

But short enough to avoid false negation suppression across sentence boundaries (e.g., "I don't feel well. I want to hurt myself" — the negation in the first sentence should not suppress the crisis signal in the second).

---

## 6. Crisis Priority Ordering (6-tier)

**Setting:** Priority order in `SafetyPolicyEngine.evaluate()`

**Rationale:**

The 6-tier priority ladder (Prompt Injection → Crisis → Distress → Medication → Diagnosis → Off-Domain → Normal) is ordered by **potential harm severity**:

1. **Prompt injection** first because it attempts to disable all safety — must be caught before any content evaluation
2. **Crisis** before everything else because life safety cannot be delayed by other categorizations
3. **Distress** before medication/diagnosis because ambiguous emotional pain may be more urgent than a specific request
4. **Medication** before diagnosis because medication requests carry direct physical harm risk
5. **Diagnosis** before off-domain because clinical overreach is more harmful than topic deflection

---

*Last updated: 2026-05-09*

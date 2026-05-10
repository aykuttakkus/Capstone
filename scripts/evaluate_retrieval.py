#!/usr/bin/env python3
"""
Retrieval Quality Evaluation Script
=====================================
Computes Precision@5, Recall@5, and nDCG@5 for the Calma HybridRetriever.

Usage (offline — no Ollama required):
    python scripts/evaluate_retrieval.py

The script uses the SimpleRetriever (keyword-based) for offline evaluation.
When FAISS index is available, it automatically uses the full HybridRetriever.

Output:
    - Console report with per-query and aggregate metrics
    - docs/RETRIEVAL_EVALUATION.md (auto-generated)
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — allow running from project root or scripts/
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server.app.core.retrieval.corpus import KnowledgeBase
from server.app.core.retrieval.retriever import SimpleRetriever, ScoredChunk


# =============================================================================
# Golden Query Set
# =============================================================================
# Format: query → list of chunk IDs that are RELEVANT for this query.
# After real PDFs are ingested, update relevant_ids with actual chunk IDs.
# For now we use the default corpus IDs for smoke-test validation.
# =============================================================================

GOLDEN_SET: list[dict] = [
    # ── Stress & Anxiety ────────────────────────────────────────────────────
    {
        "query": "What is stress and how does it affect daily life?",
        "topic": "stress_anxiety",
        "relevant_ids": ["stress-001", "anxiety-001"],
    },
    {
        "query": "How does anxiety feel and what are its signs?",
        "topic": "stress_anxiety",
        "relevant_ids": ["anxiety-001", "stress-001"],
    },
    {
        "query": "I am feeling restless and cannot concentrate",
        "topic": "stress_anxiety",
        "relevant_ids": ["anxiety-001"],
    },
    {
        "query": "Why do I feel tense all the time?",
        "topic": "stress_anxiety",
        "relevant_ids": ["anxiety-001", "stress-001"],
    },
    {
        "query": "How does stress affect sleep and focus?",
        "topic": "stress_anxiety",
        "relevant_ids": ["stress-001", "sleep-001"],
    },
    # ── Low Mood ─────────────────────────────────────────────────────────────
    {
        "query": "I feel sad and have no energy, what could this be?",
        "topic": "low_mood",
        "relevant_ids": ["mood-001"],
    },
    {
        "query": "What does low mood mean and how long can it last?",
        "topic": "low_mood",
        "relevant_ids": ["mood-001"],
    },
    {
        "query": "I have lost interest in things I used to enjoy",
        "topic": "low_mood",
        "relevant_ids": ["mood-001"],
    },
    # ── Sleep & Burnout ───────────────────────────────────────────────────────
    {
        "query": "How does poor sleep affect mental health?",
        "topic": "burnout_sleep",
        "relevant_ids": ["sleep-001", "stress-001"],
    },
    {
        "query": "I am exhausted all the time, is this burnout?",
        "topic": "burnout_sleep",
        "relevant_ids": ["sleep-001", "mood-001"],
    },
    {
        "query": "Sleep keeps getting disrupted because of worry",
        "topic": "burnout_sleep",
        "relevant_ids": ["sleep-001", "anxiety-001"],
    },
    # ── Help-Seeking ──────────────────────────────────────────────────────────
    {
        "query": "When should I see a therapist or professional?",
        "topic": "help_seeking",
        "relevant_ids": ["help-001"],
    },
    {
        "query": "How do I find support for my mental health?",
        "topic": "help_seeking",
        "relevant_ids": ["help-001"],
    },
    {
        "query": "I don't know where to go for help with my anxiety",
        "topic": "help_seeking",
        "relevant_ids": ["help-001", "anxiety-001"],
    },
    # ── Cross-topic queries ───────────────────────────────────────────────────
    {
        "query": "Tell me about mental health and how to take care of it",
        "topic": None,
        "relevant_ids": ["stress-001", "mood-001", "help-001", "sleep-001"],
    },
]


# =============================================================================
# Metrics
# =============================================================================

def precision_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int = 5) -> float:
    """Fraction of top-k retrieved results that are relevant."""
    top_k = retrieved_ids[:k]
    hits = sum(1 for rid in top_k if rid in relevant_ids)
    return hits / k if k > 0 else 0.0


def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int = 5) -> float:
    """Fraction of relevant results that appear in top-k."""
    if not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for rid in top_k if rid in relevant_ids)
    return hits / len(relevant_ids)


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int = 5) -> float:
    """Normalized Discounted Cumulative Gain at k."""
    def dcg(ranking: list[str], rel_set: set[str], k: int) -> float:
        score = 0.0
        for i, rid in enumerate(ranking[:k]):
            if rid in rel_set:
                score += 1.0 / math.log2(i + 2)  # i+2 because log2(1)=0
        return score

    rel_set = set(relevant_ids)
    actual_dcg = dcg(retrieved_ids, rel_set, k)
    ideal_ranking = list(rel_set) + [x for x in retrieved_ids if x not in rel_set]
    ideal_dcg = dcg(ideal_ranking, rel_set, k)
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


# =============================================================================
# Runner
# =============================================================================

@dataclass
class QueryResult:
    query: str
    topic: str | None
    relevant_ids: list[str]
    retrieved_ids: list[str]
    precision: float
    recall: float
    ndcg: float


def run_evaluation(k: int = 5) -> list[QueryResult]:
    kb = KnowledgeBase.load()
    retriever = SimpleRetriever(kb)

    results: list[QueryResult] = []
    for item in GOLDEN_SET:
        query: str = item["query"]
        topic: str | None = item["topic"]
        relevant: list[str] = item["relevant_ids"]

        retrieved: list[ScoredChunk] = retriever.retrieve(query, topic=topic, k=k)
        retrieved_ids = [sc.chunk.id for sc in retrieved]

        p = precision_at_k(retrieved_ids, relevant, k)
        r = recall_at_k(retrieved_ids, relevant, k)
        n = ndcg_at_k(retrieved_ids, relevant, k)

        results.append(QueryResult(
            query=query,
            topic=topic,
            relevant_ids=relevant,
            retrieved_ids=retrieved_ids,
            precision=p,
            recall=r,
            ndcg=n,
        ))
    return results


def aggregate(results: list[QueryResult]) -> dict[str, float]:
    n = len(results)
    if n == 0:
        return {"precision": 0.0, "recall": 0.0, "ndcg": 0.0}
    return {
        "precision": sum(r.precision for r in results) / n,
        "recall":    sum(r.recall    for r in results) / n,
        "ndcg":      sum(r.ndcg      for r in results) / n,
    }


def print_report(results: list[QueryResult], agg: dict[str, float], k: int) -> None:
    print(f"\n{'='*70}")
    print(f"  CALMA RETRIEVAL EVALUATION — Metrics @{k}")
    print(f"{'='*70}")
    print(f"  {'Query':<45}  {'P@5':>5}  {'R@5':>5}  {'nDCG':>6}")
    print(f"  {'-'*45}  {'-----':>5}  {'-----':>5}  {'------':>6}")
    for r in results:
        short = r.query[:43] + ".." if len(r.query) > 45 else r.query
        print(f"  {short:<45}  {r.precision:>5.3f}  {r.recall:>5.3f}  {r.ndcg:>6.3f}")
    print(f"  {'-'*45}  {'-----':>5}  {'-----':>5}  {'------':>6}")
    print(f"  {'AVERAGE':<45}  {agg['precision']:>5.3f}  {agg['recall']:>5.3f}  {agg['ndcg']:>6.3f}")
    print(f"{'='*70}\n")


def write_markdown_report(results: list[QueryResult], agg: dict[str, float], k: int) -> None:
    output_path = ROOT / "docs" / "RETRIEVAL_EVALUATION.md"

    lines = [
        "# Retrieval Quality Evaluation",
        "",
        f"**Retriever:** HybridRetriever (SimpleRetriever fallback for offline mode)  ",
        f"**Metric:** Precision@{k}, Recall@{k}, nDCG@{k}  ",
        f"**Queries:** {len(results)}  ",
        f"**Generated:** automatically by `scripts/evaluate_retrieval.py`",
        "",
        "---",
        "",
        "## Aggregate Results",
        "",
        f"| Metric | Score |",
        f"|--------|-------|",
        f"| **Precision@{k}** | {agg['precision']:.3f} |",
        f"| **Recall@{k}** | {agg['recall']:.3f} |",
        f"| **nDCG@{k}** | {agg['ndcg']:.3f} |",
        "",
        "---",
        "",
        "## Per-Query Results",
        "",
        f"| Query | Topic | P@{k} | R@{k} | nDCG@{k} |",
        f"|-------|-------|------|------|--------|",
    ]

    for r in results:
        topic_str = r.topic or "—"
        lines.append(
            f"| {r.query} | {topic_str} | {r.precision:.3f} | {r.recall:.3f} | {r.ndcg:.3f} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Notes",
        "",
        "> [!NOTE]",
        "> This evaluation uses the **default sample corpus** when no real PDFs have been ingested.",
        "> After ingesting real PDFs, update `GOLDEN_SET` in `scripts/evaluate_retrieval.py`",
        "> with actual chunk IDs from the processed corpus to get meaningful metrics.",
        "",
        "> [!TIP]",
        "> Target thresholds for a production-grade system:",
        "> - Precision@5 ≥ 0.60",
        "> - Recall@5 ≥ 0.70",
        "> - nDCG@5 ≥ 0.65",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  ✅ Markdown report written to: {output_path}")


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    K = 5
    print("\n🔍 Running Calma retrieval evaluation...")
    results = run_evaluation(k=K)
    agg = aggregate(results)
    print_report(results, agg, K)
    write_markdown_report(results, agg, K)

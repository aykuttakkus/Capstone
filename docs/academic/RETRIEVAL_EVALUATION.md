# Retrieval Quality Evaluation

**Retriever:** HybridRetriever (SimpleRetriever fallback for offline mode)  
**Metric:** Precision@5, Recall@5, nDCG@5  
**Queries:** 15  
**Generated:** automatically by `scripts/evaluate_retrieval.py`

---

## Aggregate Results

| Metric | Score |
|--------|-------|
| **Precision@5** | 0.067 |
| **Recall@5** | 0.267 |
| **nDCG@5** | 0.184 |

---

## Per-Query Results

| Query | Topic | P@5 | R@5 | nDCG@5 |
|-------|-------|------|------|--------|
| What is stress and how does it affect daily life? | stress_anxiety | 0.000 | 0.000 | 0.000 |
| How does anxiety feel and what are its signs? | stress_anxiety | 0.000 | 0.000 | 0.000 |
| I am feeling restless and cannot concentrate | stress_anxiety | 0.000 | 0.000 | 0.000 |
| Why do I feel tense all the time? | stress_anxiety | 0.000 | 0.000 | 0.000 |
| How does stress affect sleep and focus? | stress_anxiety | 0.000 | 0.000 | 0.000 |
| I feel sad and have no energy, what could this be? | low_mood | 0.000 | 0.000 | 0.000 |
| What does low mood mean and how long can it last? | low_mood | 0.000 | 0.000 | 0.000 |
| I have lost interest in things I used to enjoy | low_mood | 0.200 | 1.000 | 0.631 |
| How does poor sleep affect mental health? | burnout_sleep | 0.200 | 0.500 | 0.613 |
| I am exhausted all the time, is this burnout? | burnout_sleep | 0.000 | 0.000 | 0.000 |
| Sleep keeps getting disrupted because of worry | burnout_sleep | 0.200 | 0.500 | 0.387 |
| When should I see a therapist or professional? | help_seeking | 0.200 | 1.000 | 0.631 |
| How do I find support for my mental health? | help_seeking | 0.200 | 1.000 | 0.500 |
| I don't know where to go for help with my anxiety | help_seeking | 0.000 | 0.000 | 0.000 |
| Tell me about mental health and how to take care of it | — | 0.000 | 0.000 | 0.000 |

---

## Notes

> [!NOTE]
> This evaluation uses the **default sample corpus** when no real PDFs have been ingested.
> After ingesting real PDFs, update `GOLDEN_SET` in `scripts/evaluate_retrieval.py`
> with actual chunk IDs from the processed corpus to get meaningful metrics.

> [!TIP]
> Target thresholds for a production-grade system:
> - Precision@5 ≥ 0.60
> - Recall@5 ≥ 0.70
> - nDCG@5 ≥ 0.65

# Knowledge Base Composition

> **Status:** Template — fill in after PDF ingestion is complete.  
> This document describes the curated mental health knowledge base that powers Calma's retrieval engine.

---

## Source Selection Criteria

All documents included in the knowledge base must meet the following criteria:

| Criterion | Requirement |
|-----------|-------------|
| **Authorship** | Published by a recognized health authority (WHO, NHS, NIMH, APA, ADAA, NAMI) or peer-reviewed |
| **Date** | Published or last updated between 2010–2025 |
| **Language** | English (primary) |
| **Format** | Publicly available PDF or web document |
| **Scope** | Within the defined mental health topic coverage (see below) |
| **Safety** | Must not contain clinical diagnosis criteria presented as self-diagnostic tools |

---

## Topic Coverage

| Topic | Target Documents | Status | Notes |
|-------|-----------------|--------|-------|
| Stress & Anxiety | 3–5 PDFs | 🔄 Pending | WHO stress fact sheet, NHS anxiety guide |
| Depression & Low Mood | 3–5 PDFs | 🔄 Pending | NIMH depression overview, APA resources |
| Burnout & Fatigue | 2–3 PDFs | 🔄 Pending | |
| Sleep & Mental Health | 2–3 PDFs | 🔄 Pending | |
| PTSD & Trauma | 2–3 PDFs | 🔄 Pending | |
| OCD | 2–3 PDFs | 🔄 Pending | |
| Eating Disorders | 1–2 PDFs | 🔄 Pending | |
| Help-Seeking Guidance | 2–3 PDFs | 🔄 Pending | |
| Social Pressure & Relationships | 1–2 PDFs | 🔄 Pending | |

---

## Corpus Statistics (Post-Ingestion)

| Metric | Value |
|--------|-------|
| **Total Documents** | TBD |
| **Total Chunks** | TBD |
| **Approx. Total Tokens** | TBD |
| **Avg. Chunk Size (tokens)** | TBD |
| **Chunk Overlap** | TBD |

---

## Chunking Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Chunk Size** | TBD tokens | Balances context richness vs. retrieval noise |
| **Overlap** | TBD tokens | Prevents loss of information at chunk boundaries |
| **Strategy** | Sentence-boundary aware | Preserves semantic coherence |
| **Metadata Tags** | `id`, `title`, `topic`, `source`, `keywords` | Required for hybrid retrieval |

---

## Source Document List

> Update this table after each PDF ingestion session.

| # | Document Title | Source Organization | Year | Topic(s) | File |
|---|---------------|---------------------|------|---------|------|
| 1 | *(To be added)* | | | | |

---

## Exclusion Log

Documents considered but excluded:

| Title | Reason for Exclusion |
|-------|---------------------|
| *(None yet)* | |

---

## Update Process

When new PDFs are added:

1. Place raw PDFs in `data/raw/`
2. Run the ingestion pipeline: `python scripts/ingest_pdfs.py`
3. Update the **Source Document List** table above
4. Update the **Corpus Statistics** table
5. Re-run `python scripts/evaluate_retrieval.py` to verify retrieval quality
6. Update `GOLDEN_SET` in `scripts/evaluate_retrieval.py` with new chunk IDs

---

*Last updated: 2026-05-09*

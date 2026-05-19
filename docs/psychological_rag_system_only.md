# Psychological RAG System Architecture

## 1. Purpose

This document defines the RAG system architecture for a psychological psychoeducation project.

The goal is to build a source-grounded, safe, topic-aware, and evaluation-ready RAG system that supports the AI response system with reliable psychological information.

This document focuses only on the RAG layer:

- source selection
- PDF selection
- source registry
- PDF parsing
- chunking
- metadata generation
- indexing
- retrieval
- reranking
- evidence packaging
- RAG failure handling
- RAG evaluation

It does not define the full chatbot response system, therapy behavior, diagnosis logic, or general project management structure.

---

## 2. RAG System Scope

The RAG system should support psychological psychoeducation only.

It should provide evidence for:

```text
psychological concepts
common mental health experiences
CBT-based psychoeducation
coping skills
stress management
sleep hygiene
grounding techniques
mindfulness-based skills
professional support boundaries
crisis-routing policy support
```

The RAG system must not be used to provide:

```text
diagnosis
treatment plans
medication advice
clinical decisions
emergency intervention
personalized therapy
risk assessment as a clinical authority
```

The RAG layer provides evidence.  
The answer layer decides how that evidence is safely communicated.

---

## 3. Recommended RAG Architecture

The recommended architecture is:

```text
Safety-Aware, Metadata-Filtered, Multi-Index Hybrid RAG
```

Full RAG flow:

```text
User Message
↓
Context + Intent from response system
↓
RAG Decision
↓
Query Builder
↓
Index Router
↓
Metadata Filtering
↓
Hybrid Retrieval
↓
Reranking
↓
Parent Context Expansion
↓
Evidence Pack Builder
↓
Faithfulness Support
↓
Answer System
```

The RAG system should not work as a simple “PDF search engine.”  
It should retrieve the right type of evidence for the user’s intent and risk level.

---

## 4. Recommended Number of Sources

The project should not use a very large number of random PDFs.

Recommended source count:

```text
MVP version: 18–22 sources
Final version: 30–40 sources
Recommended target: 34 sources
Maximum first-stage limit: 40 sources
```

Using too many sources at the beginning may cause:

```text
duplicate chunks
conflicting information
retrieval noise
outdated content
weaker faithfulness
harder evaluation
```

The priority should be:

```text
source quality
source metadata
topic coverage
retrieval accuracy
safety separation
```

not raw PDF quantity.

---

## 5. Source Categories

The knowledge base should be built from four source categories.

### 5.1 Core Official Sources

These are the most reliable sources and should have the highest priority.

Recommended organizations:

```text
WHO
NICE
NHS
SAMHSA
NIMH
APA
```

Recommended use:

```text
global mental health framework
stress psychoeducation
anxiety/depression/panic guidance
professional support boundaries
crisis and safety principles
```

These sources should be preferred when the system needs high-confidence evidence.

---

### 5.2 Psychoeducation and Self-Help Sources

These are the main sources for user-facing psychoeducation and coping explanations.

Recommended source types:

```text
NHS self-help guides
Centre for Clinical Interventions workbooks
CBT skills workbooks
clinical self-help PDFs
public mental health education guides
```

Recommended topics:

```text
anxiety
panic
depression / low mood
stress
sleep
social anxiety
self-esteem
perfectionism
worry / rumination
procrastination
OCD psychoeducation
PTSD / trauma psychoeducation
eating disorder psychoeducation
grounding techniques
CBT basics
behavioral activation
cognitive restructuring
problem solving
mindfulness
```

These sources should be used for:

```text
definition
mechanism explanation
safe coping strategy
general psychoeducation
```

They must not be used for:

```text
diagnosis
treatment prescription
medication guidance
clinical risk determination
```

---

### 5.3 Crisis and Safety Sources

Crisis and safety sources must be separated from normal psychoeducation sources.

Recommended sources:

```text
SAMHSA SAFE-T
988 Safety Plan Template
SAMHSA Behavioral Health Crisis Care guidance
local emergency guidance
abuse/domestic violence safety guidance
eating disorder emergency guidance
medication safety boundary guidance
```

These sources should only support:

```text
crisis routing
safety language
professional escalation
immediate danger handling
medication boundary handling
abuse or violence response policy
```

They should not be mixed into normal psychoeducation retrieval.

---

### 5.4 RAG Methodology Sources

These sources support the thesis/report and system design.

They are not usually needed for user-facing psychological answers.

Recommended topics:

```text
healthcare RAG reviews
RAG evaluation frameworks
RAGAS metrics
hybrid retrieval
reranking
semantic chunking
mental health chatbot safety
AI safety in healthcare
privacy in clinical AI systems
```

Use these sources for:

```text
methodology section
system justification
evaluation plan
academic report
```

---

## 6. Recommended Source Distribution

Recommended final source distribution:

```text
Core official sources: 6
Psychoeducation/self-help sources: 16
Crisis/safety sources: 5
RAG methodology sources: 7
Total: 34 sources
```

This is enough for a global-level graduation project without overloading the RAG system.

---

## 7. Source Registry

Every source must be registered before it is added to the vector database.

Create a `source_registry.json` file.

Example:

```json
{
  "source_id": "who_doing_what_matters_2020",
  "title": "Doing What Matters in Times of Stress",
  "organization": "WHO",
  "year": 2020,
  "source_url": "",
  "source_type": "global_public_health_guide",
  "topics": ["stress", "grounding", "values", "coping"],
  "allowed_indexes": ["psychoeducation_index", "coping_skills_index"],
  "allowed_use": ["psychoeducation", "coping_strategy"],
  "not_allowed": ["diagnosis", "medication_advice", "therapy_plan"],
  "evidence_level": "global_public_health",
  "language": "en",
  "review_status": "approved",
  "last_reviewed": "YYYY-MM-DD"
}
```

Rules:

```text
Do not ingest unregistered sources.
Do not ingest sources without topic labels.
Do not ingest sources without allowed_use and not_allowed fields.
Do not ingest outdated sources without review.
```

---

## 8. PDF Selection Criteria

A PDF should be accepted only if it meets these criteria:

```text
from a reliable organization
publicly accessible or legally usable
relevant to psychological psychoeducation
clear publication source
clear topic coverage
not primarily opinion-based
not promotional
not medication-prescriptive for chatbot use
not diagnosis-focused for user-facing answers
```

Preferred source types:

```text
official health organization guides
clinical self-help workbooks
public mental health education PDFs
structured CBT worksheets
public crisis/safety frameworks
peer-reviewed methodology papers
```

Avoid:

```text
random blog PDFs
unverified self-help PDFs
commercial therapy marketing PDFs
old or unsupported clinical material
forums
social media posts
content without source organization
content that gives direct medication instructions
```

---

## 9. Multi-Index Structure

Do not put every document into one vector database collection.

Use separate collections/indexes:

```text
1. psychoeducation_index
2. coping_skills_index
3. safety_crisis_index
4. methodology_index
```

### 9.1 psychoeducation_index

Use for “what is it?” and “why does it happen?” questions.

Contains:

```text
anxiety
panic
depression
social anxiety
OCD
PTSD
self-esteem
sleep
stress
rumination
worry
```

Typical chunk types:

```text
definition
mechanism
symptom_info
common_experience
professional_support
```

### 9.2 coping_skills_index

Use when the user asks “what can I do?” or needs practical skills.

Contains:

```text
breathing
grounding
cognitive restructuring
behavioral activation
worry postponement
sleep hygiene
problem solving
mindfulness
values-based action
```

Typical chunk types:

```text
coping_step
exercise_instruction
reflection_prompt
skill_description
```

### 9.3 safety_crisis_index

Use only for safety-related situations.

Contains:

```text
self-harm safety
suicide prevention
emergency support
abuse and immediate danger
medication risk boundaries
severe crisis guidance
```

Typical chunk types:

```text
crisis_instruction
warning_sign
professional_escalation
safety_boundary
emergency_guidance
```

This index must not be used for normal psychoeducation unless risk is present.

### 9.4 methodology_index

Use for thesis/report/system justification.

Contains:

```text
RAG evaluation
mental health chatbot safety
hybrid retrieval
reranking
chunking methods
AI ethics
privacy
clinical AI limitations
```

This index should not be used for normal user answers.

---

## 10. PDF Ingestion Pipeline

Every PDF must pass through this pipeline:

```text
Collect source
↓
Register source in source_registry.json
↓
Extract text
↓
Clean text
↓
Preserve page numbers
↓
Detect sections and headings
↓
Create parent sections
↓
Create child chunks
↓
Assign metadata
↓
Validate chunks
↓
Embed chunks
↓
Index into correct collection
↓
Run retrieval tests
```

---

## 11. PDF Cleaning Rules

Before chunking, clean the PDF text.

Remove:

```text
repeated headers
repeated footers
page numbers inside body text
copyright repetition
navigation text
broken hyphenation
table of contents duplication
irrelevant appendix material
```

Preserve:

```text
page number metadata
section titles
subsection titles
bullet structure
exercise steps
warning statements
source attribution
```

---

## 12. Chunking Strategy

The system should use:

```text
semantic + section-aware + parent-child chunking
```

Avoid simple fixed-size chunking as the only method.

Bad approach:

```text
Split every PDF into 500-token chunks without structure.
```

Better approach:

```text
Detect sections
Create parent sections
Split into semantic child chunks
Preserve heading context
Attach metadata
Link child chunks to parent chunks
```

---

## 13. Parent-Child Chunking

Use two levels of chunks.

### Child Chunk

Purpose:

```text
precise retrieval
finding the most relevant small passage
```

Recommended size:

```text
150–300 tokens
```

### Parent Chunk

Purpose:

```text
provide enough surrounding context to the LLM
avoid fragmented meaning
```

Recommended size:

```text
700–1200 tokens
```

### Overlap

Recommended overlap:

```text
10–15%
```

or:

```text
1–2 paragraph overlap
```

Avoid excessive overlap because it can create duplicate retrieval noise.

---

## 14. Chunk Types

Every chunk should have a `chunk_type`.

Recommended chunk types:

```text
definition
mechanism
symptom_info
common_experience
coping_step
exercise_instruction
reflection_prompt
warning_sign
professional_support
crisis_instruction
boundary_policy
source_methodology
```

Examples:

```text
User asks: “What is anxiety?”
Preferred chunk_type: definition

User asks: “What can I do when I panic?”
Preferred chunk_type: coping_step or exercise_instruction

User shows self-harm risk:
Preferred chunk_type: crisis_instruction or professional_support
```

---

## 15. Chunk Metadata Schema

Every chunk must include metadata.

Recommended schema:

```json
{
  "chunk_id": "",
  "parent_id": "",
  "source_id": "",
  "source_title": "",
  "organization": "",
  "source_type": "",
  "topic": "",
  "subtopic": "",
  "chunk_type": "",
  "allowed_use": [],
  "not_allowed": [],
  "risk_level": "none | low | medium | high | crisis",
  "evidence_level": "",
  "language": "",
  "source_date": "YYYY-MM-DD",
  "last_reviewed": "YYYY-MM-DD",
  "page_number": 0,
  "section_title": "",
  "requires_disclaimer": true,
  "requires_safety_filter": false,
  "clinical_risk": "none | diagnosis | medication | crisis | eating_disorder | abuse"
}
```

Minimum required metadata:

```text
chunk_id
parent_id
source_id
source_title
organization
topic
chunk_type
allowed_use
not_allowed
risk_level
evidence_level
page_number
section_title
```

---

## 16. Chunk Validation

Before indexing, every chunk should be validated.

Check:

```text
Is the chunk too short?
Is the chunk too long?
Does it preserve meaning?
Does it include source metadata?
Does it include page number?
Does it include allowed_use?
Does it include not_allowed?
Does it have a clear chunk_type?
Does it contain medication or diagnosis risk?
Does it belong to the correct index?
```

If the chunk contains risky clinical content, mark it:

```json
{
  "requires_safety_filter": true,
  "clinical_risk": "medication"
}
```

---

## 17. RAG Decision Logic

RAG should not run for every message.

### Use RAG When

```text
the user asks for a psychological concept
the user asks why something happens
the user asks for coping strategies
the answer requires factual psychoeducation
the answer needs evidence grounding
the system needs source verification
```

### Use Limited RAG When

```text
the user mainly wants emotional support
the message is short and emotionally intense
the system should first respond with empathy
```

### Do Not Use Normal RAG When

```text
crisis is detected
self-harm risk is detected
harm to others is detected
immediate danger is detected
medication stopping/dosage request appears
abuse or violence risk appears
```

In these cases, use safety policy or safety_crisis_index only.

---

## 18. Query Builder

The user’s raw message should not be sent directly to retrieval.

Build the RAG query using:

```text
current user message
session summary
primary intent
secondary intents
risk level
target index
```

Example:

User message:

```text
Kalabalıkta herkes bana bakıyor gibi hissediyorum.
```

Generated retrieval query:

```text
social anxiety fear of negative evaluation anxious thoughts avoidance CBT psychoeducation coping
```

Query builder output:

```json
{
  "rag_query": "social anxiety fear of negative evaluation anxious thoughts avoidance CBT psychoeducation coping",
  "target_indexes": ["psychoeducation_index", "coping_skills_index"],
  "metadata_filters": {
    "topic": ["social_anxiety", "anxiety"],
    "allowed_use": ["psychoeducation", "coping_strategy"],
    "not_allowed_exclude": ["diagnosis", "medication_advice"]
  }
}
```

---

## 19. Hybrid Retrieval

Use hybrid retrieval instead of vector search only.

Recommended retrieval method:

```text
dense vector search
+ sparse / keyword search
+ rank fusion
```

Why:

```text
Dense search captures semantic meaning.
Sparse search captures exact terms.
Rank fusion combines both.
```

Recommended initial retrieval:

```text
Top 20–30 candidate chunks
```

Then send candidates to reranking.

---

## 20. Reranking

After initial retrieval, use reranking.

Reranking flow:

```text
Retrieve top 20–30 chunks
↓
Rerank by query-document relevance
↓
Select top 4–8 chunks
```

Reranking helps:

```text
reduce irrelevant context
improve answer grounding
lower hallucination risk
reduce token usage
```

---

## 21. Parent Context Expansion

Do not send only small child chunks to the answer generator.

Use this flow:

```text
Retrieve child chunk
↓
Find parent_id
↓
Load parent section
↓
Pass parent context to Evidence Pack
```

This prevents fragmented or misleading context.

---

## 22. Evidence Pack Builder

The final retrieval output should be formatted as an Evidence Pack.

Example:

```json
{
  "user_message": "",
  "primary_intent": "",
  "risk_level": "",
  "retrieval_confidence": 0.0,
  "retrieved_evidence": [
    {
      "source_title": "",
      "organization": "",
      "page_number": 0,
      "section_title": "",
      "chunk_text": "",
      "parent_context": "",
      "allowed_use": [],
      "not_allowed": [],
      "evidence_level": "",
      "chunk_type": ""
    }
  ],
  "rag_warnings": []
}
```

The Answer Generator should only use evidence that matches:

```text
user intent
allowed_use
risk level
response policy
```

---

## 23. Retrieval Confidence

The RAG system should calculate retrieval confidence.

Example:

```json
{
  "retrieval_confidence": 0.78,
  "source_quality": "high",
  "context_precision_estimate": "medium",
  "answer_allowed": true
}
```

Decision rule:

```text
0.80+     → strong evidence available
0.60–0.79 → usable evidence, cautious wording
0.40–0.59 → weak evidence, general answer only
<0.40     → no strong claim / fallback
```

---

## 24. RAG Failure Policy

If RAG does not retrieve reliable evidence:

```text
do not invent information
do not make strong claims
do not pretend the answer is evidence-based
use general, low-certainty psychoeducation if safe
or return fallback to the response system
```

Short rule:

```text
No reliable retrieval → no strong claim.
```

---

## 25. Source Traceability

Every factual answer must be internally traceable to sources.

The system does not need to show citations in every conversational answer.

However:

```text
If the user asks for sources, show sources.
If the output is a report or academic explanation, show sources.
If the answer includes factual psychoeducation, store source references internally.
If the retrieved source is weak, use cautious language.
```

Required internal trace fields:

```text
source_id
source_title
organization
page_number
section_title
chunk_id
parent_id
```

---

## 26. Safety-Aware Source Routing

The RAG system must route retrieval based on risk.

### Normal Psychoeducation

Use:

```text
psychoeducation_index
coping_skills_index
```

### Coping Strategy

Use:

```text
coping_skills_index
psychoeducation_index
```

### Crisis or Immediate Risk

Use:

```text
safety_crisis_index
```

Do not use normal psychoeducation chunks as crisis guidance.

### Methodology / Thesis

Use:

```text
methodology_index
```

Do not use methodology chunks in user-facing emotional responses.

---

## 27. Recommended Technology Stack

Recommended simple stack for a graduation project:

```text
Backend: FastAPI
Vector database: Qdrant or Chroma
PDF parsing: PyMuPDF / Unstructured / LlamaParse
Chunking: custom section-aware splitter
Embeddings: OpenAI embeddings / BGE / E5
Sparse retrieval: BM25 or Qdrant sparse vectors
Reranking: Cohere Rerank or cross-encoder reranker
Evaluation: RAGAS + custom safety tests
Database: PostgreSQL
```

Recommended practical stack:

```text
FastAPI
Qdrant
LlamaIndex or LangChain
RAGAS
PostgreSQL
```

Avoid overcomplicating the first version.

---

## 28. RAG Evaluation

The RAG system must be tested before being connected to the final answer system.

### Metrics

```text
retrieval precision
retrieval recall
context relevance
faithfulness
answer relevancy
hallucination rate
source attribution correctness
retrieval confidence accuracy
crisis source separation accuracy
medication boundary compliance
```

### Test Categories

```text
definition questions
coping strategy questions
mixed psychoeducation + coping questions
ambiguous questions
low-retrieval cases
no-retrieval cases
crisis cases
medication-related cases
abuse/immediate danger cases
off-topic cases
hallucination traps
source conflict cases
```

---

## 29. Example Test Case Format

Use this structure for RAG tests:

```json
{
  "test_id": "rag_social_anxiety_001",
  "user_message": "I feel like everyone is judging me in crowded places.",
  "expected_target_indexes": ["psychoeducation_index", "coping_skills_index"],
  "expected_topics": ["social_anxiety", "anxiety"],
  "expected_chunk_types": ["mechanism", "coping_step"],
  "must_not_retrieve": ["medication_advice", "diagnosis"],
  "expected_min_retrieval_confidence": 0.70
}
```

---

## 30. Implementation Phases

### Phase 1 — Source Registry

Build:

```text
source_registry.json
source approval rules
source tier labels
allowed_use / not_allowed rules
```

Done when:

```text
All sources are registered before ingestion.
No unapproved source enters the vector database.
```

### Phase 2 — PDF Parsing and Cleaning

Build:

```text
PDF parser
text cleaner
page number preservation
section title extraction
```

Done when:

```text
PDF text is clean, structured, and traceable to page numbers.
```

### Phase 3 — Chunking and Metadata

Build:

```text
parent chunk generator
child chunk generator
metadata generator
chunk validator
```

Done when:

```text
All chunks have metadata.
All chunks have parent-child links.
Risky chunks are flagged.
```

### Phase 4 — Indexing

Build:

```text
psychoeducation_index
coping_skills_index
safety_crisis_index
methodology_index
```

Done when:

```text
Each chunk is stored in the correct index.
Safety chunks are separated from normal psychoeducation chunks.
```

### Phase 5 — Retrieval Pipeline

Build:

```text
query builder
index router
metadata filter
hybrid retriever
reranker
parent context expander
```

Done when:

```text
The system retrieves relevant evidence for test queries.
Retrieved evidence is filtered by allowed_use and risk level.
```

### Phase 6 — Evidence Pack Integration

Build:

```text
evidence pack builder
retrieval confidence scorer
source traceability fields
RAG warnings
```

Done when:

```text
The response system receives clean, structured, source-grounded evidence.
```

### Phase 7 — RAG Evaluation

Build:

```text
RAG benchmark dataset
retrieval tests
RAGAS evaluation
custom safety retrieval tests
failure reports
```

Done when:

```text
Retrieval quality and safety separation are measurable.
RAG failures trigger fallback rules.
```

---

## 31. Recommended Folder Structure

```text
rag-system/
│
├── docs/
│   ├── rag_architecture.md
│   ├── source_selection_policy.md
│   ├── chunking_policy.md
│   ├── metadata_schema.md
│   ├── retrieval_pipeline.md
│   └── rag_evaluation_plan.md
│
├── sources/
│   ├── source_registry.json
│   ├── raw_pdfs/
│   ├── cleaned_text/
│   └── approved_sources/
│
├── src/
│   ├── ingestion/
│   │   ├── pdf_parser.py
│   │   ├── text_cleaner.py
│   │   └── section_detector.py
│   │
│   ├── chunking/
│   │   ├── parent_chunker.py
│   │   ├── child_chunker.py
│   │   ├── metadata_generator.py
│   │   └── chunk_validator.py
│   │
│   ├── indexing/
│   │   ├── index_router.py
│   │   └── vector_store.py
│   │
│   ├── retrieval/
│   │   ├── query_builder.py
│   │   ├── hybrid_retriever.py
│   │   ├── reranker.py
│   │   ├── parent_expander.py
│   │   └── evidence_pack_builder.py
│   │
│   └── evaluation/
│       ├── ragas_runner.py
│       ├── retrieval_tests.py
│       └── failure_analysis.py
│
├── schemas/
│   ├── source_registry.schema.json
│   ├── chunk_metadata.schema.json
│   ├── evidence_pack.schema.json
│   └── rag_test_case.schema.json
│
└── tests/
    ├── rag_benchmark_dataset.jsonl
    ├── test_retrieval.py
    ├── test_chunking.py
    ├── test_metadata.py
    └── test_safety_routing.py
```

---

## 32. Final RAG Design Decision

The final RAG system should be:

```text
Multi-index
Metadata-filtered
Hybrid-search based
Reranked
Parent-child chunked
Source-traceable
Safety-aware
Evaluation-ready
```

Final recommended configuration:

```text
Source count: 30–40
Recommended target: 34
Indexes: 4
Chunking: semantic + section-aware + parent-child
Child chunk: 150–300 tokens
Parent chunk: 700–1200 tokens
Overlap: 10–15%
Retrieval: hybrid search
Reranking: required
Metadata filtering: required
Source traceability: required
RAG fallback: required
Safety-crisis separation: required
```

---

## 33. Final Rule

The RAG system must not try to answer the user by itself.

Its job is:

```text
retrieve the right evidence
filter unsafe or irrelevant evidence
preserve source traceability
support the answer system
reduce hallucination risk
```

The answer system decides how to communicate the evidence safely.

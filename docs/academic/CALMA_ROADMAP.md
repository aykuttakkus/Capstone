# Calma Roadmap

## 1. Purpose

This document is the implementation roadmap for **Calma**, a local-first psychology-oriented RAG assistant.
It is written for a demo-grade but professionally structured system that can be shown to an advisor and then improved step by step.

## 2. Product Constraints

- Target device: local MacBook M4 Pro
- Budget: no paid cloud APIs for the current version
- Training: no fine-tuning for the current version
- Content source: PDFs will be uploaded manually by the team
- Tone: friendlier, warmer, less clinical
- Retention: realistic, but demo-friendly
- Privacy: a clear privacy notice is required

## 3. Recommended Base Stack

### 3.1 Model

- Primary model: `Qwen2.5 7B Instruct`
- Runtime: `Ollama`
- Why this choice:
  - strong instruction following
  - good multilingual behavior
  - works well with RAG
  - suitable for local demo usage
  - balanced quality vs. memory footprint on M4 Pro

### 3.2 Retrieval

- Hybrid retrieval: semantic + keyword + topic boost
- Vector store: FAISS
- Embeddings: local sentence-transformer model or fallback hash embeddings
- Evidence gate: required before generation

### 3.3 Memory

- Short-term session memory
- Long-term user summary memory
- Screening history memory
- Consent-aware storage

### 3.4 Safety

- Crisis detection
- Diagnosis refusal
- Medication refusal
- Off-domain refusal
- Prompt injection blocking
- Supervisor review for generated answers

## 4. Current System Snapshot

The current codebase already includes:

- authentication and onboarding
- intake questions
- PHQ-9 and GAD-7 screening
- RAG retrieval pipeline
- evidence gate
- safety policy engine
- assistant memory summaries
- conversation persistence
- conversation persistence

Current gaps:

- no real session restore API yet
- no session table yet
- message history is not modeled as first-class data
- `history` is sent to the backend but not fully used in generation
- uploaded PDFs are not yet a dedicated ingestion flow
- privacy and retention policy are not documented as a product contract

## 5. Target Architecture

```text
User
  -> Auth
  -> Onboarding / Consent
  -> Intake
  -> Screening
  -> Session Router
  -> Safety Triage
  -> Memory Fetch
  -> Hybrid Retrieval
  -> Evidence Gate
  -> LLM Generation
  -> Supervisor Review
  -> Persist Session / Messages / Summary
```

## 6. Data Model Plan

### 6.1 Core Tables

#### `users`
- id
- email
- hashed_password
- created_at
- display_name
- username
- last_phq9_score
- last_screening_date

#### `sessions`
- id
- user_id
- title
- topic
- status (`active`, `archived`, `deleted`)
- intake_json
- consent_json
- summary
- last_message_at
- created_at
- updated_at
- archived_at

#### `messages`
- id
- session_id
- user_id
- role (`user`, `assistant`)
- content
- intent
- route
- safety_mode
- sources_json
- created_at

#### `memories`
- id
- user_id
- summary_nuggets
- sentiment_trend
- preferences_json
- risk_flags_json
- updated_at

#### `screenings`
- id
- user_id
- session_id
- type (`phq9`, `gad7`)
- answers_json
- score
- severity
- crisis_flag
- created_at

#### `consents`
- id
- user_id
- consent_version
- intake_consent
- screening_consent
- privacy_notice_version
- accepted_at

### 6.2 Optional Future Tables

#### `knowledge_documents`
- id
- title
- source
- version
- uploaded_by
- uploaded_at

#### `knowledge_chunks`
- id
- document_id
- chunk_text
- chunk_metadata_json
- embedding_ref

## 7. Roadmap Phases

### Phase 0. Scope Lock and Product Decisions

Goal:
- freeze the demo scope before deeper implementation

Work items:
- confirm Calma positioning
- confirm local model choice
- confirm retention policy
- confirm PDF upload workflow
- confirm privacy notice language
- confirm that fine-tuning is out of scope for now

Deliverables:
- final scope note
- final model choice
- final data policy draft

Definition of done:
- no ambiguity about what Calma is and is not

Tests:
- scope review against product constraints
- model choice check against local M4 Pro limits
- privacy and retention consistency review

### Phase 1. Session Architecture

Goal:
- make each conversation a first-class session that can be reopened later

Work items:
- add `sessions` table
- add `messages` table
- move conversation persistence to message-level storage
- create `session_id` flow in backend
- add a session listing endpoint
- add session restore endpoint

Deliverables:
- reopenable chat sessions
- session list endpoint
- persisted chat turns

Definition of done:
- user can leave and reopen a session without losing the thread

Tests:
- session create integration test
- message persist and reload test
- session restore endpoint test
- unauthorized access rejection test

### Phase 2. Memory Design

Goal:
- separate short-term context from long-term user memory

Work items:
- keep session summary for current thread continuity
- keep user profile summary for cross-session personalization
- store screening outcomes separately
- use memory in prompt construction only when relevant

Deliverables:
- dual-memory architecture
- prompt-ready session summary
- user profile summary

Definition of done:
- the model receives compact memory, not raw chat dumps

Tests:
- memory update unit test
- session summary generation test
- prompt composition test
- safe fallback when memory is empty

### Phase 3. PDF Ingestion Pipeline

Goal:
- let the team upload PDFs and convert them into searchable knowledge chunks

Work items:
- PDF upload interface
- PDF parsing
- cleaning / normalization
- chunking strategy
- metadata tagging
- embedding generation
- index update flow

Deliverables:
- uploaded PDFs become retrievable knowledge
- source metadata is preserved

Definition of done:
- a PDF can be added, indexed, and retrieved without manual code edits

Tests:
- sample PDF parsing test
- chunking unit test
- index update smoke test
- source metadata preservation test

### Phase 4. Retrieval Quality

Goal:
- improve answer grounding and retrieval reliability

Work items:
- tune chunk size and overlap
- refine topic routing
- preserve hybrid retrieval
- keep evidence gate strict
- add answer source transparency
- optionally add reranking later

Deliverables:
- better source precision
- better answer grounding
- fewer unsupported responses

Definition of done:
- retrieved chunks are clearly relevant before generation starts

Tests:
- retrieval precision scenario tests
- evidence gate accept/reject tests
- source reference correctness tests
- retrieval fallback behavior test

### Phase 5. Safety and Clinical Boundaries

Goal:
- keep the assistant safe, bounded, and appropriate for mental health use

Work items:
- retain crisis routing
- retain diagnosis refusal
- retain medication refusal
- retain prompt-injection blocking
- make refusal responses friendlier
- keep supervisor review for final answer checks

Deliverables:
- clear safety policy
- stable refusal behavior
- crisis-sensitive handling

Definition of done:
- unsafe requests are handled consistently and politely

Tests:
- crisis keyword tests
- diagnosis refusal tests
- medication refusal tests
- prompt injection blocking tests
- supervisor override test

### Phase 6. Response Style and Conversation Flow

Goal:
- make the assistant feel warm, calm, and consistent in text-only responses

Work items:
- refine assistant response style
- keep answer formatting consistent
- soften refusal language
- improve source reference wording
- keep onboarding copy concise and friendly

Deliverables:
- friendlier assistant language
- cleaner response behavior
- more professional demo narrative

Definition of done:
- the assistant responses feel intentional, calm, and easy to explain in a demo

Tests:
- response format snapshot tests
- refusal tone tests
- source citation wording tests
- crisis message clarity tests

### Phase 7. Privacy and Retention

Goal:
- define how data is stored, for how long, and why

Proposed retention policy for the demo version:

- raw chat messages: 90 days
- session summaries: 1 year
- screening history: 1 year
- consent records: 1 year
- user-requested deletion: immediate

Work items:
- write privacy notice
- write consent notice
- document retention policy
- document delete behavior

Deliverables:
- plain-language privacy policy draft
- retention policy note

Definition of done:
- the product can be shown as privacy-aware and ethically bounded

Tests:
- consent state persistence test
- delete flow test
- retention policy documentation review
- privacy notice version test

### Phase 8. Evaluation and Quality Control

Goal:
- measure whether Calma is actually useful and safe

Work items:
- retrieval precision checks
- groundedness checks
- refusal correctness checks
- crisis routing checks
- session continuity checks
- empathy/tone checks

Deliverables:
- evaluation checklist
- scenario-based test cases
- issue log

Definition of done:
- critical flows are testable and repeatable

Tests:
- scenario-based evaluation run
- groundedness scoring
- refusal accuracy scoring
- crisis route smoke test

### Phase 9. Demo Readiness

Goal:
- prepare a polished version for advisor review

Work items:
- clean README
- final architecture diagram
- sample demo script
- seeded example PDFs
- stable onboarding and chat flow

Deliverables:
- advisor demo package
- presentation-ready product story

Definition of done:
- the system is easy to present, explain, and walk through

Tests:
- end-to-end demo smoke test
- seeded PDF flow test
- restart and login recovery test
- onboarding flow test

### Phase 10. Future Upgrade Path

Goal:
- preserve a clear next step after the demo

Possible future work:
- small LoRA or adapter tuning if hardware becomes available
- better reranking
- session search
- analytics dashboard
- source versioning
- multi-user management

Tests:
- no mandatory tests in this phase; future features should introduce their own test gates

## 8. Ownership Split

### What I will handle

- architecture design
- backend implementation
- data model changes
- session restore API
- PDF ingestion flow
- memory integration
- safety and routing work
- documentation updates

### What you will provide

- PDFs to upload
- approval of the tone and wording
- review of privacy notice language
- confirmation of demo policy choices
- any additional topic-specific documents

## 9. Immediate Implementation Order

The next steps should be done in this order:

1. session table and message table
2. session restore API
3. prompt context from session summary and memory
4. PDF upload and ingestion pipeline
5. privacy notice and retention policy
6. safety and response-style polishing
7. evaluation pass

## 10. Non-Goals for the Current Version

- fine-tuning
- cloud-paid inference
- live clinician workflows
- medical diagnosis
- medication recommendations
- emergency service replacement

## 11. Final Decision

Calma should be built as a **local-first, session-aware, privacy-conscious, evidence-grounded mental health RAG assistant**.

For the current demo, the correct strategy is:

- keep the model local
- keep the scope bounded
- keep the corpus curated
- keep the memory compact
- keep the safety rules strict
- keep the tone warm and supportive

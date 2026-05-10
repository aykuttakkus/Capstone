# Calma Zero-Cost Execution Plan

## Purpose

This document converts the zero-cost improvement backlog into an execution plan.
The goal is to improve Calma without paid infrastructure, paid APIs, or fine-tuning.

## Operating Rules

- keep everything local
- do not add cloud dependencies
- do not add paid services
- do not add fine-tuning
- do not change the UI/UX unless a backend capability strictly needs it
- every phase must pass its own tests before the next phase starts

## Current Baseline

Calma already has:

- auth and onboarding
- intake and screening
- session persistence and restore
- dual-memory behavior
- PDF ingestion
- hybrid retrieval
- evidence gate
- safety routing
- privacy and retention docs
- demo package

The remaining work is about making the product easier to control, audit, and present.

## Phase 0. Freeze Baseline

### Goal

Lock the current working state before adding zero-cost enhancements.

### Work Items

- confirm the current model choice stays `Qwen2.5 7B Instruct`
- confirm local runtime stays Ollama
- confirm the current corpus remains the authoritative corpus
- keep current tests as the baseline gate
- record the current state in docs

### Deliverables

- frozen baseline note
- stable default config
- no accidental scope drift

### Tests

- full unit test suite must pass
- Python compile check must pass
- demo smoke test must still pass

### Exit Criteria

- no baseline regression
- all current tests pass

## Phase 1. Session Management Tools

### Goal

Make past sessions easier to find and manage.

### Work Items

- session search by title, topic, date, and safety mode
- session archive action
- session delete action
- session export as JSON or Markdown

### Deliverables

- search endpoint
- archive endpoint
- delete endpoint
- export endpoint

### Tests

- search returns the expected sessions
- archive changes session status correctly
- delete removes or hides the session as intended
- export contains the expected session content and metadata

### Exit Criteria

- users can manage their session history locally without paid infrastructure

## Phase 2. Corpus Governance

### Goal

Make the PDF corpus auditable and versioned.

### Work Items

- add corpus version labels
- track which PDFs were indexed in each version
- keep inventory history for uploaded PDFs
- make reindexing deterministic
- optionally support OCR for scanned PDFs if needed

### Deliverables

- versioned inventory file
- versioned processed corpus file
- clear reindex command output

### Tests

- versioned corpus files are written correctly
- inventory tracks indexed vs skipped PDFs
- reindexing produces stable outputs
- corpus loading still works after versioning

### Exit Criteria

- corpus changes are traceable and repeatable

## Phase 3. Retrieval Transparency

### Goal

Make grounding and retrieval easier to inspect.

### Work Items

- retrieval diagnostics logging
- chunk reason tags
- top-k trace output
- source preview metadata in responses

### Deliverables

- debug-friendly retrieval logs
- clearer source metadata in answers
- better explainability for advisor review

### Tests

- top chunks are deterministic for the same query
- diagnostic output includes scores and topics
- response metadata still contains source references

### Exit Criteria

- every answer can be traced back to a small set of retrieved chunks

## Phase 4. Feedback and Evaluation

### Goal

Capture lightweight quality feedback and strengthen offline evaluation.

### Work Items

- helpful / not helpful feedback capture
- short comment field for answer quality
- expand the golden evaluation dataset
- keep offline evaluation script current

### Deliverables

- local feedback records
- larger eval dataset
- repeatable evaluation report

### Tests

- feedback entries are stored locally
- evaluation set loads correctly
- route, safety, and groundedness metrics remain stable

### Exit Criteria

- quality can be measured without paid analytics

## Phase 5. Memory Refinement

### Goal

Improve continuity while keeping prompts compact.

### Work Items

- better session title generation
- memory pruning for stale or duplicated nuggets
- clearer separation of session memory and long-term memory
- optional memory summary view for debugging

### Deliverables

- cleaner memory summaries
- more stable session titles
- controlled memory growth

### Tests

- summary remains compact
- session titles are readable
- memory pruning does not break continuity

### Exit Criteria

- memory helps continuity without creating noise

## Phase 6. Safety and Boundary Polish

### Goal

Keep boundary handling consistent and clear.

### Work Items

- more refusal test cases
- improved crisis phrasing
- improved off-domain phrasing
- prompt injection examples in the eval set

### Deliverables

- stronger safety wording
- broader refusal coverage in tests
- clearer crisis behavior

### Tests

- crisis routing still works
- diagnosis refusal still works
- medication refusal still works
- prompt injection is still blocked

### Exit Criteria

- safety remains stable after all improvements

## Phase 7. Demo Documentation Polish

### Goal

Make the project easy to present and freeze.

### Work Items

- keep the demo package updated
- keep seed PDF guidance current
- add one-page setup instructions if needed
- add one-page architecture summary if needed

### Deliverables

- polished demo materials
- clear advisor-facing explanation

### Tests

- demo smoke test still passes
- documentation references current behavior

### Exit Criteria

- the project is ready to submit without adding new features

## Recommended Order

1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3
5. Phase 4
6. Phase 5
7. Phase 6
8. Phase 7

## What We Are Not Doing

- fine-tuning
- paid APIs
- cloud inference
- cloud vector databases
- multimodal features
- large analytics dashboards
- heavy multi-agent expansion
- major UI redesigns

## Final Rule

If a change does not improve trust, control, explainability, or demo reliability, it should not be added.

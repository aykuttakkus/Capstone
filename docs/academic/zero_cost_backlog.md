# Calma Zero-Cost Improvement Plan

## Objective

Improve Calma without adding any paid infrastructure, paid APIs, or fine-tuning.
This plan only includes features that can be built locally with the current stack.

## Current Baseline

Calma already has:

- authentication
- onboarding and consent
- intake and screening
- session persistence and restore
- dual memory
- PDF ingestion
- hybrid retrieval
- evidence gate
- safety routing
- privacy and retention docs
- demo package

So the remaining work should focus on **operability, transparency, and data control**.

## Priority 1. Session Management Tools

### What to add

- session search by title, topic, and date
- session archive
- session delete
- session export

### Why it matters

- makes the app easier to use in real demos
- improves data control and privacy
- helps you reopen relevant chats fast

### Acceptance criteria

- user can search past sessions locally
- user can archive or delete a session
- user can export a session as JSON or Markdown

## Priority 2. Corpus Governance

### What to add

- PDF corpus versioning
- source inventory history
- reindex command with clear output
- optional OCR for scanned PDFs

### Why it matters

- keeps retrieval auditable
- makes updates safer
- helps explain what changed between demo versions

### Acceptance criteria

- each PDF batch has a version label
- reindexing produces deterministic outputs
- inventory shows what was included or skipped

## Priority 3. Retrieval Transparency

### What to add

- retrieval diagnostics output
- chunk reason tags
- source preview panel data in API response
- top-k trace logging

### Why it matters

- easier debugging
- stronger evidence story
- better advisor explanation

### Acceptance criteria

- every answer can show where the top chunks came from
- retrieval logs explain why a chunk was selected

## Priority 4. Feedback and Evaluation

### What to add

- helpful / not helpful feedback capture
- short user comment on answer quality
- expanded golden dataset
- nightly offline eval script

### Why it matters

- gives you improvement data without paying for analytics
- helps measure groundedness and refusal quality
- supports a serious demo story

### Acceptance criteria

- feedback is stored locally
- evaluation runs offline
- each test category has a stable baseline score

## Priority 5. Memory Refinement

### What to add

- better session title generation
- memory pruning for stale or duplicate nuggets
- clearer separation of session memory and long-term memory
- optional user memory summary viewer

### Why it matters

- improves continuity without adding model cost
- keeps prompts smaller and cleaner
- reduces memory noise

### Acceptance criteria

- session titles are readable and meaningful
- memory summaries do not grow without bound
- old or duplicated memory is pruned safely

## Priority 6. Safety and Boundary Polish

### What to add

- more refusal examples in tests
- crisis wording tuning
- off-domain wording tuning
- prompt injection examples in evaluation

### Why it matters

- improves trust
- lowers risk without new infrastructure
- strengthens the mental-health positioning

### Acceptance criteria

- refusal messages stay supportive and short
- crisis prompts continue to route correctly
- prompt injection attempts are consistently blocked

## Priority 7. Demo Polish

### What to add

- one-page setup note
- one-page demo checklist
- one-page architecture summary
- seed PDF list with version labels

### Why it matters

- makes presentation easier
- keeps the project explainable
- avoids scope creep

### Acceptance criteria

- another person can run the demo from docs alone
- the advisor can understand the architecture in a few minutes

## What Not To Build

These are not worth adding for a zero-cost finish:

- fine-tuning
- paid inference
- paid analytics
- cloud vector DBs
- big UI redesigns
- large multi-agent expansion
- web search integration
- multimodal features

## Recommended Order

1. session search, archive, delete, export
2. PDF corpus versioning
3. retrieval diagnostics
4. feedback and evaluation capture
5. memory refinement
6. safety wording polish
7. demo documentation polish

## Final Rule

If a feature does not improve trust, explainability, or local control, it should not be added.

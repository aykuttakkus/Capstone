# Calma Zero-Cost Roadmap

## Goal

Close Calma as a fully local, zero-cost demo project with the strongest possible safety, retrieval, and session continuity under the current hardware constraint (MacBook M4 Pro).

## Research-Based Stack

### LLM

Recommended default: `Qwen2.5 7B Instruct`

Why:
- runs locally through Ollama
- strong instruction following
- multilingual support
- good JSON / structured output behavior
- balanced memory footprint for demo use

Backup options:
- `Llama 3.1 8B` if reasoning / long-context becomes more important than footprint
- `Gemma 3 4B` if you need a smaller model footprint

### Embeddings

Best zero-cost options:
- `mxbai-embed-large-v1` for retrieval quality
- `nomic-embed-text-v1.5` for long-context retrieval and flexible embedding dimensions

Current project can keep its existing embedding backend if stability matters more than a marginal retrieval gain.

### Retrieval

- keep hybrid retrieval
- keep topic alignment
- keep evidence gate strict
- keep curated PDF corpus only

### Memory

- keep session memory
- keep long-term user summary memory
- keep screening history
- do not add heavy memory systems

### Safety

- keep deterministic keyword safety
- keep LLM-based nuanced safety as a second layer
- keep supervisor review

## What Is Already Good Enough

The current system already has:
- auth
- onboarding
- screening
- session persistence
- session restore
- dual-memory behavior
- PDF ingestion
- hybrid retrieval
- evidence gate
- safety routing
- privacy and retention docs
- demo package

So the remaining work should be about **closing**, not expanding.

## Remaining Work

### 1. Data Management Finish

Add only the missing zero-cost utilities that help users or the demo:
- session search by title/topic
- session archive / delete
- data export for a single user
- PDF corpus versioning

### 2. Corpus Curation

Keep the corpus controlled and stable:
- continue using only PDFs you upload
- update processed corpus when PDFs change
- avoid web-scraped or uncontrolled sources

### 3. Final Evaluation Pack

Lock the final quality story:
- retrieval tests
- safety tests
- refusal tests
- session continuity tests
- demo smoke test

### 4. Demo Packaging

Keep the advisor-facing materials current:
- demo script
- architecture diagram
- seed PDFs list
- setup steps
- expected responses / boundaries

### 5. Privacy Closure

Keep the product honest and bounded:
- final privacy notice wording
- final retention note
- deletion flow wording

## Do Not Build Now

These add cost, risk, or scope without improving the zero-cost demo enough:
- fine-tuning
- cloud inference
- paid APIs
- large analytics dashboards
- multi-agent expansion beyond the current safety / retrieval flow
- full document search UI overhaul
- multimodal vision features
- heavy personalization systems

## Best Final Scenario

The best zero-cost closure is:

1. keep `Qwen2.5 7B Instruct` as the runtime model
2. keep hybrid RAG and evidence gate
3. keep the current memory design
4. expand only with session search, deletion, export, and PDF versioning if needed
5. freeze scope and present the project as a safe, local, evidence-grounded mental health assistant

## Recommended Remaining Order

1. session search and delete/export utilities
2. PDF corpus versioning
3. final evaluation report
4. demo rehearsal and documentation polish
5. freeze the repository for submission

## Final Rule

If a new feature does not reduce risk, improve trust, or make the demo easier to present, it should not be added.

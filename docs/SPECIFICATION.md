# SPECIFICATION: Safety-Aware RAG-Based Psychological Psychoeducation System v2.1

**STATUS:** Active Implementation  
**SOURCE:** `/docs/calma_new_system.md` (Original Specification)  
**REFERENCE:** `/docs/technical/IMPLEMENTATION_PLAN_v2.md` (Implementation Timeline)

---

## Quick Navigation

This document is a **reference index** to the official specification in `calma_new_system.md`. 

### Core Architecture
- **§1**: Purpose & System Goals
- **§2**: System Positioning (What it's NOT)
- **§3**: Core System Flow (38-step pipeline)

### Components (§4-§32)
- **§4**: Context Manager — Structured context package
- **§5**: Privacy & Data Minimization — 6 core privacy rules
- **§6**: Session Summary — Structured session tracking
- **§7**: User State — Temporary psychological context
- **§8**: Risk State — Separate safety tracking
- **§9**: Safety Triage — Explicit high-risk signals
- **§10**: Subtle Distress Monitor — Indirect distress + cumulative tracking
- **§11**: Intent Detection — Mixed intents (primary + secondary)
- **§12-13**: RAG Decision & Query Generation — Conditional retrieval
- **§14**: Knowledge Base Structure — 18 topics + metadata taxonomy
- **§15**: Evidence Retrieval — Metadata-filtered, risk-aware
- **§16**: Source Traceability & Citation — When to cite
- **§17**: Response Planner — Mode/tone/length selection
- **§18**: Response Modes — 8 distinct modes:
  - §18.1: Emotional Support Mode
  - §18.2: Psychoeducation Mode
  - §18.3: Coping Strategy Mode
  - §18.4: Symptom Exploration Mode
  - §18.5: Clarification Mode
  - §18.6: Crisis Mode
  - §18.7: Repair Mode
  - §18.8: Off-Scope Mode
- **§19-25**: Response Rules — Balance, length, language, generation, over-reassurance, dependency prevention, boundaries
- **§26**: Response Quality Rubric — 11-point evaluation
- **§27**: Safety & Faithfulness Critic — 15 safety checks
- **§28**: Dependency & Boundary Critic — 5 checks
- **§29**: Fallback Behavior — 8 explicit scenarios
- **§30**: Human Escalation Logic — When to recommend professional help
- **§31**: Memory Update — Privacy-aware session updates
- **§32**: Module I/O Contracts — Explicit JSON contracts for each module
- **§33**: Complete Decision Logic — Full pipeline sequencing
- **§34**: Minimum Viable Implementation — 15 required components
- **§35-36**: Evaluation Metrics & Test Dataset

---

## Implementation Mapping

See `docs/technical/IMPLEMENTATION_STATUS.md` for which sections are:
- ✅ **Implemented** (code + tests)
- 🟡 **Partial** (exists but incomplete)
- ❌ **Missing** (planned, not yet started)

---

## Read the Full Specification

**Location:** `/docs/calma_new_system.md`

This is your **single source of truth** for system design. All implementation decisions should align with this document.

---

## Questions During Implementation?

1. **Unclear requirement?** → Check `calma_new_system.md` §X
2. **Want to deviate from spec?** → Document the rationale in commit message
3. **Found an inconsistency?** → Create an issue, don't code around it

---

**Last Updated:** 2026-05-19  
**Next Review:** After Phase 1 completion (2026-05-26)


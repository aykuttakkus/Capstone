# CODE CLEANUP ANALYSIS
**Purpose:** Identify obsolete, redundant, and architecture-misaligned code before Phase 1  
**Status:** Draft Analysis  
**Action:** Phase 0 (Pre-Phase 1 cleanup)

---

## 1. Obsolete Agents (Remove or Deprecate)

### ❌ 1.1 SentimentAgent (`sentiment_agent.py`)
- **Purpose:** LLM-based sentiment analysis
- **Problem:** 
  - Orchestrator.py already has `_detect_sentiment()` (keyword-based, faster)
  - §27 (Safety Critic) & §28 (Dependency Critic) handle sentiment already
  - Calls LLM every time (expensive, slow)
- **Status:** REDUNDANT
- **Action:** DELETE (it's already replaced by keyword detection in orchestrator)
- **Lines to Remove:** 46 lines
- **Impact on Code:** 
  - `assistant.py` calls `SentimentProfile` which can use orchestrator output instead
  - Change: `sentiment = SentimentProfile(...)` → Use orchestrator plan's sentiment

---

### ❌ 1.2 SupervisorAgent (`supervisor.py`)
- **Purpose:** Final LLM-based safety check before response
- **Problem:**
  - §27 (Safety & Faithfulness Critic) provides this as code
  - §28 (Dependency & Boundary Critic) provides this as code
  - LLM-based approach is slow + unreliable
  - Conflicts with new criitc-based architecture
- **Status:** SUPERSEDED
- **Action:** REPLACE with SafetyCritic + DependencyCritic (formalized, deterministic)
- **Lines to Remove:** 34 lines
- **Impact:** Remove call in `assistant.py` (~line 504+), use critics instead

---

### ⚠️ 1.3 VADTracker (`vad_tracker.py`)
- **Purpose:** Track Valence-Arousal-Dominance emotional dimensions
- **Problem:**
  - Not mentioned in calma_new_system.md
  - Olds MI (Motivational Interviewing) legacy design
  - Unused in current `assistant.py`
  - Can replace with simpler distress levels (0-5)
- **Status:** UNUSED/LEGACY
- **Action:** DEPRECATE (keep for compatibility, don't use in new flow)
- **Lines:** 33 lines
- **Migration Path:** Replace `pace_instruction` with new Response Planner's tone setting

---

### ⚠️ 1.4 PatternDetector (`pattern_detector.py`)
- **Purpose:** Detect conversation patterns (rumination, avoidance, etc.)
- **Problem:**
  - Not clearly used in assistant.py
  - Some logic overlaps with distress_monitor
  - Spec mentions "Subtle Distress Monitor" (§10), not pattern_detector
- **Status:** PARTIAL OVERLAP / UNUSED
- **Action:** AUDIT + CONSOLIDATE
  - If used: integrate into DistressMonitor
  - If unused: DEPRECATE
- **Lines:** 89 lines
- **Recommendation:** Check usages first before deleting

---

### ⚠️ 1.5 PhaseManager (`phase_manager.py`)
- **Purpose:** Track session phases (1-4) for MI-based conversations
- **Problem:**
  - Not in calma_new_system.md spec
  - Old design (MI phases for therapy-like flow)
  - New spec doesn't use phases
  - Can handle with session metadata instead
- **Status:** LEGACY / UNUSED
- **Action:** DEPRECATE (remove from pipeline, keep for migration if needed)
- **Lines:** 49 lines
- **Impact:** Update assistant.py to not call `phase_manager`

---

### ⚠️ 1.6 EmotionClassifier (`emotion_classifier.py`)
- **Purpose:** LLM-based emotion classification
- **Problem:**
  - Duplicate: orchestrator already detects sentiment
  - Calls LLM (slow)
  - Spec uses simpler risk levels (0-5) not emotion labels
- **Status:** REDUNDANT
- **Action:** DELETE (already replaced)
- **Lines:** 43 lines

---

### ⚠️ 1.7 ConversationStateEngine (`conversation_state.py`)
- **Purpose:** Track conversation state (distress, topics, etc.)
- **Problem:**
  - Some logic duplicates session_summary + user_state (§6-7)
  - Large file (126 lines), some unused fields
  - Overlaps with new Context Manager (§4)
- **Status:** PARTIAL OVERLAP
- **Action:** AUDIT + MERGE
  - Keep essential fields
  - Merge remaining into Context Manager
- **Lines:** 126 lines
- **Recommendation:** Review actual usage; refactor into Context Manager

---

## 2. Redundant Services/Files

### ❌ 2.1 clinical_state.py
- **Lines:** 43 lines
- **Purpose:** Track clinical state (unclear purpose)
- **Status:** UNUSED / UNCLEAR
- **Action:** DELETE or clarify usage
- **Check:** `grep -r "clinical_state" server/app/`

---

### ❌ 2.2 feedback_store.py
- **Lines:** 35 lines
- **Purpose:** Store feedback (?)
- **Status:** UNCLEAR
- **Action:** Check if still used; if not, DELETE

---

### ⚠️ 2.3 retrieval_debug.py
- **Lines:** 122 lines
- **Purpose:** Debug retrieval (diagnostics)
- **Status:** DEV ONLY (should not be in production flow)
- **Action:** Keep, but move to `tests/debug/` or mark clearly as dev-only
- **Don't use in:** Main pipeline

---

### 2.4 Services with Multiple Memory Systems
- `memory_store.py` (159 lines) — Long-term memory
- `memory_context.py` (242 lines) — Memory context building
- `memory_observability.py` (43 lines) — Memory observability
- **Problem:** 3 memory files, need consolidation
- **Action:** Review overlap; consolidate into single MemoryManager
- **Recommendation:** Phase 1.5 (post-Phase 1)

---

## 3. Code Cleanup Checklist (Phase 0)

### BEFORE Phase 1 Starts:

- [ ] **Audit Pattern Detector**
  - Check: `grep -r "pattern_detector" server/app/`
  - Action: Merge into distress_monitor or DELETE
  
- [ ] **Delete SentimentAgent**
  - Reason: Replaced by orchestrator keyword detection
  - Command: `rm server/app/core/agents/sentiment_agent.py`
  - Update: Remove imports from `assistant.py`
  
- [ ] **Delete SupervisorAgent**
  - Reason: Replaced by Safety + Dependency Critics
  - Command: `rm server/app/core/agents/supervisor.py`
  - Update: Remove calls from `assistant.py`
  
- [ ] **Delete EmotionClassifier**
  - Reason: Duplicate of sentiment detection
  - Command: `rm server/app/core/agents/emotion_classifier.py`
  - Update: Remove imports
  
- [ ] **Deprecate VADTracker**
  - Don't delete (for compatibility)
  - But don't use in new pipeline
  - Add comment: `# DEPRECATED - Use Response Planner's tone instead`
  
- [ ] **Deprecate PhaseManager**
  - Don't delete
  - Remove from assistant.py pipeline
  - Add comment: `# DEPRECATED - MI phases not in new spec`
  
- [ ] **Audit ConversationStateEngine**
  - Check actual usage
  - Merge into new Context Manager or keep slim version
  - Reduce from 126 lines to <50 lines
  
- [ ] **Audit clinical_state.py**
  - Check: `grep -r "clinical_state" server/app/`
  - If unused: DELETE
  
- [ ] **Audit feedback_store.py**
  - Check: `grep -r "feedback_store" server/app/`
  - If unused: DELETE
  
- [ ] **Mark retrieval_debug.py as DEV ONLY**
  - Add header: `# DEV ONLY - Debug utilities, don't use in production pipeline`
  - Keep but isolate
  
- [ ] **Review Response Planner (`response_planner.py`)**
  - Current: 140 lines
  - Check alignment with §17 (Response Planner spec)
  - May need refactoring in Phase 2

---

## 4. Cleanup Impact on assistant.py

**Current assistant.py:** 710 lines, imports:
```python
from server.app.core.agents.sentiment_agent import SentimentProfile  # DELETE
from server.app.core.agents.supervisor import SupervisorAgent        # DELETE
from server.app.core.agents.emotion_classifier import ...           # DELETE
from server.app.core.agents.vad_tracker import VADTracker           # DEPRECATE
from server.app.core.agents.phase_manager import phase_manager      # DEPRECATE
```

**Lines affected:** ~50-70 lines in assistant.py

**Cleanup tasks in assistant.py:**
1. Remove SentimentAgent calls
2. Remove SupervisorAgent calls  
3. Remove EmotionClassifier usage
4. Remove VADTracker usage
5. Remove PhaseManager calls
6. Update imports (delete 5 modules)

**Result:** assistant.py becomes ~650 lines (cleaner, focused)

---

## 5. Old Prompts to Review

### Prompt Files (`server/app/utils/prompts.py` or folder)
- Need to check what prompts are still used
- Old prompts referencing MI phases should be removed
- Prompts for removed agents should be deleted

**Action:**
```bash
grep -r "render_prompt" server/app/ | grep -E "(sentiment|supervisor|emotion|vad|phase)"
```
- Delete matching prompt definitions
- Keep only: orchestrator, generator, intent, RAG, safety, etc.

---

## 6. Summary: Code Cleanup Scope

| Category | Count | Action | Impact |
|----------|-------|--------|--------|
| Obsolete Agents | 3 | DELETE | -120 lines |
| Deprecated Agents | 2 | DEPRECATE | -80 lines (unused) |
| Partial Overlap | 2 | AUDIT/MERGE | -50 lines |
| Unused Services | 2 | DELETE | -70 lines |
| Unused Prompts | ~5 | DELETE | -100 lines |
| **Total Reduction** | | | **~420 lines** |

---

## 7. Revised Phase Structure

### NEW: Phase 0 (Pre-Phase 1)
**Timeline:** 1-2 days  
**Tasks:**
1. Run audits (grep for usage)
2. Delete obsolete agents (5 files)
3. Delete unused prompts
4. Update imports in assistant.py
5. Run existing tests (should still pass)
6. Commit: "refactor: remove obsolete agents (Phase 0)"

### Phase 1 (Week 1-2)
**After cleanup, add:**
1. Distress Monitor
2. Dependency Critic
3. Quality Critic
4. Fallback Handler
5. Taxonomy

### Phase 2 (Week 2-3)
**Extract pipeline modules** (on cleaner codebase)

### Phase 3 (Week 4)
**Testing + Documentation**

---

## 8. Risk Mitigation

| Risk | Mitigation |
|---|---|
| **Delete code that's actually used** | Run `grep -r` before deleting; check tests |
| **Break existing functionality** | Run full test suite after each cleanup; commit frequently |
| **Overlook deprecated code** | Add `# DEPRECATED` comments before removal |
| **Lose institutional knowledge** | Document why each module was removed (in commit message) |

---

## 9. Final Check: Spec Alignment

**Current Code Matches Spec (calma_new_system.md)?**

| Code Module | Spec §# | Status |
|---|---|---|
| SentimentAgent | N/A | ❌ NOT IN SPEC → DELETE |
| SupervisorAgent | §27 | ⚠️ Old approach → REPLACE |
| VADTracker | N/A | ❌ NOT IN SPEC → DEPRECATE |
| PhaseManager | N/A | ❌ NOT IN SPEC → DEPRECATE |
| EmotionClassifier | N/A | ❌ NOT IN SPEC → DELETE |
| ConversationStateEngine | §4? | ⚠️ Overlaps → AUDIT |
| clinical_state.py | N/A | ❌ UNCLEAR → CHECK |
| feedback_store.py | N/A | ❌ UNUSED? → CHECK |

---

## 10. Go/No-Go Decision

✅ **GO TO PHASE 1** if:
- [x] Phase 0 cleanup completed
- [x] All tests still pass
- [x] Imports cleaned up
- [x] No breaking changes to API routes
- [x] Commit history clean (`feat: remove X`, `refactor: Y`)

---

## Implementation Order (Phase 0)

1. **Day 1 (Audit & Analysis)**
   - Run all grep commands
   - Document findings
   - Create deletion checklist

2. **Day 2 (Cleanup)**
   - Delete obsolete agents (5 files)
   - Update imports in assistant.py
   - Delete unused prompts
   - Run tests
   - Commit

3. **Day 3 (Validation)**
   - Check no regressions
   - Run full test suite
   - Smoke test chat endpoint
   - Ready for Phase 1

---

**Status: READY TO AUDIT**  
**Next Step:** Execute Phase 0 before Phase 1 begins


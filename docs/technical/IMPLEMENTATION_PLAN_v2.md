# Implementation Plan v2.0
**Calma Psychology RAG System — calma_new_system.md → Production Code**

**Status:** Approved Design → Active Implementation  
**Target Duration:** 4 weeks  
**Approach:** Modular Refactor + Phased Delivery  
**Last Updated:** 2026-05-19

---

## 1. Overview & Philosophy

This plan bridges the **14 critical gaps** between `calma_new_system.md` specification and mevcut code, following a **3-phase rollout**:

1. **Phase 1 (Week 1-2): Core Additions** — Add missing critical components
2. **Phase 2 (Week 2-3): Module Extraction** — Refactor into clean pipeline layers
3. **Phase 3 (Week 4): Testing + Docs** — Comprehensive validation & documentation

**Architectural Principle:** Each module has a single responsibility, explicit input/output contracts (§32 in calma_new_system.md), and no cross-layer dependencies.

---

## 2. Phase 1: Core Additions (Week 1-2)

### 2.1 Task: Add Subtle Distress Monitor

**Current Gap:** §10 in spec but missing in code  
**Impact:** Cumulative risk tracking across turns  
**Location:** `server/app/core/agents/distress_monitor.py` (NEW)

#### 2.1.1 Module Specification

```python
# server/app/core/agents/distress_monitor.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class DistressSignal:
    category: str  # "hopelessness", "burden", "goodbye", "numbness", "withdrawal", "shame", "helplessness"
    confidence: float  # 0.0-1.0
    turn_number: int
    raw_text: str

@dataclass
class DistressAnalysis:
    subtle_signals_detected: list[DistressSignal]
    cumulative_risk_increase: bool  # True if pattern escalation detected
    risk_level_update: Optional[int]  # 0-5 (none, low, medium, high, crisis)
    recommendation: str  # Action: "monitor", "gentle_support", "safety_check", "escalate"

class SubtleDistressMonitor:
    """
    Detects indirect psychological distress signals per §10 of calma_new_system.md.
    
    Subtle signals tracked:
    - Hopelessness, meaninglessness
    - Feeling like a burden
    - Goodbye language
    - Sudden emotional numbness
    - Social withdrawal
    - Extreme shame
    - Extreme helplessness
    
    Cumulative escalation example:
      Turn 1: "I am tired." → LOW signal
      Turn 2: "Nothing feels meaningful." → MEDIUM signal
      Turn 3: "I feel like a burden." → HIGH signal
      Turn 4: "Soon everyone will be free of me." → CRISIS signal
    
    If pattern detected: increase risk sensitivity, trigger gentle safety check.
    """
    
    DISTRESS_KEYWORDS_TR = {
        "hopelessness": ["umutsuz", "umut yok", "anlamsız", "ne fayda", "boşuna"],
        "burden": ["yük", "sorun oluyorum", "engel", "başına belâ"],
        "goodbye": ["hoşça kalın", "elveda", "artık değilim", "yakında özgür"],
        "numbness": ["hiçbir şey hissetmiyorum", "uyuşmuş", "boş", "hiş"],
        "withdrawal": ["kimse görmek istemiyorum", "yalnız kalmak", "insanlardan uzak"],
        "shame": ["utanç", "rezil", "berbat insanım", "değersizim"],
        "helplessness": ["hiçbir şey yapamıyorum", "çaresizim", "kontrol edemiyorum"],
    }
    
    DISTRESS_KEYWORDS_EN = {
        "hopelessness": ["hopeless", "no point", "meaningless", "what's the use", "futile"],
        "burden": ["burden", "problem", "bother", "in the way", "weighing down"],
        "goodbye": ["goodbye", "farewell", "won't be here", "soon gone"],
        "numbness": ["can't feel", "numb", "empty", "nothing matters"],
        "withdrawal": ["don't want to see", "isolate", "stay alone", "avoid people"],
        "shame": ["ashamed", "worthless", "terrible person", "useless"],
        "helplessness": ["can't do anything", "powerless", "no control", "stuck"],
    }
    
    def analyze(
        self,
        current_message: str,
        recent_conversation: list[dict],  # [{"role": "user" | "assistant", "content": str}]
        current_risk_state: dict,  # {"current_risk_level": "none" | "low" | "medium" | "high" | "crisis"}
    ) -> DistressAnalysis:
        """
        Analyze current message + history for subtle distress patterns.
        Return escalation recommendation.
        """
        # 1. Detect signals in current message
        current_signals = self._detect_signals(current_message)
        
        # 2. Track cumulative pattern across recent turns
        user_messages = [m["content"] for m in recent_conversation if m.get("role") == "user"]
        cumulative_escalation = self._detect_cumulative_escalation(user_messages, current_signals)
        
        # 3. Recommend action
        recommendation = self._recommend_action(
            current_signals,
            cumulative_escalation,
            current_risk_state.get("current_risk_level", "none")
        )
        
        # 4. Suggest risk level update
        risk_update = self._update_risk_level(current_signals, cumulative_escalation)
        
        return DistressAnalysis(
            subtle_signals_detected=current_signals,
            cumulative_risk_increase=cumulative_escalation,
            risk_level_update=risk_update,
            recommendation=recommendation,
        )
    
    def _detect_signals(self, message: str) -> list[DistressSignal]:
        """Detect distress categories in single message."""
        normalized = message.lower().strip()
        signals = []
        
        # Check TR keywords
        for category, keywords in self.DISTRESS_KEYWORDS_TR.items():
            for keyword in keywords:
                if keyword in normalized:
                    signals.append(DistressSignal(
                        category=category,
                        confidence=0.8,  # TR keyword match = high confidence
                        turn_number=0,
                        raw_text=message,
                    ))
                    break  # One per category
        
        # Check EN keywords (if not already found)
        if not signals:
            for category, keywords in self.DISTRESS_KEYWORDS_EN.items():
                for keyword in keywords:
                    if keyword in normalized:
                        signals.append(DistressSignal(
                            category=category,
                            confidence=0.7,  # EN keyword = slightly lower
                            turn_number=0,
                            raw_text=message,
                        ))
                        break
        
        return signals
    
    def _detect_cumulative_escalation(
        self,
        recent_user_messages: list[str],
        current_signals: list[DistressSignal],
    ) -> bool:
        """
        Check if pattern escalates across turns.
        Returns True if same signal category appears 2+ times in recent history.
        """
        if len(recent_user_messages) < 2:
            return False
        
        # Count signal categories across history
        category_count = {}
        for msg in recent_user_messages:
            for signal in self._detect_signals(msg):
                category_count[signal.category] = category_count.get(signal.category, 0) + 1
        
        # Current message signals
        for signal in current_signals:
            if category_count.get(signal.category, 0) >= 1:
                return True  # Same category appears before + now
        
        return False
    
    def _recommend_action(
        self,
        signals: list[DistressSignal],
        escalation: bool,
        current_risk_level: str,
    ) -> str:
        """Recommend response strategy."""
        if escalation:
            return "safety_check"
        if signals and len(signals) >= 2:
            return "gentle_support"
        if signals:
            return "monitor"
        return "normal"
    
    def _update_risk_level(
        self,
        signals: list[DistressSignal],
        escalation: bool,
    ) -> Optional[int]:
        """
        Map signals to risk level.
        0=none, 1=low, 2=medium, 3=high, 4=crisis
        """
        if not signals:
            return None
        if escalation:
            return 3  # High
        if "burden" in [s.category for s in signals]:
            return 2  # Medium
        return 1  # Low
```

**Input/Output Contract (§32):**
```json
{
  "input": {
    "current_message": "string",
    "recent_conversation": [{"role": "user|assistant", "content": "string"}],
    "current_risk_state": {"current_risk_level": "none|low|medium|high|crisis"}
  },
  "output": {
    "subtle_signals_detected": [
      {
        "category": "hopelessness|burden|goodbye|numbness|withdrawal|shame|helplessness",
        "confidence": 0.0-1.0,
        "turn_number": int,
        "raw_text": "string"
      }
    ],
    "cumulative_risk_increase": boolean,
    "risk_level_update": 0-5 | null,
    "recommendation": "normal|monitor|gentle_support|safety_check|escalate"
  }
}
```

#### 2.1.2 Integration Point

In `server/app/services/assistant.py` _answer() method, after orchestrator.plan():

```python
# ~line 269 (after plan = self.orchestrator.plan())

distress_analysis = self.distress_monitor.analyze(
    current_message=reasoning_message,
    recent_conversation=history or [],
    current_risk_state=plan.risk_state if hasattr(plan, 'risk_state') else {},
)

# Update risk state if escalation detected
if distress_analysis.cumulative_risk_increase:
    plan.risk_level = max(plan.risk_level, distress_analysis.risk_level_update or 0)
    if distress_analysis.recommendation == "safety_check":
        # Trigger gentle safety check before normal answer
        should_clarify = True  # or insert safety question
```

**Dependencies:**
- None (pure function)

**Tests to Write:**
- `test_detect_signals_tr.py` — Test keyword matching (TR)
- `test_detect_signals_en.py` — Test keyword matching (EN)
- `test_cumulative_escalation.py` — Test multi-turn pattern
- `test_risk_update.py` — Test risk level mapping

---

### 2.2 Task: Add Dependency & Boundary Critic

**Current Gap:** §28 in spec but missing in code  
**Impact:** Prevent emotional dependency, enforce clinical boundaries  
**Location:** `server/app/core/agents/dependency_critic.py` (NEW)

#### 2.2.1 Module Specification

```python
# server/app/core/agents/dependency_critic.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class DependencyCriticResult:
    passed: bool
    failed_checks: list[str]  # e.g., ["creates_emotional_dependency", "overly_intimate"]
    rewrite_required: bool
    rewrite_instructions: list[str]
    risk_level: int  # 0=none, 1=low, 2=medium, 3=high

class DependencyCritic:
    """
    Per §28 of calma_new_system.md: Prevent emotional dependency and boundary crossing.
    
    Checks:
    1. Does the answer make the user emotionally dependent on the AI?
    2. Does it imply the AI is a therapist?
    3. Does it replace real-world support?
    4. Does it use overly intimate language?
    5. Does it encourage repeated reliance instead of coping skills?
    """
    
    # Patterns to AVOID (dependency-creating)
    DEPENDENCY_RED_FLAGS = {
        "always_available": [
            "i will always be here",
            "you can always come to me",
            "i'm here for you 24/7",
            "whenever you need",
            "any time, any place",
        ],
        "only_i_understand": [
            "only i understand you",
            "nobody else gets it like i do",
            "i know you better than",
            "you can only trust me",
        ],
        "isolation_from_support": [
            "you don't need anyone else",
            "forget what they said",
            "i'm all you need",
            "don't listen to them",
            "you can't trust others",
        ],
        "therapist_implication": [
            "i'm treating your",
            "this is therapy",
            "i'm your counselor",
            "as your therapist",
            "clinical treatment plan",
        ],
        "rescue_fantasy": [
            "i will fix this",
            "i will solve this for you",
            "trust me to handle this",
            "let me take over",
            "you don't have to do anything",
        ],
    }
    
    # Patterns ENCOURAGED (autonomy-supporting)
    GOOD_BOUNDARIES = {
        "supports_autonomy": [
            "you might consider",
            "one option is",
            "some people find it helpful",
            "it's up to you",
            "what works best for you",
        ],
        "real_world_support": [
            "a therapist might help",
            "a professional can",
            "someone you trust",
            "talking to a counselor",
            "professional support",
        ],
        "skill_building": [
            "you can practice",
            "try this technique",
            "one approach is",
            "consider trying",
            "here's a tool",
        ],
    }
    
    def critique(
        self,
        draft_response: str,
        context: dict,  # {"intent": "...", "risk_level": 0-5}
    ) -> DependencyCriticResult:
        """
        Check response for dependency-creating patterns.
        """
        normalized = draft_response.lower()
        failed_checks = []
        rewrite_instructions = []
        
        # Check 1: Emotional dependency language
        for pattern_group, patterns in self.DEPENDENCY_RED_FLAGS.items():
            for pattern in patterns:
                if pattern in normalized:
                    failed_checks.append(pattern_group)
                    rewrite_instructions.append(
                        f"Replace '{pattern}' with autonomy-supportive language"
                    )
        
        # Check 2: Presence of good boundaries
        has_good_boundary = any(
            pattern in normalized
            for patterns in self.GOOD_BOUNDARIES.values()
            for pattern in patterns
        )
        if not has_good_boundary and "emotional_support" in context.get("intent", ""):
            rewrite_instructions.append(
                "Add explicit reference to professional support or user autonomy"
            )
        
        # Check 3: High-risk contexts (crisis, high distress) may need extra care
        if context.get("risk_level", 0) >= 3:
            if not self._mentions_escalation(normalized):
                failed_checks.append("missing_escalation_in_high_risk")
                rewrite_instructions.append(
                    "Add explicit escalation to professional support given risk level"
                )
        
        passed = len(failed_checks) == 0
        risk_level = len(failed_checks)
        
        return DependencyCriticResult(
            passed=passed,
            failed_checks=failed_checks,
            rewrite_required=not passed,
            rewrite_instructions=rewrite_instructions,
            risk_level=risk_level,
        )
    
    @staticmethod
    def _mentions_escalation(text: str) -> bool:
        """Check if response includes escalation to professional."""
        escalation_markers = [
            "professional",
            "therapist",
            "counselor",
            "psychiatrist",
            "doctor",
            "mental health",
            "emergency",
            "crisis line",
            "emergency services",
        ]
        return any(marker in text for marker in escalation_markers)
```

**Input/Output Contract (§32):**
```json
{
  "input": {
    "draft_response": "string",
    "context": {
      "intent": "emotional_support|psychoeducation|...",
      "risk_level": 0-5
    }
  },
  "output": {
    "passed": boolean,
    "failed_checks": ["creates_emotional_dependency", "overly_intimate", ...],
    "rewrite_required": boolean,
    "rewrite_instructions": ["string"],
    "risk_level": 0-3
  }
}
```

#### 2.2.2 Integration Point

In `server/app/services/assistant.py` _answer() method, after answer generation (~line 569):

```python
# After payload = self.generator.build_direct_response(...)

# NEW: Dependency & Boundary Critic
if plan.safety_mode == "normal":
    dependency_result = self.dependency_critic.critique(
        draft_response=payload.answer,
        context={"intent": plan.intent, "risk_level": plan.risk_level}
    )
    
    if dependency_result.rewrite_required:
        print(f"[CRITIC] Dependency check failed: {dependency_result.failed_checks}")
        # Rewrite using instructions
        payload = self.generator.build_direct_response(
            # ... same params ...
            safety_rewrite_instructions=dependency_result.rewrite_instructions,
        )
```

**Dependencies:**
- None (pure function)

**Tests to Write:**
- `test_red_flag_detection.py` — Test dependency patterns
- `test_good_boundary_detection.py` — Test positive patterns
- `test_escalation_check.py` — Test safety escalation
- `test_rewrite_instructions.py` — Test instruction generation

---

### 2.3 Task: Build Knowledge Base Taxonomy

**Current Gap:** §14 in spec (18 topics + metadata) missing in code  
**Impact:** Prevents misuse of chunks, enables filtering  
**Location:** `data/knowledge_base_taxonomy.json` (NEW) + metadata in chunks

#### 2.3.1 Taxonomy Definition

```json
{
  "version": "1.0",
  "topics": [
    {
      "topic_id": "anxiety",
      "name": "Anxiety Disorders",
      "subtopics": ["generalized_anxiety", "social_anxiety", "panic"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis", "medication_advice"],
      "evidence_level": "peer_reviewed",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "panic",
      "name": "Panic Disorder",
      "subtopics": ["panic_attack", "agoraphobia"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis", "medication_advice"],
      "evidence_level": "peer_reviewed",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "depression",
      "name": "Depression",
      "subtopics": ["major_depression", "persistent_depressive"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis", "medication_advice"],
      "evidence_level": "peer_reviewed",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "sleep",
      "name": "Sleep Issues",
      "subtopics": ["insomnia", "sleep_hygiene"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis", "medication_advice"],
      "evidence_level": "clinical_guideline",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "stress",
      "name": "Stress & Burnout",
      "subtopics": ["work_stress", "burnout"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis"],
      "evidence_level": "clinical_guideline",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "ocd",
      "name": "OCD",
      "subtopics": ["obsessions", "compulsions"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis", "medication_advice"],
      "evidence_level": "peer_reviewed",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "ptsd",
      "name": "PTSD & Trauma",
      "subtopics": ["trauma", "flashbacks"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis", "medication_advice"],
      "evidence_level": "peer_reviewed",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "self_esteem",
      "name": "Self-Esteem",
      "subtopics": ["confidence", "self_worth"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis"],
      "evidence_level": "clinical_self_help",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "social_anxiety",
      "name": "Social Anxiety",
      "subtopics": ["social_fear", "interaction_anxiety"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis", "medication_advice"],
      "evidence_level": "peer_reviewed",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "eating_disorders",
      "name": "Eating Disorders",
      "subtopics": ["anorexia", "bulimia", "binge_eating"],
      "allowed_uses": ["explanation"],
      "not_allowed": ["diagnosis", "medication_advice", "treatment_planning"],
      "evidence_level": "peer_reviewed",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "grief",
      "name": "Grief & Loss",
      "subtopics": ["bereavement", "loss"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis"],
      "evidence_level": "clinical_self_help",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "anger",
      "name": "Anger Management",
      "subtopics": ["anger_control", "rage"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis"],
      "evidence_level": "clinical_guideline",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "cbt_basics",
      "name": "CBT Basics",
      "subtopics": ["cognitive_reframing", "behavioral_activation"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis", "therapy_planning"],
      "evidence_level": "peer_reviewed",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "mindfulness",
      "name": "Mindfulness",
      "subtopics": ["meditation", "present_moment"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis"],
      "evidence_level": "peer_reviewed",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "grounding_techniques",
      "name": "Grounding Techniques",
      "subtopics": ["5_senses", "body_scan"],
      "allowed_uses": ["explanation", "coping_strategy"],
      "not_allowed": ["diagnosis"],
      "evidence_level": "clinical_guideline",
      "clinical_scope": "psychoeducation_only"
    },
    {
      "topic_id": "crisis_safety",
      "name": "Crisis Safety",
      "subtopics": ["self_harm_alternatives", "emergency_contacts"],
      "allowed_uses": ["explanation"],
      "not_allowed": ["therapy"],
      "evidence_level": "clinical_guideline",
      "clinical_scope": "safety_only"
    },
    {
      "topic_id": "abuse_safety",
      "name": "Abuse & Domestic Violence",
      "subtopics": ["emotional_abuse", "safety_planning"],
      "allowed_uses": ["explanation", "safety_resources"],
      "not_allowed": ["diagnosis", "therapy"],
      "evidence_level": "clinical_guideline",
      "clinical_scope": "safety_only"
    },
    {
      "topic_id": "medication_safety",
      "name": "Medication Safety Boundaries",
      "subtopics": ["medication_info", "side_effects"],
      "allowed_uses": ["explanation"],
      "not_allowed": ["medication_advice", "prescription_changes"],
      "evidence_level": "peer_reviewed",
      "clinical_scope": "information_only"
    }
  ]
}
```

#### 2.3.2 Implementation: Metadata in Chunks

Each knowledge base chunk should include:

```json
{
  "id": "chunk_12345",
  "content": "...",
  "topic": "anxiety",
  "subtopic": "generalized_anxiety",
  "content_type": "psychoeducation",
  "allowed_use": ["explanation", "coping_strategy"],
  "not_allowed": ["diagnosis", "medication_advice"],
  "risk_level": "low",
  "language": "en",
  "source_type": "clinical_self_help_guide",
  "evidence_level": "peer_reviewed",
  "clinical_scope": "psychoeducation_only",
  "requires_disclaimer": true,
  "source_date": "2024-01-15",
  "last_reviewed": "2025-03-10",
  "review_required": false
}
```

#### 2.3.3 Integration Point

In `server/app/core/retrieval/evidence_gate.py`, add metadata filtering:

```python
def _is_chunk_allowed_for_use(self, chunk: dict, intent: str, risk_level: int) -> bool:
    """Check if chunk's allowed_use matches current intent."""
    allowed_uses = chunk.get("allowed_use", [])
    
    # Map intent to use case
    use_case_map = {
        "psychoeducation": "explanation",
        "coping_strategy": "coping_strategy",
        "symptom_exploration": "explanation",
    }
    required_use = use_case_map.get(intent)
    
    if required_use not in allowed_uses:
        return False  # Disallow
    
    # Check not_allowed
    not_allowed = chunk.get("not_allowed", [])
    if any(category in not_allowed for category in ["diagnosis", "medication_advice"]):
        return False
    
    # Check clinical scope
    if risk_level >= 3 and chunk.get("clinical_scope") == "psychoeducation_only":
        # High-risk context needs safety focus, skip long explanations
        return False
    
    return True
```

**Dependencies:**
- Update `rebuild_index.py` to include metadata
- Update chunk ingestion pipeline

**Tests to Write:**
- `test_taxonomy_loading.py` — Verify taxonomy JSON
- `test_metadata_filtering.py` — Test use case filtering
- `test_evidence_gate_with_metadata.py` — Integration

---

### 2.4 Task: Formalize Quality Rubric

**Current Gap:** §26 in spec (11-point rubric) missing in code  
**Impact:** Systematic response validation  
**Location:** `server/app/core/agents/quality_critic.py` (NEW)

#### 2.4.1 Module Specification

```python
# server/app/core/agents/quality_critic.py

from dataclasses import dataclass

@dataclass
class QualityCriticResult:
    passed: bool
    failed_criteria: list[str]  # Which of 11 criteria failed
    rewrite_required: bool
    rewrite_guidance: str

class QualityCritic:
    """
    Per §26 of calma_new_system.md: Validate response quality across 11 criteria.
    """
    
    RUBRIC = {
        "intent_match": {
            "description": "Does the response answer what the user actually asked?",
            "check_fn": lambda resp, intent, user_msg: True,  # Requires LLM or semantic check
        },
        "emotional_attunement": {
            "description": "Does it match the user's emotional tone?",
            "check_fn": lambda resp, intent, user_msg: True,
        },
        "evidence_grounding": {
            "description": "Are factual claims supported by retrieved sources?",
            "check_fn": lambda resp, intent, user_msg: True,
        },
        "actionability": {
            "description": "Does it include a small useful step when appropriate?",
            "check_fn": lambda resp, intent, user_msg: intent not in ["emotional_support"] or "try" in resp.lower() or "consider" in resp.lower(),
        },
        "safety": {
            "description": "Does it avoid unsafe advice?",
            "check_fn": lambda resp, intent, user_msg: "don't" not in resp.lower()[:20] or "emergency" in resp.lower(),
        },
        "boundary": {
            "description": "Does it avoid diagnosis, therapy, and medication advice?",
            "check_fn": lambda resp, intent, user_msg: not any(
                term in resp.lower() for term in ["you have", "you have been diagnosed", "this is therapy"]
            ),
        },
        "question_discipline": {
            "description": "Does it ask at most one question?",
            "check_fn": lambda resp, intent, user_msg: resp.count("?") <= 1,
        },
        "non_repetition": {
            "description": "Does it avoid repeating previously ineffective advice?",
            "check_fn": lambda resp, intent, user_msg: True,  # Requires context
        },
        "clarity": {
            "description": "Is it short, clear, and understandable?",
            "check_fn": lambda resp, intent, user_msg: 50 < len(resp) < 1500,
        },
        "escalation_correctness": {
            "description": "Does it recommend professional or emergency help when needed?",
            "check_fn": lambda resp, intent, user_msg: True,  # Risk-dependent
        },
        "cultural_safety": {
            "description": "Does it avoid stereotypes and unsupported cultural assumptions?",
            "check_fn": lambda resp, intent, user_msg: True,  # Requires domain knowledge
        },
    }
    
    def critique(self, response: str, intent: str, user_message: str) -> QualityCriticResult:
        """Evaluate response against rubric."""
        failed = []
        
        for criterion_name, criterion in self.RUBRIC.items():
            check_result = criterion["check_fn"](response, intent, user_message)
            if not check_result:
                failed.append(criterion_name)
        
        passed = len(failed) == 0
        
        guidance = ""
        if failed:
            guidance = f"Failed criteria: {', '.join(failed)}. Review and rewrite."
        
        return QualityCriticResult(
            passed=passed,
            failed_criteria=failed,
            rewrite_required=not passed,
            rewrite_guidance=guidance,
        )
```

**Integration Point:**
```python
# In assistant.py, after generation
quality_result = self.quality_critic.critique(payload.answer, plan.intent, message)
if quality_result.rewrite_required:
    print(f"[QUALITY] Failed: {quality_result.failed_criteria}")
    # Rewrite
```

**Tests to Write:**
- `test_question_discipline.py` — Verify ≤1 question
- `test_clarity.py` — Check length range
- `test_boundary_enforcement.py` — Ensure no diagnosis slips

---

### 2.5 Task: Expand Fallback Handler

**Current Gap:** §29 in spec (8 scenarios) vs. generic fallback in code  
**Impact:** Safer defaults under uncertainty  
**Location:** Update `server/app/core/agents/orchestrator.py` OR create `fallback_handler.py`

#### 2.5.1 Scenarios to Handle

```python
class FallbackHandler:
    """Per §29 of calma_new_system.md: 8 explicit fallback scenarios."""
    
    def handle_rag_failure(self, topic: str, intent: str) -> str:
        """RAG retrieval fails → give general, non-diagnostic, low-certainty response."""
        return f"""I'm not finding specific information about {topic} in my sources right now.
        
        In general, what you're describing is something many people experience. While I can't give you specific guidance without reliable sources, speaking with a mental health professional might help you understand this better.
        """
    
    def handle_intent_uncertainty(self, message: str) -> str:
        """Intent confidence is low → give brief support + one clarifying question."""
        return f"""I want to make sure I understand you correctly.
        
        It sounds like something is on your mind. Could you tell me a bit more about what's most important to discuss right now?
        """
    
    def handle_risk_uncertainty(self, message: str) -> str:
        """Risk confidence is low → use safety-aware response + gentle check."""
        return f"""I want to make sure you're okay.
        
        You mentioned something that caught my attention. Are you feeling safe right now?
        """
    
    def handle_critic_failure(self) -> str:
        """Critic output fails → use conservative response."""
        return """I want to make sure I give you helpful advice. Let me be straightforward:
        
        What you're going through is important, and I want you to know that professional support can really help. If you're struggling, reaching out to a counselor or therapist is a great step.
        """
    
    def handle_memory_update_failure(self, answer: str) -> str:
        """Memory update fails → return answer anyway, don't block."""
        return answer  # Continue with current context, avoid assuming forgotten details
    
    def handle_retrieval_low_confidence(self) -> str:
        """Retrieved source is low confidence → avoid strong claims."""
        return """Based on general psychological knowledge, here's something that might help:
        
        [General, low-confidence response without claiming certainty]
        
        Of course, speaking with someone qualified would give you more specific insight.
        """
    
    def handle_ambiguous_emotional_message(self, sentiment: str) -> str:
        """User message is ambiguous but emotionally intense → stay safe."""
        return f"""I can sense this is important to you, and I'm glad you shared it.
        
        I want to support you well, so help me understand: What's the main thing you're dealing with right now?
        """
    
    def handle_low_retrieval_confidence(self) -> str:
        """Low retrieval confidence → no strong claim."""
        return """I'm not confident enough in the information I have to give you specific guidance.
        
        A mental health professional can give you much better support than I can here. Would you be open to talking to someone?
        """
```

---

### Summary: Phase 1 Deliverables

| Task | File | Lines | Status |
|---|---|---|---|
| Distress Monitor | `core/agents/distress_monitor.py` | ~150 | New |
| Dependency Critic | `core/agents/dependency_critic.py` | ~120 | New |
| Quality Critic | `core/agents/quality_critic.py` | ~100 | New |
| Fallback Handler | `core/agents/fallback_handler.py` | ~100 | New |
| Taxonomy JSON | `data/knowledge_base_taxonomy.json` | ~250 | New |
| Integration in assistant.py | `services/assistant.py` | +50 | Modify |
| Integration in evidence_gate.py | `core/retrieval/evidence_gate.py` | +30 | Modify |
| **Total New Code** | | ~750 | |

**Estimated Effort:** 5-6 days (1 dev)  
**Testing Overhead:** +3 days  
**Total Phase 1:** 1.5-2 weeks

---

## 3. Phase 2: Module Extraction (Week 2-3)

### 3.1 Create Core Pipeline Architecture

Instead of modifying `assistant.py` monolith (710 lines), extract into explicit modules:

```
server/core/pipeline/
├── __init__.py
├── context_manager.py         # §4
├── safety_triage.py           # §9
├── distress_monitor.py        # §10 (from Phase 1)
├── intent_detector.py         # §11
├── rag_decision.py            # §12-13
├── retrieval_engine.py        # §15
├── response_planner.py        # §17
├── response_modes/
│   ├── __init__.py
│   ├── emotional_support.py   # §18.1
│   ├── psychoeducation.py     # §18.2
│   ├── coping_strategy.py     # §18.3
│   ├── symptom_exploration.py # §18.4
│   ├── clarification.py       # §18.5
│   ├── crisis.py              # §18.6
│   ├── repair.py              # §18.7
│   └── off_scope.py           # §18.8
├── critics/
│   ├── __init__.py
│   ├── quality_critic.py      # §26
│   ├── safety_critic.py       # §27
│   └── dependency_critic.py   # §28 (from Phase 1)
├── fallback_handler.py        # §29 (from Phase 1)
└── memory_updater.py          # §31
```

### 3.2 Pipeline Orchestrator

```python
# server/core/pipeline/orchestrator.py

class PipelineOrchestrator:
    """
    Unified pipeline orchestration per calma_new_system.md §3.
    
    Coordinates all modules with explicit input/output contracts.
    """
    
    def __init__(self):
        self.context_manager = ContextManager()
        self.safety_triage = SafetyTriage()
        self.distress_monitor = SubtleDistressMonitor()
        self.intent_detector = IntentDetector()
        self.rag_decision = RAGDecision()
        self.retrieval_engine = RetrievalEngine()
        self.response_planner = ResponsePlanner()
        self.response_modes = ResponseModesFactory()
        self.quality_critic = QualityCritic()
        self.safety_critic = SafetyCritic()
        self.dependency_critic = DependencyCritic()
        self.fallback_handler = FallbackHandler()
        self.memory_updater = MemoryUpdater()
    
    async def process_message(
        self,
        user_message: str,
        session: ChatSession,
        db: AsyncSession,
    ) -> ChatResponse:
        """
        Execute full pipeline per calma_new_system.md §33.
        
        1. Build context package
        2. Safety Triage
        3. Subtle Distress Monitor
        4. Intent Detection
        5. RAG Decision
        6. Evidence Retrieval
        7. Response Planning
        8. Answer Generation
        9-11. Critics
        12. Fallback (if needed)
        13. Send Response
        14. Memory Update
        """
        
        # 1. Context Manager
        context = self.context_manager.build(user_message, session, db)
        
        # 2. Safety Triage
        safety_result = self.safety_triage.evaluate(user_message)
        if safety_result.mode != "normal":
            return self._handle_safety_intercept(safety_result, context)
        
        # 3. Subtle Distress Monitor
        distress = self.distress_monitor.analyze(
            user_message,
            context["recent_conversation"],
            context["risk_state"],
        )
        
        # 4. Intent Detection
        intent = self.intent_detector.detect(user_message, context)
        
        # 5. RAG Decision
        rag_decision = self.rag_decision.decide(intent, context)
        
        # 6-7. Evidence Retrieval (conditional)
        retrievals = []
        if rag_decision.needs_rag:
            retrievals = self.retrieval_engine.retrieve(
                query=rag_decision.query,
                intent=intent,
                risk_level=context["risk_state"]["current_risk_level"],
            )
        
        # 8. Response Planning
        plan = self.response_planner.plan(intent, context, retrievals)
        
        # 9. Answer Generation
        response_builder = self.response_modes.get(plan.mode)
        draft_answer = response_builder.generate(
            user_message=user_message,
            context=context,
            retrievals=retrievals,
            plan=plan,
        )
        
        # 10-12. Critics
        quality_result = self.quality_critic.critique(draft_answer, intent, user_message)
        if quality_result.rewrite_required:
            draft_answer = response_builder.rewrite(draft_answer, quality_result.rewrite_guidance)
        
        safety_result = self.safety_critic.critique(draft_answer, context, retrievals)
        if safety_result.rewrite_required:
            draft_answer = response_builder.rewrite(draft_answer, safety_result.rewrite_guidance)
        
        dependency_result = self.dependency_critic.critique(draft_answer, context)
        if dependency_result.rewrite_required:
            draft_answer = response_builder.rewrite(draft_answer, dependency_result.rewrite_instructions[0])
        
        # 13. Fallback (if all critics failed)
        if not all([quality_result.passed, safety_result.passed, dependency_result.passed]):
            draft_answer = self.fallback_handler.handle_critic_failure()
        
        # 14. Persist & Return
        await self._persist_interaction(db, session, user_message, draft_answer, context)
        
        # 15. Memory Update
        await self.memory_updater.update(db, session, user_message, draft_answer, context)
        
        return ChatResponse(
            session_id=session.id,
            answer=draft_answer,
            intent=intent.primary_intent,
            # ... other fields
        )
```

### 3.3 Integration with FastAPI

In `server/app/services/assistant.py`, replace _answer() with:

```python
async def _answer(
    self,
    message: str,
    user: User,
    session: ChatSession,
    db: AsyncSession,
    intake: dict,
    screening: dict,
    background_tasks: BackgroundTasks,
) -> ChatResponse:
    """Thin wrapper around PipelineOrchestrator."""
    return await self.pipeline_orchestrator.process_message(
        user_message=message,
        session=session,
        db=db,
    )
```

**Estimated Effort:** 8-10 days  
**Total Phase 2:** 2-2.5 weeks

---

## 4. Phase 3: Testing + Documentation (Week 4)

### 4.1 Test Coverage

**Unit Tests** (per module):
```
tests/unit/
├── agents/
│   ├── test_distress_monitor.py
│   ├── test_dependency_critic.py
│   ├── test_quality_critic.py
│   └── test_safety_critic.py
├── pipeline/
│   ├── test_context_manager.py
│   ├── test_intent_detector.py
│   ├── test_rag_decision.py
│   ├── test_response_planner.py
│   ├── test_response_modes.py
│   └── test_fallback_handler.py
└── retrieval/
    ├── test_metadata_filtering.py
    └── test_evidence_gate.py
```

**Integration Tests**:
```
tests/integration/
├── test_pipeline_happy_path.py
├── test_pipeline_safety_intercept.py
├── test_pipeline_low_confidence.py
└── test_pipeline_memory_update.py
```

**Expected Coverage:** 85%+ of core/

### 4.2 Documentation Updates

1. **SPECIFICATION.md** (symlink/copy of calma_new_system.md)
2. **ARCHITECTURE.md** — Pipeline diagram, module responsibilities
3. **API.md** — Input/Output contracts per §32
4. **IMPLEMENTATION_STATUS.md** — Tracking which §sections implemented

```markdown
# Implementation Status

| calma_new_system.md Section | Module | Status | Notes |
|---|---|---|---|
| §1 Purpose | — | ✅ | No code |
| §4 Context Manager | `context_manager.py` | ✅ | Phase 2 |
| §9 Safety Triage | `safety_triage.py` | ✅ | Existing + enhanced |
| §10 Subtle Distress | `distress_monitor.py` | ✅ | Phase 1 |
| §11 Intent Detection | `intent_detector.py` | ✅ | Phase 2 |
| ... | | | |
```

**Estimated Effort:** 4-5 days

---

## 5. Implementation Checklist

### Phase 1 (Week 1-2):
- [ ] Create `distress_monitor.py` + tests
- [ ] Create `dependency_critic.py` + tests
- [ ] Create `quality_critic.py` + tests
- [ ] Build `knowledge_base_taxonomy.json`
- [ ] Update `evidence_gate.py` with metadata filtering
- [ ] Update `assistant.py` integration points
- [ ] Create `fallback_handler.py`
- [ ] Run Phase 1 tests (aim for 80% pass)
- [ ] Commit: "feat: add critical safety modules (Phase 1)"

### Phase 2 (Week 2-3):
- [ ] Create `server/core/pipeline/` package
- [ ] Extract `context_manager.py`
- [ ] Extract `intent_detector.py`
- [ ] Extract `rag_decision.py`
- [ ] Extract `retrieval_engine.py`
- [ ] Extract `response_planner.py`
- [ ] Create `response_modes/` with 8 builders
- [ ] Create `PipelineOrchestrator`
- [ ] Integrate with `assistant.py`
- [ ] Run Phase 2 tests (aim for 85% pass)
- [ ] Commit: "refactor: extract pipeline modules (Phase 2)"

### Phase 3 (Week 4):
- [ ] Write remaining unit tests
- [ ] Write integration tests
- [ ] Update `docs/technical/ARCHITECTURE.md`
- [ ] Create `docs/technical/API.md` (§32 contracts)
- [ ] Create `docs/technical/IMPLEMENTATION_STATUS.md`
- [ ] Create `docs/SPECIFICATION.md` (reference)
- [ ] Archive old docs (move to `docs/archive/legacy/`)
- [ ] Final smoke tests
- [ ] Commit: "docs: finalize documentation (Phase 3)"

---

## 6. Risk Mitigation

| Risk | Mitigation |
|---|---|
| **Monolithic assistant.py breaks** | Create new modules in parallel; integrate incrementally |
| **Test coverage gaps** | Write tests as you go (TDD for Phase 2) |
| **LLM dependency (Ollama)** | All modules are LLM-agnostic; generators isolated |
| **Database state corruption** | Use transactions; test with SQLite in-memory |
| **Memory update bugs** | Fallback handler in place; never blocks response |

---

## 7. Success Criteria

✅ **Phase 1 Complete:**
- All 4 new modules working
- Metadata filtering in place
- 80%+ of tests passing
- No regressions in existing features

✅ **Phase 2 Complete:**
- Pipeline orchestrator working
- 8 response modes functional
- 85%+ test coverage
- Code matches calma_new_system.md 1-1

✅ **Phase 3 Complete:**
- Comprehensive documentation
- All 14 gaps closed
- 90%+ test coverage
- Ready for academic submission

---

**Next Step:** Begin Phase 1 implementation.  
**Estimated Completion:** May 19 + 4 weeks = June 16, 2026


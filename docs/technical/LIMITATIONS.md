# Known Limitations & Bias Disclosure

This document openly acknowledges the known limitations and potential sources of bias in Calma. Transparency about limitations is a core design principle of the system.

---

## 1. Not a Clinical Tool

**Calma is an educational assistant, not a clinical product.**

| What Calma is | What Calma is NOT |
|---------------|-------------------|
| A psychoeducational information tool | A therapist or psychiatrist |
| A guided first-step support system | A diagnostic engine |
| A safety-aware conversation assistant | A treatment recommendation system |
| A source-grounded RAG application | An emergency response service |

Any user seeking clinical diagnosis, medication advice, or emergency intervention must be directed to qualified human professionals.

---

## 2. Linguistic Limitations

### English-Only Safety Keywords

The keyword safety engine (`server/app/core/safety/policy.py`) is **English-only**. Crisis keywords, diagnosis triggers, and medication patterns are defined for English text only.

**Impact:** A Turkish-speaking user who types "Kendime zarar vermek istiyorum" (I want to hurt myself) will **not** trigger the crisis detector via the keyword layer. The LLM-based `SafetyGuardian` may catch this in production if the model has multilingual capability, but this is not guaranteed.

**Mitigation:** The UI disclaimer is shown in the user's language. Future versions should add Turkish keyword coverage.

### Informal Language and Slang

Highly informal or slang expressions of distress may bypass keyword detection. The agentic safety layer (LLM-based) provides a second line of defense for nuanced cases.

---

## 3. Cultural and Demographic Bias

### Western Clinical Framework

The knowledge base draws from sources produced primarily within Western clinical frameworks (DSM-5, NHS, NIMH, APA). **Mental health concepts, symptom descriptions, and help-seeking behaviors vary significantly across cultures.**

Examples of potential cultural gaps:
- **Somatization:** Many cultures express psychological distress through physical symptoms (headache, chest tightness, fatigue). The knowledge base may not adequately address this.
- **Stigma:** Help-seeking guidance assumes a Western attitude toward professional mental health support, which carries different social stigma in different contexts.
- **Family/collectivist framing:** Concepts like "burden to others" or "family pressure" may require culturally-informed responses that the knowledge base may not provide.

### English-Centric Knowledge Base

All source PDFs are in English. Non-English-speaking users receive responses translated or framed in an English-centric context.

---

## 4. Knowledge Base Coverage Gaps

The system is only as strong as its source coverage. Topics with fewer or lower-quality documents will have:
- Lower retrieval precision
- More frequent EvidenceGate abstentions (which is the correct behavior)
- Potentially incomplete psychoeducational coverage

Coverage gaps are visible through the `EvidenceGate` — when retrieval confidence is below threshold, the system abstains rather than fabricating an answer.

---

## 5. Retrieval Limitations

- **No real-time information:** The knowledge base is static. Events, new research, or updated clinical guidelines after the PDF ingestion date are not reflected.
- **Similarity ≠ correctness:** High semantic similarity between a query and a chunk does not guarantee the chunk is the most clinically appropriate resource.
- **Adversarial paraphrasing:** A sophisticated user who rephrases crisis language in unusual ways may bypass keyword-based safety detection. The dual-layer safety design (keyword + LLM) mitigates but does not eliminate this risk.

---

## 6. Local Deployment Limitations

Calma is designed as a **local-first application**:
- Requires a running Ollama instance with the Qwen2.5 7B model
- Requires local FAISS index
- Not suitable for multi-user production deployment without additional infrastructure
- No external monitoring or human oversight mechanism in the current version

---

## 7. Not Validated in a Clinical Population

Calma has not been tested with a clinical population, validated by mental health professionals, or approved by any regulatory body. It is an academic prototype intended to demonstrate the responsible application of RAG in a high-sensitivity domain.

---

*Last updated: 2026-05-09*

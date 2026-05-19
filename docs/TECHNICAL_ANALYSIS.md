# Project Analysis: Psychology-Oriented Mental Health RAG Assistant

## 1. Executive Summary
The **Psychology-Oriented Mental Health RAG Assistant** is a specialized Retrieval-Augmented Generation (RAG) platform designed for safe, evidence-grounded psychoeducational support. Unlike generic AI chatbots, this system prioritizes clinical safety, source transparency, and guided interaction. It is architected specifically for the mental health domain, where reliability and boundary-setting are more critical than conversational fluency.

## 2. Technical Architecture
The system follows a modular, decoupled architecture centered around a RAG pipeline and a multi-layered safety engine.

### 2.1 Core Components
- **Intake & Routing**: The system begins with a structured onboarding process to identify user needs, emotional themes, and potential risks before any generation occurs.
- **Hybrid Retrieval Engine**:
    - **Semantic Search**: Uses `sentence-transformers` and a **FAISS-backed vector store** (with a robust NumPy fallback) to find chunks with similar meaning.
    - **Keyword Search**: Implements a token-overlap mechanism to capture specific terminology.
    - **Hybrid Fusion**: Combines scores (70% semantic, 30% keyword) and applies a **topic-based boost** to refine relevance.
- **Evidence Gate**: A critical validation layer that ensures the retrieved information is strong enough to support an answer. If the confidence score is too low, the system abstains rather than halluncinating.
- **Safety Policy Engine**: A prioritized, rule-based system that detects:
    - Crisis/Self-harm signals (High priority)
    - Diagnosis-seeking (Refusal)
    - Medication/Treatment requests (Refusal)
    - Prompt injections
    - Off-domain requests

### 2.2 Data Layer
- **Curated Knowledge Base**: A high-quality corpus of trusted mental health resources (e.g., stress, anxiety, burnout, sleep).
- **Vector Store**: FAISS index for high-performance retrieval, optimized with L2 normalization for cosine similarity.

## 3. Key Design Philosophies
- **Safety-First**: The system is designed to be "helpful but bounded." It explicitly refuses to act as a clinician, providing redirection instead of diagnosis.
- **Transparency**: Every answer is grounded in retrieved sources, and the system includes a template-based fallback to ensure structured, source-cited responses even if the LLM backend is unavailable.
- **Explainability**: By using rule-based classifiers for intent and safety, the system provides clear rationale for its routing decisions (e.g., "crisis language detected" or "medication request detected").

## 4. Performance Vectors to Monitor
To ensure professional-grade performance, the following technical aspects should be evaluated:
1. **Retrieval Precision (nDCG/MRR)**: How accurately the hybrid retriever surfaces the most relevant chunks from the knowledge base.
2. **Refusal Correctness**: The accuracy of the safety engine in correctly identifying and refusing diagnostic/medical requests (False Positive vs. False Negative).
3. **Groundedness (Faithfulness)**: Ensuring the LLM generation stays strictly within the bounds of the retrieved evidence.
4. **Resiliency**: The reliability of the fallback mechanism when the primary LLM (Ollama) is under high latency or unavailable.

## 5. Conclusion
This project represents a sophisticated application of RAG in a high-stakes domain. It successfully bridges the gap between static information platforms and unrestricted AI by implementing rigorous safety layers and structured interaction flows. It is technically robust, academically grounded, and professionally positioned for psychoeducational use.

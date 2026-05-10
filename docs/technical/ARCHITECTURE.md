# Calma — System Architecture

This document describes the technical architecture of **Calma**, a psychology-oriented, safety-aware psychoeducational RAG assistant.

---

## 1. System-Level Flow

```mermaid
flowchart TD
    User(["👤 User"])
    Auth["🔐 Auth\n(JWT)"]
    Onboarding["📋 Onboarding\n& Consent"]
    Intake["💬 Intake\n(PHQ-9 / GAD-7)"]
    Orchestrator["🧠 Orchestrator"]

    KwSafety["⚡ Keyword Safety Engine\n(Deterministic — Fast Path)"]
    AgSafety["🤖 Agentic Safety Guardian\n(LLM-based — Nuanced Path)"]
    Immediate["🚨 Immediate Response\n(Crisis / Refusal)"]

    IntentTopic["🗂️ Intent Classifier\n+ Topic Router"]
    HybridRetriever["🔍 Hybrid Retriever"]

    FAISS["📐 FAISS Semantic\n(70% weight)"]
    Keyword["🔤 Keyword BM25\n(30% weight)"]
    Graph["🕸️ Graph Store\n(Context Boost +0.15)"]

    EvidenceGate{"🛡️ Evidence Gate\n(score ≥ 0.22?)"}
    Abstain["📭 Abstention Response\n(Insufficient Evidence)"]
    Generator["✍️ LLM Generator\n(Qwen2.5 7B via Ollama)"]
    Supervisor["🔬 Supervisor Agent\n(Post-generation Review)"]
    ResponseFormatter["📄 Response Formatter\n(Structured Output)"]

    User --> Auth --> Onboarding --> Intake --> Orchestrator

    Orchestrator --> KwSafety
    KwSafety -->|"Crisis / Med / Diag\nPrompt Injection"| Immediate
    KwSafety -->|Normal| AgSafety
    AgSafety -->|"Unsafe (nuanced)"| Immediate
    AgSafety -->|Safe| IntentTopic

    IntentTopic --> HybridRetriever
    HybridRetriever --> FAISS
    HybridRetriever --> Keyword
    HybridRetriever --> Graph
    FAISS & Keyword & Graph --> EvidenceGate

    EvidenceGate -->|"Fail"| Abstain
    EvidenceGate -->|"Pass"| Generator
    Generator --> Supervisor --> ResponseFormatter --> User
```

---

## 2. Safety Priority Chain

The safety system applies rules in strict priority order. Once a rule matches, later rules are not evaluated.

```mermaid
flowchart LR
    P1["Priority 1\n🚫 Prompt Injection\nIgnore/override/jailbreak"]
    P2["Priority 2\n🆘 Immediate Crisis\nSelf-harm / suicide intent"]
    P3["Priority 3\n⚠️ Risk Clarification\nAmbiguous distress"]
    P4["Priority 4\n💊 Medication Refusal\nDrug / treatment requests"]
    P5["Priority 5\n🩺 Diagnosis Refusal\nDisorder labelling requests"]
    P6["Priority 6\n🌐 Off-Domain\nNon-mental-health topics"]
    P7["Priority 7\n✅ Normal\nPsychoeducational request"]

    P1 --> P2 --> P3 --> P4 --> P5 --> P6 --> P7
```

Each priority level maps to a **SafetyMode** and triggers a different response template. The dual-layer design (keyword → LLM agentic) ensures both speed (deterministic path) and nuance recall (LLM path for paraphrase attacks).

---

## 3. Data Layer

```mermaid
erDiagram
    USERS {
        int id PK
        string email
        string hashed_password
        string display_name
        float last_phq9_score
        datetime last_screening_date
    }
    SESSIONS {
        int id PK
        int user_id FK
        string title
        string topic
        string status
        json intake_json
        json consent_json
        string summary
        datetime last_message_at
    }
    MESSAGES {
        int id PK
        int session_id FK
        string role
        string content
        string intent
        string route
        string safety_mode
        json sources_json
    }
    MEMORIES {
        int id PK
        int user_id FK
        json summary_nuggets
        string sentiment_trend
        json risk_flags_json
    }
    SCREENINGS {
        int id PK
        int user_id FK
        string type
        json answers_json
        int score
        string severity
        bool crisis_flag
    }
    CONSENTS {
        int id PK
        int user_id FK
        string consent_version
        bool intake_consent
        bool screening_consent
        datetime accepted_at
    }

    USERS ||--o{ SESSIONS : "has"
    SESSIONS ||--o{ MESSAGES : "contains"
    USERS ||--o| MEMORIES : "has"
    USERS ||--o{ SCREENINGS : "completes"
    USERS ||--o{ CONSENTS : "provides"
```

---

## 4. RAG Pipeline Detail

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant HR as HybridRetriever
    participant EG as EvidenceGate
    participant LLM as LLM Generator
    participant S as Supervisor

    U->>O: Send message + session context
    O->>O: Keyword safety check (deterministic)
    O->>O: Agentic safety check (LLM)
    O->>O: Intent classify + topic route
    O->>HR: retrieve(query, topic, k=5)
    HR->>HR: FAISS semantic search (70%)
    HR->>HR: Keyword BM25 search (30%)
    HR->>HR: Graph context boost (+0.15)
    HR->>HR: Merge + rerank
    HR-->>EG: ScoredChunk list
    EG->>EG: score ≥ 0.22 AND topic aligned?
    alt Insufficient evidence
        EG-->>U: Abstention response
    else Evidence passes
        EG->>LLM: Prompt with retrieved context
        LLM-->>S: Generated answer
        S->>S: Post-generation safety review
        S-->>U: Structured response + sources
    end
```

---

## 5. Deployment Architecture

```mermaid
flowchart LR
    subgraph Host["Local Machine / Docker Host"]
        subgraph FE["Frontend Container\n(port 8080)"]
            Vite["React + Vite\nSPA"]
        end
        subgraph BE["Backend Container\n(port 8000)"]
            FastAPI["FastAPI\nUvicorn"]
            Engine["RAG Engine\n+ Safety Layer"]
        end
        subgraph Data["Data Volume"]
            SQLite["SQLite DB\n(auth, sessions, memory)"]
            FAISS_IDX["FAISS Index\n(embeddings)"]
            PDFs["PDF Corpus\n(raw sources)"]
        end
        Ollama["Ollama\nQwen2.5 7B\n(local LLM)"]
    end

    FE -->|"HTTP REST\nVITE_API_URL"| BE
    BE --> Engine
    Engine --> Data
    Engine --> Ollama
```

### Deployment Notes

- The backend container runs in production-style mode by default.
- Local development keeps hot reload in `compose.override.yaml`, not in the base image contract.
- Runtime database and FAISS state persist through the named Docker volume `calma_store`.
- The backend runtime drops to a non-root user after preparing writable data paths.

---

## 6. Agent Ecosystem

| Agent | Role | Trigger |
|-------|------|---------|
| **Orchestrator** | Central coordinator — routes every message | Every request |
| **SafetyGuardian** | LLM-based nuanced safety analysis | After keyword safety passes |
| **SentimentAgent** | Detects emotional tone → adjusts response style | Every psychoeducation response |
| **MemoryAgent** | Reads/writes cross-session user memory | Session start/end |
| **RetrievalGrader** | CRAG-style evidence validation | After FAISS retrieval |
| **Supervisor** | Post-generation safety review | After LLM generation |

---

## 7. Layer Boundaries

The repository uses a one-way dependency flow so the RAG engine stays isolated from transport and delivery concerns.

| Layer | Canonical Modules | Responsibility |
|-------|-------------------|----------------|
| Interface | `server.app.api`, `server.run`, `client/` | HTTP transport, UI, request/response shaping |
| Application | `backend.app.services` | Orchestration, workflow coordination, persistence use-cases |
| Domain / Core | `backend.app.core` | Safety, routing, retrieval, generation, agent logic |
| Persistence / Infra | `backend.app.models`, `backend.app.core.database`, `backend.app.utils.io` | Storage models, DB access, file I/O |
| Shared config | `backend.app.config`, `backend.app.utils.prompts` | Static settings and prompt templates |

Allowed import direction:
- `backend.app.api` may import `services`, `core`, `models`, and shared utils.
- `backend.app.services` may import `core`, `models`, and shared utils.
- `backend.app.core` must not import `api` or `frontend`.
- `backend.app.models` may depend on persistence helpers only.
- `backend.app.utils` must stay generic and avoid depending on higher layers.

RAG boundary:
- The RAG engine lives in `backend.app.core`.
- Delivery code, UI code, and container entrypoints stay outside the engine.
- `backend.app.services.assistant` coordinates the engine but does not own retrieval or safety policy logic.

*Last updated: 2026-05-09*

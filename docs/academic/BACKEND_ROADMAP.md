# Backend Engineering Roadmap: Secure Identity & Persistence

This roadmap outlines the transformation of the Psychology RAG Assistant from a "Stateless Prototpye" into a "Production-Grade Secure Platform." We are adopting an industry-standard **Clean Architecture** with a decoupled Persistence Layer.

## Phase 1: The Persistence Layer (Data Sovereignty)
*Objective: Transition from JSON-file memory to an ACID-compliant Relational Database.*

- **[NEW] SQL Schema (`backend/app/models/sql/models.py`)**:
    - **Users Table**: `id`, `email` (unique index), `hashed_password`, `created_at`.
    - **Memories Table**: `id`, `user_id` (FK), `summary_nuggets`, `sentiment_trend`.
    - **Conversations Table**: `id`, `user_id` (FK), `query`, `response`, `timestamp`.
- **ORM Setup**: Implement **SQLAlchemy** with `Alembic` for database migrations.
- **SQLite Configuration**: Fast, local development database that can be swapped for PostgreSQL in Production.

## Phase 2: Identity & Security (Zero-Trust)
*Objective: Implement secure authentication using industry-best practices.*

- **Password Security**: Use `passlib` with `bcrypt` (12 rounds) to ensure passwords are never stored in plain text.
- **JWT Orchestration**: 
    - Implement **JSON Web Tokens (JWT)** for stateless session management.
    - Token structure: `sub` (user_id), `exp` (expiry), `iat` (issued at).
- **OAuth2 Flow**: Integrate FastAPI's `OAuth2PasswordBearer` to enable Swagger's "Authorize" lock mechanism.

## Phase 3: Service Layer Integration (Deep Memory)
*Objective: Link the Agentic RAG logic to personal user contexts.*

- **Contextual Loading**: Update `AssistantService` to require a `User` object.
- **Memory Hot-loading**: On each request, the system fetches the specific `user_id`'s memory nuggets from the SQL store before triggering RAG.
- **Automated Commit**: At the end of every `handle_message`, the `MemoryAgent` updates the SQL database automatically.

## Phase 4: API Presentation Layer
*Objective: Expose secured endpoints with interactive documentation.*

- **Endpoint Security**: Apply `Depends(get_current_user)` to all sensitive chat and profile endpoints.
- **Registration Flow**:
    - `POST /api/auth/register`: Validate email formats, hash password, store user.
- **Authentication Flow**:
    - `POST /api/auth/login`: Exchange credentials for a JWT Bearer token.
- **Swagger Optimization**: Enable global security schemes in FastAPI app config.

## Phase 5: Privacy & Compliance (Audit Ready)
*Objective: Align with Digital Health regulations (GDPR/KVKK).*

- **Data Encryption**: (Future) Implement AES-256 encryption at rest for sensitive clinical summaries stored in SQL.
- **Audit Trails**: Link `ClinicalAuditLogger` events to specific `user_id`s for clinician review.

---

## Technical Stack
- **Framework**: FastAPI (Asynchronous IO)
- **Database**: SQLite / PostgreSQL (via SQLAlchemy)
- **Security**: JWT + Bcrypt + OAuth2
- **Validation**: Pydantic v2 (Input/Output Schemas)

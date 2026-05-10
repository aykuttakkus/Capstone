from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from urllib import error, request

from server.app.api.auth.routes import router as auth_router
from server.app.api.chat.routes import router as chat_router
from server.app.api.feedback.routes import router as feedback_router
from server.app.api.journal.routes import router as journal_router
from server.app.api.mood.routes import router as mood_router
from server.app.api.profile.routes import router as profile_router
from server.app.api.screen.routes import router as screen_router
from server.app.api.sessions.routes import router as sessions_router
from server.app.core.config import (
    APP_NAME,
    AUDIT_LOG_RETENTION_DAYS,
    DEPLOYMENT_MODE,
    ENABLE_OLLAMA_FALLBACK,
    ENABLE_QDRANT_FALLBACK,
    ENABLE_GRAPH_RAG,
    EMBEDDING_MODEL,
    FAISS_INDEX_PATH,
    FRONTEND_ORIGINS,
    GRAPH_RAG_MIN_CHUNKS,
    GRAPH_RAG_MIN_QUERY_TERMS,
    MODEL_CONTRACT_VERSION,
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    RAW_CHAT_RETENTION_DAYS,
    ENABLE_RERANKER,
    RERANK_MAX_CHARS,
    RERANK_TOP_K,
    QDRANT_COLLECTION,
    QDRANT_URL,
    RETRIEVAL_BACKEND,
    ROLLOUT_MODE,
    ROLLOUT_TRAFFIC_PERCENT,
    SCREENING_RETENTION_DAYS,
    CONSENT_RETENTION_DAYS,
    SESSION_SUMMARY_RETENTION_DAYS,
    SENSITIVE_LOG_REDACTION_ENABLED,
)
from server.app.core.database import Base, engine
from server.app.core.retrieval.index_store import VectorIndexStore
from server.app.models.schemas.config import AppConfigResponse
from server.app.models.sql import models as _models  # noqa: F401
from server.app.services.flows.intake import INTAKE_QUESTIONS
from server.app.services.flows.intake_chat import intake_chat_engine
from server.app.services.flows.screening import GAD7_QUESTIONS, PHQ9_QUESTIONS, RESPONSE_OPTIONS
from server.app.services.assistant import get_service


app = FastAPI(title=f"{APP_NAME} RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(journal_router, prefix="/api")
app.include_router(mood_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(screen_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")


def _url_is_ready(url: str, timeout: float = 2.0) -> bool:
    try:
        with request.urlopen(url, timeout=timeout):
            return True
    except (error.URLError, TimeoutError, OSError):
        return False


def _ollama_ready() -> bool:
    return _url_is_ready(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags")


def _qdrant_ready() -> bool:
    return _url_is_ready(f"{QDRANT_URL.rstrip('/')}/healthz")


def _local_index_ready() -> bool:
    try:
        index_store = VectorIndexStore(FAISS_INDEX_PATH)
        _ = index_store.load()
        return True
    except Exception:
        return False


@app.on_event("startup")
async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    warmup_assistant_service()


def warmup_assistant_service() -> None:
    # Preload the singleton so the first chat request does not pay model init cost.
    get_service()


@app.get("/api/config", response_model=AppConfigResponse)
def get_config() -> AppConfigResponse:
    first_step = intake_chat_engine.get_first_question()
    return {
        "app_name": APP_NAME,
        "deployment_mode": DEPLOYMENT_MODE,
        "embedding_model": EMBEDDING_MODEL,
        "llm_model": OLLAMA_MODEL,
        "retrieval_backend": RETRIEVAL_BACKEND,
        "qdrant_url": QDRANT_URL,
        "qdrant_collection": QDRANT_COLLECTION,
        "enable_graph_rag": ENABLE_GRAPH_RAG,
        "graph_rag_min_chunks": GRAPH_RAG_MIN_CHUNKS,
        "graph_rag_min_query_terms": GRAPH_RAG_MIN_QUERY_TERMS,
        "rollout_mode": ROLLOUT_MODE,
        "rollout_traffic_percent": ROLLOUT_TRAFFIC_PERCENT,
        "enable_qdrant_fallback": ENABLE_QDRANT_FALLBACK,
        "enable_ollama_fallback": ENABLE_OLLAMA_FALLBACK,
        "model_contract_version": MODEL_CONTRACT_VERSION,
        "sensitive_log_redaction_enabled": SENSITIVE_LOG_REDACTION_ENABLED,
        "enable_reranker": ENABLE_RERANKER,
        "rerank_top_k": RERANK_TOP_K,
        "rerank_max_chars": RERANK_MAX_CHARS,
        "retention_days": {
            "raw_chat": RAW_CHAT_RETENTION_DAYS,
            "session_summary": SESSION_SUMMARY_RETENTION_DAYS,
            "screening": SCREENING_RETENTION_DAYS,
            "consent": CONSENT_RETENTION_DAYS,
            "audit_log": AUDIT_LOG_RETENTION_DAYS,
        },
        "status": "active",
        "intake_questions": INTAKE_QUESTIONS,
        "intake_chat_enabled": True,
        "first_intake_question": first_step.next_question or "",
        "phq9_questions": PHQ9_QUESTIONS,
        "gad7_questions": GAD7_QUESTIONS,
        "response_options": RESPONSE_OPTIONS,
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "app": APP_NAME}


@app.get("/ready")
async def readiness_check() -> dict[str, object]:
    ready_checks: dict[str, object] = {
        "database": False,
        "retrieval": False,
        "local_index": False,
        "qdrant": False,
        "ollama": False,
        "config": bool(APP_NAME and EMBEDDING_MODEL and OLLAMA_MODEL),
        "rollout_mode": ROLLOUT_MODE,
        "rollout_traffic_percent": ROLLOUT_TRAFFIC_PERCENT,
    }

    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        ready_checks["database"] = True
    except Exception:
        ready_checks["database"] = False

    try:
        ready_checks["local_index"] = _local_index_ready()
    except Exception:
        ready_checks["local_index"] = False

    ready_checks["qdrant"] = _qdrant_ready() if RETRIEVAL_BACKEND == "qdrant" else ready_checks["local_index"]
    retrieval_ok = bool(ready_checks["qdrant"] if RETRIEVAL_BACKEND == "qdrant" else ready_checks["local_index"])
    if RETRIEVAL_BACKEND == "qdrant" and not retrieval_ok and ENABLE_QDRANT_FALLBACK:
        retrieval_ok = bool(ready_checks["local_index"])
    ready_checks["retrieval"] = retrieval_ok

    ready_checks["ollama"] = _ollama_ready()

    overall = bool(ready_checks["database"] and ready_checks["retrieval"] and ready_checks["config"])
    if not ready_checks["ollama"] and not ENABLE_OLLAMA_FALLBACK:
        overall = False
    degraded = overall and (not bool(ready_checks["ollama"]) or (RETRIEVAL_BACKEND == "qdrant" and not bool(ready_checks["qdrant"]) and ENABLE_QDRANT_FALLBACK))
    status = "degraded" if degraded else ("ready" if overall else "not_ready")
    return {"status": status, "ready": overall, "degraded": degraded, "checks": ready_checks}

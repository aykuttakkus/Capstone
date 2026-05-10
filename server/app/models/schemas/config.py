from __future__ import annotations

from pydantic import BaseModel


class IntakeQuestion(BaseModel):
    id: str
    label: str
    options: list[str]


class ScreeningQuestion(BaseModel):
    id: str
    text: str


class AppConfigResponse(BaseModel):
    app_name: str
    deployment_mode: str
    embedding_model: str
    llm_model: str
    retrieval_backend: str
    qdrant_url: str
    qdrant_collection: str
    enable_graph_rag: bool
    graph_rag_min_chunks: int
    graph_rag_min_query_terms: int
    rollout_mode: str
    rollout_traffic_percent: int
    enable_qdrant_fallback: bool
    enable_ollama_fallback: bool
    model_contract_version: str
    sensitive_log_redaction_enabled: bool
    enable_reranker: bool
    rerank_top_k: int
    rerank_max_chars: int
    retention_days: dict[str, int]
    status: str
    intake_questions: list[IntakeQuestion]
    intake_chat_enabled: bool = True
    first_intake_question: str = ""
    phq9_questions: list[ScreeningQuestion]
    gad7_questions: list[ScreeningQuestion]
    response_options: list[str]

from __future__ import annotations


def test_config_exposes_governance_contract(api_client) -> None:
    response = api_client.get("/api/config")

    assert response.status_code == 200
    body = response.json()

    assert body["app_name"] == "Calma"
    assert body["deployment_mode"] == "local"
    assert body["retrieval_backend"] == "faiss"
    assert body["qdrant_url"] == "http://localhost:6333"
    assert body["qdrant_collection"] == "calma_chunks"
    assert body["enable_graph_rag"] is False
    assert body["graph_rag_min_chunks"] == 400
    assert body["graph_rag_min_query_terms"] == 5
    assert body["rollout_mode"] == "stable"
    assert body["rollout_traffic_percent"] == 0
    assert body["enable_qdrant_fallback"] is True
    assert body["enable_ollama_fallback"] is True
    assert body["model_contract_version"] == "v1"
    assert body["sensitive_log_redaction_enabled"] is True
    assert body["enable_reranker"] is True
    assert body["rerank_top_k"] == 3
    assert body["rerank_max_chars"] == 1200
    assert body["retention_days"]["raw_chat"] == 90
    assert body["retention_days"]["audit_log"] == 365
    assert body["intake_chat_enabled"] is True

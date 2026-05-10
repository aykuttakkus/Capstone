from __future__ import annotations

import server.app.main as main_module


def test_ready_reports_degraded_when_ollama_is_down(api_client, monkeypatch) -> None:
    monkeypatch.setattr(main_module, "_ollama_ready", lambda: False)
    monkeypatch.setattr(main_module, "_qdrant_ready", lambda: True)
    monkeypatch.setattr(main_module, "_local_index_ready", lambda: True)

    response = api_client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["degraded"] is True
    assert body["checks"]["ollama"] is False
    assert body["status"] == "degraded"


def test_ready_is_not_ready_when_retrieval_is_down_and_no_fallback(api_client, monkeypatch) -> None:
    monkeypatch.setattr(main_module, "_ollama_ready", lambda: True)
    monkeypatch.setattr(main_module, "_qdrant_ready", lambda: False)
    monkeypatch.setattr(main_module, "_local_index_ready", lambda: False)
    monkeypatch.setattr(main_module, "RETRIEVAL_BACKEND", "qdrant")
    monkeypatch.setattr(main_module, "ENABLE_QDRANT_FALLBACK", False)

    response = api_client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is False
    assert body["status"] == "not_ready"
    assert body["checks"]["retrieval"] is False

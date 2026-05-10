from __future__ import annotations

import server.app.main as main_module


def test_startup_warms_assistant_service(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_get_service():
        calls["count"] += 1
        return object()

    monkeypatch.setattr(main_module, "get_service", fake_get_service)

    main_module.warmup_assistant_service()

    assert calls["count"] == 1

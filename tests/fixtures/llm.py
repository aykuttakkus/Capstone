from __future__ import annotations

import pytest

from server.app.core.generation.base import MockLLMBackend, UnavailableLLMBackend


@pytest.fixture
def mock_llm_backend() -> MockLLMBackend:
    return MockLLMBackend(text="Grounded answer from mock backend.")


@pytest.fixture
def offline_llm_backend() -> UnavailableLLMBackend:
    return UnavailableLLMBackend()


@pytest.fixture
def safety_stub_backend() -> MockLLMBackend:
    return MockLLMBackend(
        text='{"mode":"normal","risk_level":0,"reasoning":"safe","suggested_message":""}'
    )

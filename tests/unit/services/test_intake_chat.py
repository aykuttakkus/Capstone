from __future__ import annotations

import pytest

from server.app.core.generation.base import MockLLMBackend
from server.app.services.flows.intake_chat import IntakeChatEngine


pytestmark = [pytest.mark.unit, pytest.mark.anyio]


async def test_intake_reflection_falls_back_when_llm_is_generic() -> None:
    engine = IntakeChatEngine(
        llm_client=MockLLMBackend(
            text="I'm here to help with mental health-related questions. If you have any other questions or need assistance with something else, feel free to ask!"
        )
    )

    result = await engine.process_step(
        phase="name",
        answer="Aykut",
        accumulated={},
        lang="en",
    )

    assert result.next_phase == "concern"
    assert result.next_question is not None
    assert result.reflection == "Thanks for sharing that."
    assert "feel free to ask" not in result.reflection.lower()

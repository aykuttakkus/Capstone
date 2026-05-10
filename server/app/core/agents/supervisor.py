from __future__ import annotations
import asyncio
import json
import re

from server.app.core.generation.llm import OllamaClient
from server.app.utils.prompts import render_prompt


class SupervisorAgent:
    """
    The final safety layer. Reviews the generated answer before it is delivered
    to the user to ensure no medical advice or diagnoses were accidentally included.
    """

    def __init__(self, llm: OllamaClient | None = None) -> None:
        self.llm = llm or OllamaClient()

    async def review(self, answer: str) -> dict:
        prompt = render_prompt("agents.supervisor", ANSWER=answer)
        # Using run_in_executor to avoid blocking the event loop since OllamaClient calls are synchronous
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: self.llm.generate(prompt, temperature=0.0)
        )
        if not result.available:
            return {"is_safe": True, "violations": []}

        try:
            raw = result.text.strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
            return json.loads(raw)
        except Exception:
            return {"is_safe": True, "violations": []}

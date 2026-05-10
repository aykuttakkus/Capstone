from __future__ import annotations

from server.app.core.generation.llm import OllamaClient
from server.app.utils.prompts import render_prompt


class MemoryAgent:
    """
    Episodic Memory agent that extracts and persists clinical insights from
    interactions to maintain continuity across sessions.
    """

    def __init__(self, llm: OllamaClient | None = None) -> None:
        self.llm = llm or OllamaClient()

    def summarize_interaction(self, user_msg: str, ai_msg: str, current_memory: str = "") -> str:
        prompt = render_prompt(
            "agents.memory_agent",
            CURRENT_MEMORY=current_memory,
            USER_MSG=user_msg,
            AI_MSG=ai_msg,
        )
        result = self.llm.generate(prompt, temperature=0.1)
        if not result.available:
            return current_memory

        return result.text.strip()

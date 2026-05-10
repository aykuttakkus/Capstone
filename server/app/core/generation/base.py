"""
LLM Backend Abstraction Layer
==============================
Defines the LLMBackend protocol so the engine components are decoupled from
any specific LLM runtime (Ollama, OpenAI, mock, etc.).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(slots=True)
class LLMResult:
    available: bool
    text: str
    model: str = ""


@runtime_checkable
class LLMBackend(Protocol):
    def generate(self, prompt: str, temperature: float = 0.1) -> LLMResult:
        ...


class MockLLMBackend:
    def __init__(self, text: str = "", available: bool = True) -> None:
        self._text = text
        self._available = available

    def generate(self, prompt: str, temperature: float = 0.1) -> LLMResult:
        return LLMResult(available=self._available, text=self._text, model="mock")


class UnavailableLLMBackend:
    def generate(self, prompt: str, temperature: float = 0.1) -> LLMResult:
        return LLMResult(available=False, text="", model="unavailable")

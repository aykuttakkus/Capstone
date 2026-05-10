from __future__ import annotations

import json
import re
from dataclasses import dataclass

from server.app.core.generation.llm import OllamaClient
from server.app.core.retrieval.retriever import ScoredChunk
from server.app.services.flows.topics import infer_topic
from server.app.utils.text import tokenize
from server.app.utils.prompts import render_prompt


@dataclass(slots=True)
class GradingResult:
    is_relevant: bool
    confidence: float
    rationale: str


class RetrievalGrader:
    """
    Corrective RAG (CRAG) component.
    Grades the relevance of retrieved documents to the user query.
    """

    def __init__(self, llm: OllamaClient | None = None) -> None:
        self.llm = llm or OllamaClient()

    def _heuristic_relevance(self, query: str, chunk: ScoredChunk, query_topic: str | None) -> bool:
        query_terms = set(tokenize(query))
        chunk_terms = set(tokenize(f"{chunk.chunk.title} {chunk.chunk.content} {' '.join(chunk.chunk.keywords)}"))
        overlap = len(query_terms & chunk_terms)
        keyword_overlap = len(query_terms & set(tokenize(" ".join(chunk.chunk.keywords))))

        topic_bonus = 0.0
        if query_topic:
            from server.app.core.retrieval.retriever import topic_alignment_score

            topic_bonus = topic_alignment_score(query_topic, chunk.chunk.topic) * 3.0

        score = overlap + (keyword_overlap * 1.5) + topic_bonus
        if chunk.score >= 0.8:
            score += 0.5
        return score >= 2.0 if query_topic else score >= 1.0

    def _heuristic_batch(self, query: str, chunks: list[ScoredChunk]) -> list[bool]:
        query_topic = infer_topic(query)
        return [self._heuristic_relevance(query, chunk, query_topic) for chunk in chunks]

    def grade_batch(self, query: str, chunks: list[ScoredChunk]) -> list[bool]:
        """
        Batch grades relevance for multiple chunks in one LLM call.
        Returns a list of booleans corresponding to each chunk's relevance.
        """
        if not chunks:
            return []

        heuristic_flags = self._heuristic_batch(query, chunks)

        context = "\n".join([f"ID {i}: {c.chunk.content[:300]}" for i, c in enumerate(chunks)])

        prompt = render_prompt(
            "agents.retrieval_grader",
            QUERY=query,
            CONTEXT=context,
        )
        llm_res = self.llm.generate(prompt, temperature=0.0)
        if not llm_res.available:
            return heuristic_flags

        try:
            raw = llm_res.text.strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
            data = json.loads(raw)
            llm_flags = [bool(data.get(str(i), True)) for i in range(len(chunks))]
            return [llm_flag and heuristic_flag for llm_flag, heuristic_flag in zip(llm_flags, heuristic_flags)]
        except Exception:
            return heuristic_flags

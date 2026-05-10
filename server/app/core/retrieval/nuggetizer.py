from __future__ import annotations
import json
from server.app.core.generation.llm import OllamaClient
from server.app.core.retrieval.retriever import ScoredChunk
from server.app.utils.prompts import render_prompt

class RAGNuggetizer:
    """
    Condenses multiple RAG documents into a single, high-impact clinical "nugget".
    This prevents the main generator from being overwhelmed by context.
    """
    def __init__(self, llm: OllamaClient | None = None):
        self.llm = llm or OllamaClient()

    async def nuggetize(self, query: str, retrievals: list[ScoredChunk]) -> str:
        if not retrievals:
            return ""

        # Format the context for the nuggetizer
        context = "\n".join([f"- {item.chunk.content}" for item in retrievals[:3]]) # Top 3 chunks
        
        prompt = f"""
        You are a Clinical Knowledge Synthesizer.
        Given the following search results and a user query, extract EXACTLY ONE brief sentence 
        that contains the most relevant clinical insight for the user.

        Query: "{query}"
        Search Results:
        {context}

        Rules:
        - Return ONLY the single sentence.
        - No preamble, no "Based on...", no explanation.
        - Keep it under 20 words.
        - Tone: Professional PhD Psychologist.

        Clinical Nugget:
        """
        
        result = self.llm.generate(prompt, temperature=0.0)
        if result.available and result.text:
            return result.text.strip().split("\n")[0] # Take only the first line
        return ""

nuggetizer = RAGNuggetizer()

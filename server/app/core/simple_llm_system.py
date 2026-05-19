"""
Simplified LLM + RAG System
No complex prompts - Just natural conversation
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from server.app.core.generation.llm import OllamaClient
from server.app.rag_v2.rag_engine import RAGEngine


@dataclass(slots=True)
class SimpleContext:
    """Simple conversation context"""
    user_message: str
    conversation_history: list[str] = field(default_factory=list)
    session_id: str = "default"


@dataclass(slots=True)
class SimpleResult:
    """Simple result"""
    response: str
    used_rag: bool


class SimpleLLMSystem:
    """
    Ultra-simple system:
    1. Get user message
    2. Check if RAG info needed
    3. Send to LLM with minimal context
    4. Return natural response
    """
    
    def __init__(self):
        self.llm = OllamaClient()
        self.rag = RAGEngine()
        # Basit session tutma
        self.sessions: dict[str, list[str]] = {}
    
    def respond(self, context: SimpleContext) -> SimpleResult:
        """Main response method - SIMPLE!"""
        
        # 1. Get or create session history
        if context.session_id not in self.sessions:
            self.sessions[context.session_id] = []
        history = self.sessions[context.session_id]
        
        # 2. Check if we need RAG (simple heuristic)
        needs_info = self._needs_information(context.user_message)
        
        rag_context = ""
        if needs_info:
            try:
                rag_response = self.rag.answer(context.user_message, top_k=3)
                if rag_response.retrieved_chunks:
                    rag_context = rag_response.context
            except:
                pass  # No problem if RAG fails
        
        # 3. Build MINIMAL prompt - Let LLM be natural!
        prompt = self._build_simple_prompt(
            context.user_message,
            history,
            rag_context
        )
        
        # 4. Send to LLM
        llm_result = self.llm.generate(prompt, temperature=0.8)
        
        if llm_result.available and llm_result.text:
            response = llm_result.text.strip()
            
            # 5. Save to history
            history.append(f"User: {context.user_message}")
            history.append(f"Assistant: {response}")
            
            # Keep last 10 exchanges
            if len(history) > 20:
                self.sessions[context.session_id] = history[-20:]
            
            return SimpleResult(
                response=response,
                used_rag=bool(rag_context)
            )
        else:
            # LLM failed - simple fallback
            return SimpleResult(
                response="Anlamaya çalışıyorum. Biraz daha anlatır mısın?",
                used_rag=False
            )
    
    def _needs_information(self, message: str) -> bool:
        """Simple check: Does user want info or just chat?"""
        msg_lower = message.lower()
        
        # Info-seeking keywords
        info_keywords = [
            "what is", "how to", "nedir", "nasıl", 
            "explain", "anlat", "tell me about", 
            "techniques", "methods", "yöntem", "ipucu"
        ]
        
        # Emotional chat keywords (no info needed)
        chat_keywords = [
            "i feel", "hisset", "sad", "mutsuz",
            "lonely", "yalnız", "happy", "mutlu",
            "i think", "sanırım", "believe", "inanıyorum"
        ]
        
        # If chat keywords > info keywords, it's just chat
        chat_score = sum(1 for kw in chat_keywords if kw in msg_lower)
        info_score = sum(1 for kw in info_keywords if kw in msg_lower)
        
        return info_score > chat_score
    
    def _build_simple_prompt(self, message: str, history: list[str], rag_info: str) -> str:
        """MINIMAL prompt - LLM does the work!"""
        
        # Simple conversation history
        history_text = ""
        if history:
            # Last 6 messages only
            recent = history[-6:]
            history_text = "\n".join(recent)
        
        # Minimal, natural prompt
        if rag_info:
            # User wants info + we have RAG data
            return f"""Sen samimi bir arkadaşsın. Doğal konuş.

Önceki konuşma:
{history_text}

Kullanıcı: {message}

Yararlı bilgiler (kaynaklardan):
{rag_info[:1000]}

Kullanıcıya samimi, doğal bir yanıt ver. Bilgileri kendi cümlelerinle anlat, birebir kopyalama."""
        else:
            # Just chat, no info needed
            return f"""Sen samimi bir arkadaşsın. Doğal konuş, empati göster.

Önceki konuşma:
{history_text}

Kullanıcı: {message}

Kullanıcıya samimi, doğal bir yanıt ver. Onu anlamaya çalış."""


# Global instance
simple_system = SimpleLLMSystem()


def get_response(user_message: str, session_id: str = "default", history: list[str] = None) -> str:
    """Simple API - just message in, response out"""
    context = SimpleContext(
        user_message=user_message,
        conversation_history=history or [],
        session_id=session_id
    )
    result = simple_system.respond(context)
    return result.response

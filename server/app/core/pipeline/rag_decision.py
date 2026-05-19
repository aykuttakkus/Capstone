from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RAGDecision:
    """Decision on whether and how to use RAG."""
    use_rag: bool
    retrieve_amount: int  # 1-5, number of chunks to retrieve
    reasoning: str
    confidence: float  # 0.0-1.0


class RAGDecisionModule:
    """
    Intelligent RAG decision module that decides when to retrieve,
    balancing context relevance, conversation efficiency, and latency.
    """

    # Intent categories that don't typically need retrieval
    SELF_CONTAINED_INTENTS = {
        "emotional_support",  # Validation and empathy, not information
        "clarification",      # Clarifying previous responses
        "repair",            # Fixing misunderstandings
    }

    # Intent categories that always benefit from retrieval
    RETRIEVAL_DEPENDENT_INTENTS = {
        "psychoeducation",      # Needs evidence-based content
        "coping_strategy",      # Needs specific techniques
        "symptom_exploration",  # Needs pattern information
    }

    def __init__(self) -> None:
        self.conversation_length_threshold = 5  # Turn count for "long conversation"

    def decide(
        self,
        intent: str,
        topic: str,
        conversation_length: int,
        risk_level: int,
        has_recent_retrieval: bool = False,
    ) -> RAGDecision:
        """
        Decide whether to use RAG based on conversation context.

        Args:
            intent: User's detected intent
            topic: Conversation topic
            conversation_length: Number of turns so far
            risk_level: Current risk level (0-5)
            has_recent_retrieval: Whether we retrieved in last turn

        Returns:
            RAGDecision with use_rag flag, amount, reasoning, confidence
        """

        # Crisis/high-risk: use crisis responses, minimal retrieval
        if risk_level >= 4:
            return RAGDecision(
                use_rag=False,
                retrieve_amount=0,
                reasoning="Crisis mode: prioritize crisis protocols over RAG",
                confidence=1.0,
            )

        # Off-scope intents: no retrieval (will be handled by off-scope builder)
        if intent == "off_scope":
            return RAGDecision(
                use_rag=False,
                retrieve_amount=0,
                reasoning="Off-scope request: no RAG needed",
                confidence=1.0,
            )

        # Self-contained intents: minimal or no retrieval
        if intent in self.SELF_CONTAINED_INTENTS:
            # Exception: first turn might need context-setting retrieval
            if conversation_length <= 1:
                return RAGDecision(
                    use_rag=True,
                    retrieve_amount=2,
                    reasoning="First turn emotional support: light retrieval for context",
                    confidence=0.8,
                )
            # Long conversations: reduce retrieval to avoid repetition
            if conversation_length > self.conversation_length_threshold:
                return RAGDecision(
                    use_rag=False,
                    retrieve_amount=0,
                    reasoning="Long conversation: skip retrieval to avoid repetition",
                    confidence=0.85,
                )
            # Normal case: no retrieval for emotional support
            return RAGDecision(
                use_rag=False,
                retrieve_amount=0,
                reasoning="Emotional support: validation over information",
                confidence=0.9,
            )

        # Retrieval-dependent intents: always retrieve
        if intent in self.RETRIEVAL_DEPENDENT_INTENTS:
            # Determine retrieval amount
            if conversation_length > self.conversation_length_threshold:
                # Longer conversations: reduce to avoid repetition
                amount = 2
                reasoning = "Retrieval-dependent + long conversation: reduced retrieval"
            elif has_recent_retrieval:
                # Recently retrieved: use less
                amount = 2
                reasoning = "Retrieval-dependent: reduced after recent retrieval"
            else:
                # Standard retrieval
                amount = 3
                reasoning = "Retrieval-dependent intent: standard retrieval"

            return RAGDecision(
                use_rag=True,
                retrieve_amount=amount,
                reasoning=reasoning,
                confidence=0.95,
            )

        # Unknown intent: safe default to minimal retrieval
        return RAGDecision(
            use_rag=True,
            retrieve_amount=1,
            reasoning="Unknown intent: conservative retrieval",
            confidence=0.6,
        )

    def should_cache_retrieval(self, rag_decision: RAGDecision) -> bool:
        """Determine if retrieval results should be cached for next turn."""
        return rag_decision.use_rag and rag_decision.retrieve_amount >= 2

    def get_retrieval_context(self, rag_decision: RAGDecision) -> dict[str, int]:
        """Get context parameters for retrieval."""
        return {
            "top_k": rag_decision.retrieve_amount,
            "min_score": 0.5 if rag_decision.retrieve_amount >= 3 else 0.3,
        }

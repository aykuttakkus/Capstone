"""Main RAG engine orchestrating all components."""

from dataclasses import dataclass, field
from typing import List
from pathlib import Path

from .embedding_service import EmbeddingService
from .faiss_retriever import FAISSRetriever
from .intent_classifier import IntentClassifier
from .query_processor import QueryProcessor


@dataclass
class RAGResponse:
    """Response from RAG system."""
    query: str
    intent: str
    risk_level: int
    confidence: float
    retrieved_chunks: List[dict] = field(default_factory=list)
    context: str = ""
    sources: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class RAGEngine:
    """Main RAG orchestration engine."""

    def __init__(self, faiss_dir: str = None):
        if faiss_dir is None:
            # Try environment variable first (for Docker)
            import os
            faiss_dir = os.getenv("FAISS_INDEX_DIR", "/app/data/faiss_indexes")
            
            # Fallback to host path if not in Docker
            if not Path(faiss_dir).exists():
                faiss_dir = "/Users/aykutakkus/Desktop/Projects/Capstone/data/faiss_indexes"

        self.faiss_dir = Path(faiss_dir)
        self.embedder = EmbeddingService()
        self.retriever = FAISSRetriever(self.faiss_dir, self.embedder)
        self.classifier = IntentClassifier()
        self.processor = QueryProcessor()

    def answer(self, query: str, top_k: int = 5) -> RAGResponse:
        """Answer a user query end-to-end."""

        # 1. Classify intent and risk
        intent_result = self.classifier.classify(query)

        # 2. Check boundaries
        if intent_result.primary_intent == "off_scope":
            return RAGResponse(
                query=query,
                intent="off_scope",
                risk_level=0,
                confidence=0.9,
                warnings=["Query is outside mental health domain"],
            )

        # 3. Process query
        processed = self.processor.process(
            query,
            intent_result.primary_intent,
            intent_result.risk_level,
        )

        # 4. Retrieve context
        chunks, isolation = self.retriever.retrieve_with_isolation(
            processed.enhanced,
            intent_result.primary_intent,
            intent_result.risk_level,
            top_k=top_k,
        )

        # 5. Build response
        sources = list(set(c.source for c in chunks))
        context = "\n\n".join(f"[{c.source}] {c.content}" for c in chunks)

        warnings = []
        if intent_result.risk_level >= 3:
            warnings.append("🚨 HIGH RISK: Crisis support resources should be provided")
        if isolation == "enforced":
            warnings.append("Crisis isolation enforced - standard indexes not queried")

        return RAGResponse(
            query=query,
            intent=intent_result.primary_intent,
            risk_level=intent_result.risk_level,
            confidence=intent_result.confidence,
            retrieved_chunks=[
                {
                    "id": c.id,
                    "content": c.content[:200],
                    "source": c.source,
                    "score": c.score,
                    "clinical_risk": c.clinical_risk,
                }
                for c in chunks
            ],
            context=context,
            sources=sources,
            warnings=warnings,
        )

    def batch_answer(self, queries: List[str], top_k: int = 5) -> List[RAGResponse]:
        """Answer multiple queries."""
        return [self.answer(q, top_k) for q in queries]

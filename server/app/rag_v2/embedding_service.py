"""Embedding service for RAG system."""

from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np


class EmbeddingService:
    """Handles text embedding with multilingual support."""

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_embedding_dimension()

    def embed(self, texts: str | List[str]) -> np.ndarray:
        """Embed text or list of texts."""
        if isinstance(texts, str):
            return self.model.encode([texts], convert_to_numpy=True)[0]
        return self.model.encode(texts, convert_to_numpy=True)

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Embed texts in batches."""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_embeddings = self.model.encode(batch, convert_to_numpy=True)
            embeddings.extend(batch_embeddings)
        return np.array(embeddings, dtype=np.float32)

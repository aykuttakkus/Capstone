from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(slots=True)
class EmbeddingBackend:
    dimension: int = 384
    _model: object | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(model_name)
            dim_fn = getattr(self._model, "get_embedding_dimension", None) or getattr(self._model, "get_sentence_embedding_dimension", None)
            if dim_fn:
                self.dimension = int(dim_fn())
        except Exception:
            self._model = None

    def embed(self, text: str) -> list[float]:
        if self._model is not None:
            vector = self._model.encode([text], normalize_embeddings=True)[0]
            return [float(v) for v in vector]
        return self._hashed_embedding(text)

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if self._model is not None and texts:
            matrix = self._model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
            return [[float(v) for v in row] for row in matrix]
        return [self._hashed_embedding(t) for t in texts]

    @property
    def is_neural(self) -> bool:
        return self._model is not None

    def _hashed_embedding(self, text: str) -> list[float]:
        import hashlib
        import math
        import re

        tokens = re.findall(r"[a-z0-9']+", text.strip().lower())
        vector = [0.0] * self.dimension

        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(v * v for v in vector))
        if norm:
            vector = [v / norm for v in vector]
        return vector

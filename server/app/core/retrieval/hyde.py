"""HyDE — Hypothetical Document Embeddings (Gao et al., ACL 2023).

Instead of embedding the raw user query, we:
  1. Ask the LLM to write a short *hypothetical* answer paragraph.
  2. Embed that paragraph (it lives in the same semantic space as corpus chunks).
  3. Blend the hypothetical embedding with the original query embedding.

Why this works for Calma:
  - Short or Turkish queries are far from dense English corpus chunks.
  - A hypothetical paragraph ("CBT techniques include...") sits much closer to
    the actual stored chunks than the three-word query ("cbt for anxiety").
  - Blending (alpha=0.5) keeps query intent while gaining corpus proximity.

Reference: arXiv:2212.10496 — Gao et al., "Precise Zero-Shot Dense Retrieval
without Relevance Labels", ACL 2023.
"""

from __future__ import annotations

import hashlib
import math
import threading

from server.app.core.config import HYDE_ALPHA, OLLAMA_BASE_URL, OLLAMA_MODEL
from server.app.utils.text import infer_language

# ---------------------------------------------------------------------------
# Hypothetical document cache  (thread-safe, 256-entry FIFO)
# ---------------------------------------------------------------------------

_hypo_cache: dict[str, str] = {}
_hypo_lock = threading.Lock()
_HYPO_CACHE_MAX = 256


def _cache_key(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def _cache_get(query: str) -> str | None:
    with _hypo_lock:
        return _hypo_cache.get(_cache_key(query))


def _cache_set(query: str, hypo: str) -> None:
    with _hypo_lock:
        if len(_hypo_cache) >= _HYPO_CACHE_MAX:
            _hypo_cache.pop(next(iter(_hypo_cache)))
        _hypo_cache[_cache_key(query)] = hypo


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_PROMPT_EN = """\
You are an expert mental health assistant. Write a concise, factual paragraph \
(3-5 sentences) that directly answers the following question. Use precise \
clinical and academic terminology (e.g. DSM-5 criteria, evidence-based \
interventions, psychophysiological mechanisms). Do not add disclaimers.

Question: {query}

Answer paragraph:"""

_PROMPT_TR = """\
Sen uzman bir ruh sağlığı asistanısın. Aşağıdaki soruya doğrudan yanıt veren \
kısa ve olgusal bir paragraf yaz (3-5 cümle). \
İngilizce yaz; DSM-5 kriterleri, kanıta dayalı müdahaleler ve \
psikofiziolojik mekanizmalar gibi klinik/akademik terimler kullan. \
Uyarı veya sorumluluk reddi ekleme.

Soru: {query}

Yanıt paragrafı:"""


def _build_prompt(query: str) -> str:
    lang = infer_language(query)
    template = _PROMPT_TR if lang == "tr" else _PROMPT_EN
    return template.format(query=query)


# ---------------------------------------------------------------------------
# LLM call (lightweight — avoids circular import with generation.llm)
# ---------------------------------------------------------------------------

def _list_ollama_models(base_url: str) -> list[str]:
    """Return names of locally available Ollama models."""
    import json
    from urllib import request, error

    try:
        with request.urlopen(f"{base_url.rstrip('/')}/api/tags", timeout=3) as resp:
            body = json.loads(resp.read().decode())
        return [m["name"] for m in body.get("models", [])]
    except Exception:
        return []


def _pick_model(preferred: str, base_url: str) -> str:
    """Return `preferred` if available; otherwise fall back to the first
    listed model.  Returns `preferred` unchanged if the tags endpoint fails."""
    available = _list_ollama_models(base_url)
    if not available:
        return preferred
    if any(m == preferred or m.startswith(preferred.split(":")[0]) for m in available):
        return preferred
    return available[0]


def _call_ollama(prompt: str, base_url: str, model: str) -> str | None:
    """Returns the generated text, or None on any error."""
    import json
    from urllib import error, request

    # Auto-select an available model if the configured one isn't pulled yet
    model = _pick_model(model, base_url)

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.4, "num_predict": 160},
    }
    req = request.Request(
        f"{base_url.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
        text = str(body.get("response", "")).strip()
        return text if text else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm < 1e-9:
        return vec
    return [v / norm for v in vec]


def _blend(v1: list[float], v2: list[float], alpha: float) -> list[float]:
    """alpha=0 → pure v1, alpha=1 → pure v2."""
    blended = [(1 - alpha) * a + alpha * b for a, b in zip(v1, v2)]
    return _l2_normalize(blended)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class HyDEExpander:
    """Generates a hypothetical answer and returns a blended query embedding.

    Parameters
    ----------
    alpha:
        Blend weight between original query embedding (0) and hypothetical
        document embedding (1). Default 0.5 from Gao et al. ablations.
    ollama_base_url / ollama_model:
        Forwarded to the lightweight Ollama caller.
    """

    def __init__(
        self,
        alpha: float = HYDE_ALPHA,
        ollama_base_url: str = OLLAMA_BASE_URL,
        ollama_model: str = OLLAMA_MODEL,
    ) -> None:
        self.alpha = alpha
        self._base_url = ollama_base_url
        self._model = ollama_model

    # ------------------------------------------------------------------

    def expand_query_embedding(
        self,
        query: str,
        query_embedding: list[float],
        embedder,  # EmbeddingBackend — avoids circular import
    ) -> list[float]:
        """Return a (possibly blended) embedding for use in retrieval.

        Falls back to the original `query_embedding` if Ollama is unavailable
        or returns an empty string, so the pipeline never breaks.
        """
        hypo = self._get_hypothetical(query)
        if not hypo:
            return query_embedding  # graceful fallback

        hypo_emb = embedder.embed(hypo)
        return _blend(query_embedding, hypo_emb, self.alpha)

    def _get_hypothetical(self, query: str) -> str | None:
        cached = _cache_get(query)
        if cached is not None:
            return cached

        prompt = _build_prompt(query)
        hypo = _call_ollama(prompt, self._base_url, self._model)
        if hypo:
            _cache_set(query, hypo)
        return hypo

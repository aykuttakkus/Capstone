# Calma — RAG Master Implementation Plan

> **Versiyon:** 1.0 — Mayıs 2025  
> **Donanım:** Apple M4 Pro · 24 GB Unified Memory · 12 CPU  
> **Hedef:** 139 PDF · Türkçe + İngilizce · Psikoloji / Mental Health  
> **Mevcut LLM:** `mistral:latest` → **Hedef:** `qwen2.5:14b`  
> **Mevcut Embedding:** `all-MiniLM-L6-v2` (384 dim, kırık index) → **Hedef:** `BAAI/bge-m3` (1024 dim)  
> **Mevcut Vector Store:** FAISS (dense only) → **Hedef:** Qdrant (dense + sparse, hybrid)

---

## Bölüm 1 — Teknoloji Kararları (Gerekçeli)

### 1.1 LLM: `qwen2.5:14b`

**Neden Mistral değil?**

Mistral 7B Türkçe için resmi destek sunmuyor. TurkishMMLU benchmark'ında ölçülmemiş; testsiz model kabul edilemez.

**Karşılaştırma (ölçülmüş, kaynaklar sonda):**

| Model | TurkishMMLU | TR-MMLU | Context | RAM (Q4_K_M) | tok/s M4 Pro |
|---|---|---|---|---|---|
| **qwen2.5:14b** ✅ | **66.85** | — | 128K | ~9.5 GB | ~35-50 |
| qwen2.5:7b | 54.28 | — | 128K | ~5.0 GB | ~55-70 |
| llama3.1:8b | — | — | 128K | ~5.5 GB | ~50-65 |
| llama3.3:70b | — | 79.42 | 128K | ~43 GB ❌ | ~6-8 |
| gemma3:12b | — | — | 128K | ~8.0 GB | ~30-40 |
| mistral:7b (mevcut) | ölçülmemiş | ölçülmemiş | 32K | ~5.0 GB | ~55-70 |

**Karar: `qwen2.5:14b`**  
- TurkishMMLU'da 14B sınıfının en güçlüsü (66.85 — en yakın rakip 12B sınıfı ölçülmemiş)
- 128K native context, Ollama ile 32K olarak yapılandırılacak
- Q4_K_M ile ~9.5 GB RAM; BGE-M3 (~1.5 GB) + reranker (~1.1 GB) ile toplam ~12.1 GB — 24 GB içinde rahat
- Yapılandırılmış JSON çıktı desteği güçlü → retrieval grading, evidence gate için kritik

**`num_ctx` zorunlu:** Ollama default olarak 2,048 token context kullanır. 32,768 olarak ayarlanması şart.

---

### 1.2 Embedding: `BAAI/bge-m3`

**Neden mevcut `all-MiniLM-L6-v2` (384 dim) değil?**

- İngilizce-only, Türkçe için random'a yakın performans
- FAISS index 384 dim → embeddings.py 1024 dim → index kırık, retrieval sıfır

**Neden `multilingual-e5-large` değil?**

- 512 token context limiti: 139 PDF'deki akademik makalelerin Methods bölümleri 2.000-10.000 token. Yarısı kesilir.
- TR-MTEB'de BGE-M3'ün altında retrieval performansı

**BGE-M3'ün kritik avantajı — üç mod tek model:**

```
Dense vector  (1024 dim)  → semantik benzerlik arama
Sparse vector (lexical)   → BM25-style anahtar kelime eşleşmesi
ColBERT multi-vector      → reranking için late interaction
```

Bu üç modu çalıştırmak için normalde 3 farklı model gerekir. BGE-M3 tek forward pass'te hepsini üretiyor.

**Karar: `BAAI/bge-m3`**  
Uygulamada `sentence-transformers` üzerinden dense mode (zaten requirements.txt'te var) + `FlagEmbedding` paketinden sparse mode.

---

### 1.3 Vector Store: Qdrant (FAISS yerine)

**FAISS ne zaman mantıklı?**  
<100K vector, GPU yoksa, deployment basitliği öncelikliyse, sparse vector gerekmiyorsa.

**Bu projede neden Qdrant?**

| Özellik | FAISS | Qdrant |
|---|---|---|
| Dense + Sparse aynı collection | ❌ | ✅ Named vectors |
| Built-in hybrid search (RRF) | ❌ manuel kod | ✅ Query API |
| Metadata filtreleme | Sınırlı | ✅ Payload index |
| Incremental upsert (yeni PDF ekle) | ❌ tam rebuild | ✅ HTTP upsert |
| BGE-M3 sparse lexical weights | ❌ | ✅ SparseVectorParams |
| Docker Compose'da mevcut | — | ✅ Zaten var (v1.16.2) |
| 3.000 vektörde sorgu süresi | <1ms | <1ms |

**Qdrant zaten Docker Compose'da var** — `compose.yaml:42`. Migration maliyeti minimum; sadece `qdrant_store.py` güncelleniyor.

**Karar: Qdrant, primary backend olarak yükseltilir. FAISS kaldırılmaz, offline fallback olarak kalır.**

---

### 1.4 Hybrid Retrieval: RRF (Reciprocal Rank Fusion)

Mevcut `0.70 * semantic + 0.30 * keyword` weighted sum iki sorunu var:
1. BM25 ve cosine similarity farklı scale → normalizasyon yapılmıyor
2. Score-based combination outlier'a duyarlı

**RRF:**
```
score(d) = Σ_i  1 / (k + rank_i(d))    k=60 (standard)
```

- Parameter-free: tune etmeye gerek yok
- Scale-invariant: BM25 vs cosine score farkı yok
- Qdrant Query API native olarak destekliyor: `prefetch + query`

---

### 1.5 Reranker: `bge-reranker-v2-m3`

Mevcut `EvidenceReranker`: keyword overlap + topic alignment — neural değil.

| Reranker | MTEB-R | RAM | Dil | Karar |
|---|---|---|---|---|
| Qwen3-Reranker-8B | 69.76 | ~16 GB | 100+ | BGE-M3 + qwen2.5 ile 25+ GB eder → RAM aşılır ❌ |
| **bge-reranker-v2-m3** | 57.03 | **~1.1 GB** | 100+ | ✅ BGE-M3 ile aynı ailede |
| FlashRank MiniLM | 55.43 | ~120 MB | En | Türkçe için zayıf ❌ |

**Karar: `BAAI/bge-reranker-v2-m3`**  
RAM: 9.5 + 1.5 + 1.1 = 12.1 GB toplam. 24 GB'ın %50'si.

---

### 1.6 Chunking: Section-Aware + Recursive (512 tok, 80 overlap)

**Neden mevcut `MarkdownHeaderTextSplitter` yetersiz?**  
Token limiti yok. 35 MB "Introduction to Psychology" textbook'u 3-5 büyük chunk'a bölünür, her biri context window'u patlatır.

**Strateji: Section boundaries önce tespit et, sonra token'a böl**

```
Section tespit (Docling header parsing)
    → Her section kendi token limitiyle işlenir
    → References bölümü tamamen çıkarılır
    → Tables atomik tutulur (başlık + sütunlar + içerik = tek chunk)
```

**Section-specific token limits (MDPI Bioengineering 2025 — section-aware %87 vs fixed %13):**

| Section | Chunk Size | Overlap | Neden |
|---|---|---|---|
| Abstract | 400 tok | 0 | Atomik — bölünmemeli |
| Introduction | 512 tok | 80 | Standart |
| Methods | 768 tok | 100 | Prosedür sürekliliği |
| Results | 512 tok | 80 | Her bulgu paragrafı |
| Discussion | 512 tok | 80 | Standart |
| Conclusion | 400 tok | 0 | Atomik — klinik sonuç |
| References | — | — | **Dışarıda** |
| Tables | Tüm tablo | 0 | Atomik |
| Default | 512 tok | 80 | Bilinmeyen section |

---

### 1.7 Contextual Prefix (Anthropic, 2024)

Her chunk index'e alınmadan önce bir LLM ile 50-100 token context üretilir ve prepend edilir.

**Anthropic benchmark:** retrieval failure -49% (BM25 ile birlikte), reranker eklentisiyle -67%.

**Maliyet:** Claude Haiku API, prompt caching ile ~$0.80-2.50 (139 PDF için tek seferlik).  
Mevcut Claude API key yoksa bu adım atlanabilir veya local `qwen2.5:7b` ile çalıştırılabilir (~2-3 saat sürer ama ücretsiz).

---

## Bölüm 2 — Sistem Mimarisi

### 2.1 Ingestion Pipeline

```
data/raw/*.pdf
    │
    ▼ [AŞAMA 1]
┌─────────────────────┐
│   PDF PARSER        │  server/app/core/retrieval/ingestion/parser.py
│   Docling → MD      │  (mevcut, değişmiyor)
│   Fallback: pypdf   │
└────────┬────────────┘
         │
    ▼ [AŞAMA 2]
┌─────────────────────┐
│   SECTION DETECTOR  │  server/app/core/retrieval/ingestion/chunker.py
│   Header → section  │  (YENİDEN YAZILIYOR)
│   type belirlenir   │
└────────┬────────────┘
         │
    ▼ [AŞAMA 3]
┌─────────────────────┐
│   RECURSIVE SPLIT   │  langchain_text_splitters
│   section-aware     │  chunk_size per section type
│   token limiti      │  overlap 80-100 tok
└────────┬────────────┘
         │
    ▼ [AŞAMA 4]
┌─────────────────────┐
│   QUALITY FILTER    │  pdf_ingestion.py
│   min 50 tok        │  (güncelleniyor)
│   ref exclusion     │
│   boyama kitabı     │
└────────┬────────────┘
         │
    ▼ [AŞAMA 5 — opsiyonel]
┌─────────────────────┐
│  CONTEXTUAL PREFIX  │  server/app/core/retrieval/ingestion/contextual_prefix.py
│  LLM → 50-100 tok  │  (YENİ DOSYA)
│  chunk'a prepend   │
└────────┬────────────┘
         │
    ▼ [AŞAMA 6]
┌─────────────────────┐
│   BGE-M3 EMBED      │  server/app/core/retrieval/embeddings.py
│   dense (1024 dim)  │  (MODEL DEĞİŞİYOR)
│   sparse (lexical)  │
└────────┬────────────┘
         │
    ▼ [AŞAMA 7]
┌─────────────────────┐
│   QDRANT UPSERT     │  server/app/core/retrieval/qdrant_store.py
│   named vectors:    │  (YENİDEN YAZILIYOR)
│     dense + sparse  │
│   payload: metadata │
└─────────────────────┘
```

### 2.2 Retrieval Pipeline

```
User Query (TR/EN)
    │
    ▼
┌─────────────────────────────────────────────────┐
│   QUERY EMBED                                   │
│   BGE-M3 dense vector + sparse lexical weights  │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌─────────────┐     ┌──────────────────┐
│ DENSE SEARCH│     │  SPARSE SEARCH   │
│ Qdrant knn  │     │  Qdrant inverted │
│ top-50      │     │  top-50          │
└──────┬──────┘     └────────┬─────────┘
       │                     │
       └──────────┬──────────┘
                  ▼
       ┌──────────────────────┐
       │   RRF FUSION         │  Qdrant Query API
       │   score = Σ 1/(60+r) │  (built-in)
       │   → top-20           │
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │  NEURAL RERANKER     │  bge-reranker-v2-m3
       │  cross-encoder       │
       │  top-20 → top-5      │
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │  EVIDENCE GATE       │  (mevcut, güncelleniyor)
       │  min score 0.22      │
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │  LLM GENERATION      │  qwen2.5:14b
       │  5 chunk + prompt    │  num_ctx=32768
       └──────────────────────┘
```

---

## Bölüm 3 — Değişecek Her Şey (Dosya Bazlı)

### 3.1 Eklenecek Paketler

**`requirements.txt`'e eklenecek:**

```txt
# BGE-M3 sparse mode + reranker
FlagEmbedding==1.3.5

# BM25 fallback (BGE-M3 sparse yoksa)
rank-bm25==0.2.2

# Chunking
langchain-text-splitters==0.3.8

# Evaluation
ragas==0.2.14
```

**`requirements-dev.txt`'e eklenecek:**

```txt
# Ingestion scripts için
tqdm==4.67.1
tiktoken==0.9.0
```

### 3.2 Environment Variables

**`.env.example` değişiklikleri:**

```bash
# ESKISI
OLLAMA_MODEL=mistral:latest
EMBEDDING_MODEL=all-MiniLM-L6-v2
RETRIEVAL_BACKEND=faiss

# YENİSİ
OLLAMA_MODEL=qwen2.5:14b
EMBEDDING_MODEL=BAAI/bge-m3
RETRIEVAL_BACKEND=qdrant

# YENİ EKLENENLER
OLLAMA_NUM_CTX=32768
ENABLE_SPARSE_RETRIEVAL=true
SPARSE_WEIGHT=0.4
BGE_RERANKER_MODEL=BAAI/bge-reranker-v2-m3
RERANK_TOP_K=5
RERANK_CANDIDATES=20
CONTEXTUAL_PREFIX_ENABLED=false
CONTEXTUAL_PREFIX_MODEL=claude-haiku-3-5
```

**`compose.yaml` — backend service environment'a eklenecek:**

```yaml
OLLAMA_MODEL: ${OLLAMA_MODEL:-qwen2.5:14b}
EMBEDDING_MODEL: ${EMBEDDING_MODEL:-BAAI/bge-m3}
RETRIEVAL_BACKEND: ${RETRIEVAL_BACKEND:-qdrant}
OLLAMA_NUM_CTX: ${OLLAMA_NUM_CTX:-32768}
ENABLE_SPARSE_RETRIEVAL: ${ENABLE_SPARSE_RETRIEVAL:-true}
BGE_RERANKER_MODEL: ${BGE_RERANKER_MODEL:-BAAI/bge-reranker-v2-m3}
RERANK_CANDIDATES: ${RERANK_CANDIDATES:-20}
```

---

## Bölüm 4 — Phase-by-Phase Uygulama

---

### PHASE 0 — Ortam Hazırlığı (1 gün)

#### 0.1 Ollama Model Güncelleme

```bash
# Mevcut mistral'ı kaldır (opsiyonel, disk alanı)
ollama rm mistral:latest

# qwen2.5:14b indir
ollama pull qwen2.5:14b

# num_ctx için Modelfile oluştur
cat > /tmp/Calma-Modelfile << 'EOF'
FROM qwen2.5:14b
PARAMETER num_ctx 32768
PARAMETER temperature 0.2
PARAMETER top_p 0.9
SYSTEM "You are Calma, a compassionate and evidence-based mental health support assistant. You provide accurate psychological information grounded in scientific sources. You never diagnose, always recommend professional help when appropriate."
EOF

ollama create calma-qwen -f /tmp/Calma-Modelfile
```

**`.env`'e yaz:**
```bash
OLLAMA_MODEL=calma-qwen
```

#### 0.2 Paket Kurulumu

```bash
pip install "FlagEmbedding==1.3.5" "rank-bm25==0.2.2" \
            "langchain-text-splitters==0.3.8" \
            "ragas==0.2.14" "tqdm==4.67.1" "tiktoken==0.9.0"
```

#### 0.3 Qdrant'ın Çalıştığını Doğrula

```bash
docker compose up qdrant -d
curl http://localhost:6333/healthz
# {"status":"ok"}
```

---

### PHASE 1 — Embedding Model Migrasyonu (1-2 gün)

#### Değişen dosya: `server/app/core/retrieval/embeddings.py`

**Strateji:** Dense mode için `sentence-transformers` (zaten kurulu, Apple MPS desteği var), sparse mode için `FlagEmbedding`. Her ikisi aynı `BAAI/bge-m3` checkpoint'ini kullanır.

**Tam yeni `embeddings.py`:**

```python
from __future__ import annotations

import os
from dataclasses import dataclass, field

_DENSE_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
_ENABLE_SPARSE = os.getenv("ENABLE_SPARSE_RETRIEVAL", "true").lower() in {"1", "true", "yes"}


@dataclass(slots=True)
class EmbeddingBackend:
    dimension: int = 1024
    _dense_model: object | None = field(init=False, default=None, repr=False)
    _sparse_model: object | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            self._dense_model = SentenceTransformer(_DENSE_MODEL, trust_remote_code=True)
            dim_fn = (
                getattr(self._dense_model, "get_embedding_dimension", None)
                or getattr(self._dense_model, "get_sentence_embedding_dimension", None)
            )
            if dim_fn:
                self.dimension = int(dim_fn())
        except Exception:
            self._dense_model = None

        if _ENABLE_SPARSE:
            try:
                from FlagEmbedding import BGEM3FlagModel
                self._sparse_model = BGEM3FlagModel(_DENSE_MODEL, use_fp16=True)
            except Exception:
                self._sparse_model = None

    def embed(self, text: str) -> list[float]:
        if self._dense_model is not None:
            vec = self._dense_model.encode([text], normalize_embeddings=True)[0]
            return [float(v) for v in vec]
        return self._hashed_embedding(text)

    def embed_sparse(self, text: str) -> dict[int, float]:
        """BGE-M3 lexical weights — BM25-style sparse vector."""
        if self._sparse_model is not None:
            output = self._sparse_model.encode([text], return_dense=False, return_sparse=True)
            weights = output["lexical_weights"][0]
            return {int(k): float(v) for k, v in weights.items()}
        return {}

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if self._dense_model is not None and texts:
            matrix = self._dense_model.encode(
                texts, normalize_embeddings=True, batch_size=32, show_progress_bar=True
            )
            return [[float(v) for v in row] for row in matrix]
        return [self._hashed_embedding(t) for t in texts]

    def embed_many_sparse(self, texts: list[str]) -> list[dict[int, float]]:
        if self._sparse_model is not None and texts:
            output = self._sparse_model.encode(texts, return_dense=False, return_sparse=True, batch_size=16)
            return [
                {int(k): float(v) for k, v in weights.items()}
                for weights in output["lexical_weights"]
            ]
        return [{} for _ in texts]

    def embed_with_prefix(self, text: str, prefix: str) -> list[float]:
        return self.embed(f"{prefix} {text}")

    @property
    def is_neural(self) -> bool:
        return self._dense_model is not None

    @property
    def sparse_available(self) -> bool:
        return self._sparse_model is not None

    def _hashed_embedding(self, text: str) -> list[float]:
        import hashlib, math, re
        tokens = re.findall(r"[a-z0-9']+", text.strip().lower())
        vector = [0.0] * self.dimension
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(v * v for v in vector))
        if norm:
            vector = [v / norm for v in vector]
        return vector


_backend: EmbeddingBackend | None = None


def _get_backend() -> EmbeddingBackend:
    global _backend
    if _backend is None:
        _backend = EmbeddingBackend()
    return _backend


def embed_message(text: str) -> list[float]:
    return _get_backend().embed(text)


def embed_summary(text: str) -> list[float]:
    return _get_backend().embed(text)


def embed_sparse(text: str) -> dict[int, float]:
    return _get_backend().embed_sparse(text)


def get_embedding_dimension() -> int:
    return _get_backend().dimension
```

#### Değişen dosya: `server/app/core/config.py`

Şu anki default `all-MiniLM-L6-v2` yerine:

```python
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
ENABLE_SPARSE_RETRIEVAL = os.getenv("ENABLE_SPARSE_RETRIEVAL", "true").lower() in {"1","true","yes"}
BGE_RERANKER_MODEL = os.getenv("BGE_RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
RERANK_CANDIDATES = int(os.getenv("RERANK_CANDIDATES", "20"))
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "32768"))
```

---

### PHASE 2 — Qdrant Migration (1-2 gün)

#### Değişen dosya: `server/app/core/retrieval/qdrant_store.py`

Mevcut implementasyon dense-only ve `recreate_collection` kullanıyor (veriyi siliyor). Yeni versiyon:

```python
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from server.app.core.retrieval.corpus import KnowledgeBase, KnowledgeChunk

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, SparseVectorParams, SparseIndexParams,
        PointStruct, SparseVector, NamedVector, NamedSparseVector,
        Filter, FieldCondition, MatchValue, QueryRequest,
        Prefetch, FusionQuery, Fusion,
    )
    _QDRANT_AVAILABLE = True
except ImportError:
    _QDRANT_AVAILABLE = False


class QdrantStore:
    DENSE_NAME = "dense"
    SPARSE_NAME = "sparse"

    def __init__(self, url: str, collection_name: str) -> None:
        self.url = url
        self.collection_name = collection_name
        self._client = QdrantClient(url=url, timeout=30) if _QDRANT_AVAILABLE else None

    @property
    def available(self) -> bool:
        if self._client is None:
            return False
        try:
            self._client.get_collections()
            return True
        except Exception:
            return False

    def ensure_collection(self, dimension: int = 1024) -> None:
        if self._client is None:
            return
        existing = [c.name for c in self._client.get_collections().collections]
        if self.collection_name not in existing:
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    self.DENSE_NAME: VectorParams(size=dimension, distance=Distance.COSINE),
                },
                sparse_vectors_config={
                    self.SPARSE_NAME: SparseVectorParams(
                        index=SparseIndexParams(on_disk=False)
                    ),
                },
            )

    def upsert_chunks(
        self,
        chunks: list[KnowledgeChunk],
        dense_vectors: list[list[float]],
        sparse_vectors: list[dict[int, float]] | None = None,
    ) -> None:
        if self._client is None or not chunks:
            return

        self.ensure_collection(dimension=len(dense_vectors[0]) if dense_vectors else 1024)

        points = []
        for i, (chunk, dense) in enumerate(zip(chunks, dense_vectors)):
            sparse = sparse_vectors[i] if sparse_vectors else {}
            sparse_indices = list(sparse.keys())
            sparse_values = list(sparse.values())

            point = PointStruct(
                id=abs(hash(chunk.id)) % (2**63),
                payload={**asdict(chunk), "chunk_str_id": chunk.id},
                vector={
                    self.DENSE_NAME: dense,
                    self.SPARSE_NAME: SparseVector(
                        indices=sparse_indices, values=sparse_values
                    ),
                },
            )
            points.append(point)

        self._client.upsert(collection_name=self.collection_name, points=points)

    def hybrid_search(
        self,
        dense_query: list[float],
        sparse_query: dict[int, float],
        k: int = 20,
        topic: str | None = None,
        language: str | None = None,
    ) -> list[tuple[KnowledgeChunk, float]]:
        if self._client is None:
            return []

        query_filter = self._build_filter(topic=topic, language=language)

        try:
            results = self._client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    Prefetch(
                        query=NamedVector(name=self.DENSE_NAME, vector=dense_query),
                        limit=k * 2,
                        filter=query_filter,
                    ),
                    Prefetch(
                        query=NamedSparseVector(
                            name=self.SPARSE_NAME,
                            vector=SparseVector(
                                indices=list(sparse_query.keys()),
                                values=list(sparse_query.values()),
                            ),
                        ),
                        limit=k * 2,
                        filter=query_filter,
                    ),
                ],
                query=FusionQuery(fusion=Fusion.RRF),
                limit=k,
                with_payload=True,
            ).points
        except Exception:
            return self._dense_only_search(dense_query, k=k, topic=topic, language=language)

        return self._parse_results(results)

    def _dense_only_search(
        self, dense_query: list[float], k: int = 20,
        topic: str | None = None, language: str | None = None,
    ) -> list[tuple[KnowledgeChunk, float]]:
        query_filter = self._build_filter(topic=topic, language=language)
        results = self._client.search(
            collection_name=self.collection_name,
            query_vector=NamedVector(name=self.DENSE_NAME, vector=dense_query),
            limit=k,
            query_filter=query_filter,
            with_payload=True,
        )
        return self._parse_results(results)

    def _build_filter(self, topic: str | None, language: str | None) -> Filter | None:
        conditions = []
        if topic:
            conditions.append(FieldCondition(key="topic", match=MatchValue(value=topic)))
        if language:
            conditions.append(FieldCondition(key="language", match=MatchValue(value=language)))
        if not conditions:
            return None
        return Filter(must=conditions)

    def _parse_results(self, results: list) -> list[tuple[KnowledgeChunk, float]]:
        scored = []
        for item in results:
            payload: dict[str, Any] = item.payload or {}
            chunk = KnowledgeChunk.from_dict(payload)
            scored.append((chunk, float(item.score or 0.0)))
        return scored
```

#### Değişen dosya: `server/app/core/retrieval/hybrid_retriever.py`

**Tam yeni dosya** (mevcut dosyanın tamamı değiştiriliyor):

```python
from __future__ import annotations

import re
from pathlib import Path

from server.app.core.config import (
    ENABLE_GRAPH_RAG, GRAPH_RAG_MIN_CHUNKS, GRAPH_RAG_MIN_QUERY_TERMS,
    QDRANT_COLLECTION, QDRANT_URL, RERANK_CANDIDATES,
)
from server.app.core.retrieval.corpus import KnowledgeBase, KnowledgeChunk
from server.app.core.retrieval.embeddings import EmbeddingBackend, embed_sparse
from server.app.core.retrieval.faiss_store import FaissIndexStore
from server.app.core.retrieval.graph_store import (
    GraphStore, is_graph_friendly_query, should_enable_graph_rag,
)
from server.app.core.retrieval.qdrant_store import QdrantStore
from server.app.core.retrieval.retriever import ScoredChunk, SimpleRetriever, topic_alignment_score
from server.app.utils.text import infer_language


class HybridRetriever:
    _RRF_K: int = 60

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        faiss_store: FaissIndexStore,
        embedder: EmbeddingBackend | None = None,
        graph_path: Path | None = None,
    ) -> None:
        self.knowledge_base = knowledge_base
        self.faiss_store = faiss_store
        self.embedder = embedder or EmbeddingBackend()
        self.keyword_retriever = SimpleRetriever(knowledge_base)
        self.qdrant_store = QdrantStore(QDRANT_URL, QDRANT_COLLECTION)
        self.graph_store: GraphStore | None = None

        if ENABLE_GRAPH_RAG and should_enable_graph_rag(knowledge_base, GRAPH_RAG_MIN_CHUNKS):
            self.graph_store = GraphStore(storage_path=graph_path)
            if not self.graph_store.load():
                self.graph_store.build(knowledge_base)
                self.graph_store.save()

    def retrieve(
        self,
        query: str,
        topic: str | None = None,
        k: int = 8,
        *,
        source_kind: str | None = None,
        language: str | None = None,
        min_confidence: float | None = None,
    ) -> list[ScoredChunk]:
        candidate_k = max(k * 4, RERANK_CANDIDATES)

        # Primary: Qdrant hybrid (dense + sparse, RRF built-in via Query API)
        if self.qdrant_store.available:
            dense_vec = self.embedder.embed(query)
            sparse_vec = embed_sparse(query)
            raw = self.qdrant_store.hybrid_search(
                dense_query=dense_vec,
                sparse_query=sparse_vec,
                k=candidate_k,
                topic=topic,
                language=language,
            )
            if raw:
                scored = [ScoredChunk(chunk=c, score=s) for c, s in raw]
                scored = self._apply_graph_boost(scored, query, topic)
                scored = self._apply_post_filters(
                    scored, source_kind=source_kind, min_confidence=min_confidence
                )
                return scored[:k]

        # Fallback: FAISS dense + keyword BM25-lite via RRF
        dense_vec = self.embedder.embed(query)
        semantic_results = self.faiss_store.search(
            dense_vec,
            topic=topic,
            k=candidate_k,
            source_kind=source_kind,
            language=language,
            min_confidence=min_confidence,
        )
        keyword_results = self.keyword_retriever.retrieve(
            query,
            topic=topic,
            k=candidate_k,
            source_kind=source_kind,
            language=language,
            min_confidence=min_confidence,
        )
        merged = self._rrf_merge(semantic_results, keyword_results, k=candidate_k)
        merged = self._apply_graph_boost(merged, query, topic)
        return merged[:k]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rrf_merge(
        self,
        dense: list[tuple[KnowledgeChunk, float]],
        keyword: list[ScoredChunk],
        k: int,
    ) -> list[ScoredChunk]:
        scores: dict[str, float] = {}
        chunk_map: dict[str, KnowledgeChunk] = {}

        for rank, (chunk, _) in enumerate(dense):
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (self._RRF_K + rank + 1)
            chunk_map[chunk.id] = chunk

        for rank, sc in enumerate(keyword):
            scores[sc.chunk.id] = scores.get(sc.chunk.id, 0.0) + 1.0 / (self._RRF_K + rank + 1)
            chunk_map[sc.chunk.id] = sc.chunk

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [ScoredChunk(chunk=chunk_map[cid], score=s) for cid, s in ranked[:k]]

    def _apply_graph_boost(
        self,
        scored: list[ScoredChunk],
        query: str,
        topic: str | None,
    ) -> list[ScoredChunk]:
        if self.graph_store is None:
            return scored
        if not is_graph_friendly_query(query, topic, min_terms=GRAPH_RAG_MIN_QUERY_TERMS):
            return scored
        query_kws = re.findall(r"\w{4,}", query.lower())
        graph_ids = set(
            self.graph_store.get_related_chunks(seed_topic=topic, seed_keywords=query_kws)
        )
        for sc in scored:
            if sc.chunk.id in graph_ids:
                sc.score += 0.10
        return sorted(scored, key=lambda x: x.score, reverse=True)

    def _apply_post_filters(
        self,
        scored: list[ScoredChunk],
        *,
        source_kind: str | None,
        min_confidence: float | None,
    ) -> list[ScoredChunk]:
        result = []
        for sc in scored:
            if source_kind and sc.chunk.source_kind != source_kind:
                continue
            if min_confidence is not None and sc.chunk.confidence < min_confidence:
                continue
            result.append(sc)
        return result
```

---

### PHASE 3 — Neural Reranker (1 gün)

#### Değişen dosya: `server/app/core/retrieval/reranker.py`

Mevcut `EvidenceReranker` → `NeuralReranker` + keyword fallback korunur:

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from server.app.core.retrieval.retriever import ScoredChunk

_RERANKER_MODEL = os.getenv("BGE_RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
_RERANK_CANDIDATES = int(os.getenv("RERANK_CANDIDATES", "20"))


@dataclass(slots=True)
class RerankDecision:
    chunk_id: str
    score: float
    reason: str


class NeuralReranker:
    def __init__(self, top_k: int = 5) -> None:
        self.top_k = top_k
        self._model = None
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(_RERANKER_MODEL, max_length=512, trust_remote_code=True)
        except Exception:
            self._model = None

    def rerank(self, query: str, candidates: list[ScoredChunk]) -> list[ScoredChunk]:
        if not candidates:
            return []
        if self._model is None:
            return candidates[:self.top_k]

        pairs = [(query, f"{c.chunk.title}. {c.chunk.content[:800]}") for c in candidates]
        try:
            scores = self._model.predict(pairs, show_progress_bar=False)
            for chunk, score in zip(candidates, scores):
                chunk.score = float(score)
            return sorted(candidates, key=lambda x: x.score, reverse=True)[:self.top_k]
        except Exception:
            return candidates[:self.top_k]


# Backward-compatible singleton
reranker = NeuralReranker()
```

---

### PHASE 4 — Chunker Yeniden Yazımı (1-2 gün)

#### Değişen dosya: `server/app/core/retrieval/ingestion/chunker.py`

```python
from __future__ import annotations

import re

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    _LC_AVAILABLE = True
except ImportError:
    _LC_AVAILABLE = False

SECTION_PATTERNS: dict[str, str] = {
    "abstract":     r"(?i)^#+\s*(abstract|özet)",
    "introduction": r"(?i)^#+\s*(introduction|giriş|1[\.\s])",
    "methods":      r"(?i)^#+\s*(method|yöntem|materials?|procedure|uygulama)",
    "results":      r"(?i)^#+\s*(result|bulgular|findings?)",
    "discussion":   r"(?i)^#+\s*(discussion|tartışma)",
    "conclusion":   r"(?i)^#+\s*(conclusion|sonuç|implications?)",
    "references":   r"(?i)^#+\s*(references?|bibliography|kaynakça|kaynaklar)",
}

SECTION_CONFIG: dict[str, dict] = {
    "abstract":     {"chunk_size": 400,  "chunk_overlap": 0},
    "introduction": {"chunk_size": 512,  "chunk_overlap": 80},
    "methods":      {"chunk_size": 768,  "chunk_overlap": 100},
    "results":      {"chunk_size": 512,  "chunk_overlap": 80},
    "discussion":   {"chunk_size": 512,  "chunk_overlap": 80},
    "conclusion":   {"chunk_size": 400,  "chunk_overlap": 0},
    "default":      {"chunk_size": 512,  "chunk_overlap": 80},
}

EXCLUDED_SECTIONS = {"references"}


def _detect_section(header_text: str) -> str:
    for section_type, pattern in SECTION_PATTERNS.items():
        if re.search(pattern, header_text, re.MULTILINE):
            return section_type
    return "default"


def _split_text(text: str, section_type: str) -> list[str]:
    if not _LC_AVAILABLE:
        return [text] if len(text) > 60 else []
    cfg = SECTION_CONFIG.get(section_type, SECTION_CONFIG["default"])
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg["chunk_size"],
        chunk_overlap=cfg["chunk_overlap"],
        length_function=len,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    )
    return splitter.split_text(text)


class SectionAwareChunker:
    """
    Docling Markdown çıktısını section-aware olarak böler.
    Her section kendi token limitiyle işlenir.
    References bölümü dışarıda bırakılır.
    """

    def chunk(self, markdown_text: str) -> list[dict[str, str]]:
        sections = self._parse_sections(markdown_text)
        chunks: list[dict[str, str]] = []
        chunk_index = 1

        for section_type, section_header, section_text in sections:
            if section_type in EXCLUDED_SECTIONS:
                continue
            if len(section_text.strip()) < 60:
                continue

            pieces = _split_text(section_text, section_type)
            for piece in pieces:
                piece = piece.strip()
                if len(piece) < 60:
                    continue
                chunks.append({
                    "title": section_header[:80],
                    "content": piece,
                    "section": section_type,
                    "section_header": section_header[:120],
                    "chunk_index": str(chunk_index),
                })
                chunk_index += 1

        return chunks

    def _parse_sections(self, md: str) -> list[tuple[str, str, str]]:
        """Markdown'ı header sınırlarına göre section'lara ayırır."""
        header_re = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
        matches = list(header_re.finditer(md))

        if not matches:
            return [("default", "Content", md)]

        sections = []
        for i, match in enumerate(matches):
            header_text = match.group(0)
            section_type = _detect_section(header_text)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
            body = md[start:end].strip()
            sections.append((section_type, match.group(2).strip(), body))

        return sections
```

---

### PHASE 5 — Contextual Prefix (opsiyonel, 1 gün)

#### Yeni dosya: `server/app/core/retrieval/ingestion/contextual_prefix.py`

```python
from __future__ import annotations

import os

CONTEXT_PROMPT = """\
<document_title>{title}</document_title>
<document_intro>{intro}</document_intro>

Aşağıdaki chunk'ı bu doküman içinde konumlandırmak için 2-3 cümlelik bağlam yaz. \
Chunk hangi bölümden geldiğini ve neyi ele aldığını belirt. \
Kullanılan dille (Türkçe veya İngilizce) aynı dilde yaz. \
Sadece bağlamı yaz, başka açıklama ekleme.

<chunk>{chunk}</chunk>"""


def generate_context_prefix(
    chunk_text: str,
    doc_title: str,
    doc_intro: str,
    *,
    use_local: bool = False,
) -> str:
    """
    use_local=True: Ollama qwen2.5:7b (ücretsiz ama yavaş)
    use_local=False: Claude Haiku API (hızlı, ~$0.001/chunk)
    """
    prompt = CONTEXT_PROMPT.format(
        title=doc_title[:200],
        intro=doc_intro[:500],
        chunk=chunk_text[:600],
    )

    if use_local:
        return _local_generate(prompt)
    return _claude_generate(prompt)


def _local_generate(prompt: str) -> str:
    import json
    from urllib import request, error
    payload = {
        "model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 4096},
    }
    req = request.Request(
        f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read())
        return str(body.get("response", "")).strip()
    except Exception:
        return ""


def _claude_generate(prompt: str) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-haiku-3-5",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception:
        return ""
```

---

### PHASE 6 — LLM Client Güncelleme (yarım gün)

#### Değişen dosya: `server/app/core/generation/llm.py`

**Tam yeni dosya:**

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request

from server.app.core.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_NUM_CTX


@dataclass(slots=True)
class LLMResult:
    text: str
    available: bool


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, prompt: str, temperature: float = 0.2) -> LLMResult:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": OLLAMA_NUM_CTX,  # 32768 — qwen2.5:14b için zorunlu
                "top_p": 0.9,
            },
        }

        req = request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            # 14B model 30s'de timeout edebilir — 120s'ye çıkarıldı
            with request.urlopen(req, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
            return LLMResult(text=str(body.get("response", "")).strip(), available=True)
        except (error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return LLMResult(text="", available=False)
```

---

### PHASE 7 — Ingestion Script (2-3 gün)

#### Yeni dosya: `scripts/build_and_ingest.py`

**Tam dosya** (`kc.__dataclass_fields__` bug fix dahil, tüm `KnowledgeChunk` alanları doğru set ediliyor):

```python
#!/usr/bin/env python3
"""
Calma — Full PDF ingestion pipeline
=====================================
1. PDF parse  (Docling → Markdown, pypdf fallback)
2. Section-aware chunking  (512 tok, 80 overlap)
3. Quality filter  (min 50 char, References exclusion)
4. Optional: contextual prefix  (LLM ile 50-100 tok bağlam)
5. BGE-M3 embed  (dense 1024 dim + sparse lexical)
6. Qdrant upsert  (dense + sparse named vectors)
7. Processed corpus JSON kayıt  (FAISS fallback için)

Usage:
    python scripts/build_and_ingest.py [options]

Options:
    --pdf-dir PATH                PDF dizini (default: data/raw)
    --contextual-prefix-local     Ollama ile contextual prefix üret (ücretsiz, ~2-3 saat)
    --contextual-prefix-claude    Claude Haiku API ile prefix üret (~$1-2, ~15 dk)
    --dry-run                     Chunk sayısını göster, Qdrant'a yazma
    --reset-collection            Mevcut Qdrant collection'ı sil ve yeniden oluştur
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):  # type: ignore[misc]
        return iterable

from server.app.core.config import QDRANT_URL, QDRANT_COLLECTION, PROCESSED_CORPUS_PATH
from server.app.core.retrieval.corpus import KnowledgeChunk
from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.pdf_ingestion import build_chunks_from_pdf, infer_meta
from server.app.core.retrieval.qdrant_store import QdrantStore

EXCLUDED_PATTERNS = (
    "preventing-suicide",
    "problem-management-plus",
    "stand-up-to-stress-coloring",
)


def should_skip(pdf_path: Path) -> bool:
    name = pdf_path.name.lower()
    return any(pat in name for pat in EXCLUDED_PATTERNS)


def _get_contextual_prefix(
    chunk_text: str,
    doc_title: str,
    doc_intro: str,
    *,
    use_local: bool,
    use_claude: bool,
) -> str:
    if not use_local and not use_claude:
        return ""
    from server.app.core.retrieval.ingestion.contextual_prefix import generate_context_prefix
    return generate_context_prefix(
        chunk_text, doc_title, doc_intro, use_local=use_local
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Calma PDF ingestion pipeline")
    parser.add_argument("--pdf-dir", default="data/raw", type=Path)
    parser.add_argument("--contextual-prefix-local", action="store_true")
    parser.add_argument("--contextual-prefix-claude", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reset-collection", action="store_true")
    args = parser.parse_args()

    pdf_dir = ROOT / args.pdf_dir if not args.pdf_dir.is_absolute() else args.pdf_dir
    pdfs = sorted(p for p in pdf_dir.glob("*.pdf") if not should_skip(p))

    print(f"{'='*60}")
    print(f"  Calma PDF Ingestion Pipeline")
    print(f"{'='*60}")
    print(f"  PDF dizini  : {pdf_dir}")
    print(f"  PDF sayısı  : {len(pdfs)}")
    print(f"  Dry run     : {args.dry_run}")
    print(f"  Ctx prefix  : {'local' if args.contextual_prefix_local else 'claude' if args.contextual_prefix_claude else 'hayır'}")
    print()

    # 1. Embedding backend yükle
    print("[1/4] BGE-M3 yükleniyor...")
    t0 = time.time()
    embedder = EmbeddingBackend()
    print(f"      Dense dim : {embedder.dimension}")
    print(f"      Sparse    : {'evet' if embedder.sparse_available else 'hayır (FlagEmbedding kurulu değil)'}")
    print(f"      Süre      : {time.time() - t0:.1f}s")

    # 2. Qdrant bağlan
    store = QdrantStore(QDRANT_URL, QDRANT_COLLECTION)
    if not args.dry_run:
        if args.reset_collection:
            try:
                store._client.delete_collection(QDRANT_COLLECTION)
                print(f"[2/4] Collection '{QDRANT_COLLECTION}' silindi.")
            except Exception:
                pass
        store.ensure_collection(dimension=embedder.dimension)
        print(f"[2/4] Qdrant collection hazır: {QDRANT_COLLECTION}")
    else:
        print("[2/4] Dry run — Qdrant atlandı")

    # 3. PDF döngüsü
    print(f"\n[3/4] PDF'ler işleniyor...\n")
    all_corpus: list[dict] = []
    total_chunks = 0
    skipped_pdfs = 0

    for pdf in tqdm(pdfs, desc="PDFs"):
        meta = infer_meta(pdf)
        if not meta.include_in_index:
            skipped_pdfs += 1
            continue

        raw_chunks = build_chunks_from_pdf(pdf, prefer_layout_aware=True)
        if not raw_chunks:
            skipped_pdfs += 1
            continue

        # doc_intro: ilk chunk'ın içeriğini referans al
        doc_intro = raw_chunks[0].content[:300] if raw_chunks else ""

        chunk_texts: list[str] = []
        for rc in raw_chunks:
            text = rc.content
            prefix = _get_contextual_prefix(
                text, meta.title, doc_intro,
                use_local=args.contextual_prefix_local,
                use_claude=args.contextual_prefix_claude,
            )
            if prefix:
                text = f"{prefix}\n\n{text}"
            chunk_texts.append(text)

        # Embed
        dense_vecs = embedder.embed_many(chunk_texts)
        sparse_vecs = (
            embedder.embed_many_sparse(chunk_texts)
            if embedder.sparse_available
            else None
        )

        # KnowledgeChunk'a dönüştür — tüm alanlar explicit set ediliyor
        kc_chunks = [
            KnowledgeChunk(
                id=rc.id,
                title=rc.title,
                topic=rc.topic,
                source=rc.source,
                content=chunk_texts[i],       # prefix'li versiyon
                keywords=rc.keywords,
                section=rc.section,
                pdf_file=rc.pdf_file,
                page=rc.page,
                source_kind=rc.source_kind,
                parser_mode=rc.parser_mode,
                confidence=rc.confidence,
                language=rc.language,
            )
            for i, rc in enumerate(raw_chunks)
        ]

        if not args.dry_run:
            store.upsert_chunks(kc_chunks, dense_vecs, sparse_vecs)

        # Corpus JSON için — dataclasses.asdict kullan (slots=True ile uyumlu)
        for kc in kc_chunks:
            all_corpus.append(dataclasses.asdict(kc))

        total_chunks += len(kc_chunks)
        tqdm.write(f"  ✓ {pdf.name}: {len(kc_chunks)} chunk")

    # 4. Corpus JSON kaydet
    if not args.dry_run:
        PROCESSED_CORPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PROCESSED_CORPUS_PATH, "w", encoding="utf-8") as f:
            json.dump(all_corpus, f, ensure_ascii=False, indent=2)
        print(f"\n[4/4] Corpus JSON kaydedildi: {PROCESSED_CORPUS_PATH}")
    else:
        print(f"\n[4/4] Dry run — corpus JSON yazılmadı")

    print(f"\n{'='*60}")
    print(f"  Toplam PDF      : {len(pdfs)}")
    print(f"  İşlenen PDF     : {len(pdfs) - skipped_pdfs}")
    print(f"  Atlanan PDF     : {skipped_pdfs}")
    print(f"  Toplam chunk    : {total_chunks}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
```

**Çalıştırma:**

```bash
# Dry run — kaç chunk üretiyor gör, hiçbir şey yazılmaz
python scripts/build_and_ingest.py --pdf-dir data/raw --dry-run

# Gerçek ingestion (contextual prefix olmadan, en hızlı ~10-20 dk)
python scripts/build_and_ingest.py --pdf-dir data/raw

# Qdrant'ı temizleyip sıfırdan başla
python scripts/build_and_ingest.py --pdf-dir data/raw --reset-collection

# Contextual prefix: local Ollama (ücretsiz, ~2-3 saat)
python scripts/build_and_ingest.py --pdf-dir data/raw --contextual-prefix-local

# Contextual prefix: Claude Haiku API (~$1-2, ~15 dakika)
python scripts/build_and_ingest.py --pdf-dir data/raw --contextual-prefix-claude
```

---

---

### PHASE 8 — Index Rebuild (yarım gün)

#### Değişen dosya: `scripts/build_index.py`

Mevcut script sadece FAISS build ediyor. Yeni versiyon hem FAISS hem Qdrant'ı rebuild eder.

**Tam yeni dosya:**

```python
#!/usr/bin/env python3
"""
Calma — Index Builder
======================
FAISS ve Qdrant index'lerini (yeniden) oluşturur.

Usage:
    python scripts/build_index.py [--backend faiss|qdrant|both] [--reset]

Options:
    --backend   Hangi index build edilecek (default: both)
    --reset     Mevcut Qdrant collection'ı sil ve yeniden oluştur
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server.app.core.config import (
    FAISS_INDEX_PATH, FAISS_METADATA_PATH,
    QDRANT_URL, QDRANT_COLLECTION,
)
from server.app.core.retrieval.corpus import KnowledgeBase
from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.faiss_store import FaissIndexStore
from server.app.core.retrieval.qdrant_store import QdrantStore


def build_faiss(kb: KnowledgeBase, embedder: EmbeddingBackend) -> None:
    print("\n── FAISS Index Build ──────────────────────────")
    store = FaissIndexStore(FAISS_INDEX_PATH, FAISS_METADATA_PATH)
    t0 = time.time()
    store.build(kb, embedder)
    print(f"  ✅ {len(kb.chunks)} chunk indexlendi ({time.time() - t0:.1f}s)")
    print(f"  Dosya: {FAISS_INDEX_PATH}")

    # Smoke test
    q_emb = embedder.embed("I feel anxious and stressed")
    results = store.search(q_emb, k=3)
    if results:
        print("  Smoke test (top-3):")
        for chunk, score in results:
            print(f"    [{score:.3f}] {chunk.title[:50]}  ({chunk.topic})")
    else:
        print("  ⚠️  Smoke test: sonuç yok — embedding veya index sorununu kontrol et")


def build_qdrant(kb: KnowledgeBase, embedder: EmbeddingBackend, reset: bool) -> None:
    print("\n── Qdrant Index Build ─────────────────────────")
    store = QdrantStore(QDRANT_URL, QDRANT_COLLECTION)

    if not store.available:
        print("  ❌ Qdrant bağlantısı yok — docker compose up qdrant çalıştır")
        return

    if reset:
        try:
            store._client.delete_collection(QDRANT_COLLECTION)
            print(f"  Collection '{QDRANT_COLLECTION}' silindi")
        except Exception:
            pass

    store.ensure_collection(dimension=embedder.dimension)

    # Chunk'ları batch olarak upsert et
    texts = [
        f"{chunk.title} {chunk.content} {' '.join(chunk.keywords)}"
        for chunk in kb.chunks
    ]

    BATCH = 64
    t0 = time.time()
    total = 0

    for i in range(0, len(kb.chunks), BATCH):
        batch_chunks = kb.chunks[i : i + BATCH]
        batch_texts = texts[i : i + BATCH]

        dense_vecs = embedder.embed_many(batch_texts)
        sparse_vecs = (
            embedder.embed_many_sparse(batch_texts)
            if embedder.sparse_available
            else None
        )
        store.upsert_chunks(batch_chunks, dense_vecs, sparse_vecs)
        total += len(batch_chunks)
        print(f"  {total}/{len(kb.chunks)} chunk upsert edildi...", end="\r")

    elapsed = time.time() - t0
    print(f"\n  ✅ {total} chunk indexlendi ({elapsed:.1f}s)")
    print(f"  Sparse: {'evet (BGE-M3 lexical)' if embedder.sparse_available else 'hayır (FlagEmbedding yok)'}")

    # Smoke test
    dense_q = embedder.embed("anxiety symptoms")
    sparse_q = embedder.embed_sparse("anxiety symptoms")
    results = store.hybrid_search(dense_q, sparse_q, k=3)
    if results:
        print("  Smoke test hybrid search (top-3):")
        for chunk, score in results:
            print(f"    [{score:.3f}] {chunk.title[:50]}  ({chunk.topic})")
    else:
        print("  ⚠️  Smoke test: sonuç yok")


def main() -> None:
    parser = argparse.ArgumentParser(description="Calma Index Builder")
    parser.add_argument("--backend", choices=["faiss", "qdrant", "both"], default="both")
    parser.add_argument("--reset", action="store_true", help="Qdrant collection'ı sıfırla")
    args = parser.parse_args()

    print("=" * 50)
    print("  Calma — Index Builder")
    print("=" * 50)

    print("\n[1/3] Knowledge base yükleniyor...")
    kb = KnowledgeBase.load()
    print(f"  {len(kb.chunks)} chunk yüklendi")

    topic_counts = Counter(c.topic for c in kb.chunks)
    for topic, count in sorted(topic_counts.items()):
        print(f"    {topic}: {count}")

    print("\n[2/3] BGE-M3 yükleniyor...")
    t0 = time.time()
    embedder = EmbeddingBackend()
    print(f"  Backend : {'neural (BGE-M3)' if embedder.is_neural else 'hash fallback'}")
    print(f"  Dim     : {embedder.dimension}")
    print(f"  Sparse  : {'evet' if embedder.sparse_available else 'hayır'}")
    print(f"  Süre    : {time.time() - t0:.1f}s")

    print("\n[3/3] Index build...")

    if args.backend in ("faiss", "both"):
        build_faiss(kb, embedder)

    if args.backend in ("qdrant", "both"):
        build_qdrant(kb, embedder, reset=args.reset)

    print("\n✅ Index build tamamlandı.\n")


if __name__ == "__main__":
    main()
```

**Çalıştırma:**

```bash
# İkisini birden build et (default)
python scripts/build_index.py

# Sadece Qdrant
python scripts/build_index.py --backend qdrant

# Qdrant'ı sıfırdan build et
python scripts/build_index.py --backend qdrant --reset

# Sadece FAISS
python scripts/build_index.py --backend faiss
```

---

## Bölüm 5 — Qdrant vs FAISS: Final Karar

### Senaryo analizi

| Senaryo | Karar |
|---|---|
| 3.000 chunk, sadece dense retrieval | FAISS yeterli |
| 3.000 chunk, dense + sparse (BGE-M3) | **Qdrant** — FAISS sparse desteklemiyor |
| Metadata filtreleme (topic, language) | **Qdrant** — payload index |
| Incremental update (yeni PDF ekle) | **Qdrant** — HTTP upsert |
| Docker Compose'da zaten var | **Qdrant** — altyapı mevcut |
| Offline / disk-only deploy | FAISS fallback kalır |
| Sorgu latency (3K vector) | Her ikisi <1ms — fark yok |

**Final karar:** Qdrant primary, FAISS offline fallback.  
Mevcut `faiss_store.py` silinmez — `RETRIEVAL_BACKEND=faiss` ile aktif edilebilir.

---

## Bölüm 6 — Evaluation Framework (Bitirme Projesi için Zorunlu)

### 6.1 Golden Test Set Oluşturma

Gerçek PDF'lerden 30-50 sorgu-cevap çifti oluştur:

```
Türkçe sorgular (15 adet):
  - "Sosyal izolasyon depresyonu nasıl etkiler?"
  - "CBT teknikleri nelerdir?"
  - "Uyku düzensizliğinin anksiyete ile ilişkisi"
  ...

İngilizce sorgular (15 adet):
  - "What are the symptoms of generalized anxiety disorder?"
  - "How does CBT differ from DBT?"
  ...

Her sorgu için: expected_chunk_ids (hangi chunk'lar cevap içermeli)
```

### 6.2 Evaluation Script

#### Yeni dosya: `scripts/evaluate_rag.py`

**Tam dosya** — retrieval metrikleri (P@K, R@K, nDCG@K, MRR@K) + opsiyonel RAGAS:

```python
#!/usr/bin/env python3
"""
Calma — Unified RAG Evaluation
================================
Retrieval metrikleri: Precision@K, Recall@K, nDCG@K, MRR@K
RAG metrikleri (opsiyonel): faithfulness, answer_relevancy, context_precision

Ablation modları:
  --mode retrieval   : sadece retrieval metrikleri (Qdrant veya FAISS)
  --mode ragas       : RAGAS ile tam RAG değerlendirmesi (Ollama gerekli)
  --mode all         : ikisi birden

Golden set:
  scripts/ dizinindeki GOLDEN_SET sabiti kullanılır.
  Gerçek PDF ingestion sonrası chunk ID'leri güncellenmeli.

Çalıştır:
  python scripts/evaluate_rag.py --mode retrieval
  python scripts/evaluate_rag.py --mode ragas --output reports/ragas.json
  python scripts/evaluate_rag.py --mode all --k 5
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server.app.core.config import (
    FAISS_INDEX_PATH, FAISS_METADATA_PATH, QDRANT_URL, QDRANT_COLLECTION,
)
from server.app.core.retrieval.corpus import KnowledgeBase
from server.app.core.retrieval.embeddings import EmbeddingBackend
from server.app.core.retrieval.faiss_store import FaissIndexStore
from server.app.core.retrieval.hybrid_retriever import HybridRetriever
from server.app.core.retrieval.retriever import ScoredChunk


# =============================================================================
# Golden Set
# Format: her sorgu için expected_chunk_ids — gerçek PDF ingest sonrası güncellenecek.
# Mevcut hali sample corpus ID'leri ile çalışır (smoke test).
# Gerçek chunk ID'lerini bulmak için:
#   python -c "import json; d=json.load(open('data/processed/processed_knowledge_base.json')); [print(c['id'], c['title'][:60]) for c in d[:20]]"
# =============================================================================

GOLDEN_SET: list[dict] = [
    # ── Türkçe sorgular ──────────────────────────────────────────────────────
    {
        "query": "Sosyal izolasyon depresyonu nasıl etkiler?",
        "topic": "low_mood",
        "lang": "tr",
        "relevant_ids": ["mood-001"],  # Gerçek PDF ingest sonrası güncelle
    },
    {
        "query": "CBT teknikleri nelerdir ve nasıl uygulanır?",
        "topic": "stress_anxiety",
        "lang": "tr",
        "relevant_ids": ["stress-001", "anxiety-001"],
    },
    {
        "query": "Uyku düzensizliğinin anksiyete ile ilişkisi nedir?",
        "topic": "burnout_sleep",
        "lang": "tr",
        "relevant_ids": ["sleep-001", "anxiety-001"],
    },
    {
        "query": "Bipolar bozukluk belirtileri nelerdir?",
        "topic": "bipolar",
        "lang": "tr",
        "relevant_ids": ["mood-001"],
    },
    {
        "query": "Profesyonel psikolojik destek ne zaman alınmalı?",
        "topic": "help_seeking",
        "lang": "tr",
        "relevant_ids": ["help-001"],
    },
    # ── İngilizce sorgular ───────────────────────────────────────────────────
    {
        "query": "What are the symptoms of generalized anxiety disorder?",
        "topic": "stress_anxiety",
        "lang": "en",
        "relevant_ids": ["anxiety-001", "stress-001"],
    },
    {
        "query": "How does cognitive behavioral therapy differ from DBT?",
        "topic": "stress_anxiety",
        "lang": "en",
        "relevant_ids": ["stress-001"],
    },
    {
        "query": "What is burnout and how does it affect mental health?",
        "topic": "burnout_sleep",
        "lang": "en",
        "relevant_ids": ["sleep-001", "mood-001"],
    },
    {
        "query": "I feel sad and have no energy, what could this be?",
        "topic": "low_mood",
        "lang": "en",
        "relevant_ids": ["mood-001"],
    },
    {
        "query": "When should I see a therapist or mental health professional?",
        "topic": "help_seeking",
        "lang": "en",
        "relevant_ids": ["help-001"],
    },
    {
        "query": "How does poor sleep affect mental health and concentration?",
        "topic": "burnout_sleep",
        "lang": "en",
        "relevant_ids": ["sleep-001", "stress-001"],
    },
    {
        "query": "What are the signs of OCD and how is it treated?",
        "topic": "ocd",
        "lang": "en",
        "relevant_ids": [],  # Gerçek chunk ID'leri ile güncelle
    },
    {
        "query": "Explain the relationship between trauma and PTSD",
        "topic": "ptsd",
        "lang": "en",
        "relevant_ids": [],
    },
    {
        "query": "How does social connection protect against depression?",
        "topic": "social_pressure",
        "lang": "en",
        "relevant_ids": [],
    },
    {
        "query": "What are evidence-based interventions for eating disorders?",
        "topic": "eating_disorders",
        "lang": "en",
        "relevant_ids": [],
    },
]


# =============================================================================
# Metrik fonksiyonları
# =============================================================================

def precision_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    if not relevant or k == 0:
        return 0.0
    hits = sum(1 for rid in retrieved[:k] if rid in relevant)
    return hits / k


def recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    if not relevant:
        return 0.0
    hits = sum(1 for rid in retrieved[:k] if rid in relevant)
    return hits / len(relevant)


def ndcg_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    def dcg(ranking: list[str], rel_set: set[str], n: int) -> float:
        return sum(
            1.0 / math.log2(i + 2)
            for i, r in enumerate(ranking[:n])
            if r in rel_set
        )

    rel_set = set(relevant)
    actual = dcg(retrieved, rel_set, k)
    ideal = dcg(list(rel_set) + [x for x in retrieved if x not in rel_set], rel_set, k)
    return actual / ideal if ideal > 0 else 0.0


def mrr_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    rel_set = set(relevant)
    for i, rid in enumerate(retrieved[:k]):
        if rid in rel_set:
            return 1.0 / (i + 1)
    return 0.0


# =============================================================================
# Retrieval evaluation
# =============================================================================

@dataclass
class QueryResult:
    query: str
    topic: str | None
    lang: str
    relevant_ids: list[str]
    retrieved_ids: list[str]
    precision: float
    recall: float
    ndcg: float
    mrr: float
    latency_ms: float


def run_retrieval_evaluation(k: int = 5) -> list[QueryResult]:
    print("[1/3] Knowledge base ve retriever yükleniyor...")
    kb = KnowledgeBase.load()
    embedder = EmbeddingBackend()
    faiss_store = FaissIndexStore(FAISS_INDEX_PATH, FAISS_METADATA_PATH)
    retriever = HybridRetriever(kb, faiss_store, embedder)
    print(f"      {len(kb.chunks)} chunk yüklendi")

    results: list[QueryResult] = []
    print(f"\n[2/3] {len(GOLDEN_SET)} sorgu çalıştırılıyor...\n")

    for item in GOLDEN_SET:
        query: str = item["query"]
        topic: str | None = item.get("topic")
        lang: str = item.get("lang", "en")
        relevant: list[str] = item.get("relevant_ids", [])

        t0 = time.perf_counter()
        retrieved: list[ScoredChunk] = retriever.retrieve(query, topic=topic, k=k)
        latency_ms = (time.perf_counter() - t0) * 1000

        retrieved_ids = [sc.chunk.id for sc in retrieved]

        results.append(QueryResult(
            query=query,
            topic=topic,
            lang=lang,
            relevant_ids=relevant,
            retrieved_ids=retrieved_ids,
            precision=precision_at_k(retrieved_ids, relevant, k),
            recall=recall_at_k(retrieved_ids, relevant, k),
            ndcg=ndcg_at_k(retrieved_ids, relevant, k),
            mrr=mrr_at_k(retrieved_ids, relevant, k),
            latency_ms=latency_ms,
        ))

    return results


def print_retrieval_report(results: list[QueryResult], k: int) -> None:
    agg_p = sum(r.precision for r in results) / len(results)
    agg_r = sum(r.recall for r in results) / len(results)
    agg_n = sum(r.ndcg for r in results) / len(results)
    agg_m = sum(r.mrr for r in results) / len(results)
    agg_lat = sum(r.latency_ms for r in results) / len(results)

    en_results = [r for r in results if r.lang == "en"]
    tr_results = [r for r in results if r.lang == "tr"]

    print(f"\n{'='*72}")
    print(f"  CALMA RETRIEVAL EVALUATION — @{k}")
    print(f"{'='*72}")
    print(f"  {'Sorgu':<42}  {'Dil':3}  {'P':>5}  {'R':>5}  {'nDCG':>6}  {'ms':>5}")
    print(f"  {'-'*42}  {'---':3}  {'-----':>5}  {'-----':>5}  {'------':>6}  {'-----':>5}")

    for r in results:
        q = r.query[:40] + ".." if len(r.query) > 42 else r.query
        print(f"  {q:<42}  {r.lang:3}  {r.precision:>5.3f}  {r.recall:>5.3f}  {r.ndcg:>6.3f}  {r.latency_ms:>5.0f}")

    print(f"  {'-'*42}  {'---':3}  {'-----':>5}  {'-----':>5}  {'------':>6}  {'-----':>5}")
    print(f"  {'GENEL ORTALAMA':<42}  {'all':3}  {agg_p:>5.3f}  {agg_r:>5.3f}  {agg_n:>6.3f}  {agg_lat:>5.0f}")

    if en_results:
        ep = sum(r.precision for r in en_results) / len(en_results)
        er = sum(r.recall for r in en_results) / len(en_results)
        en_ = sum(r.ndcg for r in en_results) / len(en_results)
        print(f"  {'  İngilizce ortalama':<42}  {'en ':3}  {ep:>5.3f}  {er:>5.3f}  {en_:>6.3f}")

    if tr_results:
        tp = sum(r.precision for r in tr_results) / len(tr_results)
        tr_ = sum(r.recall for r in tr_results) / len(tr_results)
        tn = sum(r.ndcg for r in tr_results) / len(tr_results)
        print(f"  {'  Türkçe ortalama':<42}  {'tr ':3}  {tp:>5.3f}  {tr_:>5.3f}  {tn:>6.3f}")

    print(f"  MRR@{k}: {agg_m:.3f}")
    print(f"{'='*72}")

    # Hedef karşılaştırması
    targets = {"P": 0.60, "R": 0.70, "nDCG": 0.65, "MRR": 0.60}
    actual = {"P": agg_p, "R": agg_r, "nDCG": agg_n, "MRR": agg_m}
    print("\n  Hedef Karşılaştırması:")
    for name, target in targets.items():
        val = actual[name]
        status = "✅" if val >= target else "❌"
        print(f"    {status}  {name:6} : {val:.3f}  (hedef ≥ {target})")
    print()


def write_retrieval_markdown(results: list[QueryResult], k: int) -> Path:
    out = ROOT / "docs" / "RETRIEVAL_EVALUATION.md"
    agg_p = sum(r.precision for r in results) / len(results)
    agg_r = sum(r.recall for r in results) / len(results)
    agg_n = sum(r.ndcg for r in results) / len(results)
    agg_m = sum(r.mrr for r in results) / len(results)

    lines = [
        "# Retrieval Quality Evaluation",
        "",
        f"**Retriever:** HybridRetriever (Qdrant dense+sparse RRF, FAISS fallback)  ",
        f"**Embedding:** BAAI/bge-m3  ",
        f"**Metrikler:** Precision@{k}, Recall@{k}, nDCG@{k}, MRR@{k}  ",
        f"**Sorgu sayısı:** {len(results)} ({sum(1 for r in results if r.lang=='tr')} TR + {sum(1 for r in results if r.lang=='en')} EN)  ",
        "",
        "## Özet",
        "",
        f"| Metrik | Skor | Hedef | Durum |",
        f"|--------|------|-------|-------|",
        f"| Precision@{k} | {agg_p:.3f} | ≥ 0.60 | {'✅' if agg_p >= 0.60 else '❌'} |",
        f"| Recall@{k}    | {agg_r:.3f} | ≥ 0.70 | {'✅' if agg_r >= 0.70 else '❌'} |",
        f"| nDCG@{k}      | {agg_n:.3f} | ≥ 0.65 | {'✅' if agg_n >= 0.65 else '❌'} |",
        f"| MRR@{k}       | {agg_m:.3f} | ≥ 0.60 | {'✅' if agg_m >= 0.60 else '❌'} |",
        "",
        "## Sorgu Bazlı Sonuçlar",
        "",
        f"| Sorgu | Dil | Topic | P@{k} | R@{k} | nDCG@{k} | ms |",
        f"|-------|-----|-------|-------|-------|---------|-----|",
    ]
    for r in results:
        q = r.query[:50] + ".." if len(r.query) > 52 else r.query
        lines.append(
            f"| {q} | {r.lang} | {r.topic or '—'} "
            f"| {r.precision:.3f} | {r.recall:.3f} | {r.ndcg:.3f} | {r.latency_ms:.0f} |"
        )

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


# =============================================================================
# RAGAS evaluation
# =============================================================================

def run_ragas_evaluation(k: int = 5, output_path: Path | None = None) -> None:
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        )
    except ImportError:
        print("RAGAS kurulu değil: pip install ragas datasets")
        return

    from server.app.core.generation.llm import OllamaClient
    from server.app.core.retrieval.corpus import KnowledgeBase
    from server.app.core.retrieval.embeddings import EmbeddingBackend
    from server.app.core.retrieval.faiss_store import FaissIndexStore
    from server.app.core.retrieval.hybrid_retriever import HybridRetriever

    kb = KnowledgeBase.load()
    embedder = EmbeddingBackend()
    faiss_store = FaissIndexStore(FAISS_INDEX_PATH, FAISS_METADATA_PATH)
    retriever = HybridRetriever(kb, faiss_store, embedder)
    llm = OllamaClient()

    questions, answers, contexts_list, ground_truths = [], [], [], []

    # Sadece ground_truth'u dolu olan sorguları kullan
    ragas_set = [item for item in GOLDEN_SET if item.get("relevant_ids")]

    print(f"[RAGAS] {len(ragas_set)} sorgu çalıştırılıyor...")
    for item in ragas_set:
        query = item["query"]
        retrieved = retriever.retrieve(query, topic=item.get("topic"), k=k)
        context_texts = [sc.chunk.content for sc in retrieved]

        prompt = (
            "Answer the following question based only on the provided context.\n\n"
            f"Context:\n{'---'.join(context_texts[:3])}\n\n"
            f"Question: {query}\nAnswer:"
        )
        result = llm.generate(prompt)
        answer = result.text if result.available else "unavailable"

        questions.append(query)
        answers.append(answer)
        contexts_list.append(context_texts)
        ground_truths.append(" ".join(item.get("relevant_ids", [])))

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": ground_truths,
    })

    print("[RAGAS] Metrikler hesaplanıyor...")
    scores = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )

    print(f"\n{'='*50}")
    print("  RAGAS Sonuçları")
    print(f"{'='*50}")
    targets = {
        "faithfulness": 0.85,
        "answer_relevancy": 0.80,
        "context_precision": 0.80,
        "context_recall": 0.75,
    }
    for metric, target in targets.items():
        val = scores.get(metric, 0.0)
        status = "✅" if val >= target else "❌"
        print(f"  {status}  {metric:<22}: {val:.3f}  (hedef ≥ {target})")
    print(f"{'='*50}\n")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dict(scores), f, indent=2, ensure_ascii=False)
        print(f"Sonuçlar kaydedildi: {output_path}")


# =============================================================================
# Ablasyon yardımcısı
# =============================================================================

def print_ablation_hint() -> None:
    print("""
Ablasyon çalışması için farklı konfigürasyonları test et:

  # Baseline: all-MiniLM-L6-v2, fixed chunking
  EMBEDDING_MODEL=all-MiniLM-L6-v2 RETRIEVAL_BACKEND=faiss \\
    python scripts/evaluate_rag.py --mode retrieval

  # +BGE-M3 dense only
  EMBEDDING_MODEL=BAAI/bge-m3 RETRIEVAL_BACKEND=faiss \\
    python scripts/evaluate_rag.py --mode retrieval

  # +Qdrant hybrid (dense+sparse)
  EMBEDDING_MODEL=BAAI/bge-m3 RETRIEVAL_BACKEND=qdrant \\
    python scripts/evaluate_rag.py --mode retrieval

  # Full system (Qdrant + reranker)
  EMBEDDING_MODEL=BAAI/bge-m3 RETRIEVAL_BACKEND=qdrant \\
  ENABLE_RERANKER=true \\
    python scripts/evaluate_rag.py --mode all
""")


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calma RAG Evaluation")
    parser.add_argument("--mode", choices=["retrieval", "ragas", "all"], default="retrieval")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--ablation-hint", action="store_true")
    args = parser.parse_args()

    if args.ablation_hint:
        print_ablation_hint()
        sys.exit(0)

    if args.mode in ("retrieval", "all"):
        results = run_retrieval_evaluation(k=args.k)
        print_retrieval_report(results, k=args.k)
        md_path = write_retrieval_markdown(results, k=args.k)
        print(f"  Markdown raporu: {md_path}")

    if args.mode in ("ragas", "all"):
        output = args.output or ROOT / "reports" / "eval" / "ragas_results.json"
        run_ragas_evaluation(k=args.k, output_path=output)
```

**Çalıştırma:**

```bash
# Sadece retrieval metrikleri (hızlı, Ollama gerekmez)
python scripts/evaluate_rag.py --mode retrieval

# RAGAS ile tam değerlendirme (Ollama çalışıyor olmalı)
python scripts/evaluate_rag.py --mode ragas

# İkisi birden
python scripts/evaluate_rag.py --mode all --k 5

# Ablasyon komutu ipuçları
python scripts/evaluate_rag.py --ablation-hint
```

### 6.3 Ablasyon Çalışması Tasarımı

Bitirme projesi için minimum 3 karşılaştırma gerekli:

| Deney | Embedding | Chunking | Reranker | Contextual |
|---|---|---|---|---|
| Baseline | all-MiniLM-L6-v2 | Fixed-512 | Yok | Yok |
| +BGE-M3 | BGE-M3 | Fixed-512 | Yok | Yok |
| +Section chunking | BGE-M3 | Section-aware | Yok | Yok |
| +Reranker | BGE-M3 | Section-aware | bge-reranker | Yok |
| **Full system** | BGE-M3 | Section-aware | bge-reranker | Contextual prefix |

Her deney için nDCG@5, Precision@5 kayıt edilir. Tablonun her satırı bir thesis bölümü.

### 6.4 RAGAS Entegrasyonu

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

# Her test sorgusu için:
# dataset = {"question": ..., "answer": ..., "contexts": [...], "ground_truth": ...}
result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision])
```

---

## Bölüm 7 — Uygulama Sırası (Özet)

```
GÜN 1-2   PHASE 0  : Ollama → qwen2.5:14b + Modelfile, paket kurulumu
GÜN 3-4   PHASE 1  : embeddings.py → BGE-M3 (dense + sparse)
                      config.py → yeni env değerleri
GÜN 5-6   PHASE 2  : qdrant_store.py → dense+sparse named vectors, hybrid_search
                      hybrid_retriever.py → Qdrant primary + RRF fallback
GÜN 7     PHASE 3  : reranker.py → NeuralReranker (bge-reranker-v2-m3)
GÜN 8-9   PHASE 4  : chunker.py → SectionAwareChunker + RecursiveCharacterTextSplitter
GÜN 10    PHASE 6  : llm.py → num_ctx=32768, timeout=120s
GÜN 11-12 PHASE 7  : build_and_ingest.py çalıştır
                      → python scripts/build_and_ingest.py --pdf-dir data/raw
                      → ~2.800-3.200 chunk Qdrant'a yüklenir
GÜN 13    PHASE 8  : build_index.py çalıştır (FAISS fallback için)
                      → python scripts/build_index.py --backend faiss
GÜN 14    Doğrulama: evaluate_rag.py --mode retrieval
                      → ilk gerçek metrikler
GÜN 15-16 PHASE 5  : contextual_prefix.py (opsiyonel)
                      → --contextual-prefix-local veya --contextual-prefix-claude
GÜN 17+   Evaluation: evaluate_rag.py --mode all
                       Ablation çalışması (5 konfigürasyon × 4 metrik)
```

**Kritik bağımlılıklar:**
- PHASE 2 tamamlanmadan PHASE 7 çalıştırılmamalı (qdrant_store API uyumu)
- PHASE 4 tamamlanmadan PHASE 7 çalıştırılmamalı (chunker düzgün split etmeli)
- PHASE 7 tamamlanmadan evaluate_rag.py anlamlı sonuç vermez
- PHASE 5 tamamen bağımsız — istenen noktada eklenir

---

## Bölüm 8 — RAM Bütçesi (M4 Pro 24 GB)

| Bileşen | RAM |
|---|---|
| macOS + sistem | ~4.0 GB |
| Ollama `qwen2.5:14b` (Q4_K_M) | ~9.5 GB |
| BGE-M3 dense (sentence-transformers) | ~1.5 GB |
| BGE-M3 sparse (FlagEmbedding) | ~1.5 GB (paylaşımlı checkpoint) |
| bge-reranker-v2-m3 | ~1.1 GB |
| Qdrant container | ~0.3 GB |
| FastAPI backend + overhead | ~0.4 GB |
| **Toplam** | **~18.3 GB** |
| **Kalan headroom** | **~5.7 GB** |

Güvenli. Paralel ingestion sırasında spike olsa da 24 GB sınırını aşmaz.

---

## Kaynaklar

| Kaynak | Link |
|---|---|
| Qwen2.5 Technical Report (TurkishMMLU) | https://arxiv.org/pdf/2412.15115 |
| TR-MMLU Benchmark | https://arxiv.org/html/2501.00593v2 |
| CETVEL Turkish Benchmark (2025) | https://arxiv.org/abs/2508.16431 |
| BGE-M3 Paper (arXiv:2402.03216) | https://huggingface.co/BAAI/bge-m3 |
| Anthropic Contextual Retrieval | https://www.anthropic.com/news/contextual-retrieval |
| BGE-M3 + Qdrant Hybrid Search | https://github.com/yuniko-software/bge-m3-qdrant-sample |
| Qdrant Hybrid Queries (RRF) | https://qdrant.tech/documentation/search/hybrid-queries/ |
| Qdrant Sparse Vectors | https://qdrant.tech/articles/sparse-vectors/ |
| MDPI Bioengineering Chunking 2025 | https://www.mdpi.com/2673-2688/6/9/226 |
| bge-reranker-v2-m3 | https://huggingface.co/BAAI/bge-reranker-v2-m3 |
| RAGAS | https://docs.ragas.io |
| TR-MTEB (EMNLP 2025) | https://aclanthology.org/2025.findings-emnlp.471/ |
| Trustworthy AI Psychotherapy | https://arxiv.org/html/2508.11398v1 |

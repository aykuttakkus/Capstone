# RAG Pipeline 2025 — Araştırma, Analiz ve Uygulama Planı

> **Tarih:** Mayıs 2025  
> **Kapsam:** Mevcut sistemin 2024-2025 literatürüyle karşılaştırması ve geliştirilmiş mimari planı  
> **Hedef:** 139 PDF, Türkçe + İngilizce, psikoloji / mental health alanı

---

## 1. Mevcut Sistemin Gerçek Durumu

### 1.1 Kritik Hatalar (Blocker)

| Sorun | Detay | Etki |
|---|---|---|
| **FAISS index 384 dim, model 1024 dim** | `faiss_metadata.json` → `"dimension": 384`; `embeddings.py` → `multilingual-e5-large` (1024 dim) | Tüm retrieval kırık — query vektörü index'e çarpmıyor |
| **54 chunk, tamamı sample data** | `stress-001`, `anxiety-001` — elle yazılmış; gerçek PDF içeriği indexlenmemiş | Sistem gerçek bilgi döndürmüyor |
| **139 PDF hiç indexlenmemiş** | `data/raw/` doluyor ama pipeline çalıştırılmamış | Knowledge base boş |

### 1.2 Mimari Eksikler

| Bileşen | Mevcut Durum | Sorun |
|---|---|---|
| **Chunker** | `MarkdownHeaderTextSplitter` (header-based) | Token limiti yok; 35MB textbook tek chunk olabilir |
| **Embedding** | `multilingual-e5-large` (1024 dim) | Çalışıyor ama index 384 dim — model hiç kullanılmıyor |
| **Hybrid retrieval** | `0.70 * semantic + 0.30 * keyword` (weighted sum) | RRF yok; normalizasyon sorunlu |
| **Reranker** | Custom keyword overlap + topic alignment | Neural değil; out-of-domain generalisation zayıf |
| **Contextual prefix** | Yok | Her chunk bağlamdan kopuk embed ediliyor |
| **BM25** | Yok (TF-IDF benzeri custom) | Gerçek lexical retrieval eksik |

---

## 2. 2024-2025 Literatür Bulguları

### 2.1 Chunking Stratejileri

#### Late Chunking — JinaAI (Eylül 2024)
**Paper:** arXiv:2409.04701

Geleneksel RAG: `chunk → embed` (her chunk bağımsız embed edilir).  
Late Chunking: `full document encode → chunk the token representations`

```
Geleneksel:  [chunk1] → embed → v1
             [chunk2] → embed → v2   ← "the city" ne demek bilmiyor

Late:        [full document] → encode → [t1, t2, ..., tN]
             mean-pool(t1..t50) → v1
             mean-pool(t51..t100) → v2  ← "the city" = Berlin biliyor
```

**Benchmark (BEIR nDCG@10):**

| Dataset | Naive Chunking | Late Chunking | Delta |
|---|---|---|---|
| SciFact | 64.20% | 66.10% | +1.90% |
| NFCorpus (medical) | 23.46% | 29.98% | **+6.52%** |

**Bizim sistemimize etkisi:** Uzun akademik makalelerde (özellikle büyük textbook'lar) kazanç büyük. Jina-embeddings-v3 (8192 token context) gerektirir.

**Sınır:** 512-token model (mE5-large) ile çalışmaz — uzun context embedding modeli zorunlu.

---

#### Contextual Retrieval — Anthropic (Eylül 2024)

Her chunk embed edilmeden önce LLM (Claude Haiku) ile 50-100 token context üretilir ve chunk'a prepend edilir.

**Prompt:**
```
<document>{WHOLE_DOCUMENT}</document>
Aşağıdaki chunk'ı doküman içinde konumlandırmak için kısa bir bağlam yaz:
<chunk>{CHUNK_CONTENT}</chunk>
Sadece kısa bağlamı yaz, başka bir şey ekleme.
```

**Sonuç:**

| Yaklaşım | Failure Rate | Azalma |
|---|---|---|
| Baseline | 5.7% | — |
| Contextual Embeddings | 3.7% | **-35%** |
| Contextual Embeddings + BM25 | 2.9% | **-49%** |
| Contextual Embeddings + BM25 + Reranker | 1.9% | **-67%** |

**Maliyet:** Claude Haiku + prompt caching ile 139 PDF için ~$0.50-2.00 (bir kez). Prompt caching ile tekrar eden doküman okuma %90 ucuzlar.

---

#### RAPTOR — ICLR 2024 (arXiv:2401.18059)

Chunk'ları recursive olarak özetleyerek hiyerarşik bir ağaç oluşturur:

```
Leaf nodes: orijinal chunk'lar (512 token)
    ↓ GMM clustering + LLM summarization
Parent nodes: cluster özetleri (200-400 token)
    ↓ tekrar cluster + summarize
Root node: doküman özeti
```

**Neden önemli:** "Depresyonun genel tedavi yaklaşımları nelerdir?" gibi holistic sorular leaf node'lardan değil, parent/root node'lardan cevaplanır. QuALITY benchmark: +20% absolute accuracy GPT-4 ile.

**Bizim sistemimiz için:** Büyük textbook'lar (Introduction to Psychology, 35MB) için güçlü. Uygulaması karmaşık ama yüksek değer.

---

#### HyDE + HyPE (2025)

**HyDE:** Kullanıcı sorgusu için LLM ile 5 "hypothetical document" üretilir, embed edilir, ortalaması alınır, bu vektörle search yapılır.

```
Query: "Sosyal izolasyon depresyonu nasıl etkiler?"
    ↓ LLM
Hypothetical doc: "Sosyal izolasyon, kortizol seviyelerini artırarak..."
    ↓ embed
Averaged vector → similarity search
```

**HyPE:** HyDE'nin tersi — indexleme sırasında her chunk için hypothetical queries üretilir. Recall +45 puan artış gözlemlenmiş.

**Sınır:** Medical/psikoloji alanında hallucination riski var. Dikkatli uygulanmalı.

---

#### Semantic Chunking Benchmark Özeti (2024-2025)

| Strateji | Accuracy | Compute | Not |
|---|---|---|---|
| Fixed-size (512 tok, 0 overlap) | Baseline | Düşük | Cümle kesiyor |
| Sliding window (512 tok, 80-200 overlap) | +5-8% | Düşük | Pratik best default |
| Semantic (embedding-based breakpoint) | +7-9% | 3-5× | Her cümleyi embed ediyor |
| Section-aware + 512 tok sliding | En iyi (clinical) | Orta | Bizim için ideal |
| Page-level | NVIDIA: 0.648 acc | Çok düşük | Yapılandırılmış PDF'lerde |
| Adaptive topic-boundary | +74% vs fixed | Yüksek | MDPI Bioengineering 2025 |

**Kritik bulgu:** Embedding model kalitesi, chunking stratejisinin etkisinden daha büyük. Kötü model + iyi chunking < iyi model + orta chunking.

---

### 2.2 Embedding Modelleri (Haziran 2025)

#### Karşılaştırma Tablosu

| Model | MTEB Multi | TR Desteği | Context | Dim | Mod | Lisans |
|---|---|---|---|---|---|---|
| **Qwen3-Embedding-8B** | **70.58 (#1)** | 100+ dil | 32,768 | 4096 | Dense | Apache 2.0 |
| Qwen3-Embedding-0.6B | ~65+ | 100+ dil | 32,768 | 1024 | Dense | Apache 2.0 |
| **BGE-M3** | ~63.0 | 100+ dil | 8,192 | 1024 | Dense+Sparse+ColBERT | MIT |
| multilingual-e5-large | ~70-73* | 100+ dil | **512** | 1024 | Dense | MIT |
| jina-embeddings-v3 | ~65 | 89+ dil | 8,192 | 1024 | Dense | CC BY-NC 4.0 |

*mE5-large MTEB klasik benchmark'ta güçlü ama 512 token limiti uzun akademik metin için ciddi handikap.

#### Türkçe için TR-MTEB (EMNLP 2025) Bulguları

- Multilingual E5 modelleri (large varyantı) monolingual Türkçe modellerden **genel olarak üstün**
- BGE-M3, Turkish MIRACL benchmark'ta rekabetçi
- Qwen3-Embedding için henüz TR-MTEB spesifik sonuç yayınlanmamış — ama genel üstünlüğü güçlü sinyal
- **TurkEmbed (2025, arXiv:2511.08376):** Semantic similarity'de güçlü ama retrieval'da multilingual modellerin gerisinde

#### Bizim Sistem İçin Öneri

**Birincil öneri: BGE-M3**
- Dense + Sparse (SPLADE-style) + ColBERT üçü tek modelde
- 8192 token context (mE5-large'ın 512'sinin 16×'i)
- Proven production stability (2024'ten beri yaygın kullanım)
- Hybrid retrieval için ayrı BM25 indeks kurmadan sparse mode kullanılabilir

**Alternatif (daha güçlü): Qwen3-Embedding-0.6B**
- MTEB'de BGE-M3'ü geçiyor
- 32K token context (Late Chunking için ideal)
- Daha az production maturitesi — Haziran 2025'te çıktı

**Önerilmeyen: multilingual-e5-large (mevcut)**
- 512 token limiti akademik makaleler için kritik sorun
- Zaten index 384 dim ile build edilmiş — fiilen kullanılmıyor

---

### 2.3 Hybrid Retrieval: RRF vs. Weighted Sum

#### RRF (Reciprocal Rank Fusion)

```
RRF_score(d) = Σ_i  1 / (k + rank_i(d))    (k=60 standard)
```

**Avantaj:** Parameter-free, normalizasyon gerektirmez, scale farkına immune.  
**Dezavantaj:** Score magnitude bilgisini kaybeder.

#### Weighted Combination (Mevcut Sistem)

```python
combined = 0.70 * semantic + 0.30 * keyword
```

**Bruch et al. (2022):** Doğru normalize edilip tune edildiğinde weighted combination RRF'yi geçiyor.  
**Sorun:** Mevcut kodda min-max normalizasyon yok — BM25 ve cosine farklı scale'da toplanıyor.

#### Öneri

Etiketli veri yok → **RRF kullan** (robust, parameter-free).  
Etiketli sorgu-doküman çifti oluşturulduktan sonra → weighted combination'a geç.

---

### 2.4 Reranking (2025 Karşılaştırması)

| Reranker | MTEB-R | Context | Multilingual | RAM | Öneri |
|---|---|---|---|---|---|
| **Qwen3-Reranker-8B** | **69.76** | 32K | 100+ | ~16GB | SOTA, resource gerektirir |
| MixedBread mxbai-rerank-v2 | 57.49 | — | Güçlü | ~3GB | İyi alternatif |
| **BGE-reranker-v2-m3** | 57.03 | 8192 | 100+ | ~1.1GB | **Bizim için pratik seçim** |
| FlashRank MiniLM-L-12 | 55.43 | 512 | Sınırlı | ~120MB | Resource-constrained |
| Mevcut custom reranker | N/A | — | Yok | 0 | Keyword-only, zayıf |

**Bizim sistem için:** `bge-reranker-v2-m3` — multilingual, BGE-M3 ile uyumlu, makul RAM.

---

### 2.5 Mental Health / Psikoloji RAG — Özel Bulgular

#### arXiv:2508.11398 — Trustworthy AI Psychotherapy (2025)
DSM-5 knowledge base üzerine RAG kullanan sistem:
- Chunk size: **512-1024 token**
- Model: `nomic-embed-text` (biz daha iyisini kullanacağız)
- Section-aware: DSM-5 kriter bölümleri bölünmüyor
- Top-5 retrieval → reranking → response

#### MIND-SAFE Framework (PMC 2025)
- CBT, DBT protokollerini ayrı knowledge base olarak index'e alıyor
- Multi-tier safety controls (RAG üstüne ekleniyor, içine karışmıyor)

#### OnRL-RAG (arXiv:2504.02894)
- Real-time personalization için RAG + online RL
- Stres/anksiyete/depresyon tespiti ayrı bir classification katmanı

#### Kritik Klinik RAG Bulgusu (MDPI Bioengineering 2025)
Adaptive chunking (topic boundary-aware) vs. fixed-size:
- Adaptive: %87 accuracy
- Fixed-size: %13 accuracy
- **Delta: +74 puan** — psikoloji dokümanlarında section boundaries takip etmek hayati

---

## 3. Geliştirilmiş Sistem Mimarisi

### 3.1 Önerilen Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INGESTION PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  data/raw/*.pdf                                                     │
│       │                                                             │
│       ▼                                                             │
│  [1] PDF PARSER                                                     │
│      Docling (VisionPdfParser) — tablo, çok sütun, başlık algılama  │
│      Fallback: pypdf (düz metin)                                    │
│       │                                                             │
│       ▼                                                             │
│  [2] SECTION DETECTOR                                               │
│      Abstract → tek chunk (atomik)                                  │
│      Introduction → 512 tok, 80 overlap                             │
│      Methods → 512-768 tok (prosedür bölünmesin)                    │
│      Results → her bulgu paragrafı ayrı                             │
│      Discussion/Conclusion → 512 tok, 80 overlap                   │
│      References → DIŞARIDA BIRAK                                    │
│      Tables → başlık + sütun başlığı + içerik = tek atomik chunk    │
│       │                                                             │
│  [3] QUALITY FILTER                                                 │
│      min 50 token, max 1500 token                                   │
│      References bölümü exclusion                                    │
│      Boya kitabı / düşük bilgi yoğunluğu filtresi                   │
│       │                                                             │
│  [4] CONTEXTUAL PREFIX (Anthropic Contextual Retrieval)             │
│      Claude Haiku ile 50-100 token context üret                     │
│      Chunk'a prepend et                                             │
│      Prompt caching ile maliyet minimize                            │
│       │                                                             │
│  [5] EMBEDDING                                                      │
│      BGE-M3 (dense mode) → 1024 dim vector                          │
│      BGE-M3 (sparse mode) → lexical weights (SPLADE-style)          │
│       │                                                             │
│  [6] INDEX                                                          │
│      FAISS (dense vectors, 1024 dim)                                │
│      BM25 / BGE-M3 sparse index (lexical)                           │
│      Metadata: source, section, topic, page, language, confidence   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         RETRIEVAL PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  User Query (TR/EN)                                                 │
│       │                                                             │
│  [7]  QUERY EXPANSION (opsiyonel — HyDE)                            │
│       LLM ile 1-3 hypothetical document üret                        │
│       Embed et, ortalama al                                         │
│       │                                                             │
│  [8]  PARALLEL RETRIEVAL                                            │
│       Dense retrieval (BGE-M3) → top-50                             │
│       Sparse retrieval (BGE-M3 lexical) → top-50                    │
│       │                                                             │
│  [9]  RRF FUSION                                                    │
│       score(d) = 1/(60+rank_dense) + 1/(60+rank_sparse)             │
│       → top-20 candidates                                           │
│       │                                                             │
│  [10] NEURAL RERANKER                                               │
│       bge-reranker-v2-m3 (cross-encoder)                            │
│       query + chunk → relevance score                               │
│       → top-5 final chunks                                          │
│       │                                                             │
│  [11] EVIDENCE GATE (mevcut kod korunur)                            │
│       Güven skoru < 0.3 → fallback                                  │
│       │                                                             │
│  [12] LLM GENERATION                                                │
│       5 chunk + sistem promptu → response                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 3.2 Mevcut Kodla Delta (Ne Değişiyor, Ne Kalıyor)

| Bileşen | Mevcut | Yeni | Değişim |
|---|---|---|---|
| `parser.py` | Docling VisionPdfParser | ✅ Kalıyor | — |
| `chunker.py` | MarkdownHeaderTextSplitter (token limiti yok) | RecursiveCharacterTextSplitter (512 tok, 80 overlap) + section detection | **Yeniden yaz** |
| `embeddings.py` | multilingual-e5-large, 1024 dim | BGE-M3 | **Model değiştir** |
| `faiss_store.py` | 384 dim index (kırık) | 1024 dim, yeniden build | **Index rebuild** |
| `hybrid_retriever.py` | 0.70 sem + 0.30 kw (weighted sum) | RRF (dense + sparse) | **Retrieval logic değiştir** |
| `reranker.py` | Custom keyword-based | bge-reranker-v2-m3 (neural) | **Yeniden yaz** |
| `pdf_ingestion.py` | Pipeline var ama çalıştırılmamış | Contextual prefix eklenir | **Genişlet** |
| BM25 | Yok (custom TF-IDF) | BGE-M3 sparse mode veya rank_bm25 | **Ekle** |
| Contextual prefix | Yok | LLM context generation (Haiku) | **Yeni bileşen** |

---

## 4. Chunk Tahminleri (Güncel)

### 4.1 PDF Sınıflandırması (Ana Dizin: 139 PDF)

| Tür | Adet (tahmini) | Avg Token | Chunks/PDF | Toplam |
|---|---|---|---|---|
| Büyük textbook'lar (>10MB) | ~8 | ~120,000 | ~200 | ~1,600 |
| Orta akademik makaleler (1-10MB) | ~60 | ~12,000 | ~22 | ~1,320 |
| Küçük handout'lar (<1MB) | ~71 | ~3,500 | ~6 | ~426 |
| Toplam ham | | | | ~3,346 |
| Quality filter sonrası (-%15) | | | | **~2,800-3,200** |

### 4.2 Sorunlu Dosyalar (Manuel Karar Gerekli)

| Dosya | Sorun | Öneri |
|---|---|---|
| `Full.pdf` (18MB) | İsimsiz, içerik belirsiz | İçeriği kontrol et, etiketle |
| `ABUIABA9GAAgpLuMvQYol634mgQ.pdf` | Hash isimli | İçeriği kontrol et veya dışarıda bırak |
| `stand-up-to-stress-coloring-activity-book.pdf` | Boyama kitabı | **Dışarıda bırak** |
| `THEDIA1.pdf` | İçerik bilinmiyor | Kontrol et |
| DOI isimli Türkçe paper'lar (`10.xxxx.pdf`) | İsimden topic çıkarılamıyor | LLM classifier ile topic ata |

---

## 5. Uygulama Planı (Öncelik Sırası)

### Faz 1 — Blocker Fix (1-2 gün)

**1.1 Embedding modeli değiştir + index rebuild**
```python
# embeddings.py
_DEFAULT_MODEL = "BAAI/bge-m3"

# EmbeddingBackend.dimension = 1024 (zaten doğru, sadece model değişiyor)
```

**1.2 Sample chunk'ları temizle**
```python
# faiss_metadata.json ve data/store/faiss.index sıfırla
# psych_rag.db'deki sample data temizle
```

---

### Faz 2 — Chunker Yeniden Yazımı (1-2 gün)

**2.1 `ingestion/chunker.py` → RecursiveCharacterTextSplitter**

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

SECTION_CHUNK_CONFIG = {
    "abstract":     {"chunk_size": 400,  "overlap": 0},   # atomik
    "introduction": {"chunk_size": 512,  "overlap": 80},
    "methods":      {"chunk_size": 768,  "overlap": 100},  # prosedür bölünmesin
    "results":      {"chunk_size": 512,  "overlap": 80},
    "discussion":   {"chunk_size": 512,  "overlap": 80},
    "conclusion":   {"chunk_size": 400,  "overlap": 0},   # atomik
    "default":      {"chunk_size": 512,  "overlap": 80},
}

EXCLUDED_SECTIONS = {"references", "bibliography", "kaynakça", "kaynaklar"}
```

**2.2 Section detection logic**

```python
SECTION_PATTERNS = {
    "abstract":     r"^#+\s*(abstract|özet)",
    "introduction": r"^#+\s*(introduction|giriş|1\.|1\s+introduction)",
    "methods":      r"^#+\s*(method|yöntem|materials?|procedure)",
    "results":      r"^#+\s*(result|bulgular|findings?|sonuç)",
    "discussion":   r"^#+\s*(discussion|tartışma)",
    "conclusion":   r"^#+\s*(conclusion|sonuç|implications?)",
    "references":   r"^#+\s*(references?|bibliography|kaynakça)",
}
```

---

### Faz 3 — Contextual Prefix (1 gün)

**3.1 `ingestion/contextual_prefix.py` — Yeni bileşen**

```python
CONTEXT_PROMPT = """\
<document>{document_title}: {document_abstract_or_intro}</document>

Aşağıdaki chunk'ı bu doküman içinde konumlandırmak için 2-3 cümlelik Türkçe veya İngilizce (chunk diliyle aynı) bir bağlam yaz:
<chunk>{chunk_content}</chunk>

Sadece bağlamı yaz, başka açıklama ekleme."""

def generate_context(chunk: str, doc_title: str, doc_intro: str) -> str:
    # Claude Haiku ile çağrı
    # Prompt caching ile maliyet optimize et
    ...
```

**Maliyet tahmini:**
- 2,800 chunk × avg 800 input token = ~2.24M token
- Claude Haiku: $0.25/1M token (cache miss), $0.03/1M (cache hit)
- Doküman başına ilk cache miss, sonraki chunk'lar cache hit
- Tahmini toplam: **~$0.80-2.50** (tek seferlik)

---

### Faz 4 — Hybrid Retrieval: RRF (1 gün)

**4.1 `hybrid_retriever.py` → RRF**

```python
def reciprocal_rank_fusion(
    dense_results: list[tuple[str, float]],
    sparse_results: list[tuple[str, float]],
    k: int = 60,
) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for rank, (chunk_id, _) in enumerate(dense_results):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
    for rank, (chunk_id, _) in enumerate(sparse_results):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**4.2 BGE-M3 sparse mode entegrasyonu**

BGE-M3, `encode` ile hem dense hem sparse vector üretiyor:

```python
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
output = model.encode(texts, return_dense=True, return_sparse=True)
dense_vectors = output['dense_vecs']    # 1024 dim
sparse_vectors = output['lexical_weights']  # dict: token_id → weight
```

---

### Faz 5 — Neural Reranker (1 gün)

**5.1 `reranker.py` → bge-reranker-v2-m3**

```python
from FlagEmbedding import FlagReranker

class NeuralReranker:
    def __init__(self) -> None:
        self.model = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)
    
    def rerank(self, query: str, chunks: list[ScoredChunk], top_k: int = 5) -> list[ScoredChunk]:
        pairs = [(query, chunk.chunk.content[:1000]) for chunk in chunks]
        scores = self.model.compute_score(pairs, normalize=True)
        for chunk, score in zip(chunks, scores):
            chunk.score = float(score)
        return sorted(chunks, key=lambda x: x.score, reverse=True)[:top_k]
```

---

### Faz 6 — Full Pipeline Run (1-2 gün)

```bash
# 1. Index temizle
rm data/store/faiss.index data/store/faiss_metadata.json

# 2. Tüm PDF'leri işle
python scripts/build_chunks.py \
  --pdf-dir data/raw \
  --output data/processed/corpus.json \
  --with-contextual-prefix \
  --chunk-size 512 \
  --overlap 80

# 3. Index build
python scripts/build_index.py \
  --corpus data/processed/corpus.json \
  --model BAAI/bge-m3 \
  --output data/store/

# 4. Doğrulama
python scripts/eval_retrieval.py --queries data/eval/test_queries.json
```

---

## 6. Opsiyonel İyileştirmeler (Sonraki Faz)

### 6.1 RAPTOR — Hierarchical Retrieval

Büyük textbook'lar (35MB Introduction to Psychology) için:
- Leaf chunks → cluster → LLM summarize → parent node
- "Psikoloji tarihinde önemli akımlar nelerdir?" → root/parent node'dan cevap
- **Uygulama:** GitHub `parthsarthi03/raptor` — mevcut pipeline'a eklenebilir

### 6.2 HyDE — Query Expansion

```python
def expand_query_with_hyde(query: str, llm_client) -> list[float]:
    hypothesis = llm_client.generate(f"Bu soruyu cevaplayan bir paragraf yaz: {query}")
    hyp_embedding = embed(hypothesis)
    query_embedding = embed(query)
    return average([query_embedding, hyp_embedding])
```

**Dikkat:** Mental health alanında hallucinated hypothesis risk — sadece factual sorgular için.

### 6.3 Late Chunking (Jina)

`jina-embeddings-v3` (8192 token) ile tam doküman encode:
- mE5-large veya BGE-M3'ün yerini alır (context-aware chunk embeddings)
- Özellikle uzun dokümanlar için kazanç büyük
- CC BY-NC 4.0 lisans (ticari kullanım kısıtlı — akademik proje için uygun)

### 6.4 Qwen3-Embedding-0.6B

Haziran 2025'te çıktı, MTEB Multi #1. BGE-M3'ten belirgin üstün:
- 32K token context
- Production maturity henüz düşük
- 3-6 ay sonra geçiş düşünülebilir

---

## 7. Kaçınılması Gerekenler

| Yaklaşım | Neden Kaçın |
|---|---|
| `mxbai-embed-large` | Sadece İngilizce — Türkçe için ~random |
| `nomic-embed-text` | Sadece İngilizce |
| Page-level chunking (PyMuPDF default) | 35MB textbook'ta 200+ sayfalık chunk'lar |
| SPLADE standalone | MS MARCO'da train edilmiş — psikoloji out-of-domain, BM25'ten kötü olabilir |
| HyDE for clinical queries | Hallucination → yanlış terminoloji → retrieval hatası |
| Boyama kitabı indexleme | Gürültü artırır, precision düşürür |

---

## 8. Başarı Metrikleri

| Metrik | Mevcut | Hedef | Nasıl Ölç |
|---|---|---|---|
| Chunk sayısı | 54 (sample) | 2,800-3,200 | `len(corpus)` |
| Index dimension | 384 (kırık) | 1024 | `faiss_metadata["dimension"]` |
| Retrieval MRR@10 | N/A (kırık) | > 0.65 | RAGAS veya custom eval set |
| Top-5 precision | N/A | > 0.60 | Manuel annotation (20-30 sorgu) |
| Türkçe soru → TR paper retrieval | 0% | > 50% | Türkçe test sorguları |
| Context relevance (RAGAS) | N/A | > 0.70 | `ragas.evaluate()` |

---

## Kaynaklar

| Kaynak | Link |
|---|---|
| JinaAI Late Chunking (arXiv:2409.04701) | https://arxiv.org/pdf/2409.04701 |
| Anthropic Contextual Retrieval | https://www.anthropic.com/news/contextual-retrieval |
| RAPTOR (arXiv:2401.18059) | https://arxiv.org/abs/2401.18059 |
| BGE-M3 (arXiv:2402.03216) | https://huggingface.co/BAAI/bge-m3 |
| Qwen3-Embedding Blog | https://qwenlm.github.io/blog/qwen3-embedding/ |
| TR-MTEB (EMNLP 2025) | https://aclanthology.org/2025.findings-emnlp.471/ |
| TurkEmbed (arXiv:2511.08376) | https://arxiv.org/pdf/2511.08376 |
| Trustworthy AI Psychotherapy (arXiv:2508.11398) | https://arxiv.org/html/2508.11398v1 |
| OnRL-RAG Mental Health (arXiv:2504.02894) | https://arxiv.org/html/2504.02894v2 |
| Max-Min Semantic Chunking (Springer 2025) | https://link.springer.com/article/10.1007/s10791-025-09638-7 |
| SPLADE (Qdrant Article) | https://qdrant.tech/articles/modern-sparse-neural-retrieval/ |
| Analytics Vidhya Reranker Comparison 2025 | https://www.analyticsvidhya.com/blog/2025/06/top-rerankers-for-rag/ |
| Adaptive Chunking MDPI Bioengineering 2025 | https://www.mdpi.com/2673-2688/6/9/226 |
| Agentic RAG Survey (arXiv:2501.09136) | https://arxiv.org/abs/2501.09136 |

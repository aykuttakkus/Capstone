# RAG Ingestion Implementation Plan

Bu dokuman, mevcut psikoloji odakli RAG sistemine `server/app/core/retrieval/ingestion` katmanini nasil ekleyecegimizi adim adim tarif eder.
Hedef, retrieval kalitesini artirmak, PDF yapisini daha iyi korumak, topic hizasini guclendirmek ve safety riskini dusurmektir.

## 1. Mevcut Durum

1. Su anki pipeline `server/app/services/pdf_pipeline.py` ve `server/app/core/retrieval/pdf_ingestion.py` uzerinden calisiyor.
2. PDF'ler `pypdf` ile sayfa bazinda duz metne cevriliyor.
3. `server/app/core/retrieval/ingestion` klasoru var ama runtime akisinda kullanilmiyor.
4. `AssistantService` retrieval icin `HybridRetriever`, `EvidenceGate`, `RetrievalGrader` ve `AnswerGenerator` kullaniyor.
5. Topic sistemi `server/app/services/flows/topics.py` tarafinda tanimli.

## 2. Hedef Mimari

1. PDF ingestion offline calisacak.
2. PDF once layout-aware parser ile markdown'a cevrilecek.
3. Markdown semantic chunking ile bolunecek.
4. Chunk'lar topic ve metadata ile zenginlestirilecek.
5. Uretilen corpus versioned olarak saklanacak.
6. Index her corpus versiyonuna bagli olacak.
7. Query time tarafinda hybrid retrieval, rerank ve evidence gate calisacak.
8. Safety routing retrieval'dan once korunacak.

## 3. Hedef Dosya Haritasi

| Dosya | Rol |
|---|---|
| `server/app/core/retrieval/ingestion/parser.py` | PDF -> markdown parser |
| `server/app/core/retrieval/ingestion/chunker.py` | markdown -> semantic chunking |
| `server/app/core/retrieval/ingestion/classifier.py` | chunk metadata topic siniflandirma |
| `server/app/services/pdf_pipeline.py` | ingestion orkestrasyonu |
| `server/app/core/retrieval/pdf_ingestion.py` | legacy helper olarak tutulabilir veya normalize edilir |
| `server/app/core/retrieval/corpus.py` | processed corpus okuma ve version support |
| `server/app/core/retrieval/faiss_store.py` | yeni corpus versiyonuna gore index |
| `server/app/core/retrieval/hybrid_retriever.py` | retrieval fusion |
| `server/app/core/retrieval/evidence_gate.py` | evidence threshold |
| `server/app/core/agents/retrieval_grader.py` | rerank/CRAG katmani |
| `server/app/services/assistant.py` | yeni corpus ve index ile servis akisinin baglanmasi |
| `server/app/services/retrieval_debug.py` | kaynak aciklamalari ve audit |
| `server/app/services/flows/topics.py` | topic hizalama |
| `scripts/ingest_pdfs.py` | ingestion job entrypoint |
| `scripts/build_index.py` | index rebuild entrypoint |
| `scripts/evaluate_retrieval.py` | retrieval kalite olcumu |
| `tests/unit/*` | ingestion, retrieval ve versioning testleri |

## 4. Uygulama Plani

### 4.1 Baseline ve Guvenli Bosluk Analizi

1. `scripts/evaluate_retrieval.py` ile mevcut retrieval skorlarini baseline olarak kaydet.
2. `tests/unit/test_phase4_retrieval_quality.py` ve `tests/unit/test_rag.py` ile su anki davranisi sabitle.
3. Corpus'ta hangi PDF'lerin iyi, hangilerinin bozuk ciktigi kisa bir sample list ile not al.
4. Bu asamada runtime davranisini degistirme.

### 4.2 Ingestion Katmanini Aktif Etme

1. `VisionPdfParser` kullanarak PDF'i markdown'a cevir.
2. `SemanticChunker` ile markdown'u bolum bazli chunk'lara ayir.
3. `LlmMetadataClassifier` kullanmadan once topic taxonomisini `server/app/services/flows/topics.py` ile birebir hizala.
4. Ilk asamada classifier'i optional yap; topic mapping stabil degilse rule-based metadata ile basla.
5. `server/app/services/pdf_pipeline.py` icinde yeni akisi kur: parse -> chunk -> metadata -> corpus record.
6. Her ingestion calismasinda version uretilsin ve hem inventory hem corpus versioned dosyalara yazilsin.

### 4.3 Corpus ve Versioning

1. Processed corpus icin tek kaynak belirle: versioned JSON veya manifest.
2. `KnowledgeBase.load()` processed corpus varsa onu oncelikli okusun.
3. `AssistantService` baslangicta current corpus ile index uyumunu kontrol etsin.
4. Corpus degistiyse FAISS metadata ile corpus version mismatch yakalansin ve index rebuild tetiklensin.
5. `scripts/ingest_pdfs.py` ingestion sonucunu insan okuyabilir rapora cevirsin.

### 4.4 Retrieval Katmani

1. `HybridRetriever` dense similarity + mevcut keyword retriever fusion modelini korusun.
2. Eger ileride gerekli olursa keyword layer BM25 ile degistirilsin.
3. `RetrievalGrader` ilk etapta CRAG filtre olarak kalsin.
4. `EvidenceGate` topic alignment ve minimum score ile son kontrol noktasi olsun.
5. `retrieval_debug.py` sonucunda source reason tags daha acik hale getirilsin.

### 4.5 Safety ve Topic Hizalama

1. `Orchestrator` ve `RequestRouter` ayni topic taxonomy kullanmaya devam etsin.
2. Ingestion classifier topic'leri ile user query topic'leri farkliysa mapping tablosu ekle.
3. Crisis, off-domain ve prompt-injection yolları retrieval'dan once bloke edilsin.
4. Mental health use case nedeniyle, source kalitesi dusukse cevap uretmek yerine kibar abstention tercih edilsin.

### 4.6 Index Build ve Runtime Senkronizasyonu

1. `scripts/build_index.py` processed corpus uzerinden calissin.
2. FAISS metadata dosyasina corpus version yazilsin.
3. App startup sirasinda index ile corpus version karsilastirilsin.
4. Uyuşmazlik varsa servis degrade modda calismasin; rebuild ihtiyaci net gorunsun.

### 4.7 Değerlendirme ve Test

1. `tests/unit/test_pdf_ingestion.py` ingestion metadata davranisini kontrol etsin.
2. `tests/unit/test_phase3_pdf_pipeline.py` versioned corpus yazimini dogrulasin.
3. `tests/unit/test_zero_cost_phase2_corpus_versioning.py` deterministik version testi olarak kalsin.
4. `tests/unit/test_index_store.py` yeni corpus ile index search calistirsin.
5. `tests/unit/test_phase4_retrieval_quality.py` topic alignment ve retrieval sirasini korusun.
6. Retrieval kalite metrikleri: Precision@5, Recall@5, nDCG@5.
7. Acceptance hedefi: query coverage artisi, off-topic retrieval azalisi, evidence gate false positive azalisi.

## 5. Uygulama Sirasi

1. Baseline metrikleri kaydet.
2. Ingestion parser ve chunker'i aktif et.
3. Topic mapping'i sabitle.
4. Processed corpus versioning'i bagla.
5. Index rebuild akisini processed corpus'a gecir.
6. Assistant runtime'da corpus-index uyumunu kontrol et.
7. Retrieval grader ve evidence gate'i test et.
8. Evaluation script ile tekrar olc.
9. Sonucu baseline ile karsilastir.

## 6. Riskler

1. `docling` ve `langchain-text-splitters` gibi bagimliliklar kurulum maliyeti getirir.
2. LLM tabanli metadata classifier topic taxonomy ile uymazsa kaliteyi bozabilir.
3. Ingestion cagrisini request-time'a tasimak latency'yi yukseltebilir.
4. Corpus versioning ile index versioning ayrilmazsa tutarsizlik olur.
5. Mental health domain'i nedeniyle yanlis retrieval, yanlis reassurance riskini artirir.

## 7. Karar Kurallari

1. Yapisal PDF varsa layout-aware parser kullan.
2. Basit ve temiz PDF varsa lightweight extraction yeterli olabilir.
3. Topic taxonomy hizali degilse LLM classifier gecici olarak devre disi birak.
4. Evidence gate dusuk kaliteli retrieval'i engelliyorsa bunu koru.
5. GraphRAG sadece cok dokumanli ve iliski odakli sorular artarsa ekle.

## 8. Definition of Done

1. Ingestion offline calisiyor.
2. Processed corpus versioned yaziliyor.
3. Index processed corpus'a bagli.
4. Hybrid retrieval, rerank ve evidence gate birlikte calisiyor.
5. Safety routing korunuyor.
6. Testler geciyor.
7. Retrieval metrikleri baseline'a gore iyilesme gosteriyor.

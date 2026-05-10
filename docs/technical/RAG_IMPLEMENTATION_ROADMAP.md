# RAG Implementation Roadmap

Bu roadmap, psikoloji odakli RAG sisteminin ingestion, retrieval, safety ve evaluation katmanlarini asamalı olarak guclendirmek icin hazirlanmistir.

## Hedef

1. PDF ingestion kalitesini artirmak.
2. Retrieval isabetini yukselmek.
3. Topic hizasini ve safety kontrolunu guclendirmek.
4. Model cevaplarinin kaynak dayanakli ve tutarli olmasini saglamak.
5. Degisiklikleri olculebilir metriklerle dogrulamak.

## Target System

Bu proje icin nihai hedef akis su sekildedir:

1. PDF kaynaklari offline ingestion job'a girer.
2. Layout-aware parser PDF yapisini koruyarak temiz metin uretir.
3. Semantic chunking ile anlamsal sinirlara gore parcalama yapilir.
4. Metadata extraction ile topic, bolum, kaynak ve kalite etiketleri eklenir.
5. Chunk'lar versioned corpus olarak saklanir.
6. Dense retrieval ve keyword/BM25 retrieval birlikte calisir.
7. Retriever cikisina reranker uygulanir.
8. Evidence gate ve topic gating son karari verir.
9. Cevap generator sadece yeterli kanit varsa yanit uretir.
10. Korpus buyudukce GraphRAG opsiyonel olarak devreye alinir.

## Yol Haritasi

| Phase | Ad | Amaç | Ana Ciktilar | Exit Criteria |
|---|---|---|---|---|
| Phase 0 | Discovery & Baseline | Mevcut performansi sabitlemek | Baseline metrikler, mevcut akisin dokumantasyonu | Retrieval ve cevap kalitesi icin referans skorlar alindi |
| Phase 1 | Layout-Aware Ingestion | PDF yapisini kaybetmeden ingestion yapmak | Docling/LlamaParse benzeri parser, semantic chunking | PDF'ler yapisal sekilde corpus'a giriyor |
| Phase 2 | Metadata & Corpus Versioning | Chunk'lari zenginlestirmek ve versiyonlamak | Topic tags, section tags, corpus manifest | Her chunk izlenebilir ve versioned |
| Phase 3 | Hybrid Retrieval Upgrade | Dense + keyword retrieval'i birlestirmek | Hybrid retriever, BM25/keyword layer | Retrieval coverage ve relevance artiyor |
| Phase 4 | Reranking & Evidence Gate | Ilk adaylari iyilestirmek ve filtrelemek | Reranker, evidence gate, topic gating | Dusus kaliteli kaynaklar eleniyor |
| Phase 5 | Safety & Topic Alignment | Yanlis ya da riskli yanitlari engellemek | Crisis routing, abstention, escalation | Off-topic ve low-evidence cevaplar azaltiliyor |
| Phase 6 | Evaluation Harness | Degisiklikleri olcebilmek | Testler, retrieval eval scripts, audit logs | Her degisiklik sayisal olarak dogrulanabiliyor |
| Phase 7 | Controlled Rollout | Canliya guvenli gecis | Canary release, monitoring, rollback plan | Yeni akis stabil ve izlenebilir sekilde calisiyor |
| Phase 8 | Optional GraphRAG | Buyuyen korpusta iliski tabanli sorgulari guclendirmek | Entity graph, community summary | Graph ihtiyaci olursa pilot olarak devreye aliniyor |

## Phase 0: Discovery & Baseline

### Kapsam

1. Mevcut `pdf_pipeline`, `HybridRetriever`, `EvidenceGate` ve `AssistantService` akislarini belgele.
2. Retrieval kalitesini mevcut veri seti uzerinden olc.
3. Topic taxonomy ile mevcut corpus arasindaki uyumu kontrol et.

### Ciktilar

1. Baseline metrik raporu.
2. Mevcut mimari haritasi.
3. Risk ve bagimlilik listesi.

### Bitis Kriteri

1. Degisiklik oncesi performans sayisal olarak kayit altinda.

## Phase 1: Layout-Aware Ingestion

### Kapsam

1. `Docling` veya `LlamaParse` benzeri layout-aware PDF parser sec.
2. PDF'i bolum, baslik ve alt baslik yapisini koruyacak sekilde parse et.
3. Semantic chunking uygula.
4. Chunk sinirlarini dogal paragraf ve bolum sinirlarina gore ayarla.
5. Offline ingestion job olustur.

### Ciktilar

1. `server/app/core/retrieval/ingestion` aktif kullanimi.
2. Processed corpus icin layout-aware ciktilar.
3. Ingestion testleri.

### Bitis Kriteri

1. Kaynak PDF'den daha temiz, anlamli ve bolum bazli chunk'lar uretiliyor.

## Phase 2: Metadata & Corpus Versioning

### Kapsam

1. Chunk seviyesinde metadata extraction yap.
2. Topic, section, source file ve confidence tag'leri ekle.
3. Corpus manifest standardi belirle.
4. Processed corpus'u versioned olarak sakla.

### Ciktilar

1. Versioned corpus manifest.
2. Zengin metadata'li chunk kayitlari.
3. Corpus-id ve source-id eslesmesi.

### Bitis Kriteri

1. Her chunk izlenebilir ve versiyonlanabilir durumda.

## Phase 3: Hybrid Retrieval Upgrade

### Kapsam

1. Dense retrieval ile keyword retrieval'i birlikte calistir.
2. BM25 veya benzeri keyword layer'i aktif et.
3. Retrieval fusion stratejisini netlestir.
4. Index'i corpus versiyonuna bagla.
5. Startup'ta index-corpus uyum kontrolu yap.

### Ciktilar

1. Versioned corpus manifest.
2. Hybrid retrieval akisi.
3. Uyum kontrol loglari.

### Bitis Kriteri

1. Eski corpus ile yeni index karisiklik yaratmiyor.

## Phase 4: Reranking & Evidence Gate

### Kapsam

1. Retriever'dan gelen ilk adaylari reranker ile yeniden sirala.
2. Reranker icin cross-encoder veya LLM bazli bir strateji sec.
3. Evidence gate ile minimum kaynak kalitesini kontrol et.
4. Topic gating ile query-corpus hizasini dogrula.

### Ciktilar

1. Reranked candidate list.
2. Evidence-based filtering.
3. Topic-aware scoring.

### Bitis Kriteri

1. Dusuk kaliteli chunk'lar son cevaba girmiyor.

## Phase 5: Safety & Topic Alignment

### Kapsam

1. Query topic mapping ile ingestion topic mapping'i hizala.
2. Crisis routing'i netlestir.
3. Low-confidence durumunda abstention davranisi uygula.
4. Gerekirse human escalation akisi tanimla.

### Ciktilar

1. Topic alignment tablosu.
2. Safety policy enforcement.
3. Evidence-based fallback davranisi.

### Bitis Kriteri

1. Crisis, off-domain ve low-confidence sorgular dogru sekilde yönetiliyor.

## Phase 6: Evaluation Harness

### Kapsam

1. Ingestion testlerini genislet.
2. Retrieval evaluation scriptlerini standardize et.
3. Precision@K, Recall@K ve nDCG gibi metrikleri takip et.
4. Regression testleri ekle.

### Ciktilar

1. Otomatik evaluation pipeline.
2. CI'da calisan test seti.
3. Regression alarm mekanizmasi.

### Bitis Kriteri

1. Kalite degisimleri metriklerle goruluyor ve regresyonlar yakalanabiliyor.

## Phase 7: Controlled Rollout

### Kapsam

1. Yeni ingestion ve retrieval akislarini canary sekilde ac.
2. Log, latency ve failure oranlarini izle.
3. Geri alma planini hazir tut.
4. Pilot kullanici grubunda dogrula.

### Ciktilar

1. Controlled rollout plan.
2. Monitoring dashboard.
3. Rollback proseduru.

### Bitis Kriteri

1. Sistem production seviyesinde stabil calisiyor.

## Phase 8: Optional GraphRAG

### Kapsam

1. Entity extraction ve relation extraction gerekliligi olusursa Graph katmani kur.
2. Community summary ile dokuman topluluklarini ozetle.
3. Graph sorgularini klasik retrieval ile router uzerinden yonlendir.

### Ciktilar

1. Entity graph.
2. Relationship graph.
3. Graph-backed retrieval pilotu.

### Bitis Kriteri

1. Graph katmani sadece ihtiyac halinde acilan opsiyonel bir modul olarak calisiyor.

## Bagimliliklar

1. Phase 1, Phase 0 baseline tamamlanmadan baslamamali.
2. Phase 2, Phase 1 layout-aware ingestion olmadan tamamlanamaz.
3. Phase 3, Phase 2 metadata'li corpus olmadan dogru olculemez.
4. Phase 4, Phase 3 hybrid retrieval sinyalleri olmadan optimize edilemez.
5. Phase 5, Phase 4 reranking ve evidence gate sinyalleri olmadan eksik kalir.
6. Phase 6, tum onceki fazlardan veri toplar.
7. Phase 7, Phase 6 metrikleri stabil olmadan acilmaz.
8. Phase 8, Graph ihtiyaci kanitlanmadan acilmaz.

## Tavsiye Edilen Sira

1. Baseline cikart.
2. Layout-aware ingestion'i aktif et.
3. Metadata extraction ve corpus versioning kur.
4. Dense + keyword hybrid retrieval'i guclendir.
5. Reranker ve evidence gate ekle.
6. Safety ve topic hizasini sertlestir.
7. Evaluation harness'i standardize et.
8. Kontrollu rollout yap.
9. Graph ihtiyaci dogarsa opsiyonel olarak ekle.

## Basari Metrikleri

1. Retrieval Precision@5 artisi.
2. Retrieval Recall@5 artisi.
3. Off-topic hit oraninda dusus.
4. Low-evidence cevap oraninda dusus.
5. Abstention durumunda dogru yonlendirme orani.
6. Response latency'nin kabul edilebilir sinirda kalmasi.
7. Reranker ile relevance artisi.
8. Layout-aware parsing ile structure retention artisi.

## Riskler

1. LLM classifier taxonomy ile uyumlu degilse kalite dusurur.
2. Ingestion request-time calisirsa latency artar.
3. Corpus versioning index versioning ile ayrilmazsa tutarsizlik olur.
4. Fazlar birbirine bagli oldugu icin siralama bozulmamalidir.
5. GraphRAG'i erken acmak sistemi gereksiz agirlastirir.

## Definition of Done

1. Ingestion offline calisiyor.
2. Corpus versioned saklaniyor.
3. Index corpus ile senkron.
4. Layout-aware parser aktif.
5. Semantic chunking aktif.
6. Metadata extraction aktif.
7. Dense + keyword hybrid retrieval aktif.
8. Reranker ve evidence gate aktif.
9. Safety routing devrede.
10. Evaluation metrikleri kayit altinda.
11. Production rollout kontrollu yapildi.

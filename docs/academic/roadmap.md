# Calma Roadmap

## 1. Amaç

Bu belge, Calma projesi için tek referanslı uygulama yol haritasıdır. Hedef, yerel çalışabilen, psikoloji odaklı, güvenli, kaynak temelli ve demo sunumuna hazır bir RAG asistanını adım adım inşa etmektir.

## 2. Proje Çerçevesi

- Ürün adı: Calma
- Çalışma ortamı: MacBook M4 Pro
- Maliyet hedefi: ücretsiz / yerel
- Eğitim yaklaşımı: fine-tune yok
- Ana yaklaşım: RAG + memory + safety + session restore API
- İçerik kaynağı: PDF yüklemeleri kullanıcı tarafından sağlanacak
- Ton: daha dostane, sıcak, sade ve güven verici
- Gizlilik: açık, okunabilir ve ürün içinde görünür

## 3. Temel Teknik Karar

### 3.1 Model

Ana model önerisi: `Qwen2.5 7B Instruct`

Gerekçe:
- yerel kullanım için dengeli
- RAG ile iyi çalışır
- talimat takibi güçlüdür
- çok dilli kullanımda pratiktir
- M4 Pro üzerinde demo için makul bir yük oluşturur

### 3.2 Retrieval

- Hybrid retrieval: semantic + keyword + topic bonus
- Vector store: FAISS
- Embedding: local sentence-transformer veya fallback hash embedding
- Evidence gate: cevap üretmeden önce zorunlu

### 3.3 Hafıza

- Kısa vadeli session memory
- Uzun vadeli user memory summary
- Screening geçmişi
- Consent-aware storage

### 3.4 Güvenlik

- Kriz tespiti
- Tanı reddi
- İlaç reddi
- Off-domain reddi
- Prompt injection engeli
- Supervisor review

## 4. Şu Anki Durum

Mevcut sistemde zaten şunlar var:

- authentication
- onboarding
- intake akışı
- PHQ-9 ve GAD-7 screening
- RAG retrieval pipeline
- evidence gate
- safety policy engine
- memory summary mantığı
- conversation persistence

Mevcut eksikler:

- session restore API yok
- messages birinci sınıf veri olarak modellenmemiş
- `history` backendde bağlamsal olarak tam kullanılmıyor
- PDF ingestion ayrı bir ürün akışı değil
- privacy / retention policy ürün metni olarak net değil

## 5. Hedef Mimari

```text
User
  -> Auth
  -> Consent / Onboarding
  -> Intake
  -> Screening
  -> Session Router
  -> Safety Triage
  -> Memory Fetch
  -> Hybrid Retrieval
  -> Evidence Gate
  -> LLM Generation
  -> Supervisor Review
  -> Persist Session / Messages / Summary
```

## 6. Veri Modeli

### 6.1 Ana Tablolar

#### `users`
- id
- email
- hashed_password
- created_at
- display_name
- username
- last_phq9_score
- last_screening_date

#### `sessions`
- id
- user_id
- title
- topic
- status (`active`, `archived`, `deleted`)
- intake_json
- consent_json
- summary
- last_message_at
- created_at
- updated_at
- archived_at

#### `messages`
- id
- session_id
- user_id
- role (`user`, `assistant`)
- content
- intent
- route
- safety_mode
- sources_json
- created_at

#### `memories`
- id
- user_id
- summary_nuggets
- sentiment_trend
- preferences_json
- risk_flags_json
- updated_at

#### `screenings`
- id
- user_id
- session_id
- type (`phq9`, `gad7`)
- answers_json
- score
- severity
- crisis_flag
- created_at

#### `consents`
- id
- user_id
- consent_version
- intake_consent
- screening_consent
- privacy_notice_version
- accepted_at

### 6.2 Gelecek Tablolar

#### `knowledge_documents`
- id
- title
- source
- version
- uploaded_by
- uploaded_at

#### `knowledge_chunks`
- id
- document_id
- chunk_text
- chunk_metadata_json
- embedding_ref

## 7. Uygulama Fazları

### Faz 0. Scope Lock

Hedef:
- proje sınırlarını dondurmak

Yapılacaklar:
- ürün konumlandırmasını kesinleştirme
- model seçimini onaylama
- veri saklama süresini belirleme
- PDF yükleme akışını netleştirme
- gizlilik metni kararını verme
- fine-tune’ı şimdilik dışarıda bırakma

Çıktılar:
- scope notu
- model kararı
- veri politikası taslağı

Testler:
- scope dokümanı ürün kapsamı ile tutarlı mı diye review
- model kararı M4 Pro kısıtlarıyla uyumlu mu diye kontrol
- retention ve privacy kararları çelişiyor mu diye doküman testi

### Faz 1. Session Architecture

Hedef:
- her konuşmayı yeniden açılabilir bir session haline getirmek

Yapılacaklar:
- `sessions` tablosu
- `messages` tablosu
- konuşmayı message-level persistence’a çevirmek
- session id akışı eklemek
- session listesi için backend endpoint oluşturmak
- restore endpoint yazmak

Çıktılar:
- reopenable chat sessions
- session listesi
- kalıcı mesaj geçmişi

Testler:
- session oluşturma entegrasyon testi
- mesaj yazma ve geri okuma testi
- session restore endpoint test
- yetkisiz kullanıcı için erişim reddi testi

### Faz 2. Memory Architecture

Hedef:
- kısa vadeli bağlam ile uzun vadeli kullanıcı özetini ayırmak

Yapılacaklar:
- session summary
- user profile summary
- screening outcome storage
- prompt’ta yalnızca gerekli hafızayı kullanmak

Çıktılar:
- dual-memory yapı
- prompt-ready summary

Testler:
- memory update unit testi
- session summary üretim testi
- prompt context composition testi
- boş memory durumunda güvenli fallback testi

### Faz 3. PDF Ingestion

Hedef:
- PDF yüklemesini gerçek bir knowledge pipeline’a çevirmek

Yapılacaklar:
- PDF ingestion service
- PDF parse
- chunking
- metadata tagging
- embedding üretimi
- index update

Çıktılar:
- yüklenen PDF’ler arama yapılabilir hale gelir

Testler:
- sample PDF parse testi
- chunking unit testi
- index update smoke testi
- retrieve edilen chunkların kaynak metadata testi

### Faz 4. Retrieval Kalitesi

Hedef:
- cevapların kaynakla uyumunu güçlendirmek

Yapılacaklar:
- chunk boyutu ayarı
- topic routing iyileştirme
- hybrid retrieval koruma
- evidence gate’i sıkı tutma
- kaynak gösterimini netleştirme

Testler:
- retrieval precision senaryo testi
- evidence gate kabul / reddetme testi
- source reference doğruluk testi
- retrieval fallback davranış testi

### Faz 5. Safety Katmanı

Hedef:
- mental-health bağlamında güvenli sınırları korumak

Yapılacaklar:
- kriz tespiti
- tanı reddi
- ilaç reddi
- prompt injection engeli
- friendlier refusal tonları
- supervisor review

Testler:
- crisis keyword testleri
- diagnosis refusal testleri
- medication refusal testleri
- prompt injection bloklama testi
- supervisor override test

### Faz 6. Response Style ve Ton

Hedef:
- daha dostane, sakin ve profesyonel bir cevap dili oluşturmak

Yapılacaklar:
- system prompt tonunu yumuşatma
- refusal mesajlarını daha doğal hale getirme
- answer formatını sabitleme
- kaynak referans dilini netleştirme
- kriz mesajlarını kısa ve doğrudan tutma

Testler:
- response format snapshot testi
- refusal message tone testi
- source citation wording testi
- kriz mesajı uzunluk / netlik testi

### Faz 7. Privacy ve Retention

Hedef:
- veri saklama ve gizlilik politikası oluşturmak

Önerilen retention:
- raw chat: 90 gün
- session summary: 1 yıl
- screening history: 1 yıl
- consent records: 1 yıl
- user request delete: hemen

Yapılacaklar:
- privacy notice
- consent wording
- retention policy
- delete behavior

Testler:
- consent state kaydı testi
- delete flow testi
- retention policy doküman testi
- privacy notice versiyon testi

### Faz 8. Evaluation

Hedef:
- sistemin güvenli ve tutarlı çalıştığını ölçmek

Yapılacaklar:
- retrieval precision
- groundedness
- refusal correctness
- crisis routing
- session continuity
- empathy / tone check

Testler:
- scenario-based evaluation set çalıştırma
- grounded answer scoring
- refusal accuracy scoring
- crisis route smoke testi

### Faz 9. Demo Hazırlığı

Hedef:
- hocaya gösterilecek sürümü temiz ve anlatılabilir yapmak

Yapılacaklar:
- README son hali
- architecture diagram
- demo script
- seed PDF’ler
- örnek scenario akışı

Testler:
- end-to-end demo smoke testi
- seed PDF ile tam akış testi
- kurulum adımları yeniden çalıştırma testi
- başlangıç / onboarding akışı testi

### Faz 10. Gelecek İyileştirmeler

Hedef:
- ileride büyütülebilecek yol bırakmak

Olası sonraki işler:
- LoRA / adapter tuning
- reranker
- session search
- analytics
- document versioning
- daha gelişmiş memory policy

Testler:
- bu faz için zorunlu test yok; gelecekte eklenen her yeni özellik kendi testleriyle gelir

## 8. Rollerin Paylaşımı

### Benim yapacaklarım

- mimari plan
- backend uygulama
 - session restore API
- PDF ingestion
- memory entegrasyonu
- safety work
- dokümantasyon güncellemesi

### Senin yapacakların

- PDF dosyalarını sağlamak
- ton ve metin onayı vermek
- gizlilik metnini gözden geçirmek
- retention kararını onaylamak
- gerekirse domain kaynaklarını belirtmek

## 9. Uygulama Sırası

1. session architecture
2. memory architecture
3. PDF ingestion
4. retrieval iyileştirme
5. safety polish
6. response style polish
7. privacy / retention metni
8. evaluation
9. demo readiness

## 10. Şimdilik Kapsam Dışı

- fine-tune
- cloud API bağımlılığı
- klinik tanı
- ilaç önerisi
- acil servis rolü
- gerçek dünya tedavi yönlendirmesi

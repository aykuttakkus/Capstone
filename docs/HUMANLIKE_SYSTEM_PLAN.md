# Calma — Human-Like Therapy System: System Design Document

**Version:** 3.0  
**Status:** Draft — Implementation Ready  
**Last Updated:** 2026-05-17  
**Authors:** Calma Engineering Team  
**Reviewers:** —  
**Classification:** Internal — Engineering

---

## Değişiklik Geçmişi

| Versiyon | Tarih | Değişiklik |
|---|---|---|
| 1.0 | 2026-05-17 | İlk taslak — 7 sistem tasarımı |
| 2.0 | 2026-05-17 | RESPONSE_DESIGN_GUIDE entegrasyonu, Sistem G eklendi |
| 3.0 | 2026-05-17 | Araştırma sentezi (2022–2026), Sistem H + Agentic Mimari eklendi |

---

## Yönetici Özeti (Executive Summary)

Calma şu an kullanıcıya chatbot hissi veren, her seansta yabancı gibi davranan, jenerik empati üreten bir sistemdir. Bu doküman sistemi araştırma destekli, psikolog davranışını modelleyen bir platforma dönüştürecek 8 sistemin teknik tasarımını içerir.

**Temel Hedef:** Therabot (Dartmouth 2025) araştırmasının 8 haftada %51 depresyon azalması sağlayan üç kritik özelliği: seans sürekliliği, bağlam-duyarlı yanıtlar ve örüntü takibi.

**Kapsam Dışı:**
- Klinik tanı veya tedavi
- İlaç tavsiyesi
- İnsan terapisti yerine geçme

**Başarı Metrikleri:**
| Metrik | Başlangıç | Hedef |
|---|---|---|
| "Chatbot gibi" kullanıcı yorumu | ~%60 | < %20 |
| 2:1 yansıtma/soru oranı | ~%10 turda | > %80 turda |
| Seans sürekliliği (köprü notu) | %0 | > %95 |
| Faz geçiş doğruluğu | N/A | > %75 |

---

> **Tarih:** 2026-05-17  
> **Referans:** RESPONSE_DESIGN_GUIDE.md v3 · Chat pipeline analizi · Araştırma sentezi (2022–2026)  
> **Temel:** CBT (Beck) · MI/OARS (Miller & Rollnick) · SFBT (de Shazer) · ESConv (Liu 2021) · CAMI (ACL 2025)  
> **Kapsam:** Yanıt sistemi, bellek mimarisi, RAG enjeksiyonu, faz yönetimi, örüntü tespiti, sohbet durum takibi

---

## 0. Teşhis — Neden Şu An Chatbot Hissi Var?

| # | Sorun | Nerede | Etki |
|---|---|---|---|
| 1 | Bellek 420 karakter düz metin | `memory_agent.py` | Sistem her seansta yabancı gibi davranıyor |
| 2 | RAG generic fact olarak enjekte ediliyor | `generator.py` | "Kronik stres kortizol etkiler" tarzı cümleler |
| 3 | Profil verisi LLM prompt'una girmiyor | `generator.py` | İsim, geçmiş, kişisel kelimeler görmezden geliniyor |
| 4 | Soru LLM tarafından serbest üretiliyor | `prompts.yaml` | Her seferinde farklı kalitede sorular |
| 5 | Seans fazı persist edilmiyor | `session_store.py` | Sistem seans içindeki konumunu bilmiyor |
| 6 | Refleksiyon seviyesi yok | `prompts.yaml` | V adımı her zaman yüzeysel kalıyor |
| 7 | Derinleşme sinyalleri tanımlanmamış | `generator.py` | "Bilmiyorum" ve kısa cevaplar handle edilemiyor |
| 8 | Faz 2→3 geçişi sadece turn count'a bakıyor | `session_store.py` | İçgörü anı kaçırılıyor |
| 9 | Yanıt üretmeden önce diyalog eylemi seçilmiyor | `generator.py` | LLM hangi tür yanıt vereceğini bilmeden yazıyor — yansıtma mı, soru mu, özet mi? |
| 10 | Sohbet durumu (ConvState) takip edilmiyor | `assistant.py` | Hangi konular derinleştirildi, hangisi yarım kaldı, direnç var mı — sistem bilmiyor |

---

## 1. Hedef Mimari — 8 Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│  SİSTEM A   Structured Memory        (Kişiyi Tanıma Katmanı)   │
│  SİSTEM B   Dialogue Act + Policy    (Kasıtlı Eylem Seçimi)    │
│  SİSTEM C   Personalized RAG         (Bilgiyi Sahneye Koy)     │
│  SİSTEM D   Phase State Machine      (Seansta Konum Takibi)    │
│  SİSTEM E   Pattern Detector         (Gerçek Zeka Hissi)       │
│  SİSTEM F   Reflection Levels        (3 Seviye Yansıtma)       │
│  SİSTEM G   Deepening Signal Handler (Derinleşme Yönetimi)     │
│  SİSTEM H   Conversation State Engine(Sohbet Durumu + Policy)  │
└─────────────────────────────────────────────────────────────────┘
```

**Temel akış (her turda):**
```
Kullanıcı mesajı
  → ConvState güncelle (Sistem H)
  → Diyalog Eylemini Seç — Policy Decision Tree (Sistem H + B)
  → Yanıt üret — seçilen eylemle (Sistem B, C, F, G)
  → Belleği güncelle (Sistem A)
  → Faz değerlendirme (Sistem D)
```

---

## 1.5 Agentic Mimari

Bu bölüm Calma'nın ajan katmanlarını, her ajanın sorumluluğunu ve per-turn çalışma düzenini tarif eder. Mimari üç katmanlıdır: algı, karar ve yürütme.

### Katman 1 — Algı Ajanları

Katman 1 ajanları ham kullanıcı girdisini yorumlanmış duruma çevirir. Hiçbir eylem kararı vermezler; yalnızca sinyal üretirler.

| ID | Ajan | Dosya | Tür | Çıktı |
|---|---|---|---|---|
| 1A | ConversationStateEngine | `core/agents/conversation_state.py` (yeni) | Pure Python (hafif) + LLM (ağır, arka plan) | `change_talk_score`, `resistance_detected` her turda; gündem haritası her 4 turda |
| 1B | PatternDetector | `core/agents/pattern_detector.py` (yeni) | Pure Python — Counter/regex, LLM yok | Within-session örüntüler, cross-session örüntüler, bilişsel çarpıtma sinyalleri |
| 1C | Orchestrator | `core/agents/orchestrator.py` (mevcut, geliştirildi) | LLM | Intent + güvenlik + duygu durumu; artık `conv_state` + `patterns` de alıyor |
| 1D | SentimentAgent | — (emekliye ayrılıyor) | — | İşlevi Orchestrator bünyesine taşındı |

**1A — ConversationStateEngine çalışma modu:**

```
Hafif (her turda, senkron):
  - change_talk_score → score_change_talk(history)
  - resistance_detected → detect_resistance(last_user_msg)

Ağır (her 4 turda, asenkron arka plan):
  - Gündem haritalama LLM çağrısı
  - primary_concern, explored_topics, unexplored_mentions güncellenir
```

**1B — PatternDetector çalışma modu:**

```
Within-session: Counter ile tekrar eden kelime tespiti (≥3 tekrar)
Cross-session:  structured_memory["recurring_themes"] count kontrolü (≥3 seans)
Bilişsel çarpıtma: COGNITIVE_DISTORTIONS regex eşleştirmesi
```

### Katman 2 — Karar Ajanları

Katman 2 ajanları Katman 1'in ürettiği sinyalleri alarak bir sonraki yanıt stratejisine karar verir. Doğrudan kullanıcıyla iletişim kurmazlar.

| ID | Ajan | Dosya | Tür | Çıktı |
|---|---|---|---|---|
| 2A | DialoguePolicyAgent | `core/agents/dialogue_policy.py` (yeni) | Pure Python — Policy Decision Tree, LLM yok | `selected_dialogue_act` (MISC kodu) |
| 2B | PhaseManager | `core/agents/phase_manager.py` (yeni) | Pure Python | `session_phase` güncellemesi — change_talk_score tabanlı geçiş |
| 2C | ResponsePlanner | — (emekliye ayrılıyor) | — | İşlevi DialoguePolicyAgent + generator prompt'u bünyesine taşındı |

**2A — DialoguePolicyAgent karar ağacı özeti:**

```python
ConvState → distress_level ≥ 8  →  VALIDATION + SAFETY_CHECK
         → primary_concern None  →  OQ
         → resistance_detected   →  SR
         → change_talk_score > 0.6 →  OQ (amplify)
         → sustain_talk_ratio > 0.5 →  OQ (değer keşfi)
         → unexplored_mentions   →  OQ (geri dön)
         → session_phase == 1    →  OQ
         → session_phase == 2    →  CR (varsayılan) | SFBT_EXCEPTION | SFBT_MIRACLE
         → session_phase == 3    →  SFBT_SCALE
         → len(explored_topics) ≥ 3 →  SU
         → varsayılan            →  SR
```

**2B — PhaseManager geçiş mantığı:**

```
change_talk_score ≥ 0.6  →  Faz 3'e geç
insight_triggered = True →  Faz 3'e geç
turn_count ≥ 10          →  Faz 3'e geç (fallback)
closure_confirmed = True →  Faz 4'e geç
```

### Katman 3 — Yürütme Ajanları

Katman 3 ajanları Katman 2'nin kararlarını uygular: yanıt üretir, kalite denetimi yapar ve belleği günceller.

| ID | Ajan | Dosya | Tür | Değişiklik |
|---|---|---|---|---|
| 3A | AnswerGenerator | `core/generation/generator.py` (mevcut, geliştirildi) | LLM | Artık `conv_state` + `selected_act` alıyor; CoS protokolü prompt'a gömülü |
| 3B | SupervisorAgent | `core/agents/supervisor.py` (mevcut, geliştirildi) | LLM | Artık MI uyumunu da denetliyor: 2:1 oran kontrolü, yasak açılış tespiti |
| 3C | MemoryAgent | `core/agents/memory_agent.py` (mevcut, güncellendi) | LLM | Structured JSON çıktısı; worktree'de zaten güncellendi |

### Per-Turn Pipeline

```
SYNC PATH (kullanıcı bekler):
─────────────────────────────────────────────────────────────────────
[Safety Keyword]
       │
       ▼
[ConvState Light]   ← change_talk_score, resistance_detected
       │
       ▼
[PatternDetect]     ← within-session + cross-session + distortions
       │
       ▼
[Orchestrator LLM]  ← intent + safety + sentiment + conv_state + patterns
       │
       ▼
[DialoguePolicy]    ← selected_dialogue_act (MISC kodu)
       │
       ▼
[RAG Pipeline]      ← ilgili chunk, skor ≥ 0.72 ise sahne enjeksiyonu
       │
       ▼
[AnswerGenerator LLM] ← conv_state + selected_act + CoS protokolü
       │
       ▼
    RESPONSE

ASYNC PATH (arka plan, kullanıcı beklemez):
─────────────────────────────────────────────────────────────────────
[MemoryAgent LLM]          ← etkileşimden structured JSON bellek günceller
[SupervisorAgent LLM]      ← MI uyum denetimi, forbidden opening kontrolü
[PhaseManager]             ← change_talk_score tabanlı faz geçiş kararı
[ConvState Heavy]          ← her 4 turda gündem haritalama LLM çağrısı
```

### Latency Analizi

| Bileşen | Yol | LLM? | Tahmini Süre | Notlar |
|---|---|---|---|---|
| Safety Keyword | Sync | Hayır | ~0.5ms | Regex/set lookup |
| ConvState Light | Sync | Hayır | ~2ms | Pure Python — Counter + regex |
| PatternDetect | Sync | Hayır | ~1ms | Pure Python — Counter + regex |
| Orchestrator | Sync | Evet | ~3s | Mevcut latency korunur |
| DialoguePolicy | Sync | Hayır | ~0.3ms | Pure Python karar ağacı |
| RAG Pipeline | Sync | Hayır | ~200ms | Mevcut latency korunur |
| AnswerGenerator | Sync | Evet | ~5s | Mevcut latency + ~200ms prompt artışı |
| **Total Sync** | — | — | **~8s** | p95 hedef: < 12s |
| MemoryAgent | Async | Evet | ~2s | Yanıt sonrası arka plan |
| SupervisorAgent | Async | Evet | ~2s | Yanıt sonrası arka plan |
| PhaseManager | Async | Hayır | ~0.1ms | Pure Python |
| ConvState Heavy | Async (her 4 tur) | Evet | ~3s | Gündem haritalama |

**Net yeni latency (sync path): ~0ms** — Eklenen yeni ajanların tümü (ConvState Light, PatternDetect, DialoguePolicy) kural tabanlı ve LLM içermez. Toplam sync süreye etkileri 3ms civarındadır.

---

## 2. Sistem A — Structured Memory

### 2.1 Problem

```python
# Şu an — assistant.py:70
return prune_memory_text(decrypt_clinical_data(memory.summary_nuggets),
                         max_lines=6, max_chars=420)
# Çıktı: "Topic: burnout. Intent: emotional_support. Response: ..."
# → LLM için anlamsız düz metin, kişiyi tanımıyor
```

### 2.2 Hedef JSON Schema (Core Memory)

```json
{
  "v": 2,
  "preferred_name": "Zeynep",
  "recurring_themes": [
    {"theme": "iş yükü", "count": 4, "last_seen": "2026-05-15"},
    {"theme": "uyku güçlüğü", "count": 3, "last_seen": "2026-05-17"}
  ],
  "user_vocabulary": ["boşuna", "sıkışmış", "nefes alamıyorum"],
  "what_helped": ["yürüyüş", "günlük tutma"],
  "key_people": ["annesi", "iş arkadaşı Mert"],
  "mood_trend": [4, 6, 5, 4, 7],
  "milestone_moments": ["ilk kez ağladığını söyledi (seans 3)"],
  "active_action_plan": "Yatmadan 30 dk önce telefonu başka odaya bırak",
  "last_session_topic": "iş stresi ve uyku",
  "last_session_date": "2026-05-15"
}
```

### 2.3 4 Katmanlı Bellek Mimarisi

Araştırma (MemGPT, Memoria, HTM 2025) tek JSON şemasının yetmeyeceğini gösterdi. Hedef mimari:

| Katman | İçerik | Prompt'a Girişi |
|---|---|---|
| **Core Memory** | Profil, inançlar, aktif hedefler, risk flag | Her turda |
| **Episodic Memory** | Seans özetleri, içgörü anları, başarısız müdahaleler | Retrieve ile (ilgili 3 anı) |
| **Semantic Memory** | İlişkiler, örüntüler, tetikleyiciler, knowledge graph | Seans başında retrieve |
| **Working Memory** | ConvState — bu turun durumu | Her turda (bkz. Sistem H) |

**Kritik:** MemMachine (2025) araştırması LLM özetlerinin zamanla kullanıcı gerçeklerini bozduğunu gösterdi. Anahtar cümlelerin verbatim saklanması ve özet yanında ground-truth olarak tutulması gerekiyor.

### 2.4 Değişecek Dosyalar

| Dosya | Değişiklik |
|---|---|
| `core/agents/memory_agent.py` | `summarize_interaction()` → structured JSON üretir |
| `services/assistant.py` | `_get_user_memory()` / `_update_user_memory()` → JSON round-trip |
| `core/database.py` | `Memory.summary_nuggets` Text kolonu JSON string tutar, şema değişmez |

### 2.5 memory_agent Güncellenen Prompt (prompts.yaml)

```yaml
memory_agent: |
  Mevcut hafıza (JSON): $CURRENT_MEMORY
  Yeni etkileşim:
    Kullanıcı: "$USER_MSG"
    Asistan: "$AI_MSG"

  Sırayla güncelle:
  1. preferred_name  — kullanıcı adından bahsettiyse güncelle
  2. recurring_themes — bu etkileşimin ana konusunu bul, count artır,
                        last_seen bugün (YYYY-MM-DD). Max 8 tema.
  3. user_vocabulary — kullanıcının özgün kelimelerini/metaforlarını ekle. Max 12.
  4. what_helped      — işe yaradığını söylediği bir şey varsa ekle.
  5. key_people       — yeni kişi adı/rolü geçtiyse ekle. Max 8.
  6. milestone_moments — önemli an olduysa kısa not düş. Max 6.
  7. active_action_plan — asistan somut eylem önerdiyse buraya yaz.
  8. last_session_topic — bu etkileşimin ana konusu.
  9. last_session_date  — bugünün tarihi (YYYY-MM-DD).

  KURAL: Ham alıntı yok. Tanı etiketi yok ("depresyon" değil
         "3 haftadır uyku güçlüğü bildiriyor"). Sadece geçerli JSON çıktısı.
```

### 2.6 Belleğin Prompt'a Enjeksiyonu

```
[BU KİŞİYİ TANIYORSUN]
Ad: {preferred_name}
Tekrar eden konular: {recurring_themes}  ← kaç kez, ne zaman
Kendi kelimeleri: {user_vocabulary}      ← bunları V adımında kullan
İşe yarayanlar: {what_helped}
Önemli kişiler: {key_people}
Son seans: {last_session_date} — konu: {last_session_topic}
Aktif eylem planı: {active_action_plan}
Ruh hali eğilimi: {mood_trend}
```

---

## 3. Sistem B — Dialogue Act Policy + Soru Havuzu

### 3.1 Problem

LLM her yanıtta farklı kalitede sorular üretiyor. Yanıt türü (soru mu? yansıtma mı? özet mi?) serbest bırakılmış. Araştırma (PsyMix 2024, CAMI 2025) bunun temel hata olduğunu kanıtladı: **yanıt üretmeden önce eylem tipi seçilmeli.**

### 3.2 MISC Diyalog Eylemi Taksonomisi

Motivasyonel Görüşme araştırmasının standardı olan MISC kodları sistemin temel eylem dili:

| Kod | Eylem | Ne Zaman |
|---|---|---|
| **OQ** | Açık Soru | Konu netleşmedi, daha fazla bilgi lazım, keşif gerekiyor |
| **SR** | Basit Yansıtma | Kullanıcı duyulmak istiyor, direnç var |
| **CR** | Derin Yansıtma | İma edilen anlam okunabiliyor, Seviye 3 uygun |
| **AF** | Gerçek Güç Tanıma | Somut bir çaba, dayanıklılık veya farkındalık görülüyor |
| **SU** | Özet | 3+ konu konuşuldu, bağlamak gerekiyor |
| **GI** | Bilgi Verme | Kullanıcı açıkça bilgi istedi (sadece I adımında) |
| **FA** | Kolaylaştırma | "Ve?", "Devam et" — kullanıcı duraksadı |

**Altın Kural (Spillane 2022 + MI araştırması):** Her 1 OQ için 2 SR/CR. Soru oranı yüksek olduğunda sistem sorgu gibi, düşük olduğunda bilge dinleyici gibi hissettirir.

### 3.3 Policy Decision Tree — Sıradaki Eylemi Seç

ConvState'e bakarak hangi MISC eyleminin yapılacağı belirlenir:

```python
def select_dialogue_act(state: ConvState) -> str:
    # Önce güvenlik
    if state.distress_level >= 8:
        return "VALIDATION + SAFETY_CHECK"  # soru yok

    # Gündem henüz netleşmedi
    if state.primary_concern is None:
        return "OQ"  # gündem bul

    # Direnç sinyali → yansıtmaya dön, tartışma yok
    if state.resistance_detected:
        return "SR"

    # Değişim dili yüksek → genişlet, amplify et
    if state.change_talk_score > 0.6:
        return "OQ"  # "Bunu biraz daha anlat..."

    # Sustain talk baskın → değerlere geç
    if state.sustain_talk_ratio > 0.5:
        return "OQ"  # değer keşfi sorusu

    # Yarım kalan konu var → oraya dön
    if state.unexplored_mentions:
        return "OQ"  # "Daha önce {X}'den bahsetmiştin —"

    # Faz 1: Keşif
    if state.session_phase == 1:
        return "OQ"

    # Faz 2: Derinleştir
    if state.session_phase == 2:
        # SFBT koşulları
        if state.stuck_in_problem:          return "SFBT_EXCEPTION"
        if state.cannot_envision_change:    return "SFBT_MIRACLE"
        return "CR"  # varsayılan: derin yansıtma

    # Faz 3: Bağlantı + Eylem
    if state.session_phase == 3:
        return "SFBT_SCALE"  # ya da OQ eylem odaklı

    # 3+ konu konuşulduysa özet zamanı
    if len(state.explored_topics) >= 3:
        return "SU"

    return "SR"
```

### 3.4 Chain-of-Strategy (CoS) — Yanıt Üretim Protokolü

**Araştırma desteği:** PsyMix (2024), DIIR (ACL 2024) — Strateji seçimi yanıt üretiminden önce yapıldığında jenerik empati %35 azalıyor.

LLM prompt'una eklenen talimat:

```
YANIT ÜRETİM PROTOKOLÜ (CoS):

Adım 0 — Diyalog Eylemini Seç:
  ConvState ve sohbet geçmişine bakarak seç:
  [ OQ ] Açık Soru     [ SR ] Basit Yansıtma   [ CR ] Derin Yansıtma
  [ AF ] Güç Tanıma    [ SU ] Özet              [ GI ] Bilgi Ver (sadece istenince)

Adım 1 — Seçilen eylemle V adımını yap.
  Her yanıt MUTLAKA bir yansıtmayla başlar. Bilgi veya soru önce gelmez.

Adım 2 — I adımını ekle (RAG eşiği geçildiyse).

Adım 3 — E adımını ekle.

Adım 4 — S adımında seçilen eylem tipiyle bağla.
  OQ seçildiyse: tek soru, açık uçlu.
  SR/CR seçildiyse: soru olmayabilir.
  SU seçildiyse: özet + "Bunlara bakınca ne hissediyorsun?"

HEDEF ORAN: Her 1 OQ için en az 2 SR/CR.
```

### 3.5 SFBT Teknikleri — Tetik Koşulları

**Araştırma desteği:** MIT Thesis 2025 — SFBT, CBT'den daha etkili simüle senaryolarda. Üç spesifik teknik:

**İstisna Sorusu** — Kullanıcı problemi aşılmaz görünce (`stuck_in_problem = True`):
```
"Bu böyle hissetmediğin bir gün oldu mu — en son ne zaman?
 O gün ne farklıydı?"
```

**Ölçek Sorusu** — Faz 3'te ilerlemeyi somutlaştırmak için (`session_phase == 3`):
```
"0'dan 10'a kadar, bugün neredesin?
 Bir üste çıkmak nasıl görünürdü?"
```

**Mucize Sorusu** — Kullanıcı değişimi hayal edemiyor (`cannot_envision_change = True`):
```
"Yarın uyandığında bu problem çözülmüş olsaydı —
 gün boyunca ilk fark edeceğin şey ne olurdu?"
```

### 3.6 LLM Talimatı (prompts.yaml)

```
SORU KURALI:
Her yanıtta en fazla bir soru sor.
Soru üretme — önce Diyalog Eylemi Seç (CoS), sonra havuzdan uygula.
Kullanıcının kendi kelimelerini soruya yerleştir.
```

### 3.7 Soru Havuzu (prompts.yaml'a eklenecek)

```yaml
question_pool:
  exploration:
    tr:
      - "Bu duygu en çok ne zaman ortaya çıkıyor?"
      - "Böyle hissettiğinde içinden ne geçiyor?"
      - "Seni bu konuda en çok ne yoruyor?"
      - "Bu his bedeninde nerede hissettiriyor kendini?"
    en:
      - "When does this feeling tend to show up most?"
      - "What goes through your mind when this happens?"
      - "What part of this is weighing on you the most?"

  exception:
    tr:
      - "Bu his olmadığı zamanlar ne farklı oluyor?"
      - "Son zamanlarda biraz daha iyi geçen bir gün oldu mu?"
      - "Bunu daha kolay taşıdığın anlar nasıl oldu?"
    en:
      - "Are there times when this feels a bit lighter?"
      - "Has there been a day recently where things felt different?"

  clarification:
    tr:
      - "'{USER_WORD}' derken tam olarak ne kastediyorsun?"
      - "Bunu biraz daha açar mısın?"
      - "'{USER_PHRASE}' — bunu söylerken aklından ne geçiyor?"
    en:
      - "When you say '{USER_WORD}', what do you mean exactly?"
      - "Can you say more about that?"

  pattern:
    tr:
      - "Bu '{THEME}' konusu birkaç kez geldi — seninle önemli bir yeri var gibi."
      - "Fark ettim ki '{WORD}' sözcüğünü bu konuşmada birkaç kez kullandın — bu kelime ne taşıyor?"
    en:
      - "I notice '{THEME}' has come up a few times — it seems to carry weight for you."
      - "You've used the word '{WORD}' a few times — what does that word carry for you?"

  meaning:
    tr:
      - "Bu senin için ne ifade ediyor?"
      - "Bu sana kendine dair ne söylüyor?"
      - "Bu yaşanmasaydı hayatın nasıl farklı olurdu?"
    en:
      - "What does this mean to you?"
      - "What does this say to you about yourself?"

  progress:
    tr:
      - "Geçen konuşmamızdan bu yana ne biraz daha iyi gitti?"
      - "{ACTION_PLAN} için biraz alan buldun mu?"
    en:
      - "What's gone even a little bit better since we last talked?"
      - "Did you get a chance to try {ACTION_PLAN}?"

  scale:
    tr:
      - "0'dan 10'a, şu an neredesin — 0 en zor, 10 tam istediğin gibi?"
      - "Bir üste çıkmak nasıl görünürdü?"
      - "Bu kadar kalabilmek için ne yapıyorsun?"
    en:
      - "On a scale of 0-10, where are you today?"
      - "What would moving one step up look like?"

  silence:
    tr:
      - "Daha var mı?"
      - "Ve?"
      - "Devam et."
    en:
      - "What else?"
      - "And?"
      - "Go on."
    note: "Bu soruların gücü kısalığındadır. LLM hiçbir ek kelime eklemez."
```

---

## 4. Sistem C — Personalized RAG Injection

### 4.1 Problem

```python
# generator.py — şu an
context_block = f"\n[CLINICAL EVIDENCE: {clinical_nugget}]"
# Nuggetizer çıktısı: "Chronic stress elevates cortisol levels." ← generic
```

### 4.2 Hedef — Kullanıcının Sahnesine Yerleştirme

```
Kullanıcı: "3'te uyanıyorum kafam durmuyor"

❌ Eski: [CLINICAL EVIDENCE: Kronik stres kortizol seviyesini etkiler.]

✅ Yeni: "O gece 3'teki uyanış — beyin hâlâ 'tehlike var' modunda,
          gündüz kapanmayan bir şeyi gece çözmeye çalışıyor gibi."
```

### 4.3 Yeni RAG Prompt Şablonu (generator.py → _build_prompt)

```
[RAG SAHNE ENJEKSİYONU — I ADIMI]
Kullanıcının tam sözü:        "{user_message}"
Kullanıcının adı:             "{preferred_name}"
Bu seansın konusu:            "{session_topic}"
Yapılandırılmış bellekten:    "{memory_snapshot}"
İlgili araştırma içeriği:     "{raw_rag_chunk}"

GÖREV: Bu araştırma bilgisini kullanıcının kendi anlattığı sahneye
ve kendi kullandığı kelimelerine yerleştirerek 1-2 cümle yaz.
Teknik terim kullanma. Sade dile çevir. Metafor kullan.

Metafor onaylı listesi:
  anksiyete    → "beynin gereksiz yere alarm çalan duman dedektörü"
  kronik stres → "telefonun şarjının hiç tam dolmadığı durum"
  ruminasyon   → "aynı şarkının döngüde çalması"
  uyku güçlüğü → "zihnin kapatma düğmesini bulamaması"
  ya hep ya hiç → "zihin sadece iki seçenek görüyor sanki"
```

### 4.4 Anti-Hallüsinasyon Kuralı

```python
RAG_SCENE_THRESHOLD = 0.72  # config.py

if top_chunk.score >= RAG_SCENE_THRESHOLD:
    inject_rag_scene(chunk, user_message, preferred_name)
else:
    skip_I_step()  # I adımını tamamen atla — V + E + S yap
```

### 4.5 Nuggetizer Değişikliği

**Mevcut:** 20 kelime generic fact → LLM'e ekleniyor  
**Hedef:** Raw chunk içeriği doğrudan generator'a gidiyor, nuggetizer bypass edilir

---

## 5. Sistem D — Phase State Machine

### 5.1 Gerekli DB Alanları (models.py → ChatSession)

```python
class ChatSession(Base):
    # ... mevcut alanlar ...
    session_phase      = Column(Integer, nullable=False, default=1)
    turn_count         = Column(Integer, nullable=False, default=0)
    agenda_set         = Column(Boolean, nullable=False, default=False)
    insight_triggered  = Column(Boolean, nullable=False, default=False)
    closure_confirmed  = Column(Boolean, nullable=False, default=False)
```

> **Not:** SQLite `create_all` varolan tablolara kolon eklemez.  
> Migration scripti: `scripts/migrate_phase_fields.py`

### 5.2 Faz Geçiş Mantığı

```python
def determine_phase(session: ChatSession, conv_state: ConvState) -> int:
    # İlk mesaj
    if session.turn_count == 0:
        return 1

    # Gündem henüz belirlenmedi
    if not session.agenda_set and session.turn_count <= 2:
        return 1

    # Keşif — gündem var, içgörü yok, değişim dili düşük
    if session.agenda_set and not session.insight_triggered:
        if conv_state.change_talk_score < 0.5 and session.turn_count < 10:
            return 2

    # İçgörü & Eylem — değişim dili veya semantik sinyal
    if session.insight_triggered or conv_state.change_talk_score >= 0.6:
        return 3

    if session.turn_count >= 10:
        return 3

    # Kapanış
    if session.closure_confirmed:
        return 4

    return 2
```

### 5.3 Faz Geçiş Tespiti — Değişim Dili (Change Talk)

**Araştırma (CAMI 2025, MI literatürü):** Change talk, faz geçişinin en güvenilir sinyali. Keyword arama değil, DARNC kategorileri kullanılır:

| Kategori | Açıklama | Örnek İfade |
|---|---|---|
| **D**esire | Değişmek istiyor | "Farklı olmasını istiyorum", "Keşke..." |
| **A**bility | Yapabileceğini düşünüyor | "Sanırım yapabilirim", "Bunu deneyebilirim" |
| **R**eason | Değişmesinin nedeni | "Bu beni çok yoruyor", "Aileme karşı hissediyorum" |
| **N**eed | Değişmesi gerekiyor | "Böyle devam edemem", "Bir şeyler yapmalıyım" |
| **C**ommitment | Karar verdi | "Bunu deneyeceğim", "Yapacağım" |

**Karşıtı — Sustain Talk:** "Ama zor", "Olmaz", "Nasıl yapacağım bilmiyorum", "Zaten hep böyle"

```python
CHANGE_TALK_PATTERNS = {
    "desire":     ["istiyorum", "olmasını isterdim", "keşke", "i want", "i wish"],
    "ability":    ["yapabilirim", "deneyebilirim", "i could", "i might", "i can"],
    "reason":     ["çünkü", "bu yüzden", "yararlı olurdu", "because", "it would help"],
    "need":       ["zorundayım", "gerekiyor", "böyle devam edemem", "i need to", "i have to"],
    "commitment": ["yapacağım", "deneyeceğim", "i will", "i'm going to"],
}

SUSTAIN_TALK_PATTERNS = [
    "ama", "fakat", "olmaz", "yapamam", "zaten hep", "her zaman böyle",
    "but", "can't", "impossible", "always like this", "never works"
]

def score_change_talk(history: list[dict]) -> float:
    """0.0–1.0 arası değişim hazırlık skoru. 0.6+ → Faz 3 geçişi."""
    user_text = " ".join(m["content"] for m in history if m["role"] == "user").lower()
    change_hits = sum(1 for patterns in CHANGE_TALK_PATTERNS.values()
                      for p in patterns if p in user_text)
    sustain_hits = sum(1 for p in SUSTAIN_TALK_PATTERNS if p in user_text)
    total = change_hits + sustain_hits
    return change_hits / total if total > 0 else 0.0
```

### 5.4 Ek Semantik Sinyaller (Mevcut + Korunur)

```python
INSIGHT_SIGNALS = [
    "aslında sanırım", "belki bu yüzden", "şimdi anlıyorum",
    "fark ettim", "galiba şundan", "demek ki",
    "i think maybe", "i realize", "now i see", "perhaps that's why",
]

ACTION_REQUEST_SIGNALS = [
    "ne yapabilirim", "ne yapmalıyım", "nasıl", "yardım eder misin",
    "what can i do", "how do i", "what should i",
]
```

### 5.5 Gündem Haritalama (Agenda Mapping — Her 3-5 Turda)

**Araştırma (MIND-SAFE 2025):** ConvState gündem çıkarımı örtülü değil, yapılandırılmış soru ile yapılmalı.

Her 3-5 turda asistan arka planda şu çıkarımı çalıştırır:

```
GÜNDEM HARITALAMA (arka plan — LLM çağrısı):

Konuşmayı oku ve yanıtla:
1. Kullanıcının ANA sorunu nedir? (kendi sözleriyle, 1-2 cümle)
2. Hangi konular yeterince konuşuldu?
3. Hangi konular geçildi ama girilmedi?
4. Değişim dili var mı? Varsa kategori ve örnek ver. (DARNC)
5. Direnç ifadesi var mı? Varsa örnek ver.
6. Sıkıntı seviyesi 0-10 arası tahmini nedir?

JSON çıktısı ver.
```

Bu çıkarım ConvState'i günceller. Bir sonraki turdaki Policy Decision Tree güncel ConvState'e göre çalışır.

### 5.6 İlk Seans vs Geri Dönen Kullanıcı (Faz 1 Şablonları)

**İlk Seans:**
```
TR: "Hoş geldin. Burada tanı, tedavi ya da ilaç yok —
     sadece düşüncelerini birlikte anlamaya çalışabileceğin
     güvenli bir alan. Bugün seni en çok ne meşgul ediyor?"
```
**Kural:** İlk karşılamada "Nasılsın?" sorulmaz.

**Geri Dönen Kullanıcı (2–6 gün önce):**
```
TR: "Geçen konuşmamızda {topic} üzerinde durmuştuk.
     O günden bu yana nasıl geçti — bir şey değişti mi?"
```

**Geri Dönen Kullanıcı (7–30 gün önce):**
```
TR: "Bir süre olmuş. Geçen konuşmamızda {topic}dan bahsetmiştin —
     bugün oradan devam etmek ister misin, yoksa farklı bir şey mi var?"
```

**Eylem Planı Varsa:**
```
TR: "Geçen seferki {action_plan} için biraz alan ayırmıştın — o nasıl gitti?"
```

### 5.7 Faz Başına Prompt Değişkeni

```yaml
phase_instructions:
  phase_1: |
    FAZ 1 (Açılış — max 3 cümle):
    Bridge notu varsa kullan. Ruh hali sorusu sor (0-10).
    Günün odak noktasını belirle. Henüz keşfe girme.

  phase_2: |
    FAZ 2 (Keşif — max 5 cümle):
    VIE-SR yapısını tam uygula.
    RAG içeriğini kullanıcının sahnesine yerleştir.
    Policy Decision Tree'den gelen eylemi uygula.
    Derinleşme sinyallerini takip et.

  phase_3: |
    FAZ 3 (İçgörü & Eylem — max 5 cümle):
    Kullanıcıya kendi içgörüsünü özetlet.
    İşbirliğiyle micro-eylem öner.
    Kapanış mood check yap.
    "Ödev" kelimesi kesinlikle kullanılmaz.

  phase_4: |
    FAZ 4 (Kapanış — max 3 cümle):
    Sonraki seansa köprü kur. Yeni konu açma. Seans kartı hazırla.
```

---

## 6. Sistem E — Pattern Detector

### 6.1 Within-Session Pattern (aynı seans içi)

```python
# core/agents/pattern_detector.py — yeni dosya
from collections import Counter
import re

STOPWORDS = {
    "ve", "bir", "bu", "da", "de", "ki", "ile", "ben", "sen", "biz",
    "the", "a", "an", "and", "or", "but", "in", "on", "is", "it",
    "i", "you", "that", "this", "was", "are", "have", "not"
}

def detect_within_session_patterns(history: list[dict]) -> list[str]:
    user_text = " ".join(
        m["content"] for m in history if m["role"] == "user"
    ).lower()
    words = re.findall(r'\b\w{4,}\b', user_text)
    counts = Counter(w for w in words if w not in STOPWORDS)

    signals = []
    for word, count in counts.most_common(3):
        if count >= 3:
            signals.append(f"'{word}' bu seansta {count} kez tekrarlandı")
    return signals
```

Bu sinyaller prompt'a eklenir:
```
[SEANS İÇİ ÖRÜNTÜLER]
'boşuna' bu seansta 4 kez tekrarlandı
```

LLM bu görünce **Soru Havuzu → pattern** kategorisini seçer:
> "Bu 'boşuna' kelimesi bu konuşmada birkaç kez geldi — seninle önemli bir yeri var gibi görünüyor."

### 6.2 Cross-Session Pattern (seanslararası)

```python
def detect_cross_session_patterns(structured_memory: dict) -> list[str]:
    signals = []
    for theme in structured_memory.get("recurring_themes", []):
        if theme["count"] >= 3:
            signals.append(
                f"'{theme['theme']}' {theme['count']} seanstır gündemde"
            )
    return signals
```

### 6.3 Bilişsel Çarpıtma Tespiti (CBT)

```python
COGNITIVE_DISTORTIONS = {
    "all_or_nothing": [
        "hiçbir zaman", "her zaman", "tamamen", "hiçbir şey",
        "never", "always", "everything", "nothing"
    ],
    "catastrophizing": [
        "mahvoldum", "bitti", "berbat", "felaket",
        "ruined", "disaster", "terrible", "awful"
    ],
    "mind_reading": [
        "anlayamıyorlar", "düşünüyorlar", "biliyorum ne",
        "they think", "she thinks", "he knows"
    ],
    "self_blame": [
        "benim hatam", "ben yaptım", "benim yüzümden",
        "my fault", "i ruined", "because of me"
    ],
}
```

Tespit edilirse Faz 3'te CBT yeniden çerçeveleme promptu aktif olur:
```
[BİLİŞSEL ÖRÜNTÜ]
Bu seansta: all_or_nothing düşünce ("hiçbir şeyi doğru yapamıyorum")
Faz 3'te keşif yoluyla sor:
"Bazen zihin 'ya mükemmel ya hiç' moduna giriyor.
 Orta bir nokta olsa nasıl görünürdü?"
```

---

## 7. Sistem F — Reflection Levels (3 Seviye Yansıtma)

### 7.1 Temel Kural: Önce Teslim Al, Sonra İlerle

**Araştırma (MI / Active Listening literatürü):** Her yanıt bir yansıtmayla başlamalı. Bilgi veya soru önce gelmez. Bu "acknowledge before advancing" kuralı empati algısının temel taşı.

```
YANIT YAPISI (değişmez sıra):
1. Yansıtma (SR veya CR) — kullanıcının söylediğini teslim al
2. I adımı — RAG varsa, kullanıcının sahnesine yerleştir
3. E adımı — güçlendir
4. S adımı — seçilen eylemle kapat (soru veya özet)
```

### 7.2 Üç Seviye

**Seviye 1 — Basit Yansıtma (her zaman güvenli)**
```
Kullanıcı: "İşte her şey çok yoğun."
Sistem:    "Yoğunluk üst üste gelmiş."
```
Kural: Kullanıcının kendi kelimesini geri ver. **Sinonim bile kayma yaratır.** (Spillane 2022: %40 empati artışı kelime ayniyet oranıyla doğru orantılı)

**Seviye 2 — Yeniden Çerçeveleme**
```
Kullanıcı: "Hiçbir şeyi doğru yapamıyorum."
Sistem:    "Çok yüksek bir standart taşıyorsun kendin için."
```
Kullanım koşulu: Kullanıcı kendini suçlayan veya mutlakçı dil kullanıyorsa.

**Seviye 3 — Derin Tahmin / ALTI OKUMA (en güçlü)**
```
Kullanıcı: "Arkadaşlarım anlayamıyor zaten."
Sistem:    "Yalnız hissediyorsun bu konuda — görünmez gibi."
```
Kullanım koşulu: Kullanıcı söylemediği ama ima ettiği bir duygu taşıyorsa.  
Kural: "Sanki..." veya "—" ile bağla. İddialı cümle kurma. Yanlışsa kullanıcı düzeltir — bu konuşmayı ilerletir.

### 7.3 Prompts.yaml Talimatı

```
YANSITMA SEVİYESİ:
Seviye 1 — her yanıtta zorunlu temel yansıtma.
Seviye 2 — kullanıcı kendini suçladığında veya mutlakçı konuştuğunda.
Seviye 3 (ALTI OKUMA) — söylenmeyen ama ima edilen duygu netse.
  Kural: "Sanki..." veya "—" ile bağla, iddialı cümle kurma.

HEDEF ORAN: Her 1 soru için en az 2 yansıtma (SR + CR birlikte sayılır).
Yanıt MUTLAKA bir yansıtmayla başlar. Bilgi veya soru önce gelmez.
```

---

## 8. Sistem G — Deepening Signal Handler

### 8.1 Derinleşme Sinyalleri Tablosu

| Kullanıcı Sinyali | Sistem Tepkisi | Prompt Talimatı |
|---|---|---|
| "Bilmiyorum", "böyle işte" | "Bu 'bilmiyorum' bazen 'ne hissettireceğini bilmiyorum'dan geliyor. Hangisine daha yakın?" | Silence → Clarification geçişi |
| Konuyu değiştirme | Kabul et ama not et: "Tabii. Ama az önce söylediğin şeyi bir kenara bırakmadan geçemeyeceğim —" | unexplored_mentions'a ekle |
| "Saçma geliyor ama" | "Saçma değil. Devam et." | Dismissal detection |
| Çok kısa cevap (< 5 kelime) | Basit yansıtma + "Daha var mı?" | Silence sorusu |
| Risk sinyali | Faz bırakılır → Risk Protokolü devreye girer | Bkz. Bölüm 10 |

### 8.2 Sinyal Tespiti (generator.py)

```python
DISMISSAL_SIGNALS = [
    "saçma geliyor", "abartıyorum", "belki de önemli değil",
    "silly but", "sounds stupid", "maybe it doesn't matter"
]

TOPIC_SHIFT_SIGNALS = [
    "neyse", "geçelim", "başka bir şey", "farklı bir konu",
    "anyway", "never mind", "forget it", "different topic"
]

def detect_deepening_signals(user_message: str) -> dict:
    msg = user_message.lower()
    words = msg.split()
    return {
        "dismissal": any(s in msg for s in DISMISSAL_SIGNALS),
        "topic_shift": any(s in msg for s in TOPIC_SHIFT_SIGNALS),
        "very_short": len(words) < 5,
        "unknown": msg.strip() in ["bilmiyorum", "böyle işte", "i don't know", "dunno"],
    }
```

### 8.3 Direnç Yönetimi (MI — Rolling with Resistance)

**Araştırma (MI literatürü):** Direnç görünce asla tartışma, tekrar etme, açıklama yapma. Tek doğru yanıt: basit yansıtma.

```
DİRENÇ SİNYALLERİ: "ama", "anlayamazsın", "işe yaramaz", "zaten denedim"

TESPİT SONRASI:
- YAPMA: Fikrini savun, daha fazla açıkla, ikna et
- YAP: Söylediklerini yansıt + değerlerine dair açık soru

Örnek:
Kullanıcı: "Bu egzersiz fikirlerini boşver, zaten işe yaramıyor"
Sistem: "Daha önce denediğin şeyler sonuç vermemiş — bu yorucu. 
         Sence işe yarayan şey nasıl bir şey olurdu?"
```

---

## 9. Sistem H — Conversation State Engine

### 9.1 Problem

Sistem şu an her turu izole işliyor. Policy Decision Tree'nin, SFBT tetiklerinin ve Gündem Haritalama'nın çalışabilmesi için her turda güncel bir sohbet durumuna (ConvState) ihtiyaç var.

### 9.2 ConvState JSON Şeması (Working Memory)

```python
# core/agents/conversation_state.py — yeni dosya

EMPTY_CONV_STATE = {
    "primary_concern": None,           # Gerçek konu netleşti mi?
    "explored_topics": [],             # Derinleştirilmiş konular
    "unexplored_mentions": [],         # Bahsedildi ama girilmedi
    "change_talk_score": 0.0,          # 0.0–1.0 değişim hazırlığı
    "change_talk_statements": [],      # Son 5 değişim dili ifadesi
    "resistance_detected": False,      # Direnç sinyali
    "sustain_talk_ratio": 0.0,         # Sustain talk oranı
    "distress_level": 0,               # 0-10 sıkıntı tahmini
    "stuck_in_problem": False,         # SFBT İstisna Sorusu tetikleyicisi
    "cannot_envision_change": False,   # SFBT Mucize Sorusu tetikleyicisi
    "session_phase": 1,
    "phase_turn_count": 0,
    "last_dialogue_act": None,         # Son kullanılan MISC kodu
    "agenda_mapped_at_turn": 0,        # Son gündem haritalama turu
}
```

### 9.3 Güncellenme Sıklığı ve Mekanizması

```python
class ConversationStateEngine:

    def should_run_agenda_mapping(self, turn_count: int, state: dict) -> bool:
        return (turn_count - state.get("agenda_mapped_at_turn", 0)) >= 4

    async def update(
        self,
        history: list[dict],
        current_state: dict,
        turn_count: int,
        llm: OllamaClient,
    ) -> dict:
        # Change Talk her turda anlık güncellenir (hafif)
        last_user_msg = next(
            (m["content"] for m in reversed(history) if m["role"] == "user"), ""
        )
        current_state["change_talk_score"] = score_change_talk(history)
        current_state["resistance_detected"] = detect_resistance(last_user_msg)

        # Gündem Haritalama her 4 turda LLM çağrısıyla (ağır)
        if self.should_run_agenda_mapping(turn_count, current_state):
            agenda = await self._run_agenda_mapping(history, llm)
            current_state.update(agenda)
            current_state["agenda_mapped_at_turn"] = turn_count

        return current_state

    async def _run_agenda_mapping(self, history: list[dict], llm) -> dict:
        prompt = render_prompt("agents.agenda_mapper", HISTORY=format_history(history))
        result = llm.generate(prompt, temperature=0.0)
        return json.loads(result.text)
```

### 9.4 Gündem Haritalama Prompt (prompts.yaml'a eklenecek)

```yaml
agenda_mapper: |
  Aşağıdaki sohbeti oku ve JSON olarak yanıtla:

  Sohbet:
  $HISTORY

  {
    "primary_concern": "...",
    "explored_topics": ["...", "..."],
    "unexplored_mentions": ["...", "..."],
    "change_talk_score": 0.0,
    "change_talk_statements": ["..."],
    "resistance_detected": false,
    "sustain_talk_ratio": 0.0,
    "distress_level": 5,
    "stuck_in_problem": false,
    "cannot_envision_change": false
  }

  KURAL: Yalnız JSON çıktısı ver. Açıklama ekleme.
```

### 9.5 Policy Decision Tree Prompt'a Enjeksiyonu

```
[SOHBET DURUMU]
Ana konu: {primary_concern}
Derinleştirilmiş: {explored_topics}
Yarım kalan: {unexplored_mentions}
Değişim hazırlığı: {change_talk_score}/1.0
Direnç: {resistance_detected}
Sıkıntı: {distress_level}/10

[SIRADAM EYLEM]
Policy Tree sonucu: {selected_dialogue_act}
```

### 9.6 Değişecek Dosyalar

| Dosya | Değişiklik |
|---|---|
| `core/agents/conversation_state.py` | Yeni dosya — ConvState şeması, güncelleme, change talk/resistance tespiti |
| `config/prompts.yaml` | `agenda_mapper` prompt'u eklenir |
| `services/assistant.py` | `handle_message` içine ConvState yükleme/güncelleme eklenir |
| `core/generation/generator.py` | ConvState, Policy Decision Tree'ye girdi olarak verilir |

---

## 10. Risk Protokolü — Tüm Fazlardan Önce Gelir

Risk tespitinde seans fazı askıya alınır:

```
TR:
"Şu an çok ağır bir şey taşıdığın anlaşılıyor. Yalnız değilsin.
 Hemen ulaşabileceğin destek:
 Acil için 112, ruh sağlığı için ALO 182, şiddet durumunda ALO 183.
 Mümkünse şu an güvendiğin birine yakın ol."

EN:
"It sounds like you're carrying something really heavy right now.
 You're not alone.
 If you need immediate support: 988 (Suicide & Crisis Lifeline),
 or 112 for emergency services in Turkey.
 If you can, please be near someone you trust right now."
```

**Risk sonrası kural:** Bu mesajın ardından sistem normal konuşmaya dönmez. Seans orada kapanır. `session.status = "crisis_closed"` yazılır.

---

## 11. Micro-Eylem Planı Kütüphanesi

Faz 3'te LLM bu kütüphaneden seçim yapar. "Ödev" veya "homework" kelimesi hiçbir zaman kullanılmaz.

```yaml
micro_actions:
  stress_burnout:
    - "İşin bittiği anı fiziksel olarak işaretle — bilgisayarı kapat, masandan kalk."

  sleep_difficulty:
    - "Yatmadan 30 dakika önce telefonu başka bir odaya bırak — sadece 3 gece dene."

  rumination:
    - "O döngüsel düşünce geldiğinde, onu kağıda yaz ve kapağını kapat."

  low_motivation:
    - "Bu hafta sadece 1 şeyi tamamla — büyüklüğü önemli değil."

  relationship_stress:
    - "Bu hafta o kişiyle ilgili bir şeyi değiştirmeye çalışma. Sadece ne hissettiğini not et."

  self_awareness:
    - "Gün içinde kendini nasıl hissettiğini 3 kelimeyle not et — sabah, öğlen, akşam."
```

---

## 12. Seans Kartı (Faz 4 Çıktısı)

```
┌─────────────────────────────────────────────────────────┐
│  SEANS KARTI                                            │
│  Tarih: {DD Ay YYYY}                                    │
├─────────────────────────────────────────────────────────┤
│  Bugünkü konu:     {session.topic}                      │
│  Ruh hali:         {mood_score_start}/10 → {mood_end}/10│
│  Bugünkü içgörü:  "{session.user_insight}"              │
│  Bu haftaki plan:  {session.action_plan}                │
│  Sonraki seansta:  {session.bridge_note}                │
└─────────────────────────────────────────────────────────┘
```

**Kural:** `user_insight` alanı SADECE kullanıcının kendi sözlerinden alınır.

---

## 13. Dil ve Tempo Adaptasyonu

### 13.1 Dil Adaptasyonu

```
DİL ADAPTASYONU:
Kullanıcı kısa ve resmi yazıyorsa   → sistem kısa ve temiz yanıt verir
Kullanıcı uzun ve dökümlü yazıyorsa → daha sıcak, daha az yapılandırılmış
Kullanıcı çok üzgün / ağır içerik  → yavaş tempo, kısa cümleler, az bilgi
Kullanıcı hafif ve şakacı           → biraz daha hafif ton
Türkçe girdi                        → Türkçe yanıt, "sen" hitabı
İngilizce girdi                     → İngilizce yanıt
```

### 13.2 PACE TUTMA — Ağır İçerik Tespiti

```python
HEAVY_CONTENT_SIGNALS = [
    "intihar", "kendime zarar", "artık dayanamıyorum", "bitmesini istiyorum",
    "suicide", "harm myself", "can't take it anymore", "end it",
    "ağladım", "çok yoruldum", "boş geliyor", "anlamsız"
]
```

Tespit edilince:
```
PACE: Bu mesaj ağır içerik taşıyor.
Yanıtta bilgi verme. Daha az cümle. Daha fazla alan bırak.
Sadece yansıt ve tek soru sor.
```

---

## 14. Genel Yanıt Kuralları — Tüm Fazlar

### 14.1 Yasak Açılış İfadeleri

| Yasak | Neden |
|---|---|
| "Tabii ki anlıyorum." | Chatbot kalıbı |
| "Elbette / Kesinlikle / Harika" | Mekanik onay |
| "Bu çok zor, gerçekten cesursun!" | Sahte övgü |
| "Seni tamamen anlıyorum." | Sistem anlayamaz, sadece yansıtabilir |
| "Her şey yoluna girecek." | Boş güvence, klinik açıdan zararlı |
| "Bu anksiyete / depresyon belirtisi." | Tanı dili — kesinlikle yasak |
| "Yapmalısın / Etmelisin." | Direktif dil |

### 14.2 Affirmation Kuralı (Gerçek Güç Tanıma)

```
YASAK (sahte övgü):
❌ "Bunu benimle paylaştığın için çok cesursun!"
❌ "Harika bir farkındalık!"

DOĞRU (gerçek güç tanıma):
✅ "Bunu bu kadar süre taşıman ve hâlâ buraya gelmek istemene bakılırsa
    içinde ciddi bir dayanıklılık var."
✅ "Bu konuyu bu kadar net ifade etmek kolay değil — bunu yapabiliyorsun."

KURAL: Her seansta maksimum 1-2 affirmation.
```

### 14.3 Evrensel Kurallar (Araştırmadan)

```
KURAL 1 — Tek Soru: Aynı turda asla iki soru sorma.
           (MI araştırması: çift soru = sorgu hissi, empati yok)

KURAL 2 — 2:1 Oranı: Her 1 soru için en az 2 yansıtma.
           (Spillane 2022: oran bozulduğunda sistem chatbot gibi hissettiriyor)

KURAL 3 — Önce Teslim Al: Her yanıt yansıtmayla başlar.
           Bilgi veya soru önce gelmez.
           (Active listening araştırması: acknowledge before advancing)

KURAL 4 — CoS Protokolü: Yanıt üretmeden önce diyalog eylemini seç.
           (PsyMix 2024: eylem seçimi %35 daha az jenerik empati)

KURAL 5 — Format Yasağı: Bullet point, bold, başlık, kaynak atıfı yok.
```

### 14.4 Cümle Limitleri

| Faz | Min | Max |
|---|---|---|
| Faz 1 — Açılış | 1 | 3 |
| Faz 2 — Keşif | 3 | 5 |
| Faz 3 — İçgörü & Eylem | 2 | 5 |
| Faz 4 — Kapanış | 1 | 3 |

---

## 15. Değişecek Dosyalar — Tam Liste

### 15.1 Backend Değişiklikleri

| Dosya | Değişiklik | Öncelik |
|---|---|---|
| `config/prompts.yaml` | answer_system_rules + CoS talimatı + question_pool + agenda_mapper + micro_actions | Kritik |
| `core/agents/memory_agent.py` | Structured JSON çıktısı, parse, merge | Kritik |
| `core/generation/generator.py` | `_build_prompt()` + Policy Decision Tree + ConvState entegrasyonu | Kritik |
| `services/assistant.py` | ConvState yükleme/güncelleme + yeni sinyaller | Kritik |
| `models/sql/models.py` | Phase fields eklenir (`ChatSession`) | Önemli |
| `services/session_store.py` | Phase güncelleme, change talk tespiti | Önemli |
| `core/retrieval/nuggetizer.py` | Sahne-odaklı prompt veya bypass | Önemli |
| `core/agents/supervisor.py` | Deepening sinyalleri + forbidden openings güncelleme | Önemli |
| `services/flows/session_card.py` | Seans kartı oluşturma | İkincil |

### 15.2 Yeni Dosyalar

| Dosya | İçerik |
|---|---|
| `core/agents/conversation_state.py` | ConvState şeması, güncelleyici, change talk/resistance tespiti, Policy Decision Tree |
| `core/agents/pattern_detector.py` | Within-session + cross-session pattern + bilişsel çarpıtma tespiti |
| `services/bridge.py` | Bridge note oluşturma ve yönetimi |
| `scripts/migrate_phase_fields.py` | Mevcut DB için ALTER TABLE migration |

---

## 16. Uygulama Sırası

```
ADIM 1 — prompts.yaml (2 saat)
  Değişiklik: answer_system_rules → CoS talimatı + dinamik değişkenler.
              memory_agent → structured JSON çıktısı.
              question_pool + scale soruları + micro_actions + phase_instructions.
              agenda_mapper prompt'u eklenir.
  Risk: Düşük.

ADIM 2 — memory_agent.py (2 saat)
  Değişiklik: summarize_interaction() → structured JSON döner.
              _parse() → JSON veya legacy text'i handle eder.
  Risk: Orta. Mevcut memory verisi migrate edilmeli.

ADIM 3 — conversation_state.py (3 saat) [YENİ]
  Değişiklik: ConvState şeması, ConversationStateEngine sınıfı.
              Change talk scorer, resistance detector.
              Agenda mapping LLM çağrısı.
  Risk: Düşük. Yeni dosya.

ADIM 4 — generator.py (3 saat)
  Değişiklik: ConvState ve Policy Decision Tree entegrasyonu.
              Structured memory parse + profil tam enjeksiyonu.
              RAG sahne enjeksiyonu (raw chunk).
              CoS prompt protokolü.
  Risk: Orta. Prompt uzunluğu artar → latency monitör.

ADIM 5 — assistant.py (3 saat)
  Değişiklik: ConvState yükleme/güncelleme (her turda).
              _count_session_turns(), _load_session_history().
              _build_bridge_note(), bridge note generator'a aktarımı.
  Risk: Düşük. Ek DB sorgular → latency monitör.

ADIM 6 — pattern_detector.py + bridge.py (2 saat) [YENİ]
  Değişiklik: Yeni modüller oluşturulur.
  Risk: Düşük. Yeni dosyalar.

ADIM 7 — models.py + migration (3 saat)
  Değişiklik: ChatSession'a phase alanları eklenir.
              ALTER TABLE migration scripti.
  Risk: Yüksek. Backup alınmalı.

ADIM 8 — session_store.py + session_card.py (2 saat)
  Değişiklik: append_session_turn() → phase + change talk günceller.
              session_card.py → Faz 4'te kart oluşturur.
  Risk: Düşük.
```

---

## 17. Test Senaryoları

### Sistem A — Bellek
```
Seans 1: "boşuna uğraşıyorum" → user_vocabulary'e eklendi
Seans 2: Sistem "boşuna" kelimesiyle konuşuyor, adını biliyor
```

### Sistem B — Policy Decision Tree + CoS
```
ConvState: primary_concern=None, turn_count=1
Beklenti: OQ seçildi → "Bugün seni en çok ne meşgul ediyor?"

ConvState: resistance_detected=True
Beklenti: SR seçildi → "Daha önce denediğin şeyler işe yaramış gibi hissettiriyor."

ConvState: change_talk_score=0.7
Beklenti: OQ seçildi → "Bunu biraz daha anlat — nasıl görünürdü?"
```

### Sistem B — SFBT
```
ConvState: stuck_in_problem=True
Beklenti: İstisna sorusu → "Bu böyle hissetmediğin bir gün oldu mu?"

ConvState: session_phase=3
Beklenti: Ölçek sorusu → "0'dan 10'a, şu an neredesin?"
```

### Sistem C — RAG Sahne Enjeksiyonu
```
Kullanıcı: "Gece 3'te uyanıyorum kafam durmuyor"
Beklenti: "O gece 3'teki uyanış — zihin hâlâ kapanmamış bir şeyi çözmeye çalışıyor gibi."
Yasak:    "Kronik stres uyku kalitesini etkiler."
```

### Sistem D — Change Talk ile Faz Geçişi
```
Kullanıcı "yapabilirim", "deneyeceğim", "istiyorum" içeren 3 mesaj yazdı
Beklenti: change_talk_score > 0.6 → session_phase = 3
```

### Sistem F — Refleksiyon Seviyesi
```
"Arkadaşlarım anlayamıyor zaten" → Seviye 3
Beklenti: "Yalnız hissediyorsun bu konuda — görünmez gibi."
Yasak:    "Anlıyorum, bu çok zor."
```

### Sistem H — ConvState Güncellemesi
```
Turn 4: Kullanıcı "annem" ve "iş" konusunu geçti ama girilmedi
Beklenti: unexplored_mentions = ["annem", "iş durumu"]
Turn 5: Policy Tree → "Daha önce annemden bahsetmiştin — oraya dönebilir miyiz?"
```

---

## 18. Risk ve Dikkat Edilecekler

| Risk | Açıklama | Önlem |
|---|---|---|
| LLM latency | Prompt uzunluğu artar | Boş ConvState alanları prompt'tan çıkarılır |
| Agenda mapping latency | Her 4 turda ek LLM çağrısı | Arka planda çalıştır, sonraki tura etkili |
| DB migration | Phase fields mevcut DB'yi etkiler | Backup + ayrı test DB |
| Memory JSON bozulması | LLM geçersiz JSON dönebilir | `_parse()` her zaman fallback schema döner |
| Change talk false positive | Tek kelime match yanıltıcı olabilir | 2+ kategori veya 0.6+ skor eşiği |
| Policy Tree override | Kullanıcı direnci öngörülmeden direnç tespit edilirse | Sustain talk ratio da kontrol edilmeli |
| SFBT erken tetikleme | Mucize sorusu yanlış zamanda | Yalnız Faz 2'nin ortasında, distress < 7 iken |
| Reflection Level 3 hata | ALTI OKUMA yanlış tahmin | "Sanki..." ile hedging zorunlu |
| Bağımlılık riski | Uzun dönem AI kullanımı bağlılık artırabilir | Seans sonu sağlıklı sınır mesajı |

---

## 19. Performans SLA'ları

| Bileşen | Hedef Latency (p95) | Mevcut (Tahmini) | Ölçüm Yöntemi |
|---|---|---|---|
| Keyword Safety | < 1ms | ~0.5ms | Her yanıtta logla |
| ConvState Light | < 5ms | ~2ms | Her yanıtta logla |
| Pattern Detection | < 5ms | ~1ms | Her yanıtta logla |
| Orchestrator (LLM) | < 4s | ~3s | assistant.py DEBUG log |
| Dialogue Policy | < 1ms | ~0.3ms | Her yanıtta logla |
| RAG Pipeline | < 500ms | ~200ms | assistant.py DEBUG log |
| Answer Generator (LLM) | < 8s | ~5s | assistant.py DEBUG log |
| Total Sync Response | < 12s p95 | ~8s | HTTP response time |
| Memory Agent (async) | < 5s | ~2s | Background task log |
| Agenda Mapping (async) | < 6s | ~3s | Background task log |

**Alert Eşikleri:**
- Total response > 15s → Alert
- LLM unavailable → Fallback mesajı, alert
- Memory JSON parse fail rate > 5% → Alert
- ConvState update fail → Log warning, devam et (non-blocking)

---

## 20. Gözlemlenebilirlik (Observability)

Her bileşen aşağıdaki log seviyelerine göre çıktı üretir. Tüm loglar yapısal JSON formatında olmalıdır.

### 20.1 Log Seviyeleri ve İçerikleri

**DEBUG — Geliştirme ve optimizasyon için:**

| Bileşen | Loglanacak Veri |
|---|---|
| ConvState Light | `turn_count`, `change_talk_score`, `resistance_detected`, süre (ms) |
| PatternDetector | Tespit edilen kelimeler ve tekrar sayıları, çarpıtma türü (varsa) |
| DialoguePolicyAgent | Seçilen MISC kodu, karar ağacındaki dal, girdi ConvState özeti |
| RAG Pipeline | `top_chunk_score`, `threshold`, `injected: true/false`, chunk ID |
| AnswerGenerator | Seçilen CoS adımı, prompt uzunluğu (token), yanıt süresi (ms) |
| Memory Agent | JSON diff (önceki vs sonraki), başarı/hata durumu |

**INFO — Operasyonel izleme için:**

| Bileşen | Loglanacak Veri |
|---|---|
| Her yanıt turu | `session_id`, `turn_count`, `session_phase`, `selected_dialogue_act`, toplam yanıt süresi |
| Faz geçişi | `session_id`, önceki faz, yeni faz, geçiş tetikleyicisi |
| Gündem haritalama | `session_id`, haritalama turu, `primary_concern` (varsa) |
| Risk tespiti | `session_id`, tetikleyen sinyal, `session.status` güncellenmesi |
| Seans başlangıcı/bitişi | `session_id`, `user_id`, ilk/son tur zamanı |

**WARNING — Dikkat gerektiren durumlar (alarm eşiği yok, izleme gerekli):**

| Durum | Log İçeriği |
|---|---|
| Memory JSON parse hatası | `session_id`, ham LLM çıktısı, fallback schema kullanıldı |
| ConvState güncelleme başarısız | `session_id`, hata mesajı, devam edildi (non-blocking) |
| RAG skoru eşiğin altında | `session_id`, skor, I adımı atlandı |
| Yanıt süresi > 10s | `session_id`, bileşen bazında süre dökümü |
| Agenda mapping JSON parse hatası | `session_id`, ham çıktı, önceki ConvState korundu |

**ERROR — Sistem işlevini etkileyen hatalar (alert gönderilir):**

| Durum | Log İçeriği |
|---|---|
| LLM erişilemez | `session_id`, denenen endpoint, hata kodu, fallback mesaj gönderildi |
| Total response > 15s | `session_id`, tüm bileşen süreleri, kullanıcı mesajı (hash) |
| Memory JSON parse fail rate > 5% son 100 istekte | Oran, zaman penceresi, son 3 ham çıktı örneği |
| DB yazma hatası (memory / session) | `session_id`, hata detayı, kullanıcı verisi kaybı riski |

### 20.2 Örnek Yapısal Log Çıktısı

```json
{
  "level": "INFO",
  "timestamp": "2026-05-17T14:32:01.421Z",
  "component": "answer_generator",
  "session_id": "sess_abc123",
  "turn_count": 5,
  "session_phase": 2,
  "selected_dialogue_act": "CR",
  "rag_injected": true,
  "rag_chunk_score": 0.81,
  "response_time_ms": 4820,
  "prompt_tokens": 1247
}
```

### 20.3 Metrik Toplama

Her yanıt turunda şu sayaçlar güncellenir:

```
calma_response_time_ms          — histogram, p50/p95/p99
calma_dialogue_act_counts       — counter, etiket: act_type
calma_phase_transitions_total   — counter, etiket: from_phase, to_phase
calma_rag_injection_rate        — gauge, injected/total oranı
calma_memory_parse_errors_total — counter
calma_crisis_sessions_total     — counter
```

---

## 21. Sözlük (Glossary)

Bu bölüm dokümanda geçen teknik terimlerin tanımlarını içerir.

| Terim | Tanım |
|---|---|
| **AF (Affirmation)** | MISC diyalog eylem kodu. Kullanıcının gerçek çabasını, dayanıklılığını veya farkındalığını sahici biçimde tanıma. Sahte övgü ("çok cesursun!") değil, gözlemlenebilir güce işaret etme ("bunu bu kadar süre taşıyorsun"). |
| **CBT (Cognitive Behavioral Therapy)** | Bilişsel Davranışçı Terapi. Beck (1979) tarafından geliştirilen, düşünce-duygu-davranış döngüsünü hedef alan, araştırma destekli psikoterapi yaklaşımı. |
| **Change Talk** | MI'da kullanıcının değişme isteğini, yeterliliğini, nedenini, ihtiyacını veya kararlılığını dile getirdiği ifadeler. DARNC kategorileriyle sınıflandırılır. |
| **CoS (Chain-of-Strategy)** | Yanıt üretim protokolü. LLM'in yanıt yazmadan önce diyalog eylemini seçmesini zorunlu kılan adım-adım talimat yapısı. PsyMix (2024) araştırmasından türetilmiştir. |
| **Complex Reflection — CR** | MISC diyalog eylem kodu. Kullanıcının söylemediği ama ima ettiği duyguyu veya anlamı yansıtma. Seviye 3 (Derin Yansıtma) olarak da bilinir. |
| **ConvState** | Conversation State. Her seans turu sonunda güncellenen çalışma belleği (working memory). `primary_concern`, `change_talk_score`, `session_phase` gibi alanları içerir. |
| **DARNC** | Change Talk'ın 5 alt kategorisi: Desire (istek), Ability (yetenek), Reason (neden), Need (ihtiyaç), Commitment (kararlılık). MI araştırmasının standardı. |
| **Dialogue Act** | Bir yanıtın işlevsel türü. "Bu yanıt ne yapıyor?" sorusunun cevabı: soru sormak (OQ), yansıtmak (SR/CR), özetlemek (SU), güçlendirmek (AF), bilgi vermek (GI). |
| **Lexical Mirroring** | Kullanıcının kendi kelimelerini ve metaforlarını yanıtta birebir kullanma tekniği. Spillane (2022): kelime ayniyet oranı empati algısıyla doğru orantılı. |
| **MI (Motivational Interviewing)** | Motivasyonel Görüşme. Miller & Rollnick tarafından geliştirilen, direnç azaltma ve değişim motivasyonunu artırmayı hedefleyen işbirlikçi konuşma stili. |
| **MISC** | Motivational Interviewing Skill Code. MI araştırmasında diyalog eylemlerini kodlamak için kullanılan standart taksonomi. OQ, SR, CR, AF, SU, GI, FA kodlarını içerir. |
| **OARS** | MI'ın dört temel becerisi: Open Questions (açık sorular), Affirmations (güçlendirme), Reflections (yansıtmalar), Summaries (özetler). |
| **Open Question — OQ** | MISC diyalog eylem kodu. Evet/hayır ile cevaplanamayan, kullanıcıyı genişletmeye davet eden soru. "Ne hissediyorsun?" "Nasıl görünürdü?" |
| **Policy Decision Tree** | `DialoguePolicyAgent` içindeki kural tabanlı karar ağacı. ConvState'e bakarak bir sonraki MISC eylemini seçer. LLM içermez. |
| **SFBT (Solution-Focused Brief Therapy)** | Çözüm Odaklı Kısa Süreli Terapi. de Shazer tarafından geliştirilen, probleme değil çözüme ve güçlü yönlere odaklanan terapi yaklaşımı. Üç temel teknik: İstisna Sorusu, Ölçek Sorusu, Mucize Sorusu. |
| **Simple Reflection — SR** | MISC diyalog eylem kodu. Kullanıcının söylediğini kendi kelimeleriyle geri yansıtma. Seviye 1 (Basit Yansıtma). Direnç görüldüğünde birincil strateji. |
| **Summary — SU** | MISC diyalog eylem kodu. 3+ konu konuşulduğunda bağlantı kurmak için kullanılan özet yanıt. Genellikle "Bunlara bakınca ne hissediyorsun?" ile biter. |
| **Sustain Talk** | MI'da kullanıcının değişime karşı direncini, mevcut durumu sürdürme isteğini dile getirdiği ifadeler. "Ama zor", "Olmaz", "Zaten hep böyle." Change talk'un karşıtı. |
| **VAD** | Valence-Arousal-Dominance. Duygu durumu modeli. Calma sisteminde doğrudan kullanılmıyor; araştırma referansı olarak geçiyor. |
| **VIE-SR** | Calma'nın yanıt yapısı: Validate (teslim al) → Inform (bilgilendir, RAG) → Empower (güçlendir) → Suggest/Reflect (eylemle kapat). |

---

> **Bu plan** Calma'nın chatbot hissinden psikolog hissine geçişini tarif eder.  
> Adım 1-6 DB değişikliği gerektirmez, bağımsız deploy edilebilir.  
> Adım 7 en riskli adımdır, en sona bırakılır.  
> Sistem H (ConvState) tüm diğer sistemlerin çalışma kalitesini belirleyen omurgadır.  
> Bu doküman `prompts.yaml`, `generator.py`, `memory_agent.py`, `conversation_state.py` ve `assistant.py`'nin anayasasıdır.

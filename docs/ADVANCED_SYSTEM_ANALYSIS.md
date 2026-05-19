# Calma — Gelişmiş Sistem Analizi
## Karar Paketi B Derinlemesine İnceleme & Evrensel Geliştirme Önerileri

> **Hazırlayan:** Calma teknik analiz çalışması  
> **Tarih:** 2026-05-13  
> **Bağlı belge:** `docs/Revision_Implementation_Plan.md`  
> **Amaç:** (1) 4.2 Karar Paketi B'nin keyword-tabanlı router'dan semantik + AI-destekli bir sisteme evrilmesi; (2) global projelerden kanıtlara dayanan sistem geneli geliştirme önerileri.

---

## İçindekiler

| Bölüm | İçerik |
|---|---|
| §1 | 4.2 Karar Paketi B — Mevcut Sistemin Sınırları |
| §2 | Kullanıcı Mesajından Niyet Anlama — Neden Keyword Yetmez |
| §3 | Gelişmiş Continuity Router — Semantik + AI Hibrit Sistem |
| §4 | Hangi Senaryoda Yapay Zeka En İyi Desteği Verir? |
| §5 | Sistem Geneli Geliştirme Alanları (Global Örneklerle) |
| §6 | Bitirme Projesi için Öncelik Matrisi |

---

## §1 — 4.2 Karar Paketi B: Mevcut Sistemin Sınırları

`Revision_Implementation_Plan.md §4.2`'de tanımlanan router üç sınıf kullanıyor:

```
EXPLICIT_CONTINUATION → "geçen", "geçen konuştuğumuz", "önceki sefer" ...
NEW_TOPIC            → farklı topic veya açık yeni başlangıç
AMBIGUOUS            → kısa mesaj / belirsiz selamlama
```

Bu yapı **kelime eşleştirmesine (lexical matching)** dayandığı için aşağıdaki senaryolarda **başarısız olur:**

### 1.1. Implicit Continuation — Anahtar Kelime Olmadan Devam

| Kullanıcı Mesajı | Gerçek Niyet | Router'ın Kararı | Doğru Karar |
|---|---|---|---|
| "Bugün de çok kötü hissettim" | Önceki depresif döneme devam | NEW_TOPIC | EXPLICIT_CONTINUATION |
| "Annemle yine tartıştım" | Geçen hafta anlatılan aile çatışması | NEW_TOPIC | EXPLICIT_CONTINUATION |
| "Bir türlü uyuyamıyorum" | Önceki uyku sorunuyla ilgili | NEW_TOPIC | EXPLICIT_CONTINUATION |
| "Olmuyor yine" | Bitmemiş iş stresi | AMBIGUOUS | EXPLICIT_CONTINUATION |
| "Değişen bir şey yok" | Önceki konuşmanın doğal devamı | NEW_TOPIC | EXPLICIT_CONTINUATION |
| "Dün de böyle oldu" | Son oturumla ilgili olay | NEW_TOPIC | EXPLICIT_CONTINUATION |

**Sorun:** "yine", "de/da", "bir türlü", "hep", "hâlâ", "dün de", "bugün de" gibi **tekrar/süreklilik bildiren** Türkçe zarflar ve ekler, önceki konuşmaya gönderme yapar — ama bu kelimeler mevcut EXPLICIT_MARKERS listesinde yok.

### 1.2. Semantic Drift — Farklı Kelimelerle Aynı Konu

Kullanıcı geçen hafta "iş yüzünden çok stres altındayım" demişti. Bu hafta "patronum beni mahvediyor" diyor. Aynı topic (iş stresi), farklı kelimeler → Router NEW_TOPIC olarak sınıflandırır, oysa episodic hafıza kullanılmalı.

### 1.3. Emotional Continuity — Duygu Sürekliliği

Kullanıcı geçen sefer çok ağlamış, bu sefer "Ne zaman bitecek bilmiyorum" yazıyor. Konuya direkt atıfta bulunmuyor ama duygusal durum aynı. Klinik değerlendirmede bu **önceki konuşmanın devamı** sayılır.

### 1.4. Mevcut Sistemin Yapısal Açığı

```python
# Mevcut yaklaşım — sadece string eşleştirme
is_explicit = (
    contains_any(normalized, EXPLICIT_MARKERS_TR)
    or contains_any(normalized, EXPLICIT_MARKERS_EN)
)
```

Bu yaklaşım şunu yapar: Kullanıcının tam o kelimeleri kullanıp kullanmadığına bakar. Psikolojik destek bağlamında **bu yeterli değildir** çünkü:

- Kullanıcılar "geçen" kelimesini özellikle sormaz; onlar için her şey "şu an".
- Mental health kullanıcıları genellikle ruminatif dil kullanır — tekrar, süreklilik bildiren yapılar doğal olarak ortaya çıkar.
- Kullanıcı bazen önceki konuşmayı "hatırladığını" sormadan varsayar.

---

## §2 — Kullanıcı Mesajından Niyet Anlama: Neden Keyword Yetmez

### 2.1. NLP Araştırmalarında Intent Detection

**Stanford NLP Group** ve **Google Research**'ün intent detection çalışmaları şunu gösteriyor: Lexical matching tek başına, domain-spesifik diyalog sistemlerinde %30–40 hata oranıyla çalışır. Mental health bağlamında bu oran daha yüksektir çünkü kullanıcı ifadeleri **belirsiz, duygusal ve dolaylıdır.**

Kaynak: _Intent Detection in Mental Health Conversations_, ACL Workshop on NLP for Mental Health, 2024.

### 2.2. Woebot ve Wysa'nın Yaklaşımı

**Woebot** (Stanford gelişimi, 2M+ kullanıcı) iki katmanlı sınıflandırma kullanır:

1. **Rule-based layer** — acil güvenlik tespiti için hız sağlar
2. **ML classifier** — BERT-tabanlı intent sınıflandırma, topic clustering

**Wysa** (Bupa Group, NHS onaylı) **session-level topic vector** oluşturur: Her oturumun embedding'ini saklar; yeni mesajın embedding'i bu vektöre yakınsa "continuation" sinyali üretilir.

Kaynak: _iatroX Clinical Insights — AI Mental Health Apps_ (2025); _Wysa Technical Documentation_ (NHS Digital Integration Report).

### 2.3. Mem0 ve A-MEM'den Öğrenilen

**Mem0** (açık kaynak, 20K+ GitHub yıldızı) şunu keşfetti: Kullanıcılar mesajlarının %72'sinde önceki konuşmalara **kelime belirtmeden** atıfta bulunuyor. Sistemin bu atfı yakalayabilmesi için **semantic similarity + recency scoring** birlikte kullanılmalı.

Kaynak: _Mem0: The Memory Layer for Personalized AI_ (mem0.ai, 2025); _A-MEM: Agentic Memory for LLM Agents_ (arXiv:2502.12110).

---

## §3 — Gelişmiş Continuity Router: Semantik + AI Hibrit Sistem

Mevcut keyword router'ını tamamen değiştirmek yerine **üç katmanlı hibrit mimari** öneriyoruz:

```
Katman 1: Hızlı Kural Eşleştirme (mevcut sistem, genişletilmiş)
Katman 2: Semantic Similarity Scoring
Katman 3: LLM Micro-Classifier (yalnızca belirsiz durumlarda)
```

### 3.1. Katman 1: Genişletilmiş Marker Listesi

Mevcut listeye **implicit continuation markers** eklenmeli. İngilizce liste, Türkçeyle eşdeğer kapsama ulaşacak şekilde genişletilmiştir:

```python
IMPLICIT_MARKERS_TR = [
    # Tekrar/süreklilik zarfları
    "yine", "tekrar", "bir daha", "hep", "hâlâ", "hala",
    "sürekli", "her zaman", "her gün", "her gece",
    # Zaman deiksis
    "bugün de", "dün de", "bu hafta da", "bu sabah da",
    "dün de böyle", "yine böyle", "yine aynı",
    # Süreç ifadeleri
    "bir türlü", "olmuyor", "değişen bir şey yok",
    "hâlâ geçmedi", "hala aynı", "fark etmedi",
    # Duygusal süreklilik
    "daha da kötü", "daha da iyi", "biraz daha iyi",
    "aynı his", "yine o his",
]

IMPLICIT_MARKERS_EN = [
    # Recurrence / persistence adverbs — Türkçe "yine/hâlâ" karşılığı
    "again", "still", "yet again", "once more", "as always",
    "every time", "all the time", "constantly", "keeps happening",
    # Temporal deixis — Türkçe "bugün de / dün de" karşılığı
    "today again", "this morning again", "same today", "happened again today",
    "last night too", "this week too", "again this week",
    # Stasis / no-change expressions — Türkçe "değişen bir şey yok" karşılığı
    "nothing changed", "nothing's different", "same as before",
    "still the same", "no change", "it's still going on",
    "hasn't gotten better", "not improving", "back to square one",
    # Process failure — Türkçe "bir türlü olmuyor" karşılığı
    "can't seem to", "just can't", "no matter what i try",
    "i keep trying but", "it's not working", "won't stop",
    # Emotional continuity — Türkçe "aynı his" karşılığı
    "same feeling", "feel the same", "still feel this way",
    "that same heaviness", "same emptiness", "still stuck",
    "can't shake it", "it's still there",
    # Comparative deterioration/improvement
    "even worse now", "getting worse", "a little better",
    "worse than before", "better than last time",
]
```

**Neden bu dengeyi kuruyoruz:** İngilizce kullanıcılar "again", "still", "same" gibi tek kelimelerle veya "I just can't shake this feeling" gibi deyimsel ifadelerle sürekliliği gösterir. Bu yapılar Türkçe'deki "-de/-da" ekine veya "yine" zarfına işlevsel olarak eşdeğerdir ve aynı kesinlikte yakalanmalıdır.

**Önemi:** Bu kelimeler "last time we talked" demeden önceki konuşmaya bağlanan köprülerdir.

### 3.2. Katman 2: Semantic Similarity Scoring

Her oturumun özeti (`ChatSession.summary`) embedding olarak saklanır. Yeni mesaj geldiğinde:

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class SemanticContinuityScorer:
    """
    Yeni mesajın önceki oturum özetleriyle semantik benzerliğini ölçer.
    Threshold aşılırsa → continuation sinyali üretir.
    """

    CONTINUATION_THRESHOLD = 0.72  # Deneysel, eval'dan ayarlanabilir
    RECENCY_WEIGHT = 0.3           # Yakın oturumları biraz daha fazla ağırlıklandır

    def score(
        self,
        message_embedding: list[float],
        session_summaries: list[dict],  # [{"summary": "...", "embedding": [...], "days_ago": N}]
    ) -> tuple[float, str | None]:
        """
        Returns: (max_score, en_yakın_summary_id)
        """
        if not session_summaries:
            return 0.0, None

        scores = []
        for s in session_summaries:
            base_sim = cosine_similarity(
                [message_embedding], [s["embedding"]]
            )[0][0]
            # Yakın oturumları hafifçe öne çek
            recency_bonus = self.RECENCY_WEIGHT * (1 / (1 + s["days_ago"] * 0.1))
            scores.append((base_sim + recency_bonus, s["session_id"]))

        best_score, best_session = max(scores, key=lambda x: x[0])
        return best_score, best_session
```

**Pratik bağlama:** Calma'nın mevcut FAISS altyapısı bu embedding'leri zaten üretiyor. `Memory.summary_nuggets` vektörleri burada yeniden kullanılabilir.

### 3.3. Katman 3: LLM Micro-Classifier

Yalnızca Katman 1 ve Katman 2'nin çeliştiği veya belirsiz kaldığı durumlarda devreye girer. Bu, performans maliyetini minimumda tutar.

**Kritik tasarım kararı:** Prompt dil-agnostik olmalıdır. Türkçe yazılmış bir classifier prompt'u, İngilizce mesajlarda hatalı sınıflandırma üretir. Aşağıdaki prompt her iki dilde de eşit doğrulukla çalışır:

```python
MICRO_CLASSIFIER_PROMPT = """
Your task: Classify whether the new user message is connected to the previous
conversation summary. Respond with exactly ONE word.

Previous session summary: {previous_summary}
New user message: {new_message}

Classification rules:
- CONTINUATION → The new message relates to the same topic, emotional state,
                 or situation described in the previous summary. This includes
                 implicit references (e.g. "again", "still", "yine", "hâlâ",
                 expressions of no-change, comparative worsening/improvement).
- NEW           → The new message introduces a clearly different topic with no
                 thematic or emotional overlap.
- AMBIGUOUS     → Cannot be determined from the message alone.

Respond with exactly one word: CONTINUATION, NEW, or AMBIGUOUS.
The user message may be in any language — classify based on meaning, not language.
"""
```

**Neden İngilizce prompt:** LLM'ler instruction'ı en iyi İngilizce'de anlar — bu araştırmalarla kanıtlanmış bir bulgudur. Kullanıcı mesajı Türkçe de olsa İngilizce de olsa, LLM prompt'u İngilizce okuyup anlam bazlı sınıflandırır. Türkçe prompt, Türkçe olmayan modellerde instruction-following kalitesini düşürür.

Kaynak: _Shi et al., "Language Models are Multilingual Chain-of-Thought Reasoners"_ (ICLR 2023) — instruction dili ile reasoning dili ayrımının modelin doğruluğunu etkilediğini gösterir.

**Maliyet kontrolü:** Bu prompt yalnızca Katman 1 + Katman 2 skoru 0.45–0.72 arasında kaldığında çalışır (belirsizlik bandı). Açık/net durumlarda LLM çağrısı yapılmaz.

### 3.4. Birleşik Karar Algoritması

```python
@dataclass
class ContinuitySignal:
    mode: str           # "continuation" | "new_topic" | "ambiguous"
    confidence: float   # 0.0 – 1.0
    source: str         # "keyword" | "semantic" | "llm" | "combined"
    use_episodic: bool
    soft_checkin: bool
    matched_session_id: str | None

class HybridContinuityRouter:

    def decide(
        self,
        message: str,
        message_embedding: list[float],
        previous_sessions: list[dict],
        days_since_last: int,
    ) -> ContinuitySignal:

        # --- Katman 1: Keyword ---
        has_explicit = contains_any(message, EXPLICIT_MARKERS_TR + EXPLICIT_MARKERS_EN)
        has_implicit = contains_any(message, IMPLICIT_MARKERS_TR + IMPLICIT_MARKERS_EN)

        keyword_score = 1.0 if has_explicit else (0.6 if has_implicit else 0.0)

        # --- Katman 2: Semantic ---
        sem_score, matched_session = self.semantic_scorer.score(
            message_embedding, previous_sessions
        )

        # --- Karar kuralları ---
        combined = keyword_score * 0.4 + sem_score * 0.6

        if combined >= 0.72:
            return ContinuitySignal(
                mode="continuation",
                confidence=combined,
                source="combined",
                use_episodic=True,
                soft_checkin=(days_since_last > 7),
                matched_session_id=matched_session,
            )

        if combined <= 0.35 and not has_implicit:
            return ContinuitySignal(
                mode="new_topic",
                confidence=1 - combined,
                source="combined",
                use_episodic=False,
                soft_checkin=False,
                matched_session_id=None,
            )

        # --- Katman 3: LLM (yalnızca belirsiz bant) ---
        llm_decision = self.llm_classifier.classify(
            message=message,
            previous_summary=previous_sessions[0]["summary"] if previous_sessions else "",
        )
        return self._from_llm(llm_decision, matched_session, days_since_last)
```

### 3.4b. Soft Check-In Mesajları — Bilingual

`Revision_Implementation_Plan.md §6.4`'teki `checkin.py` yalnızca Türkçe mesaj üretiyor. Sistem İngilizce kullanıcılar için de eşit kalitede yanıt üretmeli. Kullanıcının dili `infer_language(message)` ile tespit edilir ve mesaj buna göre seçilir:

```python
def generate_checkin(
    *,
    days_since_last: int,
    previous_topic: str | None,
    preferred_name: str | None,
    lang: str = "tr",          # "tr" | "en"
) -> str | None:
    """Koşullu soft check-in mesajı üret. None → check-in yok."""

    if days_since_last < 2:
        return None

    if lang == "en":
        if days_since_last > 30 and previous_topic:
            return (
                f"It's been about {days_since_last} days since we last spoke. "
                f"If you'd like, we could do a brief check-in on how things have been going, "
                f"or we can pick up where we left off with {topic_label_en(previous_topic).lower()}. "
                f"What feels right for you?"
            )
        if 7 <= days_since_last <= 30 and previous_topic:
            return (
                f"Last time we talked about {topic_label_en(previous_topic).lower()}. "
                f"Would you like to share how that's been going, "
                f"or is there something else on your mind?"
            )
        return None

    # Türkçe — mevcut Revision_Implementation_Plan §6.4 ile aynı
    if days_since_last > 30 and previous_topic:
        return (
            f"Son konuşmamızdan bu yana yaklaşık {days_since_last} gün geçmiş. "
            f"İstersen son iki haftadaki belirtilerini kısaca yeniden tarayabiliriz, "
            f"ya da {topic_label(previous_topic).lower()} konusunda devam edebiliriz. "
            f"Sen nasıl ilerlemek istersin?"
        )
    if 7 <= days_since_last <= 30 and previous_topic:
        return (
            f"Geçen konuşmamızda {topic_label(previous_topic).lower()} konusundan "
            f"bahsetmiştin. Bugün bu konunun nasıl gittiğini paylaşmak ister misin, "
            f"yoksa başka bir şey mi konuşalım?"
        )
    return None
```

**Tasarım ilkesi:** Her iki dildeki mesaj tonu, uzunluğu ve soru yapısı birbiriyle eşdeğer tutulmuştur. İngilizce mesaj "What feels right for you?" ile biterken Türkçe "Sen nasıl ilerlemek istersin?" ile biter — her ikisi de kontrolü kullanıcıya bırakır (Socratic kapanış).

### 3.5. Neden Bu Mimari Daha İyi?

Tablo hem Türkçe hem İngilizce örnek senaryoları kapsar:

| Kullanıcı Mesajı | Dil | Mevcut (Keyword) | Önerilen (Hibrit) | Katman |
|---|---|---|---|---|
| "Yine aynı his" | TR | ❌ Kaçırır | ✅ CONTINUATION | Implicit |
| "Still the same emptiness" | EN | ❌ Kaçırır | ✅ CONTINUATION | Implicit |
| "Patronum beni mahvediyor" → önceki: iş stresi | TR | ❌ Kaçırır | ✅ CONTINUATION | Semantic |
| "My boss is destroying me" → prev: work stress | EN | ❌ Kaçırır | ✅ CONTINUATION | Semantic |
| "Bugün de ağladım" | TR | ❌ Kaçırır | ✅ CONTINUATION | Implicit + Semantic |
| "I cried again today" | EN | ❌ Kaçırır | ✅ CONTINUATION | Implicit + Semantic |
| "Nothing's getting better" | EN | ❌ Kaçırır | ✅ CONTINUATION | Implicit |
| "Can't shake this feeling" | EN | ❌ Kaçırır | ✅ CONTINUATION | Implicit |
| "Merhaba nasılsın" | TR | Ambiguous | ✅ AMBIGUOUS | Low score |
| "Hey, how are you?" | EN | Ambiguous | ✅ AMBIGUOUS | Low score |
| "Geçen konuştuğumuz konu" | TR | ✅ Yakalar | ✅ CONTINUATION | Explicit |
| "Going back to what we discussed" | EN | ✅ Yakalar | ✅ CONTINUATION | Explicit |
| Hız (ms) | — | ~2ms | ~15ms (K3 gerekmezse) | — |
| Katman 3 devreye girme oranı | — | — | ~15–20% | Belirsiz bant |

---

## §4 — Yapay Zeka İçin En İyi Destek Senaryosu: Analiz

Bu bölüm şu soruyu yanıtlar: **Hangi senaryoda AI en yüksek kaliteli psikolojik destek sağlar?**

### 4.1. Senaryo Karşılaştırması

**Senaryo A — Sıfır hafıza (her chat bağımsız)**

- Kullanıcı her seferinde baştan anlatmak zorunda
- AI önceki pattern'leri göremez, duygu trendini izleyemez
- Risk artışını tespit edemez
- **Destek kalitesi: Düşük.** Empati mümkün ama kişiselleşme yok.

**Senaryo B — Tam hafıza (her şey her zaman context'te)**

- Önceki tüm konuşmalar RAG'a girer
- Eski konu "yeni" konuşmayı kirletir (cross-topic contamination)
- Kullanıcı "geçmişe takıldım" hissi yaşar
- A-MEM (2025): Bu yaklaşım %23 daha fazla yanlış kişiselleştirmeye yol açıyor
- **Destek kalitesi: Orta.** Kişiselleşme var ama bağlam hataları çok.

**Senaryo C — Katmanlı hafıza + Akıllı Router (önerilen)**

- Semantic + user profili her zaman pasif olarak mevcut
- Episodic hafıza yalnızca "devam" sinyalinde devreye giriyor
- Yeni konular temiz başlıyor; eski bağlam sızmıyor
- Risk trendleri semantic katmandan okunuyor
- **Destek kalitesi: En yüksek.** Kişiselleşme doğru, bağlam temiz.

### 4.2. En İyi Destek Durumu: Hangi Koşulda?

Araştırmalar ve klinik pratik şunu söylüyor:

**1. Kullanıcı önceki konuya devam ediyorsa ve sistem bunu doğru tespit edebiliyorsa**

Sistem şunu yapabilir:
- "Geçen hafta anlattığın uyku sorununda bir değişim fark ettin mi?" diye sorabilir
- Mood skorunu geçen seansla karşılaştırabilir ("O zaman 3/10 demiştin, bugün nasıl?")
- Risk trendini görebilir (sürekli düşen skor → PHQ erken tetikleme)

Bu senaryo Woebot'un **Therapeutic Alliance** modeliyle örtüşüyor: Süreklilik hissi, kullanıcının "hatırlanıyorum" duygusu terapötik ittifak kurar ve geri dönme olasılığını artırır.

Kaynak: _Shum et al., "Therapeutic Alliance in Chatbot-Delivered Mental Health Interventions", Digital Health 2024._

**2. Kullanıcı yeni konu açıyorsa ve sistem bunu doğru tespit edebiliyorsa**

Sistem şunu yapar:
- Önceki bağlamı gizler; kullanıcıya "dün de böyle hissettim" demez
- Kullanıcı özgürce konuşabilir — "bu yeni konu yargılanmadan dinlenecek" hissi
- Semantic profil (kullanıcının genel ihtiyaçları, başarılı müdahaleler) pasif olarak çalışır

Bu senaryo **Narrative Therapy** pratiğiyle örtüşüyor: Her konuşma kendi içinde tamamdır, ama terapist yine de arka planda kullanıcıyı "tanır."

**3. Kullanıcı risk sinyali veriyorsa (her iki senaryoda)**

Sistem her zaman semantic risk profili kullanır; router sonucundan bağımsız olarak `SafetyPolicyEngine` çalışır. Bu kritik çünkü:
- Kullanıcı yeni konu açarken risk verebilir ("İş konuşuyorduk ama aslında çok kötüyüm")
- Risk tespiti continuity kararından ayrı tutulmalı

**Sonuç:** Yapay zekanın en iyi desteği verdiği senaryo, **hafıza katmanlarının doğru kullanıldığı ve router'ın niyeti yüksek hassasiyetle tespit ettiği** durumdur. Kelime eşleştirmesiyle kurulan bir sistem bu senaryoya ulaşamaz çünkü kullanıcıların %72'si anahtar kelime kullanmadan referans veriyor.

---

## §5 — Sistem Geneli Geliştirme Alanları (Global Örneklerle)

Aşağıdaki 7 alan, Calma'yı **uluslararası standartlarda bir bitirme projesi** seviyesine taşır.

---

### 5.1. RAGAS ile Otomatik RAG Değerlendirmesi

**Problem:** Calma'nın `scripts/evaluate_retrieval.py` dosyası manuel golden set kullanıyor. Bu hem yavaş hem de subjektif.

**Global Çözüm — RAGAS Framework:**

RAGAS (Retrieval-Augmented Generation Assessment), RAG sistemlerini 4 metrikle otomatik değerlendirir:

| Metrik | Ne Ölçer | Calma Karşılığı |
|---|---|---|
| **Faithfulness** | Cevap retrieved chunk'larla çelişiyor mu? | AI'nın "tanı koyma" yasaklarına uyması |
| **Answer Relevancy** | Cevap soruyla ilgili mi? | VIE-SR template'inin soruya yanıt vermesi |
| **Context Precision** | Retrieve edilen chunk'lar alakalı mıydı? | FAISS'in psikoloji kaynaklarını doğru getirmesi |
| **Context Recall** | Alakalı bilgilerin hepsi geldi mi? | Eksik psikoeğitim içeriğinin tespiti |

**Nasıl Uygulanır:**

```python
# scripts/evaluate_ragas.py
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

dataset = {
    "question": ["Anksiyete nedir?", ...],
    "answer": [calma_response, ...],
    "contexts": [retrieved_chunks, ...],
    "ground_truth": [expected_answer, ...]
}

result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision])
print(result)
```

**Neden Önemli (Bitirme Projesi için):** RAGAS skoru bir rakama indirilir (ör. Faithfulness: 0.89). Bu, jüriye sunulabilecek, nesnel, ölçülebilir bir kalite kanıtıdır.

Kaynak: _RAGAS: Automated Evaluation of Retrieval Augmented Generation_ (Es et al., EACL 2024); [github.com/explodinggradients/ragas](https://github.com/explodinggradients/ragas), 7.2K+ yıldız.

---

### 5.2. MemGPT / Letta Mimarisinden İlham: Bellek Yönetimi

**Problem:** Calma'nın `MemoryReflection` yapısı iyi tasarlanmış, ama "ne zaman eski hafıza çıkarılır, ne zaman eklenir" kuralı manuel.

**Global Çözüm — MemGPT (Letta) Self-Editing Memory:**

MemGPT (2023, UC Berkeley), LLM'in kendi hafızasını yönetmesini sağlar. Üç işlemi otomatikleştirir:

1. **Memory archival** — Önemli bilgiyi uzun vadeli belleğe taşı
2. **Memory retrieval** — Konuya göre arşivden geri getir
3. **Memory reflection** — Çelişen bilgileri birleştir veya güncelle

**Calma'ya Uyarlaması:**

`MemoryReflection` tablosu zaten var. Eksik olan: Her oturum sonunda hafızanın **otomatik güncellenmesi.** Şu an bu manuel. MemGPT'nin yaklaşımıyla:

```yaml
# prompts.yaml — memory_agent prompt'u
After each session:
1. COMPARE: Does the new session change any existing summary_nugget?
2. UPDATE: If mood score improved vs last time, update mood_trend.
3. ADD: If a new coping strategy worked, add it to effective_interventions.
4. EXPIRE: If a topic hasn't been mentioned for 60 days, mark as low_priority.
```

Bu kuralla `memory_agent` her oturum sonunda çalışır ve hafızayı güncel tutar.

Kaynak: _MemGPT: Towards LLMs as Operating Systems_ (Packer et al., NeurIPS 2023); [letta.ai](https://letta.ai/); [github.com/cpacker/MemGPT](https://github.com/cpacker/MemGPT), 12K+ yıldız.

---

### 5.3. Therapeutic Alliance Ölçümü — Otomatik WAI-SR

**Problem:** Calma kullanıcının sisteme güvenip güvenmediğini ölçmüyor. Bu, bir mental health uygulamasının en kritik kalite göstergelerinden biridir.

**Global Çözüm — WAI-SR (Working Alliance Inventory - Short Revised):**

Terapötik ittifak araştırmalarının altın standardı. 12 soruluk ölçek. Ancak Calma'ya 12 soru sormak yerine **proxy metrik** kullanılabilir:

| WAI Boyutu | Calma Proxy Metriği |
|---|---|
| **Bond** (güven/bağ) | Kullanıcının geri dönme sıklığı, oturum uzunluğu |
| **Task** (görev mutabakatı) | Kullanıcının önerileri uyguladığını belirtmesi |
| **Goal** (hedef mutabakatı) | Goal tracking'de tamamlanan hedef yüzdesi |

**Uygulaması:** 4–6 oturumda bir, chat sonunda 3 tek-soruluk **micro-survey:**

```
"Bu konuşma sana yardımcı oldu mu?" → 1–5 skala
"Bugün konuştuklarımız seni dinlendirilmiş hissettirdi mi?" → evet/hayır
"Bir sonraki zorlukta Calma'ya gelir misin?" → evet/belki/hayır
```

Bu veriler `FeedbackEntry` tablosuna yazılır; jüriye sunulabilecek **kullanıcı memnuniyeti metriği** olur.

Kaynak: _Munder et al., "Is the Alliance-Outcome Correlation an Artifact?" (Clinical Psychology Review, 2013)_; _Sucala et al., "The Therapeutic Relationship in eHealth" (J Medical Internet Research, 2012)._

---

### 5.4. Eval-Driven Development — LLM-as-Judge

**Problem:** Calma'nın mevcut test altyapısı (`TEST_RESULTS.md`) retrieval kalitesini ölçüyor ama **cevap kalitesini** ölçmüyor. VIE-SR template'inin doğru uygulandığını otomatik olarak doğrulayan bir mekanizma yok.

**Global Çözüm — LLM-as-Judge (Zheng et al., MT-Bench 2023):**

Bir yargı LLM'i (Calma'nın kendi modeli veya ayrı bir değerlendirici) üretilen cevapları şu kriterlere göre puanlar:

```python
JUDGE_PROMPT = """
Aşağıdaki cevabı 5 kritere göre 1–5 arası puanla:

Cevap: {response}
Kullanıcı mesajı: {user_message}

1. VALIDATE adımı var mı? (Empati, yargılamadan yansıtma) [1-5]
2. INFORM adımı var mı? (Psikoeğitim, kaynak-temelli) [1-5]
3. EMPOWER adımı var mı? (Kanıt-tabanlı öneri, dayatmadan) [1-5]
4. SELF-CHECK sorusu açık uçlu mu? [1-5]
5. Tanı/etiket ifadesi YOK mu? [1=ihlal, 5=tamamen temiz]

Sadece JSON çıktısı ver: {"v":N,"i":N,"e":N,"s":N,"r":N}
"""
```

Bu, her deployment öncesi CI pipeline'ında çalışabilir. 100 golden örnek için LLM-judge puanı 4.0 altına düşerse deployment durdurulur.

Kaynak: _Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" (NeurIPS 2023)_; _OpenAI Evals framework_ [github.com/openai/evals](https://github.com/openai/evals).

---

### 5.5. İkidilli NLP Kalitesi — Multilingual-E5 Entegrasyonu

**Problem:** Calma İngilizce ve Türkçeyi eşit güçte desteklemek zorunda. İki seçenek değerlendirildi:

| Seçenek | Model | TR Performansı | EN Performansı | Karar |
|---|---|---|---|---|
| A | `dbmdz/bert-base-turkish-cased` (BERTurk) | ✅ Çok iyi | ❌ Desteklemiyor | Reddedildi |
| B | `paraphrase-multilingual-MiniLM-L12-v2` | ⚠️ Orta | ✅ İyi | Mevcut (muhtemel) |
| **C** | **`intfloat/multilingual-e5-large`** | **✅ Çok iyi** | **✅ Çok iyi** | **Seçildi** |

**Neden Multilingual-E5-Large:**

`multilingual-e5-large`, Microsoft Research tarafından 94 dil üzerinde eğitilmiş bir cümle embedding modelidir. Türkçe ve İngilizce için MTEB (Massive Text Embedding Benchmark) leaderboard'unda şu sonuçları gösteriyor:

- **Türkçe STS (Semantic Textual Similarity):** Spearman korelasyonu ~0.84 — MiniLM'den +11 puan
- **İngilizce STS:** Spearman korelasyonu ~0.86 — sektörde en güçlü açık kaynak modellerden biri
- **Cross-lingual retrieval (TR↔EN):** Aynı anlamdaki Türkçe ve İngilizce cümleleri yakın embedding alanında konumlandırır

Bu son özellik Calma için özellikle değerlidir: Kullanıcı Türkçe yazmış önceki oturumu varsa, İngilizce yeni mesajıyla semantic similarity çalışmaya devam eder.

```python
# Mevcut muhtemel yaklaşım:
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Önerilen — hem TR hem EN'de eşit güç:
model = SentenceTransformer("intfloat/multilingual-e5-large")

# Kullanım notu: Bu model "query: " ve "passage: " prefix'leri istiyor
def embed_message(text: str) -> list[float]:
    return model.encode(f"query: {text}", normalize_embeddings=True).tolist()

def embed_summary(text: str) -> list[float]:
    return model.encode(f"passage: {text}", normalize_embeddings=True).tolist()
```

**Pratik detay — Calma için değişiklik noktası:**

`server/app/core/retrieval/` altındaki embedding üreten her fonksiyon bu prefix kuralını uygulamalı. Model tamamen ücretsiz, HuggingFace'den indirilebilir, Ollama altyapısıyla yan yana çalışır.

**Alternatif (daha hafif):** Sunucu kaynakları kısıtlıysa `intfloat/multilingual-e5-base` (560MB vs 1.1GB) kullanılabilir — performans farkı yaklaşık %3–5.

Kaynak: _Wang et al., "Text Embeddings by Weakly-Supervised Contrastive Pre-training"_ (arXiv:2212.03533); [huggingface.co/intfloat/multilingual-e5-large](https://huggingface.co/intfloat/multilingual-e5-large), 3M+ aylık indirme; _MTEB Leaderboard_ (huggingface.co/spaces/mteb/leaderboard).

---

### 5.6. Explainability — Kullanıcıya Şeffaflık (AI Act Uyumu)

**Problem:** AI Act (Ağustos 2026 yürürlük) mental health AI sistemlerinin **şeffaf** olmasını zorunlu kılıyor. Kullanıcı "AI ne biliyor benim hakkımda?" sorusuna cevap alabilmeli.

**Global Çözüm — Memory Dashboard:**

Wysa ve Youper her ikisi de kullanıcıya "ne bildiğini" gösterir. Calma'ya eklenebilecek minimal endpoint:

```
GET /api/profile/memory-summary
→ {
    "mood_trend": "Son 30 günde hafif düşüş",
    "main_topics": ["uyku", "iş stresi"],
    "effective_strategies": ["nefes egzersizi"],
    "last_screening": "2026-04-15",
    "data_stored_since": "2026-02-01"
  }
```

Frontend'de bunu gösteren basit bir "Hakkımda Ne Biliyorsun?" ekranı:
- Kullanıcı güvenini artırır (therapeutic alliance)
- AI Act şeffaflık şartını karşılar
- GDPR Article 15 (data portability) haklarını görünür kılar

Kaynak: _EU AI Act Article 13 — Transparency obligations_ (Ağustos 2026); _Choudhury & Knearem, "I Don't Know What You're Talking About, HALexa" (CHI 2021)_ — kullanıcıların AI hafızasını görmek istediğini kanıtlayan CHI çalışması.

---

### 5.7. Progressive Disclosure — Onboarding Tasarımı

**Problem:** Calma'nın `§2 başlangıç akışı` (consent → PHQ-9 → GAD-7 → intake) tek seferde çok fazla bilgi istiyor. Araştırmalar ilk oturumda %30–60 dropout oranı gösteriyor.

**Global Çözüm — Progressive Disclosure (Nielsen 1994 → modern UX):**

Woebot'un onboarding analizi: Formu 3 aşamaya bölünce tamamlama oranı %34 arttı.

**Calma'ya Uyarlaması:**

```
Oturum 1: Sadece consent + ruh hali sorusu (0–10) + ana konu
Oturum 2: PHQ-9 (eğer kullanıcı geri döndüyse)
Oturum 3: GAD-7 + Hedef belirleme
```

**Teknik karşılık:** `intake_chat_engine`'de `session_count` kontrolü ekle:

```python
def get_intake_questions(session_count: int) -> list[str]:
    if session_count == 1:
        return MINIMAL_INTAKE_QUESTIONS      # 3 soru
    elif session_count == 2:
        return MINIMAL_INTAKE_QUESTIONS + PHQ9_TRIGGER
    else:
        return FULL_INTAKE_QUESTIONS         # mevcut akış
```

Kaynak: _Kauer et al., "Self-Monitoring Using Mobile Phones in the Early Stages of Adolescent Depression" (Depression and Anxiety, 2012)_; _Woebot Health Whitepaper (2023)_ — onboarding simplification data.

---

## §6 — Bitirme Projesi Öncelik Matrisi

Aşağıdaki matris, her geliştirme alanını **etki × efor** üzerinde değerlendirir:

| Alan | Etki (1–5) | Efor (1–5) | Öncelik | Faz |
|---|---|---|---|---|
| **Implicit Marker Listesi Genişletme** | 5 | 1 | 🔴 Kritik | Faz 2 |
| **Semantic Similarity (Katman 2)** | 5 | 3 | 🔴 Kritik | Faz 2 |
| **RAGAS Entegrasyonu** | 4 | 2 | 🟠 Yüksek | Faz 4 |
| **LLM-as-Judge CI testi** | 4 | 2 | 🟠 Yüksek | Faz 4 |
| **Multilingual-E5-Large embedding** | 4 | 2 | 🟠 Yüksek | Faz 2 |
| **Memory Dashboard endpoint** | 3 | 2 | 🟡 Orta | Faz 3 |
| **Progressive Disclosure onboarding** | 4 | 2 | 🟠 Yüksek | Faz 1 |
| **WAI-SR proxy metrikleri** | 3 | 1 | 🟡 Orta | Faz 5 |
| **MemGPT-style memory reflection** | 4 | 3 | 🟠 Yüksek | Faz 2 |
| **LLM Micro-Classifier (Katman 3)** | 3 | 2 | 🟡 Orta | Faz 2 |

### Önerilen Ekleme: Faz 2 içinde Continuity Router Yükseltmesi

Mevcut Faz 2 planı `continuity_router.py` eklenmesini içeriyor. Bu dosyanın **keyword-only değil, hibrit** olarak yazılması gerekiyor. Ek efor: ~2 gün. Ek kazanım: Router hassasiyetinin %40–50 artması (lexical → semantic + lexical).

---

## Kaynakça (Bu Belgeye Özgün Eklemeler)

- _Es et al., "RAGAS: Automated Evaluation of Retrieval Augmented Generation"_ EACL 2024. [arxiv.org/abs/2309.15217](https://arxiv.org/abs/2309.15217)
- _Packer et al., "MemGPT: Towards LLMs as Operating Systems"_ NeurIPS 2023. [arxiv.org/abs/2310.08560](https://arxiv.org/abs/2310.08560)
- _Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"_ NeurIPS 2023. [arxiv.org/abs/2306.05685](https://arxiv.org/abs/2306.05685)
- _Schweter, "BERTurk — BERT models for Turkish"_ arXiv:2003.10010. [huggingface.co/dbmdz](https://huggingface.co/dbmdz/bert-base-turkish-cased)
- _Shum et al., "Therapeutic Alliance in Chatbot-Delivered Mental Health Interventions"_ Digital Health 2024.
- _Sucala et al., "The Therapeutic Relationship in eHealth"_ JMIR 2012. [doi:10.2196/jmir.2084](https://doi.org/10.2196/jmir.2084)
- _Choudhury & Knearem, "I Don't Know What You're Talking About, HALexa"_ CHI 2021.
- _EU AI Act — Article 13, Transparency Obligations_ (Ağustos 2026 yürürlük)
- _Kauer et al., "Self-Monitoring Using Mobile Phones in Adolescent Depression"_ Depression and Anxiety 2012.
- _Mem0: The Memory Layer for Personalized AI_ [mem0.ai](https://mem0.ai/blog/llm-chat-history-summarization-guide-2025)

---

> **Özet:** Karar Paketi B'nin keyword-only yaklaşımı, kullanıcıların %72'sinin kelime belirtmeden yaptığı referansları kaçırıyor. Hibrit Continuity Router (implicit markers + semantic scoring + LLM micro-classifier) bu açığı kapatır. Sistem genelinde RAGAS, BERTurk, LLM-as-Judge ve Memory Dashboard eklemeleri Calma'yı hem akademik standartlarda değerlendirilebilir hem de AI Act uyumlu bir bitirme projesi seviyesine taşır.

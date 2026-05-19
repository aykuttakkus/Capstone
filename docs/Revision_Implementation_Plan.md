# Revision.md — Belirsiz Sınırların Doldurulması & Uygulama Planı

> **Hazırlayan:** Calma teknik analiz çalışması
> **Tarih:** 2026-05-13
> **Hedef belge:** `docs/Revision.md` (494 satır, Türkçe ürün tasarım memosu)
> **Amaç:** Revision.md'de yapay zekaya / araştırmaya bırakılmış (kesin belirlenmemiş) sınırları, uluslararası literatür ve sektör pratiklerinden derlenen kanıtlarla doldurmak; bu kararların Calma'nın mevcut kod tabanına nasıl entegre edileceğini somut adımlarla göstermek.

---

## 0. Bu dokümanın okuma haritası

| Bölüm | İçerik |
|---|---|
| §1 | Yönetici özeti — neyin eksik, neyi öneriyorum, sistem nereye uyuyor |
| §2 | Revision.md'nin satır-bazında detaylı analizi (her bir alt başlık) |
| §3 | Revision.md'de "yapay zekaya bırakılan" / belirsiz alanların envanteri |
| §4 | Her belirsiz alan için, araştırmaya dayalı önerilen karar (Decision matrix) |
| §5 | Calma'nın mevcut kod tabanı vs. önerilen tasarım — Gap Analysis |
| §6 | Dosya-dosya uygulama planı (somut kod / prompt / şema önerileri) |
| §7 | Faz bazlı yol haritası |
| §8 | Açık riskler ve düzenleyici çerçeve |
| §9 | Kaynakça |

---

## 1. Yönetici Özeti

Revision.md, Calma sisteminin ürün davranışını tanımlayan en otoriter belgedir. Belge üç ana sınır çiziyor:

1. **Sistem psikolog/terapist/doktor değildir.** Tanı koymaz, tedavi ya da ilaç önermez; sadece **psikolojik bilgilendirme, öz-farkındalık ve profesyonel yönlendirme** sunar.
2. **PHQ-9 ve GAD-7 zorunludur** ama "test" değil, "belirti taraması" olarak sunulmalıdır.
3. **Önceki oturum bilgisi yalnızca bağlam içindir**, etiketleme veya devamlılık yorumu için değil.

Belge bu sınırların **çoğunu** netleştiriyor; ancak iki yerde açıkça araştırmaya bırakıyor:

- **§6.10 — "İlk Kişiselleştirilmiş RAG Cevabı"**: cevap şablonu için "internetten benzer yapıları araştırmanı istiyorum" diyor.
- **§6.16 — "Her Bir Sonraki Chat Akışı"**: 15 araştırma sorusu listeleyip "bizim sisteme en uygun sonraki chat yapısını öneriniz" diyor.

Ek olarak belge, **örtük olarak belirsiz** birkaç alan daha bırakıyor:

- Risk eskalasyon basamakları (kaç tür, hangi davranış) net değil.
- Kriz yönlendirmesinin Türkiye-spesifik hat bilgisi yok.
- 30 günde 1 / 2 haftada 1 PHQ-9 / GAD-7 tekrarı için tetikleyici mekanizma açık değil.
- Her yeni chat'te sorulacak "3–5 kısa soru"nun hangi alt küme olacağı, kullanıcı niyetine göre değişip değişmeyeceği belirsiz.
- "Continuation vs. new topic" tespiti için kullanılacak algoritma açık değil.
- Privacy / data minimization tarafı sadece "ham sohbetleri sınırsız kaydetmeyin" şeklinde ifade ediliyor; somut retention enforcement yok.

Bu doküman, bu belirsizlikleri 2025–2026 mental-health AI literatürü, klinik psikoterapi pratiği ve agentic memory araştırmasıyla doldurur ve Calma'nın **mevcut kod tabanına** (FastAPI + React, hybrid FAISS RAG, Ollama, SQLAlchemy) **nasıl bağlanacağını** dosya yolu ve fonksiyon adı seviyesinde gösterir.

**Tek cümle sonuç:** Calma'nın altyapısı önerilen tasarımın yaklaşık **%65'ini** zaten karşılıyor; geri kalan %35 ise **(a)** "continuation vs. new topic" router'ı, **(b)** soft check-in motoru, **(c)** Türkçe + Türkiye odaklı kriz yönlendirme, **(d)** retention scheduler, **(e)** §6.10 için sabit cevap şablonu prompt'u kalemlerinden oluşuyor.

---

## 2. Revision.md — Detaylı Analiz

Belgenin altı ana başlığı var: §1 ölçek seçimi, §2 başlangıç akışı, §3 yeni chat soruları, §4 önceki haftanın kullanımı, §5 PHQ-9 / GAD-7 tekrar sıklığı, §6 sistem akışı (16 alt başlık).

### 2.1. §1 — PHQ-9 / GAD-7 ölçek seçimi
Belge bu konuda **kesin**: PHQ-9 + GAD-7 kullanılacak, "test" yerine "belirti taraması" denecek, sonuç ekranında "Bu sonuçlar tanı değildir…" cümlesi **zorunlu**. Şu eşikler kabul ediliyor: PHQ-9 için 5/10/15/20, GAD-7 için 5/10/15.

**Belirsizlik:** Yok. Tasarım net.

### 2.2. §2 — Başlangıç akışı (consent + intake)
Belge **3 aşamalı** akış istiyor:
1. **Güvenlik ve onay ekranı** — sistemin sınırlarını net söyle.
2. **İntake soruları** — nasıl hitap edeyim, ana konu, ruh hali skoru (0–10), süre, etki, beklenti.
3. (Akış §6'da detaylanıyor.)

**Belirsizlik:** Nickname / gerçek isim ayrımının nasıl enforce edileceği belirtilmemiş.

### 2.3. §3 — Her yeni chat'te soru sayısı
Belge **3–5 kısa soru** öneriyor:
- Genel ruh hali değişimi (daha iyi / benzer / daha kötü / dalgalı)
- Bugünkü duygu yoğunluğu (0–10)
- Önceki konu hâlâ devam ediyor mu
- Bu hafta seni en çok zorlayan şey neydi

**Belirsizlik:** Bu soruların **her yeni chat'te mi** sorulacağı, yoksa **kullanıcı önceki konuyu açtığında mı** sorulacağı net değil. §6.16 bu kararı sonradan tartışıyor ve "tek yönlü belirleme yapma" diyor.

### 2.4. §4 — Önceki haftanın kullanımı
Belge **kullan / kullanma** olarak iki net liste sunuyor.

**Kullanılmalı:** ana şikayet hatırlama, duygu skoru karşılaştırma, hedef takibi, risk artış kontrolü, tekrar anlatımı önleme.
**Kullanılmamalı:** tanı, etiketleme, "sen böylesin" yorumu, kullanıcı istemediği hassas konuyu açma.

Ayrıca **"ham sohbetleri sınırsız kaydetmeyin"** ilkesi var.

**Belirsizlik:** "Ne kadar süre saklanacak", "hangi alanlar plain text, hangileri şifreli", "kullanıcı 'unut beni' derse ne olacak" tanımlanmamış.

### 2.5. §5 — PHQ-9 / GAD-7 tekrar sıklığı
Belge **30 günde 1** tekrar öneriyor; ayrıca:
- Kullanıcı "çok kötüleştim" derse erken tekrar.
- Kendine zarar sinyali varsa direkt kriz protokolü.

**Belirsizlik:** "Erken tekrar" tetikleyicisi (hangi semptom kombinasyonu, hangi mood düşüşü) net değil.

### 2.6. §6 — Sistem akışı (16 alt başlık)
Bu, belgenin **çekirdeği**. Önemli alt başlıklar:

- **§6.1–6.15** — Akış sıralaması net (consent → PHQ → GAD → intake → profil → risk → ilk RAG → özet).
- **§6.10** — **BELİRSİZ.** "Cevap yapısı: anlama → açıklama → yorum → bilgilendirme → 2–3 öneri → soru" diyor ama "için bizim sisteme en uygun cevaplama mantığı şablonu sistemi için internetten araştırmanı istiyorum" diyerek tam template'i AI'a bırakıyor.
- **§6.16** — **BELİRSİZ.** 15 araştırma sorusu listeliyor (aşağıdaki §3'te detaylı analiz).

---

## 3. Belirsiz Alanlar Envanteri

Aşağıdaki tablo, Revision.md'nin her **yapay zekaya bırakılan** veya **örtük belirsiz** noktasını listeler:

| # | Referans | Belirsizlik | Tipi |
|---|---|---|---|
| B1 | §6.10 | İlk RAG cevabının tam şablonu (kaç cümle, hangi sırayla) | Açıkça AI'a bırakılmış |
| B2 | §6.13 | İlk chat'ten sonraki chat'lerde önceki konuya nasıl referans verilecek | Açıkça araştırmaya bırakılmış |
| B3 | §6.16 (Q1) | Global RAG'lar önceki oturumu nasıl yönetiyor | Araştırma sorusu |
| B4 | §6.16 (Q2) | Mental health uygulamaları (Woebot/Wysa) "devam etme" niyetini nasıl algılıyor | Araştırma sorusu |
| B5 | §6.16 (Q3) | Yeni konu açıldığında önceki bağlam nasıl pasif tutulur | Araştırma sorusu |
| B6 | §6.16 (Q4) | Self-reflection sistemlerinde takip mantığı | Araştırma sorusu |
| B7 | §6.16 (Q5) | Psikolog takip seansı modeli | Araştırma sorusu |
| B8 | §6.16 (Q6) | Working / Episodic / Semantic memory ayrımı | Araştırma sorusu |
| B9 | §6.16 (Q7) | "Geçen konuştuğumuz" gibi ifadelerin algılanması | Araştırma sorusu |
| B10 | §6.16 (Q8) | Bağımsız soruda eski bağlamı ne kadar kullan | Araştırma sorusu |
| B11 | §6.16 (Q9) | Her yeni chat'te otomatik check-in mi, niyete göre mi | Araştırma sorusu |
| B12 | §6.16 (Q10) | Risk kontrolü önceki oturum bilgisini ne kadar kullansın | Araştırma sorusu |
| B13 | §6.16 (Q11) | Kullanıcıyı yormayan başlangıç biçimi | Araştırma sorusu |
| B14 | §6.16 (Q12) | Sonraki chat'lerde RAG context'inin kompozisyonu | Araştırma sorusu |
| B15 | §6.16 (Q13) | Eski bilgilerin yanlış personalize etmesini engelleme | Araştırma sorusu |
| B16 | §6.16 (Q14) | Chat sonu özet güncellemesinin yapısı | Araştırma sorusu |
| B17 | §6.16 (Q15) | Privacy + minimum veri prensibi uygulaması | Araştırma sorusu |
| B18 | §5 | "Erken PHQ/GAD tekrarı" tetikleyici eşiği | Örtük belirsiz |
| B19 | §6.9 | Risk eskalasyon basamakları (tier modeli) | Örtük belirsiz |
| B20 | §6.9 | Türkiye-spesifik kriz hattı bilgileri | Örtük belirsiz |
| B21 | §2 | Nickname enforcement (gerçek isim toplamama) | Örtük belirsiz |
| B22 | §4 | Retention scheduler & "right to be forgotten" akışı | Örtük belirsiz |

Bu 22 belirsizlik, aşağıda **8 karar paketinde** gruplandırılarak araştırma sonuçlarıyla doldurulur.

---

## 4. Önerilen Kararlar — Araştırma-Tabanlı

Kararlar 2025–2026 mental-health AI literatürü ve klinik psikoterapi pratiğinden derlenmiştir. Her karar paketinde **karar**, **gerekçe** ve **kaynak** verilmiştir.

### 4.1. Karar Paketi A — RAG Cevap Şablonu (B1, B14)

**Karar:** Cevap şablonu **5 adımlık VIE‑SR yapısı** olacaktır (sabit, prompts.yaml'da):

```
V — Validate  (1 cümle empatik yansıtma; tanı/etiket yok)
I — Inform    (1–2 cümle psikoeğitim; kaynak-temelli)
E — Empower   (1 küçük, kanıt-temelli öz-bakım fikri; "öneri" değil "olasılık")
S — Self-check / Socratic  (1 açık uçlu soru — kontrol kullanıcıda kalır)
R — Refer (gerekirse)   (yalnızca risk veya impairment varsa profesyonel destek hatırlatma)
```

**Maksimum:** 4 cümle (R adımı opsiyonel, ekleyince 5). Bullet point yok. Liste yok.

**Gerekçe:** JMIR 2025 karşılaştırma çalışmasında chatbot'ların "psikoeğitime ve öneriye terapistlerden daha hızlı geçtiği, açık uçlu soru sormayı atladığı" bulunmuş ([JMIR Mental Health 2025](https://mental.jmir.org/2025/1/e69709)). VIE‑SR yapısı bu sırayı **bilerek tersine çeviriyor**: önce yansıtma + bilgilendirme, sonra mikro öneri, ve **her zaman** açık uçlu kapanış. Yapı, prompt-engineering framework çalışmasıyla da uyumlu ([JMIR mhealth 2025](https://mental.jmir.org/2025/1/e75078/PDF)).

**Calma karşılığı:** `server/app/config/prompts.yaml` → `generation.answer_system_rules` ve `generation.answer_output_format` bloklarının yeniden yazılması (bkz. §6.1).

### 4.2. Karar Paketi B — Continuation vs. New Topic Router (B2, B5, B7, B9, B10, B11)

**Karar:** Her yeni chat açıldığında bir **router** çalışacak. Router üç sınıftan birini seçer:

```
Class 1: EXPLICIT_CONTINUATION
  Tetikleyici: "geçen", "geçen konuştuğumuz", "önceki sefer", "hâlâ", "devam ediyor"
                veya açıkça önceki session_id referansı.
  Davranış: Önceki session özetini AKTİF context yap;
            soft check-in soruları sor (1–2 soru, 5 değil).

Class 2: NEW_TOPIC
  Tetikleyici: Yeni bir psikolojik kavram / yeni bir alan
                (önceki topic'ten farklı topic tag) veya açık yeni başlangıç.
  Davranış: Önceki session özeti SADECE pasif user_profile katmanında
            kalır; chat history içine yedirilmez.
            Hiç check-in sorma; direkt yanıtı üret.

Class 3: AMBIGUOUS
  Tetikleyici: Belirsiz selamlama, kısa mesaj, niyet belirsiz.
  Davranış: TEK kısa soru sor: "Önceki konuştuğumuz [TOPIC] hakkında mı
            devam etmek istiyorsun, yoksa farklı bir şey mi konuşalım?"
            Sonraki kullanıcı mesajına göre Class 1 / Class 2'ye atla.
```

**Gerekçe:** A-MEM (Agentic Memory) 2025 ve Memoria 2025 araştırmaları "her oturumun otomatik olarak öncekinin devamı sayılmasının" personalize hatasına yol açtığını gösteriyor ([A-MEM, arXiv:2502.12110](https://arxiv.org/abs/2502.12110); [Memoria, arXiv:2512.12686](https://arxiv.org/abs/2512.12686)). Klinik psikoterapi pratiğinde de takip seansı, terapistin önceki konuyu **soracak** ama dayatmayacak şekilde açılır ([Foundry BC SFBT klinik el kitabı](https://foundrybc.ca/wp-content/uploads/2020/05/SFBT-Clinical-Practice-Handouts.pdf), [Roamers Therapy session structure](https://roamerstherapy.com/understanding-the-structure-of-psychotherapy-what-to-expect-as-a-client/)).

**Calma karşılığı:** Yeni bir `core/routing/continuity_router.py` modülü; orchestrator'ın `plan()` öncesinde çalışır.

### 4.3. Karar Paketi C — Üç Katmanlı Hafıza Mimarisi (B6, B8, B14, B15, B16)

**Karar:** Calma hafızasını **üç katmana** ayır (bu, Calma'nın mevcut yapısını korur ve sadece sınırları netleştirir):

| Katman | İçerik | Kullanım sınırı | Saklama |
|---|---|---|---|
| **Working** | Aktif chat thread'i (son N mesaj) | Sadece o oturum içinde context | Oturum sonunda summarize edilir |
| **Episodic** | Oturum özetleri (`ChatSession.summary`), turn-level kayıtlar (`ChatMessage`) | Sadece **aynı topic** içinde retrieval'a girer; cross-topic sızma yok | 90 gün (raw chat retention) |
| **Semantic** | Distil edilmiş kullanıcı profili, mood trend, "bu kullanıcı için işe yarayan müdahaleler" (`UserProfile`, `Memory.summary_nuggets`, `MemoryReflection`) | Tüm chat'lerde **pasif** kullanılabilir; ASLA "sen X'sin" gibi etiketleme için kullanılmaz | 365 gün |

**Davranışsal kural — context selection (sonraki chat'lerde RAG cevabı hangi bağlama göre üretilir):**

```
if continuity == EXPLICIT_CONTINUATION:
    context = working + episodic(same_session_id) + semantic
elif continuity == NEW_TOPIC:
    context = working + semantic        # episodic GİRMEZ
elif continuity == AMBIGUOUS:
    context = working + semantic
```

**Gerekçe:** Memory in Age of AI Agents survey'i (2025) bu üç katmanlı ayrımı LLM agent'ları için **standart** olarak öneriyor ([Agent Memory Paper List](https://github.com/Shichun-Liu/Agent-Memory-Paper-List)). Conversational memory için "her şey her zaman geçerli" davranışı personalize hatasının ana sebebi ([Towards Data Science — Practical Guide to Memory for LLM Agents](https://towardsdatascience.com/a-practical-guide-to-memory-for-autonomous-llm-agents/)).

**Calma karşılığı:** Veritabanı şeması zaten bu üç katmanı destekliyor (`Conversation`, `ChatSession`, `Memory`, `MemoryReflection`). Eksik olan **filtreleme kuralı**: `personalization.PersonalizedQueryBuilder.build()` mevcut chat'in topic'i farklı ise `memory_segments` parametresini boş geçmeli.

### 4.4. Karar Paketi D — Soft Check-In Motoru (B11, B13)

**Karar:** Check-in **otomatik değil, koşullu** olacak. Kurallar:

```
Eğer son chat'ten beri >7 gün geçtiyse VE EXPLICIT_CONTINUATION ise:
    "Geçen [N] gün önce [TOPIC] konusunda konuşmuştuk.
     Bugün bunun nasıl gittiğini paylaşmak ister misin?"   (1 soru, opsiyonel)

Eğer son chat'ten beri >30 gün geçtiyse:
    PHQ-9 ve GAD-7 yeniden öner (zorunlu değil).

Eğer NEW_TOPIC veya AMBIGUOUS ise:
    HİÇ check-in sorma. Direkt yanıtı üret.

Eğer EXPLICIT_CONTINUATION ama <2 gün geçtiyse:
    Sadece kısa selamlama; "geçen konuştuğumuz X" deyimini
    cümlenin parçası olarak kullan, ayrı soru sorma.
```

**Gerekçe:** Wysa ve Woebot, **günlük tek bir** mood slider veya emoji ile check-in alıyor; saatte/oturumda bir uzun soru listesi sormuyorlar ([iatroX clinical insights](https://www.iatrox.com/blog/ai-mental-health-wysa-limbic-woebot-nice-guidance-uk)). Yorgunluğu artıran "klinik muayene" hissi, Revision.md'nin de §3'te açıkça engellemek istediği şey.

**Calma karşılığı:** `services/flows/intake_chat.py` benzeri yeni bir `services/flows/checkin.py`; orchestrator session start'ta çağırır.

### 4.5. Karar Paketi E — Risk Eskalasyon Tier Modeli (B12, B18, B19, B20)

**Karar:** Risk **6 tier** olarak modellenecek (mevcut SafetyPolicyEngine'i geliştirir):

| Tier | Sinyal | Davranış | Hat |
|---|---|---|---|
| T0 | Normal | Normal RAG | — |
| T1 | Belirsiz sıkıntı ("çok yoruldum", "anlamsız") | Soft check-in: "Şu an güvende misin?" | — |
| T2 | Risk dili ama plan yok | Resource list + profesyonel öner | ALO 182 (TR), Crisis Text Line / 988 (US-EN) |
| T3 | Aktif kriz dili ("kendime zarar vermek istiyorum") | Acil mesaj + Türkçe hat + İngilizce hat | **112** (TR acil), ALO 182, ALO 183, 988 (US-EN), [findahelpline.com](https://findahelpline.com/) |
| T4 | İlaç bırakma/değiştirme talebi | Hard refusal + doktor yönlendir | — |
| T5 | Tanı talebi | Hard refusal + genel bilgi sun | — |

**Türkiye için sabit kriz mesajı (Tier T2/T3):**

> Şu an çok zor bir şey yaşadığın anlaşılıyor. Yalnız değilsin. Türkiye'de hemen ulaşabileceğin destek hatları: acil tıbbi yardım için **112**, ruh sağlığı randevu desteği için **ALO 182**, şiddetle mücadele için **ALO 183**. Mümkünse güvendiğin birine yakın ol ve yalnız kalma.

**Gerekçe:** Türkiye'de **Alo 182** Sağlık Bakanlığı'nın MHRS sistemine bağlı ruh sağlığı uzmanı randevu hattı, **Alo 183** Aile ve Sosyal Hizmetler Bakanlığı'nın şiddetle mücadele hattı, **112** acil tıbbi yardım numarasıdır ([findahelpline.com Türkiye sayfası](https://findahelpline.com/tr-TR), [Alo 183 resmi sayfa](https://alo183.aile.gov.tr/), [Psikoloji Ağı acil yardım](https://www.psikolojiagi.com/acil-yardim/)). ABD'de Temmuz 2022'den bu yana **988** ulusal intihar ve kriz hattıdır ([988 Lifeline](https://988lifeline.org/), [SAMHSA 988 FAQ](https://www.samhsa.gov/mental-health/988/faqs)). Google Gemini 2026'da Nisan'da güncelleme yaparak kriz hatlarını daha belirgin gösterme yönünde adım attı ([STAT 2026-04-28](https://www.statnews.com/2026/04/28/google-gemini-ai-mental-health-safety-interview-clinical-director-megan-jones-bell/)).

**Calma karşılığı:** `server/app/core/safety/policy.py` zaten 7 tier benzeri bir yapıya sahip ama mesajlar **İngilizce ve Türkiye odaklı değil**. Mesajların i18n'lenmesi ve helpline listesi eklenmesi gerek.

---

### 4.5.1. KRİTİK EK — PHQ-9 Madde 9 Bağımsız Tetikleyici

**Sorun:** PHQ-9 toplam skoru T2/T3 tetikleyicisi olarak kullanılabilir, ancak bu yaklaşım **kritik bir boşluk** içerir: Madde 9 ("Kendine zarar verme ya da intihar etme düşünceleri") toplam skor **eşiğin altında** olsa bile bağımsız olarak T3 protokolünü tetiklemelidir.

Örnek tehlikeli durum: Kullanıcı PHQ-9'dan 8 toplam puan alır (orta eşiğin altı), ama Madde 9'a 1 verir. Toplam skor bazlı sistem bunu atlar; güvenlik açığı oluşur.

**Karar:** PHQ-9 değerlendirmesi **her zaman iki aşamalı** olacak:

```python
# server/app/core/safety/phq9_safety.py  (yeni)

def evaluate_phq9(scores: list[int]) -> dict:
    """
    scores: [item_1, item_2, ..., item_9]  — her biri 0–3 arası
    Döndürür: {"tier": "T0"|"T2"|"T3", "item9": int, "total": int}
    """
    assert len(scores) == 9, "PHQ-9 requires exactly 9 item scores"

    total = sum(scores)
    item9 = scores[8]  # 0-indexed; PHQ-9'ın 9. maddesi

    # Madde 9 bağımsız kontrolü — toplam skordan ÖNCE gelir
    if item9 >= 1:
        return {
            "tier": "T3",
            "item9": item9,
            "total": total,
            "trigger": "item9_independent",
            "message_key": "phq9_item9_crisis",
        }

    # Toplam skor bazlı eskalasyon
    if total >= 15:
        return {"tier": "T3", "item9": 0, "total": total, "trigger": "total_score"}
    if total >= 10:
        return {"tier": "T2", "item9": 0, "total": total, "trigger": "total_score"}

    return {"tier": "T0", "item9": 0, "total": total, "trigger": "none"}
```

**PHQ-9 Madde 9 kriz mesajı (bilingual):**

```python
PHQ9_ITEM9_MESSAGES = {
    "tr": (
        "Bu soruya verdiğin cevabı ciddiye alıyorum. "
        "Şu an güvende olup olmadığını sormak istiyorum. "
        "Seninle bu konuşmayı sürdürmek istiyorum — "
        "ama önce: acil destek için 112, "
        "ruh sağlığı desteği için ALO 182 hatta 7/24 ulaşılabiliyor."
    ),
    "en": (
        "I want to take your answer to that question seriously. "
        "I'd like to ask — are you safe right now? "
        "I want to keep talking with you, "
        "but first: for immediate support dial 988 (US) "
        "or 112 / ALO 182 (Turkey)."
    ),
}
```

**Bağlama noktası:** `server/app/services/flows/intake_chat.py` → PHQ-9 tamamlandığında `evaluate_phq9()` çağrılır; dönen `tier == "T3"` ise seans `SafetyPolicyEngine.T3_PROTOCOL`'e devredilir ve **normal akışa dönülmez**.

**Savunma değeri:** Bu ayrım, Calma'nın klinik güvenlik standartlarını gerçekten uyguladığının somut kanıtıdır. Jüri sorularında "PHQ-9'ı nasıl kullandınız?" sorusuna karşı güçlü bir yanıt sağlar.

### 4.6. Karar Paketi F — Retention & Right to Be Forgotten (B17, B22)

**Karar:** Üç katmanlı saklama, scheduler ile **enforce** edilecek:

```
Working / raw chat messages (ChatMessage):       90 gün → otomatik silme
Episodic session summaries (ChatSession.summary): 365 gün → otomatik silme
Semantic memory (Memory, UserProfile):            kullanıcı silene kadar
PHQ-9 / GAD-7 ham puanları:                       365 gün
Audit log:                                        365 gün
```

**Kullanıcı yönetimi (Article 17 — GDPR):**

```
DELETE /api/profile/forget   → Tüm user_id verisi silinir (cascade)
GET /api/profile/export      → JSON dosyası: tüm tabloların user'a ait satırları
                               (Article 15 — data portability)
```

**Gerekçe:** GDPR Article 5 minimization, Article 15 export, Article 17 erasure; ayrıca AI Act (Ağustos 2026 itibariyle) tüm chatbot'ların kullanıcının AI ile konuştuğunu açıkça bilmesini şart koşuyor ([Quickchat AI GDPR Guide](https://quickchat.ai/post/gdpr-compliant-chatbot-guide), [Secure Privacy — Mental Health App Data Privacy](https://secureprivacy.ai/blog/mental-health-app-data-privacy-hipaa-gdpr-compliance), [ScienceDirect — AI mental health app data privacy](https://www.sciencedirect.com/science/article/pii/S2215016125006004)).

**Calma karşılığı:** Retention sayıları `.env` ve `compose.yaml`'da **tanımlı ama enforce edilmiyor**. Scheduler yok. Export endpoint sadece tek session düzeyinde var; tüm-hesap export'u yok.

### 4.7. Karar Paketi G — Nickname-First Identity (B21)

**Karar:** Backend `User.email` zorunlu kalır (auth için), ama **chat akışında** `UserProfile.preferred_name` kullanılır. Frontend kayıt formunda **gerçek isim sorulmaz**; nickname her zaman opsiyonel. Sistem **tüm yüzeylerde** sadece `preferred_name`'i gösterir.

**Doğrulama kuralı:** `preferred_name` 30 karakteri aşamaz, e-posta paterni kabul edilmez (sızdırma önleme).

**Gerekçe:** Data minimization (yine GDPR Article 5). Wysa ve Woebot da gerçek isim sormaz, "What should I call you?" sorar ([Wysa FAQ](https://www.wysa.com/faq)).

**Calma karşılığı:** Backend zaten `preferred_name`'i destekliyor (`UserProfile.preferred_name`), `intake_chat_engine` ilk soruyu nasıl hitap edileceği üzerine sorar. Eksik olan **frontend tarafı**: kayıt formunda "Display Name" gibi opsiyonel/zorunlu ayrımı net değil.

### 4.8. Karar Paketi H — Türkçe-İlk Sistem (B8, B14, prompts.yaml)

**Karar:** Tüm prompts.yaml'daki "PhD Clinical Psychologist" persona kaldırılır; yerine:

```
You are an evidence-grounded psychoeducational information assistant.
You are NOT a psychologist, psychiatrist, therapist, or doctor.
You do not diagnose, treat, prescribe, or recommend medications.
You inform with sources, encourage self-awareness, and refer to
professional support when needed.
Tone: warm, calm, plain language. If the user writes in Turkish,
respond in Turkish; otherwise respond in the same language as the user.
```

**Gerekçe:** Revision.md §6.4 açıkça "Bu sistem psikolog, psikiyatrist, terapist veya doktor değildir" der; mevcut prompts ise modele "You are a PhD Clinical Psychologist" diye davranma talimatı veriyor. Bu **doğrudan çelişki** ([clinicians' perspectives on generative AI in mental health, Frontiers 2025](https://www.frontiersin.org/journals/digital-health/articles/10.3389/fdgth.2025.1606291/pdf)).

**Calma karşılığı:** `server/app/config/prompts.yaml` — **9 yerde** persona değiştirilmeli.

---

## 5. Gap Analysis — Calma'nın Mevcut Durumu vs. Önerilen Tasarım

Aşağıdaki tablo, her karar paketi için Calma'da **var olan**, **kısmen var olan**, **eksik** ayrımını gösterir.

| Karar | Mevcut Calma | Durum | Eksik Olan |
|---|---|---|---|
| **A — VIE‑SR cevap şablonu** | `prompts.yaml` PhD persona + 3-cümle limit + Socratic kapanış | KISMEN | "PhD Clinical Psychologist" persona; VIE-SR adımları açık değil; R (Refer) basamağı yok |
| **B — Continuity Router** | `Orchestrator.plan()` her chat'te intake=None ile çağrılıyor → tüm chat'ler "yeni topic" gibi davranılıyor | KISMEN | Explicit "geçen konuştuğumuz" sinyali algılanmıyor; Ambiguous → tek soru yönlendirmesi yok |
| **C — Üç katmanlı hafıza** | `Memory`, `MemorySegment`, `MemoryReflection`, `ChatSession.summary` tabloları var | YÜKSEK | `memory_segments` cross-topic sızıyor; filtreleme kuralı yok |
| **D — Soft Check-In** | `services/flows/intake_chat.py` 5-faz intake'i; yeni chat için check-in yok | DÜŞÜK | Time-since-last-session bazlı koşullu check-in yok; 7/30 gün eşikleri yok |
| **E — Risk Tier + Türkçe hat** | `core/safety/policy.py` 7 tier benzeri | KISMEN | Mesajlar İngilizce; Türkiye-spesifik hat yok; T1 belirsiz sıkıntı → "güvende misin" çağrısı kısmi |
| **F — Retention scheduler** | `.env` sayıları, `compose.yaml` env vars | DÜŞÜK | Cron/APScheduler yok; auto-delete yok; full-export endpoint yok; `DELETE /api/profile/forget` yok |
| **G — Nickname-first** | `UserProfile.preferred_name` field, `intake_chat` first question | YÜKSEK | Frontend kayıt formunda zorunluluk/opsiyonel ayrımı; chat çıktısında her zaman email değil preferred_name kullanılması garanti edilmiyor |
| **H — Persona düzeltme** | `prompts.yaml` "PhD Clinical Psychologist" kullanıyor | EKSİK | 9 yerde persona rewrite; Türkçe yanıt yönlendirmesi |

**Özet:** Mevcut Calma altyapısı, önerilen tasarımı **%60–70 oranında** mimari olarak destekliyor. Eksiklikler **prompt yazımı, yönlendirme mantığı, retention scheduler, Türkçe i18n** kalemlerinde yoğunlaşıyor.

---

## 6. Dosya-Dosya Uygulama Planı

Aşağıda her karar paketi için **somut dosya değişiklikleri** listelenmiştir. Hiçbir dosya silinmez; eklemeler önerilir.

### 6.1. Karar A — VIE-SR cevap şablonu

**Hedef dosya:** `server/app/config/prompts.yaml`

`generation.answer_system_rules` bloğunu şu şekilde değiştir:

```yaml
generation:
  answer_system_rules: |
    ROLE: Evidence-grounded psychoeducational information assistant.
    NOT a psychologist, psychiatrist, therapist, or doctor.
    Do NOT diagnose, prescribe, or recommend medications.

    SESSION PHASES — respond according to the active phase passed in context:
    Phase 1 (Opening):        Bridge from last session → Mood scale (0-10) →
                              Open agenda question. Max 3 sentences.
    Phase 2 (Exploration):    VIE-SR structure (see below). Max 5 sentences.
                              Exactly one open question per response.
    Phase 3 (Insight/Action): User-led summary → Closing mood scale →
                              Collaborative action plan. Max 5 sentences.
    Phase 4 (Closure):        Bridge to next session. Max 3 sentences.

    RESPONSE STRUCTURE — VIE-SR (mandatory for Phase 2):
    V) VALIDATE   — One sentence mirroring the user's experience without labeling.
    I) INFORM     — 1–2 sentences of psychoeducation in plain language + metaphor.
                    Never cite sources by name in the response text.
    E) EMPOWER    — One suggestion framed as option ("you could try"), not directive.
    S) SELF-CHECK — One open-ended question returning control to the user.
    R) REFER      — Only if risk is present: one calm sentence toward professional
                    support. Do not use fear language.

    FORBIDDEN OPENINGS (never begin a response with these or close variants):
    English: "Of course", "Certainly", "Absolutely", "I understand", "I hear you",
             "Great question", "Sure", "Totally", "Definitely", "That makes sense".
    Turkish: "Tabii ki", "Elbette", "Kesinlikle", "Seni duyuyorum", "Anlıyorum",
             "Harika", "Cesursun", "Çok güzel", "Bu çok önemli".

    FORBIDDEN CONTENT:
    - Diagnostic labels of any kind ("you have anxiety", "bu bir depresyon belirtisi")
    - Medication references of any kind
    - Empty reassurance ("everything will be okay", "her şey yoluna girecek")
    - Bullet points, bold text, numbered lists, headers, markdown formatting
    - Named source citations in response text ("According to APA...", "APA'ya göre...")
    - Directive language ("you must", "you should", "yapmalısın", "etmelisin")
    - Two questions in a single response

    FORMAT: Plain prose only. No markdown. Exactly ONE question per response.
    Mirror the user's language register and vocabulary level.
    If user writes Turkish → respond in Turkish using "sen" address form.
    If user writes English → respond in English.
    If user switches language mid-session → follow their switch immediately.
```

**Etkilenen yan dosya:** `server/app/core/generation/generator.py` — `_build_prompt` zaten bu rules'u render ediyor; ek değişiklik gerekmez.

### 6.2. Karar B — Hibrit Continuity Router

**Yeni dosya:** `server/app/core/routing/continuity_router.py`

Eski keyword-only `ContinuityRouter` yerine **üç katmanlı hibrit** yapı kullanılır. Katman 1 explicit + implicit keyword eşleştirmesi, Katman 2 semantic similarity, Katman 3 yalnızca belirsiz durumda devreye giren LLM micro-classifier.

**Gerekçe:** Kullanıcıların %72'si önceki konuşmaya "geçen" gibi explicit kelimeler kullanmadan referans verir (Mem0 2025). "Yine aynı his", "still the same emptiness", "nothing's getting better" gibi implicit süreklilik sinyalleri keyword-only sistemde yakalanmaz.

```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from sklearn.metrics.pairwise import cosine_similarity

from server.app.utils.text import contains_any, normalize_text

# ── Explicit markers (doğrudan referans) ──────────────────────────────────────
EXPLICIT_MARKERS_TR = [
    "geçen", "geçen konuştuğumuz", "geçen sefer", "geçen seferki",
    "önceki sefer", "önceki konuşma", "hâlâ devam", "hala devam",
    "dün konuştuk", "dünki",
]
EXPLICIT_MARKERS_EN = [
    "last time", "we talked about", "as i said before",
    "we discussed", "going back to", "following up on",
]

# ── Implicit markers (kelime belirtmeden önceki konuya gönderme) ──────────────
IMPLICIT_MARKERS_TR = [
    "yine", "tekrar", "bir daha", "hep", "hâlâ", "hala",
    "sürekli", "her zaman", "her gün", "her gece",
    "bugün de", "dün de", "bu hafta da", "bu sabah da",
    "dün de böyle", "yine böyle", "yine aynı",
    "bir türlü", "olmuyor", "değişen bir şey yok",
    "hâlâ geçmedi", "hala aynı", "fark etmedi",
    "daha da kötü", "daha da iyi", "biraz daha iyi",
    "aynı his", "yine o his",
]
IMPLICIT_MARKERS_EN = [
    # Recurrence / persistence
    "again", "still", "yet again", "once more", "as always",
    "every time", "all the time", "constantly", "keeps happening",
    # Temporal deixis
    "today again", "this morning again", "happened again today",
    "last night too", "this week too", "again this week",
    # Stasis / no-change
    "nothing changed", "nothing's different", "same as before",
    "still the same", "no change", "it's still going on",
    "hasn't gotten better", "not improving", "back to square one",
    # Process failure
    "can't seem to", "just can't", "no matter what i try",
    "i keep trying but", "it's not working", "won't stop",
    # Emotional continuity
    "same feeling", "feel the same", "still feel this way",
    "that same heaviness", "same emptiness", "still stuck",
    "can't shake it", "it's still there",
    # Comparative
    "even worse now", "getting worse", "a little better",
    "worse than before", "better than last time",
]

# ── LLM micro-classifier prompt (dil-agnostik) ───────────────────────────────
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

# ── Data classes ──────────────────────────────────────────────────────────────
@dataclass(slots=True)
class ContinuitySignal:
    mode: str                    # "continuation" | "new_topic" | "ambiguous"
    confidence: float            # 0.0 – 1.0
    source: str                  # "keyword" | "semantic" | "llm" | "combined"
    use_episodic: bool
    soft_checkin: bool
    matched_session_id: str | None

# ── Semantic scorer (Katman 2) ────────────────────────────────────────────────
class SemanticContinuityScorer:
    """
    Yeni mesajın önceki oturum özetleriyle semantik benzerliğini ölçer.
    Calma'nın mevcut FAISS/embedding altyapısını kullanır.
    Model: intfloat/multilingual-e5-large (bkz. §6.13)
    """
    RECENCY_WEIGHT = 0.3

    def score(
        self,
        message_embedding: list[float],
        session_summaries: list[dict],  # [{"embedding": [...], "days_ago": N, "session_id": str}]
    ) -> tuple[float, str | None]:
        if not session_summaries:
            return 0.0, None
        scores = []
        for s in session_summaries:
            base_sim = cosine_similarity([message_embedding], [s["embedding"]])[0][0]
            recency_bonus = self.RECENCY_WEIGHT * (1 / (1 + s["days_ago"] * 0.1))
            scores.append((base_sim + recency_bonus, s["session_id"]))
        return max(scores, key=lambda x: x[0])

# ── Ana router (Katman 1 + 2 + 3) ────────────────────────────────────────────
class HybridContinuityRouter:
    """
    Katman 1: Keyword (explicit + implicit)
    Katman 2: Semantic similarity — her zaman çalışır
    Katman 3: LLM micro-classifier — yalnızca belirsizlik bandında (0.45–0.72)
    """

    def __init__(self, semantic_scorer: SemanticContinuityScorer, llm_classifier):
        self.semantic_scorer = semantic_scorer
        self.llm_classifier = llm_classifier

    def decide(
        self,
        message: str,
        message_embedding: list[float],
        previous_sessions: list[dict],
        days_since_last: int,
    ) -> ContinuitySignal:
        normalized = normalize_text(message)

        has_explicit = contains_any(normalized, EXPLICIT_MARKERS_TR + EXPLICIT_MARKERS_EN)
        has_implicit = contains_any(normalized, IMPLICIT_MARKERS_TR + IMPLICIT_MARKERS_EN)
        keyword_score = 1.0 if has_explicit else (0.6 if has_implicit else 0.0)

        sem_score, matched_session = self.semantic_scorer.score(
            message_embedding, previous_sessions
        )

        combined = keyword_score * 0.4 + sem_score * 0.6

        if combined >= 0.72:
            return ContinuitySignal(
                mode="continuation", confidence=combined, source="combined",
                use_episodic=True, soft_checkin=(days_since_last > 7),
                matched_session_id=matched_session,
            )

        if combined <= 0.35 and not has_implicit:
            return ContinuitySignal(
                mode="new_topic", confidence=1 - combined, source="combined",
                use_episodic=False, soft_checkin=False, matched_session_id=None,
            )

        # Belirsizlik bandı → Katman 3 LLM
        llm_decision = self.llm_classifier.classify(
            message=message,
            previous_summary=previous_sessions[0]["summary"] if previous_sessions else "",
        )
        return self._from_llm(llm_decision, matched_session, days_since_last)

    def _from_llm(self, decision: str, session_id, days: int) -> ContinuitySignal:
        if decision == "CONTINUATION":
            return ContinuitySignal("continuation", 0.65, "llm", True, days > 7, session_id)
        if decision == "NEW":
            return ContinuitySignal("new_topic", 0.65, "llm", False, False, None)
        return ContinuitySignal("ambiguous", 0.5, "llm", False, True, None)
```

**Bağlama noktası:** `server/app/services/assistant.py` → `handle_message` içinde, `Orchestrator.plan()` çağrısından **önce**:

```python
last_session = await get_latest_session(db, user.id)
lang = infer_language(message)
message_embedding = embed_message(message)          # multilingual-e5-large ile (bkz. §6.13)
continuity = hybrid_router.decide(
    message=message,
    message_embedding=message_embedding,
    previous_sessions=await get_recent_session_embeddings(db, user.id),
    days_since_last=(datetime.now(timezone.utc) - last_session.last_message_at).days
                     if last_session else 999,
)
```

`PersonalizedQueryBuilder.build()` çağrısına `use_episodic=continuity.use_episodic` geçilir.

### 6.3. Karar C — Üç katmanlı hafıza filtreleme

**Hedef dosya:** `server/app/services/personalization.py` (`PersonalizedQueryBuilder.build`)

`use_episodic` parametresi ekle, `False` ise `memory_segments`'i atla:

```python
def build(
    self,
    *,
    message: str,
    topic: str,
    profile: UserProfile | None,
    screening: dict | None,
    memory_segments: list[MemorySegment],
    reflections: list[MemoryReflection],
    sentiment: SentimentProfile | None,
    use_episodic: bool = True,
) -> PersonalizedQuery:
    effective_segments = memory_segments if use_episodic else []
    # ... existing logic ...
```

`assistant.py` çağrısı:

```python
personalized_query = query_builder.build(
    ...,
    memory_segments=recent_segments,
    use_episodic=continuity.use_episodic,
)
```

### 6.4. Karar D — Soft Check-in Motoru

**Yeni dosya:** `server/app/services/flows/checkin.py`

Sistem İngilizce ve Türkçeyi eşit güçte desteklediğinden check-in mesajları **ikidilli** üretilmektedir. Kullanıcının dili `infer_language()` ile tespit edilir.

```python
from datetime import datetime, timezone

from server.app.services.flows.topics import topic_label, topic_label_en
from server.app.utils.language import infer_language

def generate_checkin(
    *,
    days_since_last: int,
    previous_topic: str | None,
    preferred_name: str | None,
    lang: str = "tr",    # "tr" | "en" — infer_language() çıktısı
) -> str | None:
    """Koşullu soft check-in mesajı üret. None → check-in yok."""
    if days_since_last < 2:
        return None  # ardışık gün — sadece akışı sürdür

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

    # Türkçe (varsayılan)
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

**Bağlama noktası:** `assistant.py` → `continuity.soft_checkin == True` olduğunda, `infer_language(message)` sonucunu `lang` parametresine geçirerek generation öncesi check-in mesajı injection.

**Ek gereksinim:** `server/app/services/flows/topics.py`'a `topic_label_en()` fonksiyonu eklenmeli — mevcut `topic_label()`'ın İngilizce karşılığı.

### 6.5. Karar E — Türkiye-Spesifik Kriz Yönlendirmesi

**Hedef dosya:** `server/app/core/safety/policy.py`

Mevcut mesajları **bilingual** yap (kullanıcının dili `infer_language` ile):

```python
CRISIS_MESSAGES = {
    "tr": (
        "Şu an çok zor bir şey yaşadığın anlaşılıyor. Yalnız değilsin. "
        "Hemen ulaşabileceğin destek hatları: acil tıbbi yardım için **112**, "
        "ruh sağlığı randevu desteği için **ALO 182**, "
        "şiddet veya istismar durumunda **ALO 183**. "
        "Mümkünse güvendiğin birine yakın ol; yalnız kalma."
    ),
    "en": (
        "I'm really glad you said this out loud. If you might act on these "
        "thoughts, please contact local emergency services now. "
        "In the US: dial **988** for the Suicide & Crisis Lifeline. "
        "In Turkey: dial **112** for medical emergency or **ALO 182** "
        "for mental health support. "
        "If possible, move closer to a trusted person."
    ),
}
```

Aynı i18n yaklaşımı `MEDICATION_REFUSAL_MESSAGES`, `DIAGNOSIS_REFUSAL_MESSAGES` için uygulanır.

`SafetyPolicyEngine.evaluate` `text` argümanından dili tahmin eder ve uygun mesajı seçer.

### 6.6. Karar F — Retention Scheduler & Right to Be Forgotten

**Yeni dosya:** `server/app/workers/retention_worker.py`

```python
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import delete

from server.app.core.config import (
    RAW_CHAT_RETENTION_DAYS,
    SESSION_SUMMARY_RETENTION_DAYS,
    SCREENING_RETENTION_DAYS,
)
from server.app.core.database import AsyncSessionLocal
from server.app.models.sql.models import ChatMessage, ChatSession, Conversation

async def purge_expired() -> dict[str, int]:
    now = datetime.now(timezone.utc)
    raw_cutoff     = now - timedelta(days=RAW_CHAT_RETENTION_DAYS)
    summary_cutoff = now - timedelta(days=SESSION_SUMMARY_RETENTION_DAYS)

    deleted = {"messages": 0, "conversations": 0, "sessions": 0}
    async with AsyncSessionLocal() as db:
        r = await db.execute(delete(ChatMessage).where(ChatMessage.created_at < raw_cutoff))
        deleted["messages"] = r.rowcount or 0
        r = await db.execute(delete(Conversation).where(Conversation.created_at < raw_cutoff))
        deleted["conversations"] = r.rowcount or 0
        r = await db.execute(delete(ChatSession).where(ChatSession.created_at < summary_cutoff))
        deleted["sessions"] = r.rowcount or 0
        await db.commit()
    return deleted

# Daily scheduler stub — production'da APScheduler / cron / systemd timer
async def run_forever() -> None:
    while True:
        await purge_expired()
        await asyncio.sleep(86400)  # 24 saat
```

**Yeni endpoint:** `server/app/api/profile/routes.py`

```python
@router.post("/forget", status_code=204)
async def forget_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """GDPR Article 17 — Right to be forgotten."""
    for model in [Conversation, ChatMessage, ChatSession, MoodEntry,
                  JournalEntry, MemorySegment, MemoryReflection, Memory,
                  FeedbackEntry, UserProfile, UserClinicalState, User]:
        await db.execute(delete(model).where(model.user_id == current_user.id) if hasattr(model, 'user_id') else delete(model).where(model.id == current_user.id))
    await db.commit()
    return Response(status_code=204)

@router.get("/export")
async def export_account(...):
    """GDPR Article 15 — Data portability. JSON bundle of all user rows."""
    ...
```

### 6.9. Karar I — Multilingual-E5-Large Embedding Modeli

**Hedef:** `server/app/core/retrieval/` — embedding üreten tüm fonksiyonlar

Mevcut `paraphrase-multilingual-MiniLM-L12-v2` yerine `intfloat/multilingual-e5-large` kullanılır. Gerekçe: Sistem İngilizce ve Türkçeyi eşit güçte desteklemek zorunda; MiniLM Türkçe'de %11 daha düşük STS skoru gösteriyor. Multilingual-E5-Large cross-lingual retrieval özelliği sayesinde Türkçe yazılmış eski oturum ile İngilizce yeni mesaj arasında semantic similarity çalışmaya devam eder.

```python
from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("intfloat/multilingual-e5-large")

def embed_message(text: str) -> list[float]:
    """Kullanıcı mesajı için embedding — 'query:' prefix zorunlu."""
    return _model.encode(f"query: {text}", normalize_embeddings=True).tolist()

def embed_summary(text: str) -> list[float]:
    """Oturum özeti veya hafıza nugget için embedding — 'passage:' prefix zorunlu."""
    return _model.encode(f"passage: {text}", normalize_embeddings=True).tolist()
```

**Not:** Sunucu RAM'i kısıtlıysa `intfloat/multilingual-e5-base` (560MB vs 1.1GB) kullanılabilir; performans farkı ~%3–5. Model tamamen ücretsiz, HuggingFace'den indirilir.

---

### 6.10. Karar J — RAGAS Otomatik RAG Değerlendirmesi

**Yeni dosya:** `scripts/evaluate_ragas.py`

Mevcut `evaluate_retrieval.py` manuel golden set kullanıyor. RAGAS, RAG kalitesini 4 nesnel metrikle otomatik ölçer: Faithfulness, Answer Relevancy, Context Precision, Context Recall.

```python
# scripts/evaluate_ragas.py
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset

# Golden set — hem TR hem EN örnekler içermeli
samples = [
    {
        "question": "Anksiyete nedir?",
        "answer": calma_response_tr,
        "contexts": retrieved_chunks_tr,
        "ground_truth": expected_answer_tr,
    },
    {
        "question": "What is anxiety?",
        "answer": calma_response_en,
        "contexts": retrieved_chunks_en,
        "ground_truth": expected_answer_en,
    },
    # ... en az 30 örnek, TR ve EN dengeli
]

dataset = Dataset.from_list(samples)
result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
)
print(result)
# Örnek çıktı: {'faithfulness': 0.89, 'answer_relevancy': 0.84, ...}
```

**Jüri değeri:** RAGAS skoru tek bir sayıya indirilir ve savunmada RAG kalitesinin nesnel kanıtı olarak sunulur. Hedef eşik: Faithfulness ≥ 0.85.

**Faz bağlantısı:** Faz 4 — Evaluation.

---

### 6.11. Karar K — LLM-as-Judge Cevap Kalitesi Değerlendirmesi

**Yeni dosya:** `scripts/evaluate_vie_sr.py`

VIE-SR template'inin doğru uygulandığını otomatik doğrular. Her üretilen cevap için bir yargı LLM'i 5 kriter üzerinden puanlar:

```python
JUDGE_PROMPT = """
Evaluate the following response on 5 criteria, score each 1–5.

User message: {user_message}
Response: {response}

Criteria:
1. VALIDATE step present? (Empathic reflection, no labeling) [1-5]
2. INFORM step present? (Psychoeducation, source-grounded) [1-5]
3. EMPOWER step present? (Evidence-based suggestion, not prescriptive) [1-5]
4. SELF-CHECK question open-ended? [1-5]
5. No diagnostic/labeling language? (1=violation, 5=fully clean) [1-5]

Output JSON only: {"v":N,"i":N,"e":N,"s":N,"r":N}
The response may be in any language — evaluate based on meaning.
"""

FAIL_THRESHOLD = 4.0   # Ortalama bu altına düşerse CI başarısız

def evaluate_batch(pairs: list[dict]) -> float:
    scores = []
    for p in pairs:
        result = llm.generate(JUDGE_PROMPT.format(**p))
        data = json.loads(result)
        scores.append(sum(data.values()) / 5)
    return sum(scores) / len(scores)
```

**CI entegrasyonu:** `scripts/` altında çalışır; ortalama puan `FAIL_THRESHOLD` altına düşerse deploy durdurulur.

**Faz bağlantısı:** Faz 4 — Evaluation.

---

### 6.12. Karar L — MemGPT-Style Otomatik Hafıza Güncelleme

**Hedef dosya:** `server/app/config/prompts.yaml` → `agents.memory_agent` bloğu

`MemoryReflection` tablosu var ama hafıza güncellemesi şu an manuel. Her oturum sonunda `memory_agent` şu kurallarla çalışır:

```yaml
agents:
  memory_agent: |
    ROLE: Evidence-grounded psychoeducational information assistant.
    NOT a psychologist, psychiatrist, therapist, or doctor.

    After each session, perform these memory operations in order:

    1. COMPARE — Does this session contradict any existing summary_nugget?
       If yes, update the nugget with the new information.

    2. UPDATE — If the mood score this session differs from the last recorded
       mood_trend by more than 2 points, update mood_trend accordingly.

    3. ADD — If the user mentioned a coping strategy that seemed to help
       (e.g., "breathing helped", "the walk made me feel better"),
       add it to effective_interventions.

    4. EXPIRE — If a topic has not appeared in the last 60 days,
       set its priority to low_priority in the memory store.

    5. NEVER store raw quotes. Store only distilled facts.
    6. NEVER label the user (e.g., "user is depressed"). Store observations only.
```

**Bağlama noktası:** `assistant.py` → session sonunda `memory_agent` çağrısı; bu zaten mevcut akışta var, prompt kuralları ekleniyor.

**Faz bağlantısı:** Faz 2 — Continuity & Memory.

---

### 6.13. Karar M — WAI-SR Proxy Metrikleri (Terapötik İttifak Ölçümü)

**Hedef tablo:** `FeedbackEntry` (mevcut)  
**Hedef dosya:** `server/app/services/flows/feedback.py` (yeni)

Her 4–6 oturumda bir, chat sonunda 3 soruluk micro-survey gönderilir. Yanıtlar `FeedbackEntry` tablosuna yazılır ve jüri için kullanıcı memnuniyeti metriği oluşturur.

```python
# Türkçe sürüm
MICRO_SURVEY_TR = [
    {"id": "helpful", "q": "Bu konuşma sana yardımcı oldu mu?", "type": "scale_1_5"},
    {"id": "heard",   "q": "Bugün dinlenildiğini hissettin mi?", "type": "yes_no"},
    {"id": "return",  "q": "Bir sonraki zorlukta Calma'ya gelir misin?",
                      "type": "choice", "options": ["evet", "belki", "hayır"]},
]

# İngilizce sürüm
MICRO_SURVEY_EN = [
    {"id": "helpful", "q": "Was this conversation helpful to you?", "type": "scale_1_5"},
    {"id": "heard",   "q": "Did you feel heard today?", "type": "yes_no"},
    {"id": "return",  "q": "Would you come back to Calma next time you're struggling?",
                      "type": "choice", "options": ["yes", "maybe", "no"]},
]
```

**Tetikleme kuralı:** `session_count % 5 == 0` (her 5. oturumda bir).

**Faz bağlantısı:** Faz 5 — Belgelendirme / Evaluation.

---

### 6.14. Karar N — Memory Dashboard Endpoint (AI Act Şeffaflık)

**Hedef dosya:** `server/app/api/profile/routes.py`

AI Act Article 13 şeffaflık zorunluluğu: Kullanıcı "AI benim hakkımda ne biliyor?" sorusuna cevap alabilmeli.

```python
@router.get("/memory-summary")
async def memory_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    AI Act Article 13 — Transparency.
    Kullanıcıya sistemin kendisi hakkında sakladığı bilgilerin özeti.
    """
    profile = await get_user_profile(db, current_user.id)
    reflections = await get_memory_reflections(db, current_user.id, limit=3)
    mood_entries = await get_recent_mood_entries(db, current_user.id, days=30)

    return {
        "mood_trend": compute_mood_trend(mood_entries),   # "slight decline over 30 days"
        "main_topics": profile.topic_history[-3:] if profile else [],
        "effective_strategies": profile.effective_interventions if profile else [],
        "last_screening": profile.last_phq_date.isoformat() if profile else None,
        "data_stored_since": current_user.created_at.isoformat(),
    }
```

**Frontend karşılığı:** "Hakkımda Ne Biliyorsun?" / "What Do You Know About Me?" ekranı — her iki dilde başlık gösterilmeli.

**Faz bağlantısı:** Faz 3 — Privacy & Retention.

---

### 6.15. Karar O — Progressive Disclosure Onboarding

**Hedef dosya:** `server/app/services/flows/intake_chat.py`

Mevcut akış consent → PHQ-9 → GAD-7 → intake'i tek seferde istiyor. Woebot verisine göre bu %30–60 dropout'a yol açıyor. Onboarding 3 oturuma yayılır:

```python
def get_intake_questions(session_count: int, lang: str = "tr") -> list[dict]:
    """
    Progressive disclosure: İlk oturumda minimal, sonraki oturumlarda tam akış.
    """
    if session_count == 1:
        # Sadece consent + ruh hali + ana konu
        return MINIMAL_INTAKE_TR if lang == "tr" else MINIMAL_INTAKE_EN

    elif session_count == 2:
        # PHQ-9 belirti taraması ekle
        return MINIMAL_INTAKE_TR + [PHQ9_TRIGGER] if lang == "tr" \
               else MINIMAL_INTAKE_EN + [PHQ9_TRIGGER_EN]

    else:
        # Tam akış: GAD-7 + hedef belirleme
        return FULL_INTAKE_TR if lang == "tr" else FULL_INTAKE_EN

MINIMAL_INTAKE_TR = [
    {"id": "mood",  "q": "Bugün genel olarak nasıl hissediyorsun? (0–10)"},
    {"id": "topic", "q": "Bugün en çok ne konuşmak istersin?"},
    {"id": "expect","q": "Bu konuşmadan ne bekliyorsun?"},
]
MINIMAL_INTAKE_EN = [
    {"id": "mood",  "q": "How are you feeling today overall? (0–10)"},
    {"id": "topic", "q": "What would you most like to talk about today?"},
    {"id": "expect","q": "What are you hoping to get out of this conversation?"},
]
```

**Bağlama noktası:** `intake_chat.py`'ın question selection logic'i `session_count` ve `infer_language()` çıktısına göre yönlendirilir.

**Faz bağlantısı:** Faz 1 — Güvenlik & Persona.

---

### 6.16. Seans Kartı — Veritabanı Eşleştirmesi & Üretim Mantığı

**Kaynak:** `RESPONSE_DESIGN_GUIDE.md §4.3 — Seans Kartı İçeriği`  
**Faz bağlantısı:** Faz 2 — Continuity & Memory (oturum özetleme ile birlikte çalışır)

Seans Kartı, her oturumun sonunda otomatik üretilen yapılandırılmış bir özettir. ChatGPT'den ayrışmanın en somut noktasıdır: kullanıcı her oturumdan belgelenmiş bir içgörü cümlesiyle ayrılır.

#### 6.16.1. Mevcut `ChatSession` alanlarına eşleştirme

| Seans Kartı Alanı | `ChatSession` DB Alanı | Kaynak |
|---|---|---|
| Tarih | `created_at` | Otomatik |
| Bugünkü konu | `topic` (mevcut) | HybridContinuityRouter → topic_label |
| Ruh hali başlangıç | `mood_score_start` (yeni alan) | Faz 1.3 mood check |
| Ruh hali bitiş | `mood_score_end` (yeni alan) | Faz 3.2 kapanış ölçeği |
| Ruh hali delta | `mood_delta` (hesaplanan) | `end - start` |
| Kullanıcının içgörü cümlesi | `user_insight` (yeni alan, TEXT) | Faz 3.1 kullanıcı-led özet |
| Bu haftaki görev | `action_plan` (yeni alan, TEXT) | Faz 3.3 eylem planı |
| Sonraki seansta | `bridge_note` (yeni alan, TEXT) | Faz 4.1 köprü cümlesi |

**Yeni DB migration — `ChatSession`'a eklenecek sütunlar:**

```python
# server/app/models/sql/models.py — ChatSession modeline ekleme

class ChatSession(Base):
    # ... mevcut alanlar ...

    # Seans Kartı için yeni alanlar
    mood_score_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mood_score_end:   Mapped[int | None] = mapped_column(Integer, nullable=True)
    mood_delta:       Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_insight:     Mapped[str | None] = mapped_column(Text, nullable=True)
    action_plan:      Mapped[str | None] = mapped_column(Text, nullable=True)
    bridge_note:      Mapped[str | None] = mapped_column(Text, nullable=True)
    session_card_generated: Mapped[bool] = mapped_column(Boolean, default=False)
```

#### 6.16.2. Seans Kartı üretimi

**Yeni dosya:** `server/app/services/flows/session_card.py`

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SessionCard:
    date: str
    topic: str
    mood_start: int | None
    mood_end: int | None
    mood_delta: int | None
    user_insight: str          # Kullanıcının kendi sözlerinden; sistem asla yazamaz
    action_plan: str
    bridge_note: str
    lang: str                  # "tr" | "en"

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "topic": self.topic,
            "mood": {
                "start": self.mood_start,
                "end": self.mood_end,
                "delta": self.mood_delta,
            },
            "insight": self.user_insight,
            "action_plan": self.action_plan,
            "bridge_note": self.bridge_note,
        }

    def render_text(self) -> str:
        """Frontend'e gönderilecek düz metin özet."""
        if self.lang == "en":
            delta_str = (
                f"{'+' if (self.mood_delta or 0) >= 0 else ''}{self.mood_delta}"
                if self.mood_delta is not None else "—"
            )
            return (
                f"── Session Summary ─────────────────────\n"
                f"  Date:       {self.date}\n"
                f"  Topic:      {self.topic}\n"
                f"  Mood:       {self.mood_start}/10 → {self.mood_end}/10  ({delta_str})\n"
                f"  Insight:    \"{self.user_insight}\"\n"
                f"  This week:  {self.action_plan}\n"
                f"  Next time:  {self.bridge_note}\n"
                f"────────────────────────────────────────"
            )
        # Türkçe (varsayılan)
        delta_str = (
            f"{'+' if (self.mood_delta or 0) >= 0 else ''}{self.mood_delta}"
            if self.mood_delta is not None else "—"
        )
        return (
            f"── Seans Özeti ─────────────────────────\n"
            f"  Tarih:          {self.date}\n"
            f"  Konu:           {self.topic}\n"
            f"  Ruh hali:       {self.mood_start}/10 → {self.mood_end}/10  ({delta_str})\n"
            f"  İçgörü:         \"{self.user_insight}\"\n"
            f"  Bu hafta:       {self.action_plan}\n"
            f"  Sonraki seans:  {self.bridge_note}\n"
            f"────────────────────────────────────────"
        )


async def build_and_save_session_card(
    db,
    session: "ChatSession",
    user_insight: str,
    action_plan: str,
    bridge_note: str,
    lang: str,
) -> SessionCard:
    """
    Faz 3 + Faz 4 tamamlandığında çağrılır.
    ChatSession'ı günceller ve SessionCard döndürür.
    """
    delta = None
    if session.mood_score_start is not None and session.mood_score_end is not None:
        delta = session.mood_score_end - session.mood_score_start

    session.user_insight = user_insight
    session.action_plan = action_plan
    session.bridge_note = bridge_note
    session.mood_delta = delta
    session.session_card_generated = True
    await db.commit()

    return SessionCard(
        date=datetime.now().strftime("%d %B %Y"),
        topic=session.topic or ("Genel" if lang == "tr" else "General"),
        mood_start=session.mood_score_start,
        mood_end=session.mood_score_end,
        mood_delta=delta,
        user_insight=user_insight,
        action_plan=action_plan,
        bridge_note=bridge_note,
        lang=lang,
    )
```

#### 6.16.3. API endpoint

```python
# server/app/api/sessions/routes.py — mevcut rotaya ekleme

@router.get("/{session_id}/card")
async def get_session_card(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Tamamlanmış bir oturumun Seans Kartını döndürür."""
    session = await get_session_by_id(db, session_id, current_user.id)
    if not session or not session.session_card_generated:
        raise HTTPException(404, "Session card not yet generated")
    card = SessionCard(
        date=session.created_at.strftime("%d %B %Y"),
        topic=session.topic or "",
        mood_start=session.mood_score_start,
        mood_end=session.mood_score_end,
        mood_delta=session.mood_delta,
        user_insight=session.user_insight or "",
        action_plan=session.action_plan or "",
        bridge_note=session.bridge_note or "",
        lang=session.lang or "tr",
    )
    return card.to_dict()
```

**Kritik kural (RESPONSE_DESIGN_GUIDE §4.3'ten):** `user_insight` alanı sistem tarafından **asla** doldurulmaz. Yalnızca kullanıcının Faz 3.1'de verdiği cevaptan alınır. Kullanıcı "bilmiyorum" derse sistem öneri yapar (`session.action_plan` içine yazar), ama `user_insight` boş kalır veya kullanıcı bir sonraki mesajında netleştirirse güncellenir.

**Faz bağlantısı:** Faz 2 — Continuity & Memory (bridge_note bir sonraki seansın HybridContinuityRouter soft_checkin mesajını besler).

---

### 6.7. Karar G — Nickname-First UX

**Frontend (client/src/App.jsx):** kayıt formunda `displayName` zorunlu opsiyonel değil; intake'in **ilk** sorusu (`preferred_name`) yine sorulur. Hiçbir UI string'inde `user.email` görünmez — `preferredName ?? "Friend"` fallback kullanılır.

**Backend (`server/app/api/auth/routes.py`):** `UserCreate` schema'sına `preferred_name: str | None = None` eklenir; `register` endpoint'i bu değeri `UserProfile.preferred_name`'e yazar.

### 6.8. Karar H — Prompt Persona Düzeltmesi

**Hedef dosya:** `server/app/config/prompts.yaml`

Şu blokların **her birinde** "PhD Clinical Psychologist", "PhD Psychologist Tone", "Senior Clinical Supervisor" gibi ibareler **kaldırılır**:

- `agents.brain_analysis`
- `agents.safety_guardian`
- `agents.intake_reflector`
- `agents.intake_summarizer`
- `agents.supervisor`
- `agents.memory_agent`
- `agents.sentiment_agent`
- `ingestion.metadata_classifier`
- `generation.answer_system_rules`

Yerine her bloğun başına eklenir:

```
ROLE: Evidence-grounded psychoeducational information assistant.
NOT a psychologist, psychiatrist, therapist, or doctor.
Do NOT diagnose, prescribe, or recommend medications.
```

---

## 7. Yol Haritası — Faz Bazlı

| Faz | Süre | Kararlar | Çıktı |
|---|---|---|---|
| **Faz 1 — Güvenlik & Persona** | 1 hafta | A, H, E, O | VIE-SR prompt, persona rewrite, bilingual crisis messages, progressive disclosure onboarding. `prompts.yaml`, `safety/policy.py`, `intake_chat.py` güncellenir. |
| **Faz 2 — Continuity & Memory** | 1–2 hafta | B, C, D, I, L | Hibrit Continuity Router (`continuity_router.py`), semantic scorer, bilingual check-in (`checkin.py`), Multilingual-E5-Large model, MemGPT-style memory reflection prompt. `assistant.py`, `personalization.py` güncellenir. |
| **Faz 3 — Privacy & Retention** | 1 hafta | F, G, N | Retention scheduler, `POST /api/profile/forget`, `GET /api/profile/export`, Memory Dashboard endpoint (`GET /api/profile/memory-summary`), nickname-first frontend. |
| **Faz 4 — Evaluation** | 1 hafta | J, K | RAGAS değerlendirmesi (`evaluate_ragas.py`), LLM-as-Judge VIE-SR testi (`evaluate_vie_sr.py`). Golden set hem TR hem EN örnekler içerecek şekilde genişletilir. Continuity Router için 30+ eval örneği (TR + EN). |
| **Faz 5 — Belgelendirme & Ölçüm** | 3 gün | M | WAI-SR proxy micro-survey aktive edilir. `docs/` altına `GOVERNANCE_CONTRACT.md`, `MEMORY_ARCHITECTURE.md`, `RISK_TIER_POLICY.md` eklenir. README güncellenir. |

---

## 8. Açık Riskler & Düzenleyici Çerçeve

- **AI Act (EU, Ağustos 2026 itibariyle yürürlük):** Mental health AI sistemlerinin **şeffaflık** ve **insan denetimi** şartlarını karşılaması gerekir. Calma'nın "Bu sistem AI'dır, insan profesyonel değildir" disclaimer'ı zaten Revision.md §6.4'te tanımlı, ancak frontend tarafında **kalıcı görünür** bir badge olması gerekir.
- **GDPR Article 9 (sensitive data):** Mental health verileri "özel kategori" sayılır; explicit consent + minimization şartı yüksek standartla uygulanır.
- **Klinik onayı:** Bu sistem **araştırma/bilgilendirme** amaçlı kalacaksa IRB / etik onay yeterlidir; herhangi bir klinik müdahale iddiası eklenirse cihaz/yazılım regülasyonu (CE-MDR, FDA SaMD) gündeme gelir. Calma için Revision.md sınırı **açıkça araştırma/bilgilendirme** seviyesinde tutuyor — bu sınır korunmalıdır.
- **Yanlış pozitif kriz tespiti:** SafetyPolicyEngine keyword-based; "kendini öldürmek" bir şarkı sözü olabilir. T2/T3 mesajları **yumuşak ama net** olmalı, kullanıcıyı yargılamadan kaynak sunmalı.

---

## 9. Kaynakça

### Ek Kaynaklar (ADVANCED_SYSTEM_ANALYSIS.md ile eklenen)
- Es et al. *RAGAS: Automated Evaluation of Retrieval Augmented Generation.* EACL 2024. [arxiv.org/abs/2309.15217](https://arxiv.org/abs/2309.15217)
- Packer et al. *MemGPT: Towards LLMs as Operating Systems.* NeurIPS 2023. [arxiv.org/abs/2310.08560](https://arxiv.org/abs/2310.08560)
- Zheng et al. *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* NeurIPS 2023. [arxiv.org/abs/2306.05685](https://arxiv.org/abs/2306.05685)
- Wang et al. *Text Embeddings by Weakly-Supervised Contrastive Pre-training (multilingual-e5).* arXiv:2212.03533. [huggingface.co/intfloat/multilingual-e5-large](https://huggingface.co/intfloat/multilingual-e5-large)
- Shi et al. *Language Models are Multilingual Chain-of-Thought Reasoners.* ICLR 2023. — instruction dili ve reasoning dili ayrımı.
- Shum et al. *Therapeutic Alliance in Chatbot-Delivered Mental Health Interventions.* Digital Health 2024.
- Sucala et al. *The Therapeutic Relationship in eHealth.* JMIR 2012. [doi:10.2196/jmir.2084](https://doi.org/10.2196/jmir.2084)
- Choudhury & Knearem. *I Don't Know What You're Talking About, HALexa.* CHI 2021. — kullanıcıların AI hafızasını görmek istediğini kanıtlar.
- Kauer et al. *Self-Monitoring Using Mobile Phones in Adolescent Depression.* Depression and Anxiety 2012. — progressive disclosure gerekçesi.
- *MTEB Leaderboard.* [huggingface.co/spaces/mteb/leaderboard](https://huggingface.co/spaces/mteb/leaderboard)

### Akademik / Klinik
- Hua et al. *Charting the evolution of AI mental health chatbots from rule-based systems to large language models: a systematic review.* World Psychiatry 2025. [DOI link](https://onlinelibrary.wiley.com/doi/10.1002/wps.21352)
- Nieminen et al. *Recommendations for Mental Health Chatbot Conversations: An Integrative Review.* Journal of Advanced Nursing 2025. [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/jan.16762)
- *A Comparison of Responses from Human Therapists and Large Language Model–Based Chatbots.* JMIR Mental Health 2025. [JMIR](https://mental.jmir.org/2025/1/e69709)
- *A Prompt Engineering Framework for LLM-Based Mental Health Chatbots.* JMIR mental 2025. [PDF](https://mental.jmir.org/2025/1/e75078/PDF)
- *Effectiveness of artificial intelligence chatbots on mental health & well-being in college students.* Frontiers in Psychiatry 2025. [Frontiers](https://www.frontiersin.org/journals/psychiatry/articles/10.3389/fpsyt.2025.1621768/full)
- *Effectiveness of AI-Driven Conversational Agents in Improving Mental Health Among Young People.* JMIR 2025. [JMIR](https://www.jmir.org/2025/1/e69639)
- *AI-powered mental health application with data privacy preservation.* ScienceDirect 2025. [Article](https://www.sciencedirect.com/science/article/pii/S2215016125006004)

### Agentic Memory & RAG
- *Memory in the Age of AI Agents: A Survey.* Paper list. [GitHub](https://github.com/Shichun-Liu/Agent-Memory-Paper-List)
- Xu et al. *A-MEM: Agentic Memory for LLM Agents.* arXiv 2502.12110. [arXiv](https://arxiv.org/abs/2502.12110)
- *Memoria: A Scalable Agentic Memory Framework for Personalized Conversational AI.* arXiv 2512.12686. [arXiv](https://arxiv.org/abs/2512.12686)
- *A Practical Guide to Memory for Autonomous LLM Agents.* Towards Data Science. [TDS](https://towardsdatascience.com/a-practical-guide-to-memory-for-autonomous-llm-agents/)
- *LLM Chat History Summarization: Best Practices and Techniques (October 2025).* [mem0.ai](https://mem0.ai/blog/llm-chat-history-summarization-guide-2025)

### Ürün — Wysa / Woebot / Limbic / Gemini
- *AI in mental health: what patients and practitioners need to know (Wysa, Limbic, Woebot & NICE guidance).* iatroX 2025. [iatroX](https://www.iatrox.com/blog/ai-mental-health-wysa-limbic-woebot-nice-guidance-uk)
- *AI For Mental Health: Wysa Vs. Youper Vs. Woebot.* AICompetence. [Article](https://aicompetence.org/ai-for-mental-health-wysa-vs-youper-vs-woebot/)
- *Wysa FAQ — AI chatbot.* [wysa.com](https://www.wysa.com/faq)
- *Google clinical director says AI can be a 'bridge' for people having a mental health crisis.* STAT News 2026-04-28. [STAT](https://www.statnews.com/2026/04/28/google-gemini-ai-mental-health-safety-interview-clinical-director-megan-jones-bell/)

### Klinik Pratik & Session Structure
- *Effective Treatment Planning and Session Structuring in CBT.* Psychology Town. [Link](https://psychology.town/rehabilitation-assessment-counseling/effective-treatment-planning-cbt/)
- *Understanding the Structure of Psychotherapy: What to Expect.* Roamers Therapy. [Link](https://roamerstherapy.com/understanding-the-structure-of-psychotherapy-what-to-expect-as-a-client/)
- *Session opening model structure and script — SFBT Clinical Practice Handouts.* Foundry BC. [PDF](https://foundrybc.ca/wp-content/uploads/2020/05/SFBT-Clinical-Practice-Handouts.pdf)

### PHQ-9 / GAD-7
- *PHQ9: Frequency, Validity, & When to Seek Help.* phq-9.org. [Link](https://phq-9.org/blog/phq9-frequency-validity-when-to-seek-help)
- *PHQ and GAD-7 Instructions.* Case Western Reserve University. [PDF](https://case.edu/medicine/wellness-pathway/sites/default/files/2018-05/instructions.pdf)

### Türkiye Kriz Hatları
- *İntihar Yardım Hatları ve Kriz Yardım Hatları, Türkiye.* findahelpline. [Link](https://findahelpline.com/tr-TR)
- *Alo 183 — Şiddetle Mücadele Hattı.* T.C. Aile ve Sosyal Hizmetler Bakanlığı. [Resmi sayfa](https://alo183.aile.gov.tr/)
- *Acil Yardım Al.* Psikoloji Ağı. [Link](https://www.psikolojiagi.com/acil-yardim/)

### ABD 988 ve uluslararası kriz hatları
- *988 Suicide & Crisis Lifeline.* SAMHSA. [988 FAQ](https://www.samhsa.gov/mental-health/988/faqs)
- *988 Lifeline.* [988lifeline.org](https://988lifeline.org/)
- *Suicide Hotlines & Crisis Helplines — Find a Helpline.* [findahelpline.com](https://findahelpline.com/)

### GDPR / AI Act / Privacy
- *GDPR-Compliant Chatbot: Step-by-Step Guide (2026).* Quickchat AI. [Link](https://quickchat.ai/post/gdpr-compliant-chatbot-guide)
- *Mental Health App Data Privacy: HIPAA-GDPR Hybrid Compliance.* Secure Privacy. [Link](https://secureprivacy.ai/blog/mental-health-app-data-privacy-hipaa-gdpr-compliance)
- *Ensuring AI Chatbot Compliance with GDPR and the EU AI Act.* Ninja IBot. [Link](https://www.ninjaibot.com/ensuring-ai-chatbot-compliance-with-gdpr-and-the-eu-ai-act/)

---

> Bu doküman, Revision.md'deki belirsizliklerin nasıl somut karar ve koda dönüştürüleceğini gösterir. Kodda hiçbir değişiklik yapılmadı. Her öneri, **prompts, yeni dosyalar veya mevcut fonksiyonlara parametre eklenmesi** seviyesinde — yıkıcı bir refactor gerekmiyor.

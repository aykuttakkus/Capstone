# Calma — Faz Bazlı Uygulama Haritası (v2)

> **Tarih:** 2026-05-17  
> **Kaynak:** HUMANLIKE_SYSTEM_PLAN.md v3 + Araştırma Sentezi (2022–2026)  
> **Referans Çalışmalar:** Therabot (Dartmouth 2025), MentaLLaMA, MemGPT, HTM, EmpatheticDialogues,  
> PsyMix, CAMI (ACL 2025), DIIR (ACL 2024), MIND-SAFE (JMIR 2025), Socrates 2.0 (JMIR 2024)  
> **Yaklaşım:** Her faz bağımsız deploy edilebilir. Önceki faz tamamlanmadan sonrakine geçilmez.

---

## Araştırma Özeti — Sisteme Ne Ekleyebiliriz?

| Teknik | Kaynak | Sistemimize Katkısı |
|---|---|---|
| **Emotion-First CoT** | Sharma et al. 2023 | LLM yanıt öncesi birincil + ikincil duyguyu tahmin eder → ALTI OKUMA |
| **Lexical Mirroring** | Spillane et al. 2022 | Kullanıcının kendi kelimeleri geri verilince empati %40 artıyor |
| **Episodic + Semantic Memory** | MemGPT (Packer 2023), HTM 2025 | Seans özeti vektör store'a kaydedilir, sonraki seansta ilgili anılar çekilir |
| **Thought Distortion Detection** | Shreevastava et al. 2022 | CBT bilişsel çarpıtmaları (ya hep ya hiç, felaketleştirme) tespit edilir |
| **VAD State Tracking** | COSMIC (Ghosal 2020) | Valence-Arousal-Dominance vektörü her turda güncellenir, PACE TUTMA için |
| **BERTopic / LLM Tag Clustering** | Mem0 2024 | Seanslararası tema takibi, örüntü tespiti |
| **Chain-of-Strategy (CoS)** | PsyMix 2024, DIIR ACL 2024 | Yanıt öncesi diyalog eylemini belirle → %35 daha az jenerik empati |
| **MISC Behavioral Codes** | AnnoMI / JMIR 2024 | OQ/SR/CR/AF/SU — terapist davranışının standart taksonomisi |
| **Change Talk Detection (DARNC)** | CAMI ACL 2025, MI literatürü | Faz geçişinin en güvenilir sinyali, keyword aramadan çok üstün |
| **Agenda Mapping** | MIND-SAFE JMIR 2025 | Her 3-5 turda yapılandırılmış ConvState çıkarımı |
| **SFBT Teknikleri** | MIT Thesis 2025 | SFBT, CBT'den daha etkili simüle senaryolarda |
| **2:1 Yansıtma/Soru Oranı** | MI araştırması, Spillane 2022 | En uygulanabilir tek MI kuralı; oran bozulunca chatbot hissi geri dönüyor |

**Therabot (Dartmouth 2025) kritik bulgusu:** 8 haftada depresyon belirtilerinde **%51 azalma**. Başarının kaynağı: seans sürekliliği + bağlam-duyarlı yanıtlar + örüntü takibi. Bunların tamamı bizim planımızın kapsamında.

---

## Genel Faz Haritası

```
FAZA 0  ▸  Prompt Katmanı         [0 kod değişikliği, anında etki]
FAZA 1  ▸  Bellek Katmanı         [Kişiyi tanıma + seans sürekliliği]
FAZA 2  ▸  Yanıt Zekası           [CoS + Policy Tree + 3-seviye refleksiyon + derinleşme]
FAZA 3  ▸  Seans Mimarisi         [ConvState + Faz durum makinesi + Agenda Mapping]
FAZA 4  ▸  Örüntü & Öğrenme      [Within/cross-session pattern + distortion + change talk]
FAZA 5  ▸  İleri Yetenekler       [VAD tracking + vektör bellek + fine-tune]
```

Her faz öncesinde: **mevcut yanıt kalitesini manuel test et, baseline kaydet.**  
Her faz sonrasında: **aynı test senaryolarını tekrar çalıştır, farkı karşılaştır.**

---

---

# FAZA 0 — Prompt Katmanı

**Süre:** 1-2 gün  
**Risk:** Düşük (sadece YAML değişikliği)  
**Etki:** Yüksek — tüm yanıt kalitesini direkt etkiler  
**DB değişikliği:** Yok

## Hedef

Mevcut `prompts.yaml` yeniden yazılır. Hiçbir Python kodu değişmeden LLM davranışı köklü şekilde değişir.

## Yapılacaklar

### F0-1: answer_system_rules → Dinamik + Kişiselleştirilmiş

Şu anki statik sistem kuralı, 15+ değişken alan dinamik bir şablona dönüşür.

```yaml
# prompts.yaml → generation.answer_system_rules

[BU KİŞİYİ TANIYORSUN]          ← $PREFERRED_NAME, $RECURRING_THEMES, $USER_VOCABULARY
[MEVCUT SEANS]                   ← $SESSION_PHASE, $TURN_COUNT, $BRIDGE_NOTE
[FAZ TALİMATLARI]                ← $PHASE_INSTRUCTION (faza göre değişken)
[SOHBET DURUMU]                  ← $CONV_STATE (primary_concern, explored, unexplored)
[VIE-SR + CoS PROTOKOLÜ]        ← MISC taksonomisi + Policy Tree talimatı gömülü
[SORU HAVUZU]                    ← Tüm kategoriler + Scale + SFBT soruları
[YASAK AÇILIŞLAR]                ← Tam liste
[REFLEKSIYON SEVİYELERİ]        ← 3 seviye talimatı + 2:1 oran kuralı
[DEPRİNLEŞME SİNYALLERİ]       ← Tablo hali prompt'a girer
[DİL ADAPTASYONU]                ← Kullanıcı tonuna göre sistem tonu
```

### F0-2: Chain-of-Strategy (CoS) — Yanıt Üretim Protokolü

**Araştırma desteği:** PsyMix (2024), DIIR (ACL 2024) — Strateji seçimi önce yapıldığında jenerik empati %35 azalıyor.

```yaml
# answer_system_rules'a eklenir
YANIT ÜRETİM PROTOKOLÜ (CoS):
Adım 0 — Diyalog Eylemini Seç:
  [ OQ ] Açık Soru     — konu netleşmedi / keşif gerekiyor
  [ SR ] Basit Yansıtma — kullanıcı duyulmak istiyor / direnç var
  [ CR ] Derin Yansıtma — ima edilen anlam okunabiliyor
  [ AF ] Güç Tanıma    — somut dayanıklılık görülüyor
  [ SU ] Özet          — 3+ konu konuşuldu, bağlamak gerek
  [ GI ] Bilgi Ver     — sadece kullanıcı açıkça istediğinde

Adım 1 — Seçilen eylemle V adımını yap. Her yanıt yansıtmayla başlar.
Adım 2 — I adımını ekle (RAG eşiği geçildiyse, kullanıcının sahnesine yerleştir).
Adım 3 — E adımını ekle.
Adım 4 — S adımında seçilen eylemle kapat.

HEDEF ORAN: Her 1 OQ için en az 2 SR/CR.
YASAK: Aynı turda 2 soru.
```

### F0-3: SFBT Tetik Koşulları ve Soru Havuzu Genişletmesi

Scale sorusu, Mucize sorusu ve İstisna sorusu kategorileri eklenir:

```yaml
# question_pool'a eklenecek
scale:
  tr:
    - "0'dan 10'a, şu an neredesin — 0 en zor, 10 tam istediğin gibi?"
    - "Bir üste çıkmak nasıl görünürdü?"
    - "Bu kadar kalabilmek için ne yapıyorsun?"
  en:
    - "On a scale of 0-10, where are you today?"
    - "What would moving one step up look like?"

sfbt_exception:
  tr:
    - "Bu böyle hissetmediğin bir gün oldu mu son zamanlarda?"
    - "O farklı günde ne değişmişti?"
  en:
    - "Are there times when this feels a bit lighter?"
    - "What was different on those days?"

sfbt_miracle:
  tr:
    - "Yarın uyandığında bu problem çözülmüş olsaydı — gün boyunca ilk fark edeceğin şey ne olurdu?"
  en:
    - "Imagine this was resolved overnight — what would you notice first tomorrow morning?"
```

### F0-4: Emotion-First Chain-of-Thought

```yaml
# answer_system_rules'a eklenir
EMOSYONELANALİZ (yanıt öncesi):
Adım 1 — Kullanıcının mesajında BİRİNCİL duyguyu belirle (söylenen).
Adım 2 — İKİNCİL duyguyu tahmin et (ima edilen, söylenmeyen).
           "Arkadaşlarım anlayamıyor" → birincil: hayal kırıklığı, ikincil: yalnızlık
Adım 3 — V adımında BİRİNCİL duyguyu yansıt.
Adım 4 — CR uygunsa İKİNCİL duyguyu da dahil et (Seviye 3).
```

### F0-5: memory_agent Prompt → Structured JSON

Mevcut serbest metin özeti → JSON schema output.

### F0-6: Gündem Haritalama Prompt (agenda_mapper)

```yaml
agenda_mapper: |
  Aşağıdaki sohbeti oku ve JSON olarak yanıtla:
  Sohbet: $HISTORY

  {
    "primary_concern": "...",
    "explored_topics": ["..."],
    "unexplored_mentions": ["..."],
    "change_talk_score": 0.0,
    "change_talk_statements": ["..."],
    "resistance_detected": false,
    "distress_level": 5,
    "stuck_in_problem": false,
    "cannot_envision_change": false
  }
```

## Test Senaryoları

```
Test 1 — CoS protokolü
  Input: "Arkadaşlarım anlayamıyor zaten"
  Beklenti: CR seçildi → "Yalnız hissediyorsun bu konuda — görünmez gibi."
  Yasak: "Anlıyorum bu zor olmalı."

Test 2 — İlk mesaj
  Beklenti: OQ seçildi → "Bugün seni en çok ne meşgul ediyor?"
  Yasak: "Merhaba! Size nasıl yardımcı olabilirim?"

Test 3 — Kısa cevap + SR
  Input: "Bilmiyorum"
  Beklenti: FA → SR → "Bu 'bilmiyorum' bazen 'ne hissettireceğini bilmiyorum'dan geliyor."
```

---

---

# FAZA 1 — Bellek Katmanı

**Süre:** 2-3 gün  
**Risk:** Orta (mevcut bellek formatı değişiyor)  
**Etki:** Çok yüksek — sistemin "kişiyi tanımasının" temeli  
**DB değişikliği:** Hayır

## Hedef

Kullanıcı her seansta yabancıyla değil, onu tanıyan biriyle konuştuğunu hisseder.

## Araştırma Desteği

**MemGPT (Packer 2023):** Episodic memory — geçmiş etkileşimleri yapılandırılmış özet olarak saklar, ilgili anları yeni sorguyla retrieve eder. %70 daha yüksek görev tamamlama oranı.

**MemMachine (2025):** Ground-truth-preserving memory — LLM özetleri zamanla kullanıcı gerçeklerini bozuyor. Verbatim anahtar cümleler özet yanında saklanmalı.

**HTM (Hierarchical Therapy Memory, 2025):** Global state (kullanıcı profili) + episodik özetler katmanlaması. Latency ve tutarlılık ikisi de iyileşiyor.

## Yapılacaklar

### F1-1: memory_agent.py → Structured JSON Çıktısı

```python
# Değiştirilecek: core/agents/memory_agent.py

class MemoryAgent:
    def summarize_interaction(self, user_msg, ai_msg, current_memory="", mood_score=None) -> str:
        # Eski: Serbest metin özet döner
        # Yeni: Structured JSON döner veya mevcut JSON'u günceller

    @staticmethod
    def parse(raw: str | None) -> dict:
        # JSON ise parse et, legacy text ise migrate et
        # Her zaman geçerli schema döner (fallback garantili)

    def mood_trend_summary(self, memory: dict) -> str:
        # [4, 6, 5] → "recent: [4,6,5], avg: 5.0/10 (stable)"
```

**Kritik:** LLM geçersiz JSON dönebilir. `parse()` her durumda boş schema döner — asla crash yok.

### F1-2: Legacy Memory Migration

```python
def migrate_legacy(text: str) -> dict:
    schema = dict(_EMPTY_SCHEMA)
    if text.strip():
        schema["recurring_themes"] = [
            {"theme": text[:80], "count": 1, "last_seen": str(date.today())}
        ]
    return schema
```

### F1-3: assistant.py → Bellek Akışı Güncelleme

```python
# services/assistant.py — değişecek metodlar

async def _get_user_memory(self, db, user_id) -> str:
    # JSON string döner (şifrelenmiş)
    # Artık prune_memory_text() çağrılmaz

async def _update_user_memory(self, db, user_id, new_summary) -> None:
    # JSON string kaydeder (şifreli) — kesilmez

# YENİ:
async def _count_session_turns(self, db, session_id) -> int
async def _load_session_history(self, db, session_id, limit=12) -> list[dict]
async def _get_previous_session(self, db, user_id, current_id) -> ChatSession | None
def _build_bridge_note(self, prev_session, structured_memory) -> str | None
```

### F1-4: Belleğin Prompt'a Enjeksiyonu

```
[BU KİŞİYİ TANIYORSUN]
Ad: Zeynep
Tekrar eden konular: iş yükü (4x), uyku güçlüğü (3x)
Kendi kelimeleri: boşuna, sıkışmış, nefes alamıyorum
İşe yarayanlar: yürüyüş, günlük tutma
Önemli kişiler: annesi, iş arkadaşı Mert
Son seans: 2026-05-15 — iş stresi ve uyku
Aktif eylem planı: Yatmadan 30dk önce telefon başka odaya
Ruh hali: [4, 6, 5] avg 5.0/10 (stable)
```

### F1-5: Bridge Mechanism

```python
if days_ago <= 6:
    bridge = f"Geçen konuşmamızda {topic} üzerinde durmuştuk. O günden bu yana nasıl geçti?"
elif days_ago <= 30:
    bridge = f"Bir süre olmuş. {topic}dan bahsetmiştin — bugün oradan devam etmek ister misin?"
else:
    bridge = None  # çok uzun süre → yeni seans gibi başla

if active_action_plan:
    bridge += f" {action_plan} için biraz alan buldun mu?"
```

## Test Senaryoları

```
Test 1 — JSON round-trip
  Seans 1'de "boşuna" kelimesi 3 kez kullanılır
  Seans 2 başında: sistem "boşuna" kelimesini prompt'unda taşımalı

Test 2 — Bridge
  Son seans 4 gün önce, konu "iş stresi"
  Beklenti: "Geçen konuşmamızda iş stresi üzerinde durmuştuk. O günden bu yana nasıl geçti?"

Test 3 — Legacy migration
  Mevcut kullanıcı "Topic: burnout. Intent: emotional_support." belleğe sahip
  Beklenti: Schema'ya migrate edildi, crash yok
```

---

---

# FAZA 2 — Yanıt Zekası

**Süre:** 3-4 gün  
**Risk:** Orta  
**Etki:** Çok yüksek — "insan hissi" bu fazda oluşuyor  
**DB değişikliği:** Hayır

## Hedef

CoS protokolü aktif. V adımı 3 seviyeli. Policy Decision Tree çalışıyor. RAG kullanıcının sahnesine iner. Derinleşme sinyalleri ve direnç tanınır.

## Araştırma Desteği

**Lexical Mirroring (Spillane 2022):** Kullanıcının kendi kelimeleri yansıtıldığında empati algısı %40 artıyor.

**Chain-of-Strategy (PsyMix 2024):** Strategy prediction before generation reduces generic empathy by 35%.

**SFBT (MIT Thesis 2025):** Solution-focused questioning outperforms CBT in simulated PHQ-9 improvement.

## Yapılacaklar

### F2-1: generator.py → _build_prompt() Tam Yeniden Yazımı

```python
def _build_prompt(self, message, topic, retrievals, ...,
                  turn_count=0, within_session_patterns=None,
                  bridge_note=None, preferred_name=None,
                  structured_memory=None, conv_state=None) -> str:

    # 1. Structured memory parse
    mem = structured_memory or {}

    # 2. ConvState al (Policy Decision Tree için)
    state = conv_state or EMPTY_CONV_STATE

    # 3. Policy Decision Tree → diyalog eylemi seç
    selected_act = select_dialogue_act(state)

    # 4. Profil bilgilerini çıkar
    resolved_name = preferred_name or mem.get("preferred_name") or "the user"
    recurring_themes = format_themes(mem.get("recurring_themes"))
    ...

    # 5. Faz tespiti
    phase = state.get("session_phase", derive_phase(turn_count))

    # 6. RAG sahne enjeksiyonu
    rag_content = extract_rag_content(retrievals, min_score=0.72)

    # 7. Tüm değişkenlerle system_rules render
    system_rules = render_prompt("generation.answer_system_rules",
        PREFERRED_NAME=resolved_name,
        CONV_STATE=format_conv_state(state),
        SELECTED_DIALOGUE_ACT=selected_act,
        SESSION_PHASE=phase_label,
        TURN_COUNT=str(turn_count),
        BRIDGE_NOTE=bridge_note or "n/a",
        WITHIN_SESSION_PATTERNS=patterns_str,
        ...
    )

    output_format = render_prompt("generation.answer_output_format",
        RAG_CONTENT=rag_content or "(none — skip I step)",
        USER_MESSAGE=message,
    )

    return f"{system_rules}\n\n{output_format}"
```

### F2-2: Refleksiyon 3 Seviyesi

```
YANSITMA SEVİYELERİ:

Seviye 1 — Basit Yansıtma (her zaman):
  Kullanıcının kendi kelimesini değiştirmeden geri ver.
  "İşte her şey çok yoğun." → "Yoğunluk üst üste gelmiş."

Seviye 2 — Yeniden Çerçeveleme (mutlakçı dil varsa):
  "Hiçbir şeyi doğru yapamıyorum." → "Çok yüksek bir standart taşıyorsun kendin için."

Seviye 3 — Derin Tahmin / ALTI OKUMA (ima edilen duygu netse):
  "Arkadaşlarım anlayamıyor." → "Yalnız hissediyorsun bu konuda — görünmez gibi."
  Kural: "sanki" veya "—" ile bağla. Yanlışsa kullanıcı düzeltir, bu iyidir.

HEDEF: Her 1 soru için 2 yansıtma (SR + CR birlikte sayılır).
```

### F2-3: Personalized RAG Injection

```python
def _extract_rag_content(retrievals, min_score=0.72) -> str:
    qualified = [r for r in retrievals if r.score >= min_score]
    if not qualified:
        return ""
    top = qualified[0]
    sentences = split_sentences(top.chunk.content)
    return " ".join(sentences[:3])[:240]
    # Raw içerik, nuggetized değil
    # LLM bunu kullanıcının sahnesine yerleştirecek
```

### F2-4: Derinleşme Sinyal Tespiti

```python
DISMISSAL_SIGNALS = [
    "saçma geliyor", "abartıyorum", "önemli değil",
    "silly but", "sounds stupid", "doesn't matter"
]
TOPIC_SHIFT_SIGNALS = [
    "neyse", "geçelim", "anyway", "never mind", "forget it"
]

def detect_deepening_signals(user_message: str) -> dict:
    msg = user_message.lower()
    return {
        "dismissal":   any(s in msg for s in DISMISSAL_SIGNALS),
        "topic_shift": any(s in msg for s in TOPIC_SHIFT_SIGNALS),
        "very_short":  len(msg.split()) < 5,
        "i_dont_know": msg.strip() in ["bilmiyorum", "böyle işte", "i don't know"],
    }
```

### F2-5: Policy Decision Tree (generator.py'e)

```python
def select_dialogue_act(state: dict) -> str:
    if state.get("distress_level", 0) >= 8:
        return "VALIDATION"
    if not state.get("primary_concern"):
        return "OQ"
    if state.get("resistance_detected"):
        return "SR"
    if state.get("change_talk_score", 0) > 0.6:
        return "OQ"  # amplify change talk
    if state.get("unexplored_mentions"):
        return "OQ"  # yarım kalan konuya dön
    if state.get("stuck_in_problem"):
        return "SFBT_EXCEPTION"
    if state.get("cannot_envision_change"):
        return "SFBT_MIRACLE"
    phase = state.get("session_phase", 1)
    if phase == 1:
        return "OQ"
    if phase == 2:
        return "CR"
    if phase == 3:
        return "SFBT_SCALE"
    return "SR"
```

### F2-6: PACE TUTMA — Ağır İçerik

```python
HEAVY_CONTENT_SIGNALS = [
    "artık dayanamıyorum", "bitmesini istiyorum", "boş geliyor",
    "can't take it", "end it", "what's the point"
]

def detect_heavy_content(user_message: str) -> bool:
    return any(s in user_message.lower() for s in HEAVY_CONTENT_SIGNALS)

# Tespit edilince prompt'a eklenir:
# "PACE: Ağır içerik. Az cümle. Bilgi verme. Sadece yansıt ve tek soru sor."
```

## Test Senaryoları

```
Test 1 — Policy Tree: Direnç
  ConvState: resistance_detected=True
  Input: "Bu egzersiz fikirlerini boşver, zaten işe yaramıyor"
  Beklenti: SR → "Daha önce denediğin şeyler sonuç vermemiş — bu yorucu."
  Yasak: "Ama egzersizin yararları var çünkü..."

Test 2 — SFBT İstisna
  ConvState: stuck_in_problem=True
  Beklenti: "Bu böyle hissetmediğin bir gün oldu mu son zamanlarda?"

Test 3 — RAG Sahne Enjeksiyonu
  Input: "Her şeyi doğru yapamıyorum"
  Beklenti: "Zihin bazen 'ya mükemmel ya hiç' moduna giriyor — orta noktayı görmesi zorlaşıyor gibi."
  Yasak: "Bilişsel çarpıtma yaşıyor olabilirsiniz."
```

---

---

# FAZA 3 — Seans Mimarisi

**Süre:** 4-5 gün  
**Risk:** Orta-Yüksek (DB değişikliği + yeni dosya)  
**Etki:** Yüksek — seans akışı gerçek terapi yapısını kazanıyor  
**DB değişikliği:** Evet — ChatSession'a 5 alan

## Hedef

Sistem seansin hangi noktasında olduğunu bilir, her fazda farklı davranır. ConvState her turda güncellenir. Gündem haritalama aktif çalışır. İçgörü anını kaçırmaz.

## Yapılacaklar

### F3-1: models.py → ChatSession Phase Alanları

```python
class ChatSession(Base):
    # EKLENECEK 5 ALAN:
    session_phase     = Column(Integer, nullable=False, default=1)
    turn_count        = Column(Integer, nullable=False, default=0)
    agenda_set        = Column(Boolean, nullable=False, default=False)
    insight_triggered = Column(Boolean, nullable=False, default=False)
    closure_confirmed = Column(Boolean, nullable=False, default=False)
```

### F3-2: scripts/migrate_phase_fields.py

```python
import sqlite3

conn = sqlite3.connect("data/store/psych_rag.db")
cursor = conn.cursor()

new_columns = [
    ("session_phase",     "INTEGER NOT NULL DEFAULT 1"),
    ("turn_count",        "INTEGER NOT NULL DEFAULT 0"),
    ("agenda_set",        "BOOLEAN NOT NULL DEFAULT 0"),
    ("insight_triggered", "BOOLEAN NOT NULL DEFAULT 0"),
    ("closure_confirmed", "BOOLEAN NOT NULL DEFAULT 0"),
]

for col_name, col_def in new_columns:
    try:
        cursor.execute(f"ALTER TABLE sessions ADD COLUMN {col_name} {col_def}")
        print(f"Added: {col_name}")
    except sqlite3.OperationalError:
        print(f"Already exists: {col_name}")

conn.commit()
conn.close()
```

**Önce backup:** `cp data/store/psych_rag.db data/store/psych_rag_backup_$(date +%Y%m%d).db`

### F3-3: core/agents/conversation_state.py (Yeni Dosya)

```python
# core/agents/conversation_state.py

EMPTY_CONV_STATE = {
    "primary_concern": None,
    "explored_topics": [],
    "unexplored_mentions": [],
    "change_talk_score": 0.0,
    "change_talk_statements": [],
    "resistance_detected": False,
    "sustain_talk_ratio": 0.0,
    "distress_level": 0,
    "stuck_in_problem": False,
    "cannot_envision_change": False,
    "session_phase": 1,
    "phase_turn_count": 0,
    "last_dialogue_act": None,
    "agenda_mapped_at_turn": 0,
}

class ConversationStateEngine:

    def __init__(self, llm: OllamaClient | None = None):
        self.llm = llm or OllamaClient()

    async def update(self, history, current_state, turn_count) -> dict:
        # Change talk her turda (hafif, regex)
        current_state["change_talk_score"] = score_change_talk(history)
        current_state["resistance_detected"] = detect_resistance(
            next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        )

        # Agenda mapping her 4 turda (LLM çağrısı)
        if self._should_map_agenda(turn_count, current_state):
            agenda = await self._run_agenda_mapping(history)
            current_state.update(agenda)
            current_state["agenda_mapped_at_turn"] = turn_count

        return current_state

    def _should_map_agenda(self, turn_count, state) -> bool:
        return (turn_count - state.get("agenda_mapped_at_turn", 0)) >= 4

    async def _run_agenda_mapping(self, history) -> dict:
        prompt = render_prompt("agents.agenda_mapper",
                               HISTORY=format_history(history))
        result = self.llm.generate(prompt, temperature=0.0)
        raw = result.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
```

### F3-4: Faz Geçiş Mantığı — Change Talk Entegrasyonu

```python
# session_store.py güncelleme

def determine_phase(session: ChatSession, conv_state: dict) -> int:
    if session.turn_count == 0:
        return 1
    if not session.agenda_set and session.turn_count <= 2:
        return 1

    # Change talk skoru faz 3 için yeterince yüksekse
    if conv_state.get("change_talk_score", 0) >= 0.6:
        session.insight_triggered = True

    # Semantik sinyaller (ek kontrol)
    # ...insight/action detection mevcut koddan

    if session.agenda_set and not session.insight_triggered and session.turn_count < 10:
        return 2
    if session.insight_triggered or session.turn_count >= 10:
        return 3
    if session.closure_confirmed:
        return 4
    return 2
```

### F3-5: assistant.py → ConvState Entegrasyonu

```python
# handle_message'e eklenecek

# ConvState yükle (session'a bağlı, JSON olarak saklanır)
conv_state = await self._load_conv_state(db, session.id)

# Her turda güncelle
conv_state = await self.conv_state_engine.update(
    history=session_history,
    current_state=conv_state,
    turn_count=turn_count,
)

# generator.build_grounded'a yeni parametre
payload = self.generator.build_grounded(
    ...
    conv_state=conv_state,
)

# Arka planda kaydet
await self._save_conv_state(db, session.id, conv_state)
```

### F3-6: Seans Kartı (session_card.py)

```python
async def build_and_save_session_card(db, session: ChatSession) -> None:
    if session.mood_score_start and session.mood_score_end:
        session.mood_delta = session.mood_score_end - session.mood_score_start
    if session.action_plan:
        # Memory agent'e "active_action_plan" güncelle
        pass
    session.session_card_generated = True
    await db.flush()
```

## Test Senaryoları

```
Test 1 — ConvState güncellemesi
  Turn 3: Kullanıcı "annem" ve "iş" geçti ama girilmedi
  Beklenti: unexplored_mentions = ["annem", "iş durumu"]
  Turn 4: Policy Tree → OQ "Daha önce annemden bahsetmiştin..."

Test 2 — Change Talk → Faz 3 geçişi
  Kullanıcı "yapabilirim", "deneyeceğim" içeren mesajlar yazdı
  Beklenti: change_talk_score > 0.6 → insight_triggered=True → phase=3

Test 3 — Agenda mapping tetiklenmesi
  Turn 4: Agenda mapper çalışır
  Beklenti: primary_concern netleşti, unexplored_mentions güncellendi
```

---

---

# FAZA 4 — Örüntü & Öğrenme

**Süre:** 3-4 gün  
**Risk:** Düşük (yeni dosyalar)  
**Etki:** Yüksek — "Bu kelimeyi birkaç kez kullandın" anı burada oluşuyor  
**DB değişikliği:** Hayır

## Hedef

Sistem hem aynı seans içinde hem de seanslararası tekrar eden kelimeleri, temaları ve bilişsel örüntüleri fark eder. Change talk tespiti daha sofistike hale gelir.

## Yapılacaklar

### F4-1: core/agents/pattern_detector.py (Yeni Dosya)

```python
def detect_within_session_patterns(history: list[dict]) -> list[str]:
    """Kullanıcı aynı kelimeyi 3+ kez kullandıysa sinyal üret."""
    ...

def detect_cognitive_distortions(history: list[dict]) -> list[str]:
    """CBT bilişsel çarpıtmalarını tespit et."""
    DISTORTIONS = {
        "all_or_nothing": ["hiçbir zaman", "her zaman", "never", "always"],
        "catastrophizing": ["mahvoldum", "bitti", "ruined", "disaster"],
        "mind_reading":    ["anlayamıyorlar", "they think", "she knows"],
        "self_blame":      ["benim hatam", "my fault", "because of me"],
    }
    ...

def detect_cross_session_patterns(structured_memory: dict) -> list[str]:
    """3+ seanstır gelen temalar."""
    ...
```

### F4-2: assistant.py → Pattern Integration

```python
session_history = await self._load_session_history(db, session.id)
within_patterns  = detect_within_session_patterns(session_history)
cross_patterns   = detect_cross_session_patterns(structured_memory)
distortions      = detect_cognitive_distortions(session_history)

all_patterns = within_patterns + cross_patterns
# distortions → ayrı prompt sinyali
```

### F4-3: Distortion-Aware Prompting

```
[BİLİŞSEL ÖRÜNTÜ]
Bu seansta: all_or_nothing ("hiçbir şeyi doğru yapamıyorum")
Faz 3'te keşif yoluyla sun:
"Bazen zihin 'ya mükemmel ya hiç' moduna giriyor.
 Orta bir nokta olsa nasıl görünürdü?"
```

### F4-4: Change Talk Tespiti Güçlendirme

DARNC kategorileri pattern_detector.py'e taşınır, daha geniş corpus ile çalışır:

```python
CHANGE_TALK_PATTERNS = {
    "desire":     ["istiyorum", "olmasını isterdim", "keşke", "i want", "i wish"],
    "ability":    ["yapabilirim", "deneyebilirim", "i could", "i might"],
    "reason":     ["çünkü", "bu yüzden", "yararlı olurdu", "because"],
    "need":       ["zorundayım", "böyle devam edemem", "i need to", "i have to"],
    "commitment": ["yapacağım", "deneyeceğim", "i will", "i'm going to"],
}
```

## Test Senaryoları

```
Test 1 — Within-session kelime tespiti
  "boşuna" 4 kez geçiyor
  Beklenti: within_patterns = ["'boşuna' bu seansta 4 kez tekrarlandı"]

Test 2 — Cross-session tema
  recurring_themes'de "uyku güçlüğü" count=4
  Beklenti: cross_patterns = ["'uyku güçlüğü' 4 seanstır gündemde"]

Test 3 — Bilişsel çarpıtma
  "Hiçbir şeyi doğru yapamıyorum, her zaman böyle"
  Beklenti: distortions = ["all_or_nothing"]
```

---

---

# FAZA 5 — İleri Yetenekler

**Süre:** 1-2 hafta  
**Risk:** Yüksek (yeni modeller, vektör store, fine-tune)  
**Etki:** Çok yüksek — araştırma seviyesi yetenekler  
**DB değişikliği:** Evet (vektör store ekleme)

## Hedef

Sistem duygu durumunu sürekli izler, seanslararası bağlamı vektör tabanlı arar, ve belirli alanlarda fine-tune edilmiş modeller kullanır.

## Araştırma Desteği

**VAD State Tracking (COSMIC 2020):** Her konuşma turunda Valence-Arousal-Dominance vektörü güncellenir. PACE TUTMA otomatik hale gelir.

**GoEmotions (Google 2021):** 27 ince duygu kategorisi. Hugging Face'den direkt kullanılabilir.

**MemGPT-style Retrieval:** Seans özetleri vektörleştirilip Chroma'ya kaydedilir. Yeni seans açılışında "bu kullanıcının en ilgili 3 geçmiş anısı" otomatik çekilir.

## Yapılacaklar

### F5-1: Emotion Classifier Per Turn

```python
# core/agents/emotion_classifier.py (YENİ)
from transformers import pipeline

classifier = pipeline(
    "text-classification",
    model="SamLowe/roberta-base-go_emotions",
    top_k=3
)

def classify_emotion(text: str) -> list[dict]:
    return classifier(text, truncation=True)[0]
```

### F5-2: VAD State Tracking

```python
class VADTracker:
    def __init__(self):
        self.state = {"valence": 0.5, "arousal": 0.5, "dominance": 0.5}

    def update(self, emotion_label: str, score: float) -> None:
        VAD_MAP = {
            "sadness": {"valence": -0.8, "arousal": -0.4, "dominance": -0.5},
            "fear":    {"valence": -0.7, "arousal":  0.6, "dominance": -0.6},
            "anger":   {"valence": -0.6, "arousal":  0.8, "dominance":  0.3},
            "joy":     {"valence":  0.8, "arousal":  0.6, "dominance":  0.5},
        }
        if emotion_label in VAD_MAP:
            for dim, val in VAD_MAP[emotion_label].items():
                self.state[dim] = 0.7 * self.state[dim] + 0.3 * val

    @property
    def is_heavy(self) -> bool:
        return self.state["valence"] < -0.4 and self.state["arousal"] > 0.3

    @property
    def pace_instruction(self) -> str:
        if self.is_heavy:
            return "PACE: Heavy. Short sentences. Less info. More space."
        return ""
```

### F5-3: Vector Memory Store

```python
# core/memory/vector_store.py (YENİ)
import chromadb

class TherapeuticVectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="data/vector_store")
        self.collection = self.client.get_or_create_collection("session_memories")

    def add_session_memory(self, user_id, session_id, summary, embedding):
        self.collection.add(
            documents=[summary],
            embeddings=[embedding],
            ids=[f"{user_id}_{session_id}"],
            metadatas=[{"user_id": user_id, "session_id": session_id}]
        )

    def retrieve_relevant(self, user_id, query_embedding, n_results=3):
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"user_id": user_id}
        )
```

### F5-4: Fine-Tuning Yol Haritası

**MentaLLaMA (Yang 2024):** Reddit mental health verisiyle fine-tune edilmiş LLaMA-2. Depresyon/PTSD tespitinde GPT-3.5'i geçti.

```
1. Veri toplama: Calma chat logları (KVKK uyumlu, anonimleştirilmiş)
2. Etiketleme: Her yanıta MISC kodu + VIE-SR adım etiketi + kalite skoru
3. Fine-tune: Mistral-7B veya LLaMA-3-8B (LoRA ile, A100 olmadan yapılabilir)
4. Değerlendirme: Empati skoru + 2:1 oran uyumu + CoS adherence
Tahmini süre: 2-3 ay veri toplama + 1 hafta fine-tune
```

---

---

## Faz Zaman Çizelgesi

```
HAFTA 1
  Faza 0 — Prompt Katmanı          ████ (1-2 gün)
  Faza 1 — Bellek Katmanı          ████████████ (3 gün)

HAFTA 2
  Faza 2 — Yanıt Zekası            ████████████████ (4 gün)

HAFTA 3
  Faza 3 — Seans Mimarisi          ████████████████████ (5 gün)
  (migration + ConvState + yeni dosyalar)

HAFTA 4
  Faza 4 — Örüntü & Öğrenme       ████████████ (3-4 gün)

HAFTA 5-6
  Faza 5 — İleri Yetenekler        ████████████████████████
```

---

## Kritik Başarı Metrikleri

Her fazın başında ve sonunda bu metrikleri ölç:

| Metrik | Ölçüm Yöntemi | Hedef |
|---|---|---|
| Chatbot hissi | Manuel test (10 seans, 2 farklı kişi) | "Chatbot gibi" yorumu < %20 |
| 2:1 oran uyumu | Yanıt transcript analizi | > %80 turda sağlanıyor |
| V adımı kalitesi | Kullanıcının kendi kelimesi geri verildi mi? | > %80 |
| I adımı kişisellik | Sahne enjeksiyonu mu yoksa generic fact mi? | > %70 sahne |
| Policy Tree uyumu | Seçilen eylem ConvState'e uygun mu? | > %85 |
| Change talk tespiti | 0.6+ skor → Faz 3 geçişi doğru zamanlıydı mı? | > %75 |
| Tekrar eden kelime tespiti | 3+ tekrar → pattern sorusu geldi mi? | > %90 |
| Bridge kuruldu mu? | Geri dönen kullanıcıda köprü cümlesi var mı? | > %95 |

---

## Risklerin Özeti

| Risk | Faza | Önlem |
|---|---|---|
| LLM latency artışı | 0, 2 | Prompt uzunluğu optimize edilir, boş ConvState alanları çıkarılır |
| Agenda mapping latency | 3 | Arka planda çalıştır, sonucu bir sonraki tura yansıt |
| Memory JSON bozulması | 1 | `parse()` her zaman fallback schema döner |
| DB migration crash | 3 | Backup + ayrı test DB'sinde önce çalıştır |
| Change talk false positive | 3, 4 | 2+ DARNC kategorisi VE 0.6+ skor eşiği birlikte |
| Policy Tree over-correction | 2 | Direnç tespiti 2+ sinyal gerektirmeli |
| SFBT erken tetikleme | 2 | Mucize sorusu yalnız Faz 2 ortasında, distress < 7 |
| Emotion classifier yanlış | 5 | Override mekanizması: LLM kendi tespitini yapabilmeli |
| Fine-tune KVKK | 5 | Veri anonimleştirme protokolü şarttır |

---

> **Bu harita** Calma'yı araştırma literatürüyle hizalanmış,  
> sistematik olarak geliştirilebilir bir platform haline getiriyor.  
> Sistem H (ConvState) olmadan Faza 2'nin Policy Decision Tree'si çalışamaz.  
> Faza 0-2 hiçbir DB değişikliği gerektirmez — anında deploy edilebilir.  
> Therabot'un 8 haftada %51 depresyon azalması bu sistemin doğru yönde olduğunun kanıtıdır.

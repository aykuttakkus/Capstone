# Calma RAG Corpus — Profesyonel Kalite Denetim Raporu

**Tarih:** Mayıs 2026  
**Kapsam:** 135 PDF, 9.046 chunk, 23,4 milyon karakter  
**Amaç:** Mevcut corpus kalitesini değerlendirmek, silinmesi gerekenleri belirlemek, eksik konu başlıklarını saptamak ve global düzeyde onaylı kaynak önerileri sunmak.

---

## 1. Yönetici Özeti

Mevcut corpus'ta **9.046 chunk** bulunmakta olup bunların büyük çoğunluğu klinik psikoloji odaklı değildir. Toplam chunk'ların yaklaşık **%35-40'ı genel psikoloji ders kitaplarından** (intro textbooks), **%15'i akademik araştırma makalelerinden** (uygulanabilir klinik içerik sunmayan), **%5'i tamamen alakasız (pazarlama, egzersiz psikolojisi, ceza hukuku)** kaynaklardandır. Gerçek psikoeğitim/terapi odaklı materyal corpus'un yalnızca **%40-45'ini** oluşturmaktadır.

**Acil öneri:** 15 PDF silinmeli, 4 PDF değerlendirilmeli, 20+ yeni kaynak eklenmeli.

---

## 2. Corpus Genel Görünümü

| Metrik | Değer |
|---|---|
| Toplam PDF sayısı | 135 |
| Toplam chunk | 9.046 |
| Toplam karakter | 23.409.590 |
| Ortalama chunk uzunluğu | 2.588 karakter |
| Gürültü chunk (<100 karakter) | ~295 (%3.3) |
| İnce chunk (<300 karakter) | ~420 (%4.6) |
| Parser modu | %100 legacy (tüm PDF'ler sayfa başına 1 chunk) |

### Konu Dağılımı

| Konu | Chunk | Oran | Yorum |
|---|---|---|---|
| social_pressure | 2.635 | %29 | Akademik makaleler şişiriyor |
| stress_anxiety | 1.855 | %21 | Makul ama dağınık |
| psychoeducation | 1.789 | %20 | Genel ders kitapları şişiriyor |
| low_mood | 1.098 | %12 | Yetersiz |
| help_seeking | 1.079 | %12 | Çoğu alakasız içerik |
| burnout_sleep | 543 | %6 | **Ciddi eksik** |
| bipolar | 17 | %0.2 | Sembolik |
| psychosis | 12 | %0.1 | Sembolik |
| eating_disorders | 8 | %0.1 | **Neredeyse yok** |
| ocd | 8 | %0.1 | **Neredeyse yok** |
| ptsd | 2 | %0.02 | **Tamamen yok sayılabilir** |

---

## 3. PDF Kalite Değerlendirmesi

### 🔴 KESİNLİKLE SİLİNMELİ (Alakasız İçerik)

| PDF Dosyası | Chunk | Sorun |
|---|---|---|
| `the-future-of-personalization-and-how-to-get-ready-for-it.pdf` | 7 | **McKinsey pazarlama makalesi** — psikoloji ile sıfır ilgisi |
| `what-is-personalization.pdf` | 7 | **McKinsey pazarlama açıklaması** — tamamen alakasız |
| `Zenko+and+Jones+(Eds.)+Book+Version+(2021).pdf` | 806 | **Egzersiz ve spor psikolojisi ders kitabı** — klinik ruh sağlığı değil; corpus'un en büyük gürültü kaynağı |
| `Mental-Disorders-and-the-Criminal-Justice-System-1775320786.pdf` | 514 | **Ceza hukuku odaklı** — terapi/psikoeğitim değil |
| `10.51538-intjourexerpsyc.1366313-3433357.pdf` | 7 | Türk egzersiz psikolojisi dergisi — spor motivasyonu |
| `10.55376-ijtsep.1452804-3794812.pdf` | 18 | Türk spor psikolojisi — engelli sporcular |
| `10.55376-ijtsep.1607482-4467857 (1).pdf` | 11 | Türk spor psikolojisi — engelli sporcularda motivasyon |
| `Emotional-Regulation-March-2022.pdf` | 44 | **%55 gürültü chunk**, ortalama içerik 124 karakter — pratik olarak boş |

**Toplam silinecek:** ~1.414 chunk (%15.6)

---

### 🟠 SİLİNMESİ ÖNERİLEN (Genel Ders Kitapları — Klinik Değil)

Bu PDF'ler meşru psikoloji içeriği sunmaktadır ancak Calma'nın ihtiyacı olan **uygulanabilir klinik psikoeğitim** değil, **akademik giriş dersi materyali**dir. RAG sorgu kalitesini düşürmekte, konu sınıflandırmasını bozmaktadır.

| PDF Dosyası | Chunk | Sorun |
|---|---|---|
| `Introduction-to-Psychology-1st-Canadian-Edition-1660157192.pdf` | 786 | Genel giriş psikolojisi ders kitabı (Kanada) — ders kitabı içeriği |
| `General Psychology_ An Introduction.pdf` | 559 | GALILEO/NOBA genel psikoloji ders kitabı |
| `Human-Development-1775689275.pdf` | 518 | Gelişim psikolojisi ders kitabı — klinik odak yok |
| `Psychology-1600182266.pdf` | 423 | Genel psikoloji ders kitabı |
| `Full.pdf` (LibreTexts Social Psychology) | 468 | Sosyal psikoloji ders kitabı — çok akademik |
| `loneliness-by-benjamin-mijuskovic.pdf` | 300 | **Telif hakkı korumalı** ("All rights reserved"), felsefi/edebi yaklaşım — klinik değil |

**Toplam silinecek:** ~3.054 chunk (%33.8)

> **Not:** Bu 6 PDF silindiğinde corpus klinik kalite açısından ciddi oranda iyileşir. `social_pressure` ve `psychoeducation` topic'lerdeki yapay şişkinlik ortadan kalkar.

---

### 🟡 DEĞERLENDİRİLMELİ (Kısmi Değer)

| PDF Dosyası | Chunk | Durum | Öneri |
|---|---|---|---|
| `Handbook-of-emotion-regulation.pdf` | 673 | Akademik el kitabı — içeriğin %30'u klinik açıdan değerli | Sadece klinik bölümleri yeniden ingestion ile tut |
| `THEDIA1.pdf` (DBT Workbook) | 343 | McKay'in DBT becerileri kitabı — **değerli içerik** ancak telif hakkı belirsiz | Telif hakkını kontrol et |
| `Early-Adolescent-Skills.pdf` | 390 | Ergen becerileri — uygulama hedef kitlesine uyuyorsa tut | Hedef kitleye göre karar ver |
| `Fundamentals-of-Psychological-Disorders.pdf` | 339 | Bozuklukların temelleri — bazı bölümler klinik açıdan değerli | Kısmen tut |

---

### 🟢 KALİTELİ — KALSIN

Bu PDF'ler Calma'nın çekirdeğini oluşturmalıdır:

| PDF Dosyası | Chunk | İçerik | Kaynak |
|---|---|---|---|
| `DealingwithDistress.pdf` | 42 | CBT öz-yardım çalışma kitabı | Carol Vivyan / GetSelfHelp |
| `social-anxiety-challenging-anxious-thinking.pdf` | 21 | Sosyal anksiyete CBT çalışma sayfası | CCI |
| `social-anxiety-scotland.pdf` | 31 | Sosyal anksiyete rehberi | NHS Scotland |
| `MHF-UK-Uncertain-times-Anxiety-in-the-UK...pdf` | 40 | Anksiyete raporu | Mental Health Foundation UK |
| `DISTRESS TOLERANCE SKILLS MANUAL e-version.pdf` | 13 | DBT sıkıntı toleransı | Klinik el kitabı |
| `EMOTION REGULATION SKILLS MANUAL.pdf` | 15 | Duygu düzenleme becerileri | Klinik el kitabı |
| `Cognitive-Distortions.pdf` | 7 | Bilişsel çarpıtmalar | Psikoeğitim |
| `cognitive-distortions (1).pdf` | 1 | Bilişsel çarpıtmalar listesi | Psikoeğitim |
| `Finding-the-Calm-Emotional-Regulation.pdf` | 12 | Duygu düzenleme | Psikoeğitim |
| `Post-Traumatic-Growth-Handout.pdf` | 2 | PTG el broşürü | Klinik |
| `repetitive-negative-thinking-rumination.pdf` | 11 | Ruminasyon | Araştırma/klinik |
| `Anxiety_Sensitivity_and_Catastrophizing.pdf` | 12 | Anksiyete bilişleri | Klinik |
| `FS_GriefInAdults_EN_2025.pdf` | 5 | Yas/kayıp | Klinik |
| `Im-So-Stressed-Out.pdf` | 2 | Stres psikoeğitim | NIMH |
| `depression.pdf` | 8 | Depresyon | NIMH |
| `surgeon-general-social-connection-advisory.pdf` | 82 | Sosyal bağlantı | US Surgeon General |
| `Trauma-Informed-Behaviour-Support...pdf` | 176 | Travma bilgili destek | Klinik rehber |
| `HO15_ThnkngAbtThnkng.pdf` | 3 | Düşünce kalıpları | CBT çalışma sayfası |
| `Thinking Errors and Self Defeating Beliefs...pdf` | 3 | Düşünce hataları | CBT |
| `Coping+Strategies.pdf` | 4 | Başa çıkma stratejileri | Psikoeğitim |
| `rtp_unit-2-workbook.pdf` | 15 | Psikolojik esneklik | Çalışma kitabı |
| `Learned-Helplessness.pdf` | 24 | Öğrenilmiş çaresizlik | Psikoloji |
| `Breakup-Book1.pdf` | 59 | İlişki ayrılığı | Öz-yardım |
| `1907mindreading.pdf` | 77 | Zihin okuma / sosyal biliş | Psikoeğitim |
| `Psychology_of_Loneliness_FINAL_REPORT.pdf` | 66 | Yalnızlık araştırması | Mental Health Foundation |

---

### 🔵 TÜRKÇE AKADEMİK MAKALELER (Özel Durum)

12 adet Türkçe DOI numaralı makale mevcut (toplam ~181 chunk). Bunlar İngilizce bir RAG sistemi için retrieval kalitesini düşürmektedir çünkü dil sınıflandırması `tr` olarak işaretlenmiş, ancak İngilizce bir uygulama için gerçek değerleri sınırlıdır. **Sistem Türkçe kullanıcılara hizmet verecekse tutulabilir, yalnızca İngilizce ise kaldırılmalıdır.**

---

## 4. Konu Boşluğu Analizi

Aşağıdaki klinik konu başlıkları **global ruh sağlığı uygulamaları için kritik** olmakla birlikte corpus'ta ya hiç yoktur ya da sembolik düzeydedir:

| Eksik Konu | Mevcut Durum | Öncelik |
|---|---|---|
| **Panik bozukluk / Panic attacks** | Çok az | 🔴 Kritik |
| **Uyku hijyeni / İnsomnia** | 543 chunk ama kalitesiz | 🔴 Kritik |
| **Mindfulness / Farkındalık** | Yok | 🔴 Kritik |
| **PTSD / Travma** | 2 chunk | 🔴 Kritik |
| **Öz-şefkat / Self-compassion** | Çok az | 🔴 Kritik |
| **OCD** | 8 chunk | 🟠 Yüksek |
| **Yeme bozuklukları** | 8 chunk | 🟠 Yüksek |
| **Öfke yönetimi** | Yok | 🟠 Yüksek |
| **Yas ve kayıp** | 5 chunk | 🟠 Yüksek |
| **Özgüven / Self-esteem (pratik)** | Akademik makaleler var, çalışma kitabı yok | 🟠 Yüksek |
| **Sınır koyma** | 7 chunk | 🟡 Orta |
| **Problem çözme** | Çok az | 🟡 Orta |
| **Sosyal beceriler** | Akademik düzeyde var | 🟡 Orta |
| **Davranışsal aktivasyon (depresyon)** | Yok | 🟡 Orta |
| **Kaygı günlüğü / Exposure therapy basics** | Yok | 🟡 Orta |
| **İki kutuplu bozukluk psikoeğitim** | 17 chunk (NIMH broşürü) | 🟡 Orta |

---

## 5. Önerilen Yeni Kaynaklar

Aşağıdaki kaynaklar **ücretsiz, globally onaylı ve klinik düzeyde** materyaller sunmaktadır:

### 🏆 Tier 1 — Birincil Öncelik (Hemen Ekle)

**Centre for Clinical Interventions (CCI) — Perth, WA, Australia**  
*Psikoloji uygulamaları için altın standart ücretsiz çalışma kitapları*  
URL: https://www.cci.health.wa.gov.au/Resources/Looking-After-Yourself

| Çalışma Kitabı | Konu | Sayfa |
|---|---|---|
| Worry & Rumination | Kaygı / Ruminasyon | ~80 |
| Panic Stations | Panik bozukluk | ~80 |
| What? Me Worry?! | Endişe | ~80 |
| Overcoming Disordered Eating | Yeme bozuklukları | ~80 |
| This Way Up — Depression | Depresyon | ~80 |
| Building Self-Compassion | Öz-şefkat | ~80 |
| Achieving Balance | Mükemmeliyetçilik | ~80 |
| Introduction to Mindfulness | Farkındalık | ~60 |
| Act to Live (ACT) | Kabul-kararlılık terapisi | ~80 |
| Tolerating Distress | Sıkıntı toleransı | ~60 |

**NHS — Self-Help Guides (UK National Health Service)**  
URL: https://www.nhsinform.scot/illnesses-and-conditions/mental-health  
*NHS içerikleri Crown Copyright — serbestçe kullanılabilir*

| Kılavuz | Konu |
|---|---|
| Understanding Panic Attacks | Panik |
| Understanding Sleep Problems | Uyku |
| Understanding Depression | Depresyon |
| Understanding Anxiety | Anksiyete |
| Understanding Low Self-Esteem | Özgüven |
| Understanding OCD | OKB |
| Understanding PTSD | Travma |
| Living Life to the Full | CBT yaşam becerileri |

**NIMH — National Institute of Mental Health (US)**  
URL: https://www.nimh.nih.gov/health/publications  
*Kamu malı — serbestçe kullanılabilir*

| Yayın | Konu |
|---|---|
| Anxiety Disorders | Anksiyete |
| Depression | Depresyon |
| PTSD | Travma |
| Bipolar Disorder | İki kutuplu |
| Eating Disorders | Yeme bozuklukları |
| OCD | OKB |
| So Stressed Out (zaten mevcut) | Stres |
| Sleep Disorders | Uyku |

---

### 🥈 Tier 2 — Yüksek Öncelik

**GetSelfHelp.co.uk — Carol Vivyan**  
*Serbest terapi amaçlı kullanım — CBT çalışma sayfaları*  
URL: https://www.getselfhelp.co.uk/freedownloads.htm  
*Zaten bazı PDF'ler mevcut, aşağıdakiler eksik:*

| Çalışma Sayfası | Konu |
|---|---|
| Thought Records | Düşünce kaydı (CBT) |
| Behavioural Activation | Davranışsal aktivasyon |
| Sleep Diary & Sleep Hygiene | Uyku hijyeni |
| Anger Management | Öfke yönetimi |
| Grounding Techniques | Topraklama teknikleri |
| Mindfulness Exercises | Farkındalık |
| Grief & Loss | Yas |
| Self-Esteem | Özgüven |

**Mind — UK Mental Health Charity**  
URL: https://www.mind.org.uk/information-support/types-of-mental-health-problems/  
*Erişilebilir dilde klinik doğrulukta*

| Kılavuz | Konu |
|---|---|
| About Anxiety | Anksiyete |
| About Depression | Depresyon |
| About OCD | OKB |
| About PTSD | Travma |
| About Panic Attacks | Panik |
| About Self-harm | Öz-zarar |
| About Grief | Yas |
| About Loneliness | Yalnızlık |
| About Sleep Problems | Uyku |

**Beyond Blue — Australia**  
URL: https://www.beyondblue.org.au/the-facts  
*Klinik doğrulukta, sade dil*

| Kaynak | Konu |
|---|---|
| Understanding Anxiety | Anksiyete |
| Understanding Depression | Depresyon |
| Worry Time | Endişe yönetimi |
| Relaxation Techniques | Gevşeme |

---

### 🥉 Tier 3 — Orta Öncelik

**SAMHSA (Substance Abuse and Mental Health Services Administration — US)**  
URL: https://store.samhsa.gov  
*Kamu malı — ücretsiz*  
Önerilen: Trauma-Informed Care, Building Resilience, Mental Health Recovery

**Psychology Tools**  
URL: https://psychologytools.com/download-therapy-worksheets/  
*Ücretsiz çalışma sayfaları (profesyonel lisans gerektiren premium içerik ayrı)*

**ACT (Acceptance and Commitment Therapy) — Free Resources**  
- Steven Hayes'in ACT açık erişim materyalleri
- Russ Harris'in "The Happiness Trap" ücretsiz kaynakları (https://www.actmindfully.com.au)

---

## 6. Temizlik Sonrası Beklenen İyileşme

| Metrik | Şu an | Temizlik Sonrası |
|---|---|---|
| Toplam chunk | 9.046 | ~4.500 |
| Klinik odaklı chunk oranı | %40 | **%85+** |
| Gürültü chunk | %3.3 | <%1 |
| Kapsanan klinik konu | 6 | **15+** |
| Ortalama retrieval kalitesi | Düşük-orta | **Yüksek** |

---

## 7. Uygulama Öncelikleri

### Hemen (Bu Hafta)
1. 🔴 8 alakasız PDF'i sil (bkz. Bölüm 3 — Kırmızı liste)
2. 🔴 6 genel ders kitabını sil (bkz. Bölüm 3 — Turuncu liste)
3. 🔴 Gürültü chunk filtresi: minimum 150 karakter (şu an 0 karakter)

### Kısa Vade (1-2 Hafta)
4. 🟠 CCI çalışma kitaplarını indir ve ekle (10 kitap × ~80 sayfa = ~800 yüksek kalite chunk)
5. 🟠 NHS self-help kılavuzlarını ekle (8 kılavuz)
6. 🟠 NIMH eksik yayınlarını ekle

### Orta Vade (1 Ay)
7. 🟡 Chunk boyutunu düzelt: sayfa başına 1 chunk → 400-500 token chunks + %10 overlap
8. 🟡 GetSelfHelp eksik çalışma sayfalarını ekle
9. 🟡 Mind UK ve Beyond Blue kılavuzlarını ekle
10. 🟡 Topic sınıflandırmasını genişlet: 6 topic → 15 topic

---

## 8. Teknik Not: Chunk Kalite Sorunları

Corpus analizi sırasında tespit edilen yapısal sorunlar:

1. **Tüm PDF'ler legacy mode ile işlenmiş** — Docling (vision parser) hiç çalışmamış. Görsel ağırlıklı sayfalar (diyagramlar, tablolar) boş veya düşük içerikli chunk üretiyor.

2. **Sayfa başına 1 chunk** (ortalama 2.588 karakter, ~650 token) — Embedding sinyali çok geniş alana yayılıyor, anlam netliği azalıyor. Önerilen: 400-500 token + %10 overlap.

3. **Topic sınıflandırması tutarsız** — Aynı PDF'in farklı sayfaları farklı topic'lere atanıyor. Topic PDF düzeyinde kilitlenmeli, sayfa düzeyinde değişmemeli.

4. **258 gürültü chunk** (footer, sayfa numarası, kapak sayfası) — Minimum içerik filtresi 100 → 150 karakter olarak güncellenmeli.

---

## 9. Lisans Risk Matrisi

Yeni kaynak eklemeden önce lisans durumunu netleştirmek kritiktir:

| Kaynak | Ticari Uygulama Riski | Gereken Aksiyon |
|---|---|---|
| **NIMH** | ✅ Yok — kamu malı | Sadece atıf |
| **SAMHSA** | ✅ Yok — kamu malı | Sadece atıf |
| **CCI** | ✅ Düşük — "serbestçe kullanılabilir" yazıyor | Ticari kullanım için CCI'ya e-posta: cci@health.wa.gov.au |
| **WHO** | 🟡 Orta — CC BY-NC-SA (ticari olmayan) | Calma'nın iş modeline göre WHO'dan onay alın |
| **NHS (OGL)** | ✅ Düşük — Open Government Licence | Atıf yeterli; NHS England'ı bilgilendirin |
| **Getselfhelp.co.uk** | 🟡 Orta — "eğitim amaçlı" | Carol Vivyan ile iletişim: carol@getselfhelp.co.uk |
| **Mind UK** | 🔴 Yüksek — tüm haklar saklı | Resmi lisans müzakeresi: legal@mind.org.uk |
| **Beyond Blue** | 🔴 Yüksek — tüm haklar saklı | Resmi lisans müzakeresi: info@beyondblue.org.au |
| **Psychology Tools** | 🔴 Yüksek — ücretli ürün | Ticari lisans satın alınması gerekir |

---

## 10. Altın Standart Müfredat (Referans)

NICE kılavuzları, APA klinik pratik kılavuzları ve WHO mhGAP çerçevesine göre kapsamlı bir ruh sağlığı self-help uygulaması şu konuları içermelidir:

**Seviye 1 — Temel (herkes için):**
- Duygular ve zihin-beden bağlantısı
- Stres temelleri (savaş-kaç tepkisi)
- Farkındalık temelleri (MBSR)
- Uyku hijyeni
- Değerler ve anlam (ACT)

**Seviye 2 — Yaygın sunumlar:**
- Depresyon (psikoeğitim + davranışsal aktivasyon + düşünce sorgulama)
- Anksiyete ve endişe (CBT modeli + endişe yönetimi)
- Panik bozukluk (panik döngüsü)
- Sosyal anksiyete (bilişsel model + maruz bırakma temelleri)
- Tükenmişlik (tanım, aşamalar, iyileşme)
- Uyku sorunları (CBT-I: uyarıcı kontrol, uyku kısıtlaması)

**Seviye 3 — Beceri tabanlı:**
- CBT çekirdek beceriler (düşünce kayıtları, davranışsal deneyler)
- Duygu düzenleme (DBT)
- Problem çözme
- ACT: defüzyon, kabul, değerler
- Öz-şefkat (Kristin Neff çerçevesi)

**Seviye 4 — Yaşam olayları:**
- Yas ve kayıp
- İlişki güçlükleri
- Travma psikoeğitimi (sadece eğitim, travma işleme değil)
- Yaşam geçişleri ve uyum

**Seviye 5 — Güvenlik:**
- İntihar düşüncelerini anlamak (damgalama karşıtı + güvenlik planlaması)
- Krize ne zaman ve nasıl yardım aranır
- Birini destekleme

---

*Rapor: Corpus analizi (9.046 chunk, 135 PDF) + global kaynak araştırması kombinasyonu ile oluşturulmuştur.*  
*Corpus verileri: Mayıs 2026. Kaynak araştırması bilgi kesim tarihi: Ağustos 2025.*

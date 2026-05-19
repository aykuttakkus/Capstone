# Calma — Retrieval Quality Evaluation

**Tarih:** 2026-05-18 06:17 UTC  
**Backend:** qdrant  
**Metrik:** P@5, R@5, nDCG@5, MRR@5  
**Sorgu sayısı:** 23  
**Corpus:** 23 golden query, gerçek PDF corpus  

---

## Özet

| Metrik | Skor | Hedef | Durum |
|--------|------|-------|-------|
| **Precision@5** | 0.583 | ≥ 0.4 | ✅ |
| **Recall@5** | 0.614 | ≥ 0.4 | ✅ |
| **nDCG@5** | 0.750 | ≥ 0.45 | ✅ |
| **MRR@5** | 1.000 | ≥ 0.5 | ✅ |

**Latency:** p50 = 6715 ms  |  p95 = 8298 ms

---

## Sorgu Detayları

| Sorgu | Topic | P@5 | R@5 | nDCG@5 | MRR@5 | ms |
|-------|-------|------|------|---------|--------|-----|
| What is stress and how does it affect the body? | stress_anxiety | 0.400 | 0.333 | 0.553 | 1.000 | 8063 |
| How does anxiety feel and what are its physical signs? | stress_anxiety | 1.000 | 0.833 | 1.000 | 1.000 | 5276 |
| I feel tense and restless all the time | stress_anxiety | 0.800 | 0.444 | 0.869 | 1.000 | 5905 |
| What are coping strategies for managing stress? | stress_anxiety | 0.800 | 0.500 | 0.869 | 1.000 | 5861 |
| I feel sad and have no energy | low_mood | 0.800 | 1.000 | 0.956 | 1.000 | 6508 |
| What is the difference between sadness and depression? | low_mood | 0.400 | 0.667 | 0.651 | 1.000 | 7498 |
| I have lost interest in things I used to enjoy | low_mood | 0.600 | 0.750 | 0.805 | 1.000 | 5950 |
| depression and self-worth hopeless worthless | low_mood | 0.400 | 0.500 | 0.637 | 1.000 | 7168 |
| What is burnout and how is it different from stress? | burnout_sleep | 0.400 | 0.667 | 0.765 | 1.000 | 7711 |
| I am exhausted all the time even after sleeping | burnout_sleep | 0.600 | 0.600 | 0.723 | 1.000 | 6491 |
| Sleep problems insomnia restless nights anxiety | burnout_sleep | 0.600 | 0.600 | 0.655 | 1.000 | 6807 |
| academic burnout student exam stress exhaustion | burnout_sleep | 0.600 | 1.000 | 1.000 | 1.000 | 5918 |
| social pressure mental health relationships | social_pressure | 0.600 | 0.600 | 0.655 | 1.000 | 6090 |
| loneliness isolation and mental wellbeing | social_pressure | 0.400 | 0.667 | 0.671 | 1.000 | 7641 |
| How to set boundaries in relationships | social_pressure | 0.800 | 0.667 | 0.869 | 1.000 | 6957 |
| When should I see a therapist or mental health professional? | help_seeking | 0.400 | 0.667 | 0.765 | 1.000 | 6140 |
| How do I find mental health support and treatment? | help_seeking | 0.400 | 0.500 | 0.637 | 1.000 | 5731 |
| stres ve kaygı nasıl azaltılır | stress_anxiety | 0.800 | 0.444 | 0.854 | 1.000 | 6699 |
| depresyon belirtileri ve tedavisi | low_mood | 0.600 | 0.750 | 0.832 | 1.000 | 8783 |
| uyku sorunları tükenmişlik yorgunluk | burnout_sleep | 0.400 | 0.400 | 0.485 | 1.000 | 8071 |
| mental health care and wellbeing | — | 0.600 | 0.429 | 0.723 | 1.000 | 6715 |
| OCD obsessive compulsive disorder symptoms | — | 0.400 | 0.500 | 0.559 | 1.000 | 7269 |
| trauma PTSD post-traumatic stress | — | 0.600 | 0.600 | 0.723 | 1.000 | 8298 |

---

## Notlar

> Golden set chunk ID'leri gerçek corpus'a dayanmaktadır.
> Düşük recall, ilgili chunk'ın corpus'ta olmadığını veya farklı bir ID ile
> indexlendiğini gösterebilir. Chunk ID'lerini `faiss_metadata.json`'dan doğrulayın.
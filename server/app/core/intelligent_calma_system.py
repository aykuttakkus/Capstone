"""
8-Step Intelligent LLM + RAG System
Kullanıcıyı anlayan, doğal ve faydalı yanıtlar veren sistem
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from server.app.core.generation.llm import OllamaClient
from server.app.rag_v2.rag_engine import RAGEngine


@dataclass
class UserUnderstanding:
    """Kullanıcıyı anlama sonucu"""
    original_message: str
    emotion: str  # yalnız, üzgün, kaygılı, meraklı, vb.
    need: str  # duygusal_destek, bilgi, öneri, sadece_konuşma
    topics: list[str]  # yalnızlık, anksiyete, uyku, vb.
    urgency: str  # düşük, orta, yüksek, acil


@dataclass  
class ConversationResult:
    """Sonuç"""
    response: str
    understanding: UserUnderstanding
    used_rag: bool


class IntelligentCalmaSystem:
    """
    8 Adımlı Akıllı Sistem:
    1. Anla (Understand)
    2. Duygu ve İhtiyaç Çıkar (Extract)
    3. Hemen Kaynak Çağırma (Delay RAG)
    4. Bilgi Gerekiyorsa RAG Çağır (Conditional)
    5. Yapıştırma, İşle (Process)
    6. Sadeleştir (Simplify)
    7. En Fazla 1 Soru (Limit)
    8. Faydalı Cevap (Valuable)
    """
    
    def __init__(self):
        self.llm = OllamaClient()
        self.rag = RAGEngine()
        self.sessions: dict[str, list[dict]] = {}
    
    def respond(self, user_message: str, session_id: str = "default") -> ConversationResult:
        """Ana yanıt fonksiyonu"""
        
        # 1. ADIM: Kullanıcıyı Anla
        understanding = self._understand_user(user_message)
        
        # 2. ADIM: Duygu ve İhtiyaç Çıkarıldı (understanding içinde)
        
        # Session geçmişini al
        history = self.sessions.get(session_id, [])
        
        # 3. ADIM: Hemen Kaynak Çağırma - Önce karar ver
        needs_rag = self._decide_if_rag_needed(understanding)
        
        rag_info = ""
        if needs_rag:
            # 4. ADIM: Bilgi Gerekiyorsa RAG Çağır
            try:
                rag_result = self.rag.answer(user_message, top_k=2)
                if rag_result.retrieved_chunks:
                    rag_info = rag_result.context
            except:
                pass
        
        # 5-6-7-8. ADIMLAR: İşle, Sadeleştir, 1 Soru, Faydalı Cevap
        response = self._generate_intelligent_response(
            user_message,
            understanding,
            history,
            rag_info
        )
        
        # Session'a kaydet
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({
            "user": user_message,
            "understanding": understanding,
            "assistant": response
        })
        
        # Sadece son 5 konuşmayı tut
        if len(self.sessions[session_id]) > 5:
            self.sessions[session_id] = self.sessions[session_id][-5:]
        
        return ConversationResult(
            response=response,
            understanding=understanding,
            used_rag=bool(rag_info)
        )
    
    def _understand_user(self, message: str) -> UserUnderstanding:
        """1. ADIM: Kullanıcıyı gerçekten anla"""
        
        prompt = f"""Bu mesajı analiz et:

Mesaj: "{message}"

Şu formatta yanıt ver:
DUYGU: [yalnız/üzgün/kaygılı/öfkeli/meraklı/nötr/mutlu]
İHTİYAÇ: [duygusal_destek/bilgi/öneri/sadece_konuşma]
KONULAR: [konu1, konu2]
ACİLLİK: [düşük/orta/yüksek/acil]

Analiz:"""
        
        result = self.llm.generate(prompt, temperature=0.3)
        
        if result.available:
            # Basit parsing
            text = result.text.strip()
            
            # Varsayılan değerler
            emotion = "nötr"
            need = "sadece_konuşma"
            topics = []
            urgency = "düşük"
            
            # Parse et
            for line in text.split("\n"):
                if "DUYGU:" in line:
                    emotion = line.split(":")[1].strip().lower()
                elif "İHTİYAÇ:" in line or "IHTIYAC:" in line:
                    need = line.split(":")[1].strip().lower()
                elif "KONULAR:" in line:
                    topics = [t.strip() for t in line.split(":")[1].split(",")]
                elif "ACİLLİK:" in line or "ACILLIK:" in line:
                    urgency = line.split(":")[1].strip().lower()
            
            return UserUnderstanding(
                original_message=message,
                emotion=emotion,
                need=need,
                topics=topics,
                urgency=urgency
            )
        
        # Fallback
        return UserUnderstanding(
            original_message=message,
            emotion="nötr",
            need="sadece_konuşma",
            topics=[],
            urgency="düşük"
        )
    
    def _decide_if_rag_needed(self, understanding: UserUnderstanding) -> bool:
        """3-4. ADIM: RAG gerekli mi?"""
        
        # Bilgi ihtiyacı varsa RAG çağır
        if understanding.need in ["bilgi", "öneri"]:
            return True
        
        # Belirli konular varsa RAG çağır
        info_topics = ["anksiyete", "depresyon", "uyku", "stres", "teknik", "yöntem"]
        for topic in understanding.topics:
            if any(info in topic.lower() for info in info_topics):
                return True
        
        # Duygusal destek sadece konuşma - RAG gerekmez
        return False
    
    def _generate_intelligent_response(
        self,
        user_message: str,
        understanding: UserUnderstanding,
        history: list[dict],
        rag_info: str
    ) -> str:
        """5-6-7-8. ADIMLAR: İşle, Sadeleştir, 1 Soru, Faydalı"""
        
        # Geçmişi formatla
        history_text = ""
        if history:
            for h in history[-3:]:  # Son 3 konuşma
                history_text += f"Kullanıcı: {h['user']}\n"
                history_text += f"Sen: {h['assistant'][:100]}...\n\n"
        
        # RAG bilgisini işle (yapıştırma)
        processed_info = ""
        if rag_info:
            # RAG bilgisini sadeleştir
            processed_info = self._simplify_rag_info(rag_info, understanding)
        
        # Yanıt üret
        if understanding.need == "duygusal_destek":
            prompt = f"""Empatik bir arkadaş gibi yanıt ver.

Önceki konuşma:
{history_text}

Kullanıcı şunu söyledi: "{user_message}"
Kullanıcı {understanding.emotion} hissediyor.

Görev:
1. Önce duygusunu doğrula ("Anlıyorum, yalnız hissetmek zor...")
2. Kısa ve samimi destek ver
3. EN FAZLA 1 kısa soru sor (konuşmayı devam ettirmek için)
4. Kullanıcı cevap vermese bile faydalı olsun

Yanıtın:"""
        
        elif understanding.need in ["bilgi", "öneri"] and processed_info:
            prompt = f"""Bilgiyi kullanıcının anlayacağı şekilde anlat.

Önceki konuşma:
{history_text}

Kullanıcı sordu: "{user_message}"

Kaynaklardan bulunan bilgiler:
{processed_info}

Görev:
1. Bilgiyi kendi cümlelerinle, sade anlat
2. Birebir kopyalama
3. Kullanıcının seviyesine göre sadeleştir
4. EN FAZLA 1 kısa soru sor
5. Kullanıcı cevap vermese bile faydalı olsun

Yanıtın:"""
        else:
            prompt = f"""Doğal sohbet et.

Önceki konuşma:
{history_text}

Kullanıcı: "{user_message}"

Görev:
1. Samimi ve doğal yanıt ver
2. Konuşmayı kesme, devam ettir
3. EN FAZLA 1 kısa soru sor
4. Kullanıcı cevap vermese bile faydalı olsun

Yanıtın:"""
        
        result = self.llm.generate(prompt, temperature=0.7)
        
        if result.available and result.text:
            return result.text.strip()
        
        return "Anlamaya çalışıyorum. Biraz daha anlatır mısın?"
    
    def _simplify_rag_info(self, rag_info: str, understanding: UserUnderstanding) -> str:
        """5-6. ADIM: RAG bilgisini işle ve sadeleştir"""
        
        # RAG bilgisini LLM'e sadeleştir
        prompt = f"""Bu bilgileri çok sade ve anlaşılır şekilde özetle:

Bilgiler:
{rag_info[:1500]}

Kullanıcı {understanding.emotion} hissediyor ve {understanding.need} arıyor.

Sadeleştirilmiş özet (3-4 cümle):"""
        
        result = self.llm.generate(prompt, temperature=0.5)
        
        if result.available:
            return result.text.strip()
        
        # Fallback - ilk 500 karakteri al
        return rag_info[:500]


# Global instance
intelligent_system = IntelligentCalmaSystem()


def get_smart_response(user_message: str, session_id: str = "default") -> str:
    """Basit API"""
    result = intelligent_system.respond(user_message, session_id)
    return result.response

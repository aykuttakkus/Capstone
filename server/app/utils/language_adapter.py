from __future__ import annotations

"""Language detection and bilingual (Turkish/English) response adaptation."""

_TR_INDICATORS = [
    "ım", "im", "um", "üm",   # Turkish suffixes
    "mı", "mi", "mu", "mü",   # question particles
    " ve ", " ile ", " de ", " da ", " ki ",  # common Turkish words
    "için", "ama", "çok", "nasıl", "neden", "çünkü",
    "hissediyorum", "istiyorum", "bilmiyorum", "yapamıyorum",
    "yardım", "kaygı", "endişe", "üzgün", "mutsuz",
]

_TR_OPENING_TEMPLATES = [
    "Bunu benimle paylaştığın için teşekkür ederim.",
    "Seni duyuyorum.",
    "Bu hissiyatı yaşamak gerçekten zorlu olabilir.",
]

_EN_OPENING_TEMPLATES = [
    "Thank you for sharing this with me.",
    "I hear you.",
    "That sounds genuinely difficult.",
]


def detect_language(message: str) -> str:
    """Return 'tr' if message is likely Turkish, else 'en'."""
    lowered = message.lower()
    tr_hits = sum(1 for indicator in _TR_INDICATORS if indicator in lowered)
    return "tr" if tr_hits >= 2 else "en"


class LanguageAdapter:
    """Adapt system prompts and response openings to detected user language."""

    def adapt_system_note(self, detected_language: str) -> str:
        """Return a language instruction to embed in the system prompt."""
        if detected_language == "tr":
            return (
                "Kullanıcı Türkçe yazıyor. Yanıtlarını Türkçe ver. "
                "Klinik sınırları koru; teşhis ve ilaç önerisi yapma."
            )
        return (
            "Respond in English. Maintain clinical boundaries; "
            "avoid diagnosis and medication advice."
        )

    def warm_opening(self, detected_language: str) -> str:
        """Return a culturally appropriate warm opening line."""
        templates = _TR_OPENING_TEMPLATES if detected_language == "tr" else _EN_OPENING_TEMPLATES
        return templates[0]

    def adapt_crisis_numbers(self, detected_language: str, country_code: str = "TR") -> str:
        """Return localised crisis resource text."""
        resources = {
            "TR": {
                "tr": "🆘 Acil yardım için: 182 (İntihar Önleme Hattı) veya 112 (Acil Servis).",
                "en": "🆘 Emergency (Turkey): 182 (Suicide Prevention Line) or 112 (Emergency).",
            },
            "US": {
                "tr": "🆘 Kriz hattı (ABD): 988 (Suicide & Crisis Lifeline).",
                "en": "🆘 Crisis line (US): Call or text 988 (Suicide & Crisis Lifeline).",
            },
        }
        country_resources = resources.get(country_code, resources["TR"])
        return country_resources.get(detected_language, country_resources["en"])


language_adapter = LanguageAdapter()

from __future__ import annotations

from dataclasses import dataclass

from server.app.utils.text import contains_any, normalize_text


@dataclass(slots=True)
class IntentClassification:
    label: str
    confidence: float
    rationale: str


class IntentClassifier:
    """
    Rule-based intent classifier for English mental health queries.

    Labels (in priority order):
      crisis_related   — serious self-harm or distress signals (handled by safety
                         policy but mirrored here for transparency)
      help_seeking     — user wants to know where/how to get support
      coping_info      — user wants practical coping strategies
      psychoeducation  — user wants to understand a topic
      general          — catch-all
    """

    def classify(self, text: str) -> IntentClassification:
        normalized = normalize_text(text)

        if contains_any(normalized, [
            "help", "support", "what should i do", "where can i go",
            "who can i talk to", "need someone", "seeking help",
            "find a therapist", "see a professional", "should i see",
            "how to get help", "resources",
        ]):
            return IntentClassification("help_seeking", 0.88, "help-seeking language detected")

        if contains_any(normalized, [
            "coping", "cope", "how to cope", "how to deal",
            "what can i do", "how do i manage",
            "technique", "strategy", "exercise", "breathing",
            "relax", "calm down", "grounding",
        ]):
            return IntentClassification("coping_info", 0.84, "coping language detected")

        if contains_any(normalized, [
            "what is", "what are", "explain", "tell me about",
            "i want to understand", "how does", "why do i",
            "what does it mean", "signs of", "symptoms of",
            "stress", "anxiety", "depression", "burnout",
            "panic", "ocd", "ptsd", "trauma",
            "low mood", "feeling down",
        ]):
            return IntentClassification("psychoeducation", 0.78, "psychoeducation language detected")

        return IntentClassification("general", 0.50, "no strong intent signal")

from __future__ import annotations

from server.app.utils.text import contains_any, contains_any_typo_tolerant, normalize_text


TOPIC_KEYWORDS = {
    "stress_anxiety": ["stress", "anxiety", "panic", "worry", "kaygi", "stres"],
    "low_mood": ["low mood", "depressed", "sad", "hopeless", "mood", "cok uzgun", "depresif"],
    "burnout_sleep": ["burnout", "fatigue", "sleep", "tired", "uyku", "yorgun"],
    "social_pressure": ["relationship", "social", "family", "pressure", "iletişim", "arkadas"],
    "help_seeking": ["help", "support", "where to start", "yardim", "destek"],
}


TOPIC_LABELS = {
    "stress_anxiety": "Stress and Anxiety",
    "low_mood": "Low Mood",
    "burnout_sleep": "Burnout and Sleep",
    "social_pressure": "Social and Relationship Pressure",
    "help_seeking": "Help Seeking",
    "general": "General Psychoeducation",
}


def infer_topic(message: str, intake: dict[str, str] | None = None) -> str:
    # Priority 1: Current message (What is the user asking right now?)
    normalized_msg = normalize_text(message)
    for topic, keywords in TOPIC_KEYWORDS.items():
        if contains_any(normalized_msg, keywords) or contains_any_typo_tolerant(normalized_msg, keywords):
            return topic

    # Priority 2: Intake data (If message is vague, look at their history)
    if intake:
        main_issue = normalize_text(str(intake.get("main_issue", "")))
        for topic, keywords in TOPIC_KEYWORDS.items():
            if contains_any(main_issue, keywords) or contains_any_typo_tolerant(main_issue, keywords):
                return topic

    return "general"


def topic_label(topic: str) -> str:
    return TOPIC_LABELS.get(topic, TOPIC_LABELS["general"])

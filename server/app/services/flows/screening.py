from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class Question(TypedDict):
    id: str
    text: str


@dataclass(slots=True)
class ScreeningResult:
    scale_name: str
    score: int
    severity: str
    crisis_flag: bool


# ──────────────────────────────────────────────────────────────
# PHQ-9 (Depression Screening)
# ──────────────────────────────────────────────────────────────
PHQ9_QUESTIONS: list[Question] = [
    {"id": "phq_1", "text": "Little interest or pleasure in doing things"},
    {"id": "phq_2", "text": "Feeling down, depressed, or hopeless"},
    {"id": "phq_3", "text": "Trouble falling or staying asleep, or sleeping too much"},
    {"id": "phq_4", "text": "Feeling tired or having little energy"},
    {"id": "phq_5", "text": "Poor appetite or overeating"},
    {"id": "phq_6", "text": "Feeling bad about yourself, or that you are a failure"},
    {"id": "phq_7", "text": "Trouble concentrating on things, such as reading or watching TV"},
    {"id": "phq_8", "text": "Moving or speaking so slowly that other people could have noticed? Or the opposite"},
    {"id": "phq_9", "text": "Thoughts that you would be better off dead, or of hurting yourself in some way"},
]

def score_phq9(answers: dict[str, int]) -> ScreeningResult:
    """Calculates PHQ-9 score (0-27) and severity."""
    total = sum(answers.values())
    crisis = answers.get("phq_9", 0) > 0
    
    if total <= 4:
        severity = "Minimal"
    elif total <= 9:
        severity = "Mild"
    elif total <= 14:
        severity = "Moderate"
    elif total <= 19:
        severity = "Moderately Severe"
    else:
        severity = "Severe"
        
    return ScreeningResult("PHQ-9", total, severity, crisis)


# ──────────────────────────────────────────────────────────────
# GAD-7 (Anxiety Screening)
# ──────────────────────────────────────────────────────────────
GAD7_QUESTIONS: list[Question] = [
    {"id": "gad_1", "text": "Feeling nervous, anxious or on edge"},
    {"id": "gad_2", "text": "Not being able to stop or control worrying"},
    {"id": "gad_3", "text": "Worrying too much about different things"},
    {"id": "gad_4", "text": "Trouble relaxing"},
    {"id": "gad_5", "text": "Being so restless that it is hard to sit still"},
    {"id": "gad_6", "text": "Becoming easily annoyed or irritable"},
    {"id": "gad_7", "text": "Feeling afraid as if something awful might happen"},
]

def score_gad7(answers: dict[str, int]) -> ScreeningResult:
    """Calculates GAD-7 score (0-21) and severity."""
    total = sum(answers.values())
    
    if total <= 4:
        severity = "Minimal"
    elif total <= 9:
        severity = "Mild"
    elif total <= 14:
        severity = "Moderate"
    else:
        severity = "Severe"
        
    return ScreeningResult("GAD-7", total, severity, False)

RESPONSE_OPTIONS = [
    "Not at all",
    "Several days",
    "More than half the days",
    "Nearly every day"
]

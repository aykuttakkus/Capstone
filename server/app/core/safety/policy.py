from __future__ import annotations

import re
from dataclasses import dataclass

from server.app.utils.text import contains_any

_NEGATION_PATTERNS = re.compile(
    r"\b(not|never|don'?t|doesn'?t|didn'?t|won'?t|wouldn'?t|haven'?t|hasn'?t|can'?t|cannot)\b",
    re.IGNORECASE,
)
_NEG_WINDOW = 40


def _negated(text: str, match_start: int) -> bool:
    window = text[max(0, match_start - _NEG_WINDOW): match_start]
    return bool(_NEGATION_PATTERNS.search(window))


def contains_any_non_negated(text: str, phrases: list[str]) -> bool:
    normalized = text.strip().lower()
    for phrase in phrases:
        idx = normalized.find(phrase.lower())
        if idx != -1 and not _negated(normalized, idx):
            return True
    return False


CRISIS_KEYWORDS = [
    "kill myself", "killing myself",
    "suicide", "suicidal",
    "end my life", "end it all",
    "want to die", "i want to die",
    "not want to be alive", "don't want to be alive",
    "take my own life",
    "hurt myself", "hurting myself",
    "self harm", "self-harm", "selfharm",
    "cutting myself", "cut myself",
    "i'm not safe", "i am not safe", "not safe right now",
    "going to hurt myself",
    "plan to hurt",
    "no reason to live",
    "ready to give up",
    "can't go on",
    "cannot go on",
]

CLARIFICATION_KEYWORDS = [
    "i cannot do this anymore", "i can't do this anymore",
    "i can't take this anymore", "i cannot take this anymore",
    "everything feels pointless", "nothing feels worth it",
    "everything feels completely pointless",
    "i feel like disappearing", "want to disappear",
    "i feel unsafe", "feeling unsafe",
    "i give up", "want to give up",
    "no point anymore", "there's no point", "there is no point",
    "i feel hopeless", "completely hopeless",
    "i feel like a burden",
    "everyone would be better without me",
    "better off without me",
    "i feel nothing", "feel completely empty",
    "can't see a way out", "cannot see a way out",
    "life has no meaning", "no meaning to life",
    "i don't see the point", "i do not see the point",
    "i am so tired of everything",
    "i feel empty inside",
    "nothing matters anymore",
]

DIAGNOSIS_KEYWORDS = [
    "do i have",
    "am i bipolar", "am i depressed", "am i schizophrenic",
    "am i anxious", "am i autistic",
    "diagnose me", "can you diagnose",
    "what disorder do i have", "what condition do i have",
    "what mental illness do i have",
    "do i have depression", "do i have anxiety",
    "do i have ocd", "do i have ptsd",
    "do i have adhd",
    "tell me if this is",
    "is this a mental illness",
    "is this depression", "is this anxiety or", "is this anxiety",
    "sounds like i have", "think i might have",
    "what diagnosis", "what's my diagnosis", "what is my diagnosis",
    "what's wrong with me mentally",
    "could this be a disorder",
    "based on my symptoms, what",
    "based on what i said, what",
]

MEDICATION_KEYWORDS = [
    "should i take", "should i start taking",
    "what medication", "what medicine", "what drug",
    "which antidepressant", "antidepressants",
    "medication for anxiety", "medication for depression",
    "ssri", "snri", "benzodiazepine", "xanax", "prozac",
    "sertraline", "fluoxetine", "citalopram",
    "what dose", "what dosage", "how much should i take",
    "should i stop my medication", "should i stop taking",
    "can i stop my medication",
    "treatment plan", "prescribe", "prescription",
    "what pill", "which pill",
    "should i increase", "should i decrease",
]

OFF_DOMAIN_KEYWORDS = [
    "what food", "what should i eat", "diet plan", "weight loss",
    "stock market", "investment", "cryptocurrency",
    "write my essay", "write my code",
    "capital of", "population of",
    "football match", "basketball game",
    "recipe for", "how to cook",
    "who won the",
]

PROMPT_INJECTION_KEYWORDS = [
    "ignore your instructions", "ignore your rules",
    "forget your guidelines", "forget your rules",
    "you are now", "pretend you are", "act as a doctor",
    "act as a therapist", "act as a psychiatrist",
    "pretend to be", "from now on you are",
    "system prompt", "developer message", "hidden instructions",
    "override", "jailbreak",
    "disable safety", "ignore safety",
    "your new instructions are",
    "disregard previous",
]


@dataclass(slots=True)
class SafetyDecision:
    mode: str
    reason: str
    message: str
    risk_level: int


class SafetyPolicyEngine:
    def evaluate(self, text: str) -> SafetyDecision:
        normalized = text.strip().lower()

        if contains_any(normalized, PROMPT_INJECTION_KEYWORDS):
            return SafetyDecision(
                mode="prompt_injection_blocked",
                reason="prompt_injection_detected",
                message=(
                    "I can’t follow requests to override my safety rules or hidden instructions. "
                    "I’m here to help with safe, psychoeducational mental health information."
                ),
                risk_level=0,
            )

        if contains_any_non_negated(normalized, CRISIS_KEYWORDS):
            return SafetyDecision(
                mode="crisis_support",
                reason="crisis_language_detected",
                message=(
                    "I'm really glad you said this out loud. If you might act on these thoughts, "
                    "please contact local emergency services or a crisis line now. If possible, "
                    "move closer to a trusted person and do not stay alone."
                ),
                risk_level=3,
            )

        if contains_any_non_negated(normalized, CLARIFICATION_KEYWORDS):
            return SafetyDecision(
                mode="risk_clarification",
                reason="ambiguous_distress_detected",
                message=(
                    "I want to check in before we continue. Are you safe right now? "
                    "Do you need urgent support, or would you like to keep talking here?"
                ),
                risk_level=1,
            )

        if contains_any(normalized, MEDICATION_KEYWORDS):
            return SafetyDecision(
                mode="medication_refusal",
                reason="medication_request_detected",
                message=(
                    "I can’t give medication advice, dosage instructions, or treatment recommendations. "
                    "For medication questions, please speak with a doctor or pharmacist. "
                    "I can still share general psychoeducational information."
                ),
                risk_level=0,
            )

        if contains_any(normalized, DIAGNOSIS_KEYWORDS):
            return SafetyDecision(
                mode="diagnosis_refusal",
                reason="diagnosis_request_detected",
                message=(
                    "I can’t diagnose mental health conditions or confirm a disorder. Only a qualified professional can do that. "
                    "I can still explain the topic in general terms and point you to trusted information."
                ),
                risk_level=0,
            )

        if contains_any(normalized, OFF_DOMAIN_KEYWORDS):
            return SafetyDecision(
                mode="off_domain",
                reason="off_domain_request_detected",
                message=(
                    "That topic is outside Calma’s scope. I’m here for mental health topics like stress, anxiety, low mood, burnout, sleep, and help-seeking."
                ),
                risk_level=0,
            )

        return SafetyDecision(mode="normal", reason="no_safety_signal", message="", risk_level=0)

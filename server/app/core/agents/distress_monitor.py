from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DistressSignal:
    category: str
    confidence: float
    turn_number: int
    raw_text: str


@dataclass(slots=True)
class DistressAnalysis:
    signals: list[DistressSignal] = field(default_factory=list)
    escalation_detected: bool = False
    cumulative_risk: float = 0.0
    recommended_action: str = ""
    current_distress_level: int = 0


class SubtleDistressMonitor:
    DISTRESS_KEYWORDS = {
        "hopelessness": [
            "hopeless", "no point", "won't get better", "nothing works", "give up",
            "umutsuz", "hiçbir şey işe yaramıyor", "vazgeç"
        ],
        "burden": [
            "burden", "weight", "drag down", "trouble", "problem for", "yük", "çekiş",
            "aileme yük", "insanları rahatsız ediyor"
        ],
        "goodbye": [
            "goodbye", "goodbye letter", "say goodbye", "better off", "without me",
            "hoşça", "mektup", "daha iyi olur"
        ],
        "numbness": [
            "numb", "empty", "nothing matters", "don't care", "disconnected", "boş hisset",
            "umurumda değil", "kopuk"
        ],
        "withdrawal": [
            "isolate", "alone", "withdraw", "hide", "stay away", "uzaklaş", "çekil",
            "yalnız kalmak", "insanlardan uzaklaş"
        ],
        "shame": [
            "ashamed", "embarrassed", "worthless", "failure", "disgrace", "utanç",
            "başarısız", "değersiz", "rezil"
        ],
        "helplessness": [
            "helpless", "can't control", "powerless", "stuck", "trapped", "çaresiz",
            "sıkışmış", "kötü durumdayım"
        ],
    }

    def __init__(self) -> None:
        self.signal_history: list[DistressSignal] = []

    def analyze(
        self,
        current_message: str,
        recent_conversation: list[dict[str, Any]],
        current_risk_state: dict[str, Any],
        turn_number: int = 0,
    ) -> DistressAnalysis:
        analysis = DistressAnalysis()

        # Step 1: Detect signals in current message
        signals = self._detect_signals(current_message, turn_number)
        analysis.signals = signals

        # Step 2: Check for cumulative escalation
        if self._detect_cumulative_escalation(recent_conversation, signals):
            analysis.escalation_detected = True

        # Step 3: Compute cumulative risk
        current_risk = current_risk_state.get("distress_level", 0)
        analysis.cumulative_risk = min(current_risk + len(signals) * 0.1, 1.0)
        analysis.current_distress_level = int(analysis.cumulative_risk * 5)

        # Step 4: Recommend action
        analysis.recommended_action = self._recommend_action(
            signals, analysis.escalation_detected, current_risk
        )

        # Track for history
        self.signal_history.extend(signals)

        return analysis

    def _detect_signals(self, message: str, turn_number: int) -> list[DistressSignal]:
        signals = []
        normalized = message.lower()

        for category, keywords in self.DISTRESS_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in normalized:
                    confidence = 0.6 if len(keyword) > 5 else 0.4
                    if keyword.lower() == normalized.strip():
                        confidence = 0.95

                    signals.append(
                        DistressSignal(
                            category=category,
                            confidence=confidence,
                            turn_number=turn_number,
                            raw_text=message,
                        )
                    )
                    break

        return signals

    def _detect_cumulative_escalation(
        self, recent_user_messages: list[dict[str, Any]], current_signals: list[DistressSignal]
    ) -> bool:
        if not recent_user_messages:
            return False

        if len(current_signals) == 0:
            return False

        recent_signal_count = len(self.signal_history[-10:]) if self.signal_history else 0
        escalation_threshold = 3

        return recent_signal_count >= escalation_threshold and len(current_signals) > 0

    def _recommend_action(
        self, signals: list[DistressSignal], escalation: bool, current_risk: int
    ) -> str:
        if not signals:
            return "continue_normally"

        if escalation or current_risk > 3:
            critical_categories = {"goodbye", "hopelessness", "helplessness"}
            has_critical = any(s.category in critical_categories for s in signals)

            if has_critical:
                return "escalate_to_crisis_resources"
            else:
                return "increase_safety_checks"

        if current_risk >= 2:
            return "validate_and_explore_support"

        return "continue_with_gentle_monitoring"

    def reset_history(self) -> None:
        self.signal_history.clear()

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class RiskState:
    """
    Unified risk state tracking throughout conversation.
    Consolidates risk information from multiple sources.
    """
    current_risk_level: str  # "none", "low", "medium", "high", "crisis"
    risk_indicators: list[str] = field(default_factory=list)
    cumulative_risk_signals: list[str] = field(default_factory=list)
    crisis_protocol_active: bool = False
    needs_human_support: bool = False
    last_risk_check: datetime | None = None
    safety_analysis_reasoning: str = ""
    escalation_recommended: bool = False

    def escalate(self, reason: str) -> None:
        """Mark for escalation."""
        self.needs_human_support = True
        self.escalation_recommended = True
        if reason not in self.risk_indicators:
            self.risk_indicators.append(reason)

    def activate_crisis_protocol(self) -> None:
        """Activate crisis protocol."""
        self.crisis_protocol_active = True
        self.current_risk_level = "crisis"
        self.needs_human_support = True
        self.last_risk_check = datetime.now()

    def is_high_risk(self) -> bool:
        """Check if current state is high or crisis risk."""
        return self.current_risk_level in ["high", "crisis"]

    def update_risk_check(self, new_level: str, reasoning: str) -> None:
        """Update risk check timestamp and level."""
        current_rank = self._risk_rank(self.current_risk_level)
        new_rank = self._risk_rank(new_level)
        if current_rank < self._risk_rank("high") or new_rank >= current_rank:
            self.current_risk_level = new_level
        self.last_risk_check = datetime.now()
        self.safety_analysis_reasoning = reasoning

    @staticmethod
    def _risk_rank(level: str) -> int:
        return {
            "none": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
            "crisis": 4,
        }.get(level, 0)

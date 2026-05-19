# DEPRECATED: Old Valence-Arousal-Dominance model, not in current spec.
# Use Response Planner's tone setting instead. Kept for compatibility only.
# TODO: Remove in next major refactor

from __future__ import annotations

from dataclasses import dataclass, field


VAD_MAP = {
    "sadness": {"valence": -0.8, "arousal": -0.4, "dominance": -0.5},
    "fear": {"valence": -0.7, "arousal": 0.6, "dominance": -0.6},
    "anger": {"valence": -0.6, "arousal": 0.8, "dominance": 0.3},
    "joy": {"valence": 0.8, "arousal": 0.6, "dominance": 0.5},
    "neutral": {"valence": 0.0, "arousal": 0.0, "dominance": 0.0},
}


@dataclass(slots=True)
class VADTracker:
    state: dict[str, float] = field(default_factory=lambda: {"valence": 0.5, "arousal": 0.5, "dominance": 0.5})

    def update(self, emotion_label: str, score: float) -> None:
        delta = VAD_MAP.get(emotion_label, VAD_MAP["neutral"])
        for dimension, value in delta.items():
            self.state[dimension] = 0.7 * self.state[dimension] + 0.3 * value * max(score, 0.1)

    @property
    def is_heavy(self) -> bool:
        return self.state["valence"] < -0.4 and self.state["arousal"] > 0.3

    @property
    def pace_instruction(self) -> str:
        if self.is_heavy:
            return "PACE: Heavy. Short sentences. Less info. More space."
        return ""

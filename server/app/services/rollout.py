from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class RolloutDecision:
    enabled: bool
    mode: str
    traffic_percent: int
    reason: str


def should_enable_feature(user_id: int | None = None) -> RolloutDecision:
    mode = (os.getenv("ROLLOUT_MODE", "stable") or "stable").strip().lower()
    traffic_percent = max(0, min(100, int(os.getenv("ROLLOUT_TRAFFIC_PERCENT", "0"))))

    if mode in {"off", "disabled"}:
        return RolloutDecision(False, mode, traffic_percent, "rollout_disabled")
    if mode in {"stable", "full"}:
        return RolloutDecision(True, mode, traffic_percent, "rollout_enabled")
    if mode in {"canary", "partial"}:
        if user_id is None:
            return RolloutDecision(False, mode, traffic_percent, "missing_user_id")
        bucket = abs(int(user_id)) % 100
        return RolloutDecision(bucket < traffic_percent, mode, traffic_percent, f"bucket_{bucket}")
    return RolloutDecision(True, mode, traffic_percent, "unknown_mode_default_on")

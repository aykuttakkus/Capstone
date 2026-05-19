# DEPRECATED: Overlaps with Distress Monitor (§10) spec.
# Unused in current pipeline. May be consolidated with new Distress Monitor in Phase 1.
# Kept for compatibility only.
# TODO: Review and consolidate in Phase 1

from __future__ import annotations

import re
from collections import Counter
from typing import Any


WORD_RE = re.compile(r"[a-zA-ZçğıöşüÇĞİÖŞÜ']+")

COGNITIVE_DISTORTIONS = {
    "all_or_nothing": ["hiçbir zaman", "her zaman", "never", "always", "ya hep ya hiç"],
    "catastrophizing": ["mahvoldum", "bitti", "ruined", "disaster", "felaket", "done"],
    "mind_reading": ["anlayamıyorlar", "they think", "she knows", "they know", "biliyorlar"],
    "self_blame": ["benim hatam", "my fault", "because of me", "suçum", "ben yüzünden"],
}

CHANGE_TALK_PATTERNS = {
    "desire": ["istiyorum", "olmasını isterdim", "keşke", "i want", "i wish"],
    "ability": ["yapabilirim", "deneyebilirim", "i could", "i might"],
    "reason": ["çünkü", "bu yüzden", "yararlı olurdu", "because"],
    "need": ["zorundayım", "böyle devam edemem", "i need to", "i have to"],
    "commitment": ["yapacağım", "deneyeceğim", "i will", "i'm going to"],
}


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _user_messages(history: list[dict[str, Any]]) -> list[str]:
    return [str(item.get("content", "")) for item in history if item.get("role") == "user" and str(item.get("content", "")).strip()]


def detect_within_session_patterns(history: list[dict[str, Any]]) -> list[str]:
    tokens = Counter()
    for message in _user_messages(history):
        for token in WORD_RE.findall(message.lower()):
            if len(token) < 4:
                continue
            tokens[token] += 1

    patterns: list[str] = []
    for word, count in tokens.most_common():
        if count < 3:
            continue
        patterns.append(f"'{word}' bu seansta {count} kez tekrarlandı")
        if len(patterns) >= 5:
            break
    return patterns


def detect_cognitive_distortions(history: list[dict[str, Any]]) -> list[str]:
    seen: list[str] = []
    for message in _user_messages(history):
        normalized = _normalize(message)
        for key, markers in COGNITIVE_DISTORTIONS.items():
            if key in seen:
                continue
            if any(marker in normalized for marker in markers):
                seen.append(key)
    return seen


def detect_cross_session_patterns(structured_memory: dict[str, Any]) -> list[str]:
    patterns: list[str] = []
    recurring = structured_memory.get("recurring_themes", []) if isinstance(structured_memory, dict) else []
    for item in recurring:
        if not isinstance(item, dict):
            continue
        theme = str(item.get("theme", "")).strip()
        if not theme:
            continue
        try:
            count = int(item.get("count", 0))
        except (TypeError, ValueError):
            count = 0
        if count >= 3:
            patterns.append(f"'{theme}' {count} seanstır gündemde")
    return patterns


def detect_change_talk_patterns(text: str) -> list[str]:
    normalized = _normalize(text)
    patterns: list[str] = []
    for label, markers in CHANGE_TALK_PATTERNS.items():
        if any(marker in normalized for marker in markers):
            patterns.append(label)
    return patterns

from __future__ import annotations

import difflib
import re
from typing import Iterable


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def tokenize(text: str) -> list[str]:
    return re.findall(r"[^\W_]+", normalize_text(text), flags=re.UNICODE)


def contains_any(text: str, phrases: Iterable[str]) -> bool:
    normalized = normalize_text(text)
    return any(phrase.lower() in normalized for phrase in phrases)


def contains_any_typo_tolerant(text: str, phrases: Iterable[str], *, cutoff: float = 0.8) -> bool:
    normalized = normalize_text(text)
    tokens = tokenize(normalized)

    for phrase in phrases:
        normalized_phrase = normalize_text(str(phrase))
        if normalized_phrase in normalized:
            return True

        if " " in normalized_phrase or len(normalized_phrase) < 5:
            continue

        for token in tokens:
            if difflib.SequenceMatcher(None, token, normalized_phrase).ratio() >= cutoff:
                return True

    return False


def fuzzy_token_overlap(left: Iterable[str], right: Iterable[str], *, cutoff: float = 0.84) -> int:
    left_tokens = [token for token in left if token]
    right_tokens = [token for token in right if token]
    if not left_tokens or not right_tokens:
        return 0

    matches = 0
    used_right: set[int] = set()
    for left_token in left_tokens:
        for index, right_token in enumerate(right_tokens):
            if index in used_right:
                continue
            if left_token == right_token:
                matches += 1
                used_right.add(index)
                break
            if len(left_token) < 4 or len(right_token) < 4:
                continue
            if difflib.SequenceMatcher(None, left_token, right_token).ratio() >= cutoff:
                matches += 1
                used_right.add(index)
                break

    return matches


def infer_language(text: str) -> str:
    normalized = normalize_text(text)
    turkish_chars = set("çğıöşüİÇĞİÖŞÜ")
    if any(char in normalized for char in turkish_chars):
        return "tr"

    tr_markers = {"ve", "ile", "bir", "bu", "için", "gibi", "ama", "daha", "çok", "üzüntü", "kaygı", "anksiyete", "stres"}
    tokens = set(tokenize(normalized))
    if len(tokens & tr_markers) >= 2:
        return "tr"
    return "en"


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]

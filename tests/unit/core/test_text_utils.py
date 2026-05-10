from __future__ import annotations

from server.app.utils.text import fuzzy_token_overlap, infer_language, tokenize


def test_tokenize_preserves_turkish_characters() -> None:
    tokens = tokenize("anksiyete ve uyku")

    assert "anksiyete" in tokens
    assert "uyku" in tokens


def test_fuzzy_token_overlap_handles_common_typos() -> None:
    assert fuzzy_token_overlap(["anxiaty"], ["anxiety"]) == 1


def test_infer_language_detects_turkish_text() -> None:
    assert infer_language("anksiyete ve stres") == "tr"

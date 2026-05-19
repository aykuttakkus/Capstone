from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from server.app.core.config import PROCESSED_CORPUS_PATH, RAW_CORPUS_PATH
from server.app.utils.io import load_json
from server.app.utils.text import infer_language


EVIDENCE_LEVEL_RANK = {
    "low_confidence": 0,
    "educational": 1,
    "clinical_self_help": 2,
    "peer_reviewed": 3,
    "clinical_guideline": 4,
}


@dataclass(slots=True)
class KnowledgeChunk:
    id: str
    title: str
    topic: str
    source: str
    content: str
    keywords: list[str] = field(default_factory=list)
    section: str = ""
    pdf_file: str = ""
    page: int = 0
    source_kind: str = "user_corpus"
    parser_mode: str = "legacy"
    confidence: float = 1.0
    language: str = "en"
    allowed_use: list[str] = field(default_factory=lambda: [
        "psychoeducation",
        "coping_strategy",
        "symptom_exploration",
        "emotional_support",
    ])
    not_allowed: list[str] = field(default_factory=lambda: ["diagnosis", "medication_advice"])
    risk_level: str = "none"
    content_type: str = "psychoeducation"
    evidence_level: str = "educational"
    clinical_scope: str = "psychoeducation_only"
    requires_disclaimer: bool = True
    source_date: str | None = None
    last_reviewed: str | None = None
    review_required: bool = False
    # Spec §32.6 additional metadata fields
    clinical_risk: str = "none"       # none | low | medium | high | crisis
    parent_id: str | None = None      # parent chunk ID for hierarchical retrieval
    organization: str = ""            # authoring organization or publisher
    subtopic: str = "general"         # fine-grained subtopic within topic
    action_type: str = "explanation"  # explanation | exercise | self_help | psychoeducation
    audience: str = "adult"           # adult | youth | professional
    page_range: str = ""              # page range reference (e.g. "2-3")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "KnowledgeChunk":
        return cls(
            id=str(payload.get("id", payload.get("title", "chunk"))),
            title=str(payload.get("title", "Untitled")),
            topic=str(payload.get("topic", "general")),
            source=str(payload.get("source", "Unknown source")),
            content=str(payload.get("content", "")),
            keywords=[str(item) for item in payload.get("keywords", [])],
            section=str(payload.get("section", "")),
            pdf_file=str(payload.get("pdf_file", "")),
            page=int(payload.get("page", 0) or 0),
            source_kind=str(payload.get("source_kind", "user_corpus")),
            parser_mode=str(payload.get("parser_mode", "legacy")),
            confidence=float(payload.get("confidence", 1.0) or 1.0),
            language=str(payload.get("language", infer_language(f"{payload.get('title', '')} {payload.get('content', '')}"))),
            allowed_use=[str(item) for item in payload.get("allowed_use", [
                "psychoeducation",
                "coping_strategy",
                "symptom_exploration",
                "emotional_support",
            ])],
            not_allowed=[str(item) for item in payload.get("not_allowed", ["diagnosis", "medication_advice"])],
            risk_level=str(payload.get("risk_level", "none")),
            content_type=str(payload.get("content_type", "psychoeducation")),
            evidence_level=str(payload.get("evidence_level", "educational")),
            clinical_scope=str(payload.get("clinical_scope", "psychoeducation_only")),
            requires_disclaimer=bool(payload.get("requires_disclaimer", True)),
            source_date=str(payload["source_date"]) if payload.get("source_date") else None,
            last_reviewed=str(payload["last_reviewed"]) if payload.get("last_reviewed") else None,
            review_required=bool(payload.get("review_required", False)),
            clinical_risk=str(payload.get("clinical_risk", "none")),
            parent_id=str(payload["parent_id"]) if payload.get("parent_id") else None,
            organization=str(payload.get("organization", "")),
            subtopic=str(payload.get("subtopic", "general")),
            action_type=str(payload.get("action_type", "explanation")),
            audience=str(payload.get("audience", "adult")),
            page_range=str(payload.get("page_range", "")),
        )


def default_corpus() -> list[KnowledgeChunk]:
    return [
        KnowledgeChunk(id="stress-001", title="What stress is", topic="stress_anxiety", source="Sample corpus", content="Stress is a natural response to pressure or change. It can affect sleep, focus, and energy when it lasts for a long time.", keywords=["stress", "pressure", "sleep", "focus"], language="en"),
        KnowledgeChunk(id="anxiety-001", title="General anxiety signs", topic="stress_anxiety", source="Sample corpus", content="Anxiety can show up as worry, restlessness, tension, and trouble concentrating. It is useful to distinguish general information from diagnosis.", keywords=["anxiety", "worry", "restlessness", "tension"], language="en"),
        KnowledgeChunk(id="mood-001", title="Low mood overview", topic="low_mood", source="Sample corpus", content="Low mood may involve reduced interest, fatigue, and feeling emotionally heavy. Persistent symptoms are worth discussing with a professional.", keywords=["mood", "sad", "fatigue", "interest"], language="en"),
        KnowledgeChunk(id="sleep-001", title="Sleep and mental health", topic="burnout_sleep", source="Sample corpus", content="Sleep and mental health influence each other. Poor sleep can make stress harder to manage, while stress can disrupt sleep quality.", keywords=["sleep", "burnout", "fatigue", "mental health"], language="en"),
        KnowledgeChunk(id="help-001", title="When to seek support", topic="help_seeking", source="Sample corpus", content="Seeking support can be helpful when emotional difficulty lasts, grows stronger, or affects daily life. Trusted professionals can offer guidance.", keywords=["help", "support", "professional", "guidance"], language="en"),
    ]


@dataclass(slots=True)
class KnowledgeBase:
    chunks: list[KnowledgeChunk]

    @classmethod
    def load(cls, path: Path | None = None) -> "KnowledgeBase":
        if path is not None:
            raw = load_json(path, default=[])
        else:
            raw = load_json(RAW_CORPUS_PATH, default=[])
            processed = load_json(PROCESSED_CORPUS_PATH, default=[])
            if processed:
                raw = [*raw, *processed]

        if not raw:
            return cls(chunks=default_corpus())

        chunks = [KnowledgeChunk.from_dict(item) for item in raw]
        return cls(chunks=chunks)

    def signature(self) -> str:
        payload = [
            {
                "id": chunk.id,
                "title": chunk.title,
                "topic": chunk.topic,
                "source": chunk.source,
                "content": chunk.content,
                "keywords": chunk.keywords,
                "section": chunk.section,
                "pdf_file": chunk.pdf_file,
                "page": chunk.page,
                "source_kind": chunk.source_kind,
                "parser_mode": chunk.parser_mode,
                "confidence": chunk.confidence,
                "language": chunk.language,
                "allowed_use": chunk.allowed_use,
                "not_allowed": chunk.not_allowed,
                "risk_level": chunk.risk_level,
                "content_type": chunk.content_type,
                "evidence_level": chunk.evidence_level,
                "clinical_scope": chunk.clinical_scope,
                "requires_disclaimer": chunk.requires_disclaimer,
                "source_date": chunk.source_date,
                "last_reviewed": chunk.last_reviewed,
                "review_required": chunk.review_required,
            }
            for chunk in self.chunks
        ]
        digest = hashlib.sha256()
        digest.update(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        return digest.hexdigest()[:16]


def evidence_level_at_least(actual: str, minimum: str | None) -> bool:
    if not minimum:
        return True
    return EVIDENCE_LEVEL_RANK.get(actual, 0) >= EVIDENCE_LEVEL_RANK.get(minimum, 0)


def metadata_matches_filters(
    chunk: KnowledgeChunk,
    *,
    intent: str | None = None,
    risk_level: str | None = None,
    allowed_use: list[str] | None = None,
    exclude_not_allowed: list[str] | None = None,
    min_evidence_level: str | None = None,
    freshness_required: bool = False,
    clinical_scope: str | None = None,
) -> bool:
    uses = allowed_use or ([intent] if intent else [])
    if uses and not any(use in chunk.allowed_use for use in uses):
        return False

    exclusions = exclude_not_allowed or []
    if exclusions and any(item in chunk.not_allowed for item in exclusions):
        return False

    if not evidence_level_at_least(chunk.evidence_level, min_evidence_level):
        return False

    if clinical_scope and chunk.clinical_scope != clinical_scope:
        return False

    if freshness_required and chunk.review_required and not chunk.last_reviewed:
        return False

    if risk_level in {"none", "low", None, ""} and chunk.risk_level in {"high", "crisis"}:
        return False

    return True

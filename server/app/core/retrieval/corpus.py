from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from server.app.core.config import PROCESSED_CORPUS_PATH, RAW_CORPUS_PATH
from server.app.utils.io import load_json
from server.app.utils.text import infer_language


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
    page_start: int = 0
    page_end: int = 0
    source_kind: str = "user_corpus"
    parser_mode: str = "legacy"
    confidence: float = 1.0
    language: str = "en"
    word_count: int = 0

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "KnowledgeChunk":
        page = int(payload.get("page", payload.get("page_start", 0)) or 0)
        page_start = int(payload.get("page_start", page) or page)
        page_end = int(payload.get("page_end", page_start or page) or (page_start or page))
        content = str(payload.get("content", ""))
        return cls(
            id=str(payload.get("id", payload.get("title", "chunk"))),
            title=str(payload.get("title", "Untitled")),
            topic=str(payload.get("topic", "general")),
            source=str(payload.get("source", "Unknown source")),
            content=content,
            keywords=[str(item) for item in payload.get("keywords", [])],
            section=str(payload.get("section", "")),
            pdf_file=str(payload.get("pdf_file", "")),
            page=page,
            page_start=page_start,
            page_end=page_end,
            source_kind=str(payload.get("source_kind", "user_corpus")),
            parser_mode=str(payload.get("parser_mode", "legacy")),
            confidence=float(payload.get("confidence", 1.0) or 1.0),
            language=str(payload.get("language", infer_language(f"{payload.get('title', '')} {payload.get('content', '')}"))),
            word_count=int(payload.get("word_count", len(content.split())) or len(content.split())),
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
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "source_kind": chunk.source_kind,
                "parser_mode": chunk.parser_mode,
                "confidence": chunk.confidence,
                "language": chunk.language,
                "word_count": chunk.word_count,
            }
            for chunk in self.chunks
        ]
        digest = hashlib.sha256()
        digest.update(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        return digest.hexdigest()[:16]

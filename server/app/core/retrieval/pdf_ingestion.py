from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from server.app.core.retrieval.ingestion.classifier import LlmMetadataClassifier
from server.app.core.retrieval.ingestion.chunker import SemanticChunker
from server.app.core.retrieval.ingestion.parser import VisionPdfParser
from server.app.services.flows.topics import TOPIC_KEYWORDS
from server.app.utils.text import contains_any, infer_language, normalize_text, tokenize


@dataclass(slots=True)
class PDFDocumentMeta:
    filename: str
    title: str
    topic: str
    include_in_index: bool
    source_kind: str


@dataclass(slots=True)
class PDFPageChunk:
    id: str
    title: str
    topic: str
    source: str
    content: str
    keywords: list[str]
    pdf_file: str
    page: int
    source_kind: str
    section: str = ""
    parser_mode: str = "legacy"
    confidence: float = 1.0
    language: str = "en"


EXCLUDED_FILENAME_PATTERNS: tuple[str, ...] = ("preventing-suicide", "problem-management-plus")

TOPIC_RULES: tuple[tuple[str, str], ...] = (
    ("perinatal-depression", "low_mood"),
    ("depression", "low_mood"),
    ("sleep", "burnout_sleep"),
    ("burnout", "burnout_sleep"),
    ("fatigue", "burnout_sleep"),
    ("stress", "stress_anxiety"),
    ("anxiety", "stress_anxiety"),
    ("social", "social_pressure"),
    ("relationship", "social_pressure"),
    ("family", "social_pressure"),
    ("pressure", "social_pressure"),
    ("obsessive-compulsive-disorder", "ocd"),
    ("psychosis", "psychosis"),
    ("schizophrenia", "psychosis"),
    ("post-traumatic-stress-disorder", "ptsd"),
    ("traumatic-events", "ptsd"),
    ("bipolar", "bipolar"),
    ("eating-disorders", "eating_disorders"),
    ("talking-with-a-health-care-provider", "help_seeking"),
    ("clinical-research-trials", "help_seeking"),
    ("genes", "psychoeducation"),
    ("adolescent-skills", "help_seeking"),
)

TOPIC_KEYWORD_OVERRIDES: dict[str, list[str]] = {
    "low_mood": ["depression", "mood", "sad", "hopeless", "low mood"],
    "stress_anxiety": ["stress", "anxiety", "worry", "panic", "tension"],
    "burnout_sleep": ["burnout", "sleep", "fatigue", "tired", "restless", "insomnia"],
    "social_pressure": ["relationship", "social", "family", "pressure"],
    "ocd": ["obsession", "compulsion", "ocd"],
    "psychosis": ["psychosis", "hallucination", "delusion", "schizophrenia"],
    "ptsd": ["trauma", "ptsd", "post-traumatic", "flashback"],
    "bipolar": ["bipolar", "manic", "hypomanic"],
    "eating_disorders": ["eating disorder", "anorexia", "bulimia", "arfid", "binge"],
    "help_seeking": ["help", "provider", "treatment", "clinical trial"],
    "psychoeducation": ["genes", "mental health"],
}

CURRENT_TOPICS = set(TOPIC_KEYWORD_OVERRIDES) | {"general"}
TOPIC_PRIORITY: tuple[str, ...] = ("burnout_sleep", "low_mood", "stress_anxiety", "social_pressure", "help_seeking")


def slugify(value: str) -> str:
    value = normalize_text(value)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def humanize_filename(filename: str) -> str:
    base = Path(filename).stem
    base = base.replace("_", " ").replace("-", " ")
    base = re.sub(r"\s+\d+$", "", base)
    base = re.sub(r"\s+", " ", base).strip()
    return base.title() if base else "Untitled source"


def infer_topic_from_filename(filename: str) -> str:
    normalized = normalize_text(filename)
    for pattern, topic in TOPIC_RULES:
        if pattern in normalized:
            return topic
    return "psychoeducation"


def is_indexable(filename: str) -> bool:
    normalized = normalize_text(filename)
    return not any(pattern in normalized for pattern in EXCLUDED_FILENAME_PATTERNS)


def source_kind_for(filename: str) -> str:
    normalized = normalize_text(filename)
    if "preventing-suicide" in normalized:
        return "safety_reference"
    if "problem-management-plus" in normalized:
        return "intervention_manual"
    return "user_corpus"


def _detect_topic_from_text(text: str) -> str | None:
    normalized = normalize_text(text)
    for topic in TOPIC_PRIORITY:
        keywords = TOPIC_KEYWORDS.get(topic, TOPIC_KEYWORD_OVERRIDES.get(topic, []))
        if contains_any(normalized, keywords):
            return topic
    return None


def _refine_topic(base_topic: str, title: str, content: str) -> str:
    if base_topic not in {"general", "psychoeducation"}:
        return base_topic
    detected = _detect_topic_from_text(f"{title} {content}")
    return detected or base_topic


def _seed_keywords(topic: str, title: str, extra_keywords: list[str] | None = None) -> list[str]:
    seeds = set(keyword_seed(topic, title))
    if extra_keywords:
        seeds.update(normalize_text(str(item)) for item in extra_keywords if str(item).strip())
    return sorted(seeds)


def infer_meta(pdf_path: Path) -> PDFDocumentMeta:
    filename = pdf_path.name
    return PDFDocumentMeta(filename=filename, title=humanize_filename(filename), topic=infer_topic_from_filename(filename), include_in_index=is_indexable(filename), source_kind=source_kind_for(filename))


def extract_pdf_pages(pdf_path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(pdf_path))
    pages: list[tuple[int, str]] = []

    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            pages.append((index, text))

    return pages


def keyword_seed(topic: str, title: str) -> list[str]:
    seeds = set(tokenize(title))
    seeds.add(topic)
    for keyword in TOPIC_KEYWORD_OVERRIDES.get(topic, []):
        seeds.update(tokenize(keyword))
    return sorted(seeds)


def _build_legacy_chunks_from_pdf(pdf_path: Path) -> list[PDFPageChunk]:
    meta = infer_meta(pdf_path)
    chunks: list[PDFPageChunk] = []
    for page_number, text in extract_pdf_pages(pdf_path):
        topic = _refine_topic(meta.topic, meta.title, text)
        chunks.append(
            PDFPageChunk(
                id=f"{slugify(pdf_path.stem)}-p{page_number}",
                title=f"{meta.title} - Page {page_number}",
                topic=topic,
                source=f"{meta.title} ({meta.filename}) page {page_number}",
                content=text,
                keywords=keyword_seed(topic, meta.title),
                pdf_file=meta.filename,
                page=page_number,
                source_kind=meta.source_kind,
                section=f"Page {page_number}",
                parser_mode="legacy",
                confidence=0.85 if topic != meta.topic else 1.0,
                language=infer_language(text),
            )
        )
    return chunks


def _build_layout_aware_chunks(pdf_path: Path, *, enable_llm_classifier: bool = False) -> list[PDFPageChunk]:
    meta = infer_meta(pdf_path)

    try:
        parser = VisionPdfParser()
        chunker = SemanticChunker()
    except Exception:
        return []

    try:
        markdown_text = parser.parse(pdf_path)
        semantic_chunks = chunker.chunk(markdown_text)
    except Exception:
        return []

    classifier = LlmMetadataClassifier() if enable_llm_classifier else None
    chunks: list[PDFPageChunk] = []

    for index, chunk in enumerate(semantic_chunks, start=1):
        title = str(chunk.get("title", "")).strip() or f"{meta.title} - Section {index}"
        content = str(chunk.get("content", "")).strip()
        if len(content) < 60:
            continue

        topic = _refine_topic(meta.topic, title, content)
        confidence = 0.92 if topic != meta.topic else 0.84
        extra_keywords: list[str] = []

        if classifier is not None:
            classified = classifier.classify(content, title)
            candidate_topic = str(classified.get("topic", "general"))
            if candidate_topic in CURRENT_TOPICS and candidate_topic != "general":
                topic = candidate_topic
                confidence = 0.95
            extra_keywords = [str(item) for item in classified.get("keywords", [])][:5]

        section = str(chunk.get("section", title)).strip() or title
        chunks.append(
            PDFPageChunk(
                id=f"{slugify(pdf_path.stem)}-c{index}",
                title=title[:120],
                topic=topic,
                source=f"{meta.title} ({meta.filename}) :: {section}",
                content=content,
                keywords=_seed_keywords(topic, title, extra_keywords),
                pdf_file=meta.filename,
                page=index,
                source_kind=meta.source_kind,
                section=section[:160],
                parser_mode="layout_aware",
                confidence=confidence,
                language=infer_language(f"{title} {content}"),
            )
        )

    return chunks


def build_chunks_from_pdf(
    pdf_path: Path,
    *,
    prefer_layout_aware: bool = True,
    enable_llm_classifier: bool = False,
) -> list[PDFPageChunk]:
    if prefer_layout_aware:
        structured_chunks = _build_layout_aware_chunks(pdf_path, enable_llm_classifier=enable_llm_classifier)
        if structured_chunks:
            return structured_chunks
    return _build_legacy_chunks_from_pdf(pdf_path)


def build_corpus_from_pdf_dir(
    pdf_dir: Path,
    include_non_indexable: bool = False,
    *,
    prefer_layout_aware: bool = True,
    enable_llm_classifier: bool = False,
) -> list[dict[str, object]]:
    corpus: list[dict[str, object]] = []
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        meta = infer_meta(pdf_path)
        if not meta.include_in_index and not include_non_indexable:
            continue
        for chunk in build_chunks_from_pdf(
            pdf_path,
            prefer_layout_aware=prefer_layout_aware,
            enable_llm_classifier=enable_llm_classifier,
        ):
            corpus.append({
                "id": chunk.id,
                "title": chunk.title,
                "topic": chunk.topic,
                "source": chunk.source,
                "content": chunk.content,
                "keywords": chunk.keywords,
                "pdf_file": chunk.pdf_file,
                "page": chunk.page,
                "source_kind": chunk.source_kind,
                "section": chunk.section,
                "parser_mode": chunk.parser_mode,
                "confidence": chunk.confidence,
                "language": chunk.language,
            })
    return corpus


def build_inventory(pdf_dir: Path) -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        meta = infer_meta(pdf_path)
        inventory.append({"filename": meta.filename, "title": meta.title, "topic": meta.topic, "include_in_index": meta.include_in_index, "source_kind": meta.source_kind})
    return inventory

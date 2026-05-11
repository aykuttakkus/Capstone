from __future__ import annotations

import math
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
class PDFExtractedPage:
    page_number: int
    text: str


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
    page_start: int = 0
    page_end: int = 0
    word_count: int = 0


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
REFERENCE_SECTION_HEADINGS: tuple[str, ...] = (
    "references",
    "bibliography",
    "works cited",
    "further reading",
    "literature cited",
    "author contributions",
    "declaration of conflicting interests",
    "source(s) of support",
    "funding",
    "acknowledgments",
    "acknowledgements",
)
PAGE_NUMBER_ONLY_RE = re.compile(r"^(?:page\s+)?(?:\d+|[ivxlcdm]+)(?:\s*(?:/|of)\s*\d+)?$", flags=re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", flags=re.IGNORECASE)
DOI_RE = re.compile(
    r"(?:https?://(?:dx\.)?doi\.org/\S+|doi:\s*\S+|\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b)",
    flags=re.IGNORECASE,
)
REFERENCE_CITATION_RE = re.compile(r"\([A-Z][A-Za-z'`\-]+(?:\s+et al\.)?,\s*\d{4}[a-z]?\)")
YEAR_TOKEN_RE = re.compile(r"\b(?:19|20)\d{2}[a-z]?\b")
SYMBOL_CLUSTER_RE = re.compile(r"(?:[●•▪◦■□▲△▼◆◇○◯]\s*){10,}")
AXIS_LABEL_RE = re.compile(r"(?:[−-]?\d+(?:\.\d+)?\s+){4,}[−-]?\d+(?:\.\d+)?")
FIGURE_TOKEN_RE = re.compile(r"\b(?:figure|fig\.|table|study)\s+\d+\b", flags=re.IGNORECASE)


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


def _normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.replace("\u00a0", " ").strip())


def _normalize_block(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized_lines: list[str] = []
    blank_run = 0
    for raw_line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            blank_run += 1
            if blank_run <= 1:
                normalized_lines.append("")
            continue
        blank_run = 0
        normalized_lines.append(line)
    return "\n".join(normalized_lines).strip()


def _strip_doi_email_noise(text: str) -> str:
    text = EMAIL_RE.sub(" ", text)
    text = DOI_RE.sub(" ", text)
    return _normalize_block(text)


def _looks_like_page_number_line(line: str) -> bool:
    return bool(PAGE_NUMBER_ONLY_RE.fullmatch(_normalize_line(line)))


def _is_reference_heading(line: str) -> bool:
    normalized = _normalize_line(line).lower().lstrip("#").strip().rstrip(":.;")
    return normalized in REFERENCE_SECTION_HEADINGS


def _alpha_text_ratio(text: str) -> float:
    non_space_chars = [char for char in text if not char.isspace()]
    if not non_space_chars:
        return 0.0
    alpha_chars = sum(1 for char in non_space_chars if char.isalpha())
    return alpha_chars / len(non_space_chars)


def _digit_ratio(text: str) -> float:
    non_space_chars = [char for char in text if not char.isspace()]
    if not non_space_chars:
        return 0.0
    digit_chars = sum(1 for char in non_space_chars if char.isdigit())
    return digit_chars / len(non_space_chars)


def _symbol_ratio(text: str) -> float:
    non_space_chars = [char for char in text if not char.isspace()]
    if not non_space_chars:
        return 0.0
    symbol_chars = sum(1 for char in non_space_chars if not char.isalnum())
    return symbol_chars / len(non_space_chars)


def _citation_marker_count(text: str) -> int:
    marker_count = len(REFERENCE_CITATION_RE.findall(text))
    marker_count += text.lower().count("et al.")
    marker_count += text.lower().count("doi:")
    marker_count += len(YEAR_TOKEN_RE.findall(text))
    return marker_count


def _contains_tail_marker(text: str) -> bool:
    normalized = normalize_text(text)
    return any(marker in normalized for marker in REFERENCE_SECTION_HEADINGS)


def _is_reference_dominated_text(text: str) -> bool:
    normalized = normalize_text(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not normalized:
        return False

    citation_markers = _citation_marker_count(text)
    short_reference_lines = sum(
        1
        for line in lines
        if len(line) < 180 and (len(REFERENCE_CITATION_RE.findall(line)) > 0 or len(YEAR_TOKEN_RE.findall(line)) >= 2)
    )
    if _contains_tail_marker(text) and citation_markers >= 2:
        return True
    if short_reference_lines >= 4:
        return True
    return citation_markers >= 18


def _is_low_quality_chunk(
    *,
    title: str,
    content: str,
    section: str,
    page_start: int = 0,
    page_end: int = 0,
    total_pages: int = 0,
) -> bool:
    text = " ".join(part for part in (title, section, content) if part).strip()
    if not text:
        return True

    alpha_ratio = _alpha_text_ratio(content)
    digit_ratio = _digit_ratio(content)
    symbol_ratio = _symbol_ratio(content)
    symbol_clusters = len(SYMBOL_CLUSTER_RE.findall(content))
    has_axis_artifact = bool(AXIS_LABEL_RE.search(content))
    has_figure_marker = bool(FIGURE_TOKEN_RE.search(text))
    leading_excerpt = content[:320]
    leading_axis_artifact = bool(AXIS_LABEL_RE.search(leading_excerpt))
    leading_symbol_artifact = bool(SYMBOL_CLUSTER_RE.search(leading_excerpt))
    citation_markers = _citation_marker_count(content)
    near_tail = bool(total_pages and page_start and page_start >= max(1, math.floor(total_pages * 0.75)))
    reference_dominated = _is_reference_dominated_text(text)

    if alpha_ratio < 0.45:
        return True
    if symbol_clusters >= 1 and (alpha_ratio < 0.7 or symbol_ratio > 0.18):
        return True
    if has_figure_marker and (leading_axis_artifact or leading_symbol_artifact):
        return True
    if has_axis_artifact and has_figure_marker and (alpha_ratio < 0.72 or digit_ratio > 0.12):
        return True
    if symbol_ratio > 0.28 and alpha_ratio < 0.65:
        return True
    if near_tail and _contains_tail_marker(text):
        return True
    if reference_dominated and (near_tail or citation_markers >= 18):
        return True
    return False


def _detect_repeating_edge_lines(raw_pages: list[PDFExtractedPage]) -> set[str]:
    counts: dict[str, int] = {}
    for page in raw_pages:
        normalized_lines = [_normalize_line(line) for line in page.text.splitlines()]
        normalized_lines = [line for line in normalized_lines if line]
        edge_lines = normalized_lines[:2] + normalized_lines[-2:]
        for line in set(edge_lines):
            if len(line) < 3 or len(line) > 120:
                continue
            if _looks_like_page_number_line(line):
                continue
            counts[line] = counts.get(line, 0) + 1

    threshold = max(3, math.ceil(len(raw_pages) * 0.3))
    return {line for line, count in counts.items() if count >= threshold}


def _clean_page_text(raw_text: str, repeated_lines: set[str]) -> str:
    cleaned_lines: list[str] = []
    for raw_line in raw_text.splitlines():
        line = _normalize_line(raw_line)
        if not line or line in repeated_lines or _looks_like_page_number_line(line):
            continue
        line = _strip_doi_email_noise(line)
        line = _normalize_line(line)
        if line:
            cleaned_lines.append(line)
    return _normalize_block("\n".join(cleaned_lines))


def _remove_reference_tail(pages: list[PDFExtractedPage]) -> list[PDFExtractedPage]:
    if len(pages) < 3:
        return pages

    search_start = max(0, int(len(pages) * 0.6))
    for page_index in range(search_start, len(pages)):
        lines = pages[page_index].text.splitlines()
        for line_index, line in enumerate(lines):
            if not _is_reference_heading(line):
                continue
            trimmed_text = _normalize_block("\n".join(lines[:line_index]))
            retained = pages[:page_index]
            if trimmed_text:
                retained.append(PDFExtractedPage(page_number=pages[page_index].page_number, text=trimmed_text))
            return retained
    for page_index in range(search_start, len(pages)):
        if not _is_reference_dominated_text(pages[page_index].text):
            continue
        trailing_pages = pages[page_index:]
        dominated_count = sum(1 for page in trailing_pages if _is_reference_dominated_text(page.text))
        if dominated_count >= max(1, len(trailing_pages) - 1):
            return pages[:page_index]
    return pages


def extract_pdf_page_records(pdf_path: Path) -> list[PDFExtractedPage]:
    reader = PdfReader(str(pdf_path))
    raw_pages: list[PDFExtractedPage] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            raw_pages.append(PDFExtractedPage(page_number=index, text=text))

    repeated_lines = _detect_repeating_edge_lines(raw_pages)
    cleaned_pages = [
        PDFExtractedPage(page_number=page.page_number, text=_clean_page_text(page.text, repeated_lines))
        for page in raw_pages
    ]
    cleaned_pages = [page for page in cleaned_pages if page.text]
    return _remove_reference_tail(cleaned_pages)


def extract_pdf_pages(pdf_path: Path) -> list[tuple[int, str]]:
    return [(page.page_number, page.text) for page in extract_pdf_page_records(pdf_path)]


def keyword_seed(topic: str, title: str) -> list[str]:
    seeds = set(tokenize(title))
    seeds.add(topic)
    for keyword in TOPIC_KEYWORD_OVERRIDES.get(topic, []):
        seeds.update(tokenize(keyword))
    return sorted(seeds)


def _page_payloads(pages: list[PDFExtractedPage]) -> list[dict[str, object]]:
    return [{"page": page.page_number, "text": page.text} for page in pages if page.text]


def _page_label(page_start: int, page_end: int) -> str:
    if page_start and page_end and page_start != page_end:
        return f"Pages {page_start}-{page_end}"
    if page_start:
        return f"Page {page_start}"
    return "General Information"


def _clean_layout_aware_markdown(markdown_text: str) -> str:
    text = _strip_doi_email_noise(markdown_text)
    reference_matches = list(
        re.finditer(
            r"(?im)^(?:#{1,6}\s*)?(references|bibliography|works cited|further reading|literature cited)\s*$",
            text,
        )
    )
    for match in reference_matches:
        if match.start() >= int(len(text) * 0.6):
            text = text[: match.start()]
            break
    return _normalize_block(text)


def _build_legacy_chunks_from_pdf(pdf_path: Path) -> list[PDFPageChunk]:
    meta = infer_meta(pdf_path)
    page_records = extract_pdf_page_records(pdf_path)
    if not page_records:
        return []

    chunker = SemanticChunker()
    raw_chunks = chunker.chunk(None, page_records=_page_payloads(page_records), default_title=meta.title)
    total_pages = max((page.page_number for page in page_records), default=0)
    chunks: list[PDFPageChunk] = []
    for index, chunk in enumerate(raw_chunks, start=1):
        content = str(chunk.get("content", "")).strip()
        if len(content) < 60:
            continue
        page_start = int(chunk.get("page_start", 0) or 0)
        page_end = int(chunk.get("page_end", page_start) or page_start)
        page = page_start or page_end
        page_label = _page_label(page_start, page_end)
        title = str(chunk.get("title", "")).strip() or meta.title
        if page_label not in title:
            title = f"{title} - {page_label}"
        section = str(chunk.get("section", page_label)).strip() or page_label
        if _is_low_quality_chunk(
            title=title,
            content=content,
            section=section,
            page_start=page_start,
            page_end=page_end,
            total_pages=total_pages,
        ):
            continue
        topic = _refine_topic(meta.topic, title, content)
        chunks.append(
            PDFPageChunk(
                id=f"{slugify(pdf_path.stem)}-p{page_start or index}-{page_end or page_start or index}-{index}",
                title=title[:120],
                topic=topic,
                source=f"{meta.title} ({meta.filename}) {page_label.lower()}",
                content=content,
                keywords=_seed_keywords(topic, title),
                pdf_file=meta.filename,
                page=page,
                source_kind=meta.source_kind,
                section=section[:160],
                parser_mode="legacy",
                confidence=0.85 if topic != meta.topic else 1.0,
                language=infer_language(f"{title} {content}"),
                page_start=page_start or page,
                page_end=page_end or page,
                word_count=int(chunk.get("word_count", len(content.split())) or len(content.split())),
            )
        )
    return chunks


def _build_layout_aware_chunks(pdf_path: Path, *, enable_llm_classifier: bool = False) -> list[PDFPageChunk]:
    meta = infer_meta(pdf_path)
    page_records = extract_pdf_page_records(pdf_path)
    total_pages = max((page.page_number for page in page_records), default=0)

    try:
        parser = VisionPdfParser()
        chunker = SemanticChunker()
    except Exception:
        return []

    try:
        markdown_text = parser.parse(pdf_path)
        markdown_text = _clean_layout_aware_markdown(markdown_text)
        semantic_chunks = chunker.chunk(markdown_text, page_records=_page_payloads(page_records), default_title=meta.title)
    except Exception:
        return []

    classifier = LlmMetadataClassifier() if enable_llm_classifier else None
    chunks: list[PDFPageChunk] = []

    for index, chunk in enumerate(semantic_chunks, start=1):
        title = str(chunk.get("title", "")).strip() or f"{meta.title} - Section {index}"
        content = str(chunk.get("content", "")).strip()
        if len(content) < 60:
            continue
        page_start = int(chunk.get("page_start", 0) or 0)
        page_end = int(chunk.get("page_end", page_start) or page_start)
        page = page_start or page_end

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
        if _is_low_quality_chunk(
            title=title,
            content=content,
            section=section,
            page_start=page_start,
            page_end=page_end,
            total_pages=total_pages,
        ):
            continue
        chunks.append(
            PDFPageChunk(
                id=f"{slugify(pdf_path.stem)}-c{index}",
                title=title[:120],
                topic=topic,
                source=f"{meta.title} ({meta.filename}) :: {section}",
                content=content,
                keywords=_seed_keywords(topic, title, extra_keywords),
                pdf_file=meta.filename,
                page=page,
                source_kind=meta.source_kind,
                section=section[:160],
                parser_mode="layout_aware",
                confidence=confidence,
                language=infer_language(f"{title} {content}"),
                page_start=page_start or page,
                page_end=page_end or page,
                word_count=int(chunk.get("word_count", len(content.split())) or len(content.split())),
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
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "source_kind": chunk.source_kind,
                "section": chunk.section,
                "parser_mode": chunk.parser_mode,
                "confidence": chunk.confidence,
                "language": chunk.language,
                "word_count": chunk.word_count,
            })
    return corpus


def build_inventory(pdf_dir: Path) -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        meta = infer_meta(pdf_path)
        inventory.append({"filename": meta.filename, "title": meta.title, "topic": meta.topic, "include_in_index": meta.include_in_index, "source_kind": meta.source_kind})
    return inventory

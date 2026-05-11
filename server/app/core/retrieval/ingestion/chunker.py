from __future__ import annotations

import re


class SemanticChunker:
    """
    Splits content semantically when headings are available, then enforces a
    stable word-window size so retrieval quality does not depend on PDF page
    boundaries.
    """

    MIN_WORDS = 500
    TARGET_WORDS = 650
    MAX_WORDS = 800
    OVERLAP_WORDS = 100

    def __init__(self) -> None:
        self.splitter = None
        try:
            from langchain_text_splitters import MarkdownHeaderTextSplitter

            headers_to_split_on = [
                ("#", "Header_1"),
                ("##", "Header_2"),
                ("###", "Header_3"),
            ]
            self.splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)
        except ImportError:
            self.splitter = None

    def chunk(
        self,
        markdown_text: str | None,
        *,
        page_records: list[dict[str, object]] | None = None,
        default_title: str = "General Information",
    ) -> list[dict[str, object]]:
        normalized_pages = self._normalize_page_records(page_records or [])
        semantic_sections = self._semantic_sections(markdown_text)
        if semantic_sections:
            semantic_chunks: list[dict[str, object]] = []
            for section in semantic_sections:
                title = str(section.get("title", "")).strip() or default_title
                content = str(section.get("content", "")).strip()
                section_title = str(section.get("section", title)).strip() or title
                if len(content) < 60:
                    continue
                semantic_chunks.extend(self._finalize_section(title, section_title, content, normalized_pages))
            if semantic_chunks:
                return semantic_chunks

        fallback_text = markdown_text or "\n\n".join(str(page.get("text", "")) for page in normalized_pages)
        return self._fixed_size_chunks(normalized_pages, fallback_text, default_title)

    def _semantic_sections(self, markdown_text: str | None) -> list[dict[str, str]]:
        if not markdown_text or self.splitter is None:
            return []
        try:
            splits = self.splitter.split_text(markdown_text)
        except Exception:
            return []

        sections: list[dict[str, str]] = []
        for doc in splits:
            headers = [str(value).strip() for key, value in doc.metadata.items() if key.startswith("Header_") and str(value).strip()]
            title = " - ".join(headers) if headers else "General Information"
            content = doc.page_content.strip()
            if len(content) > 60:
                sections.append(
                    {
                        "title": title[:120],
                        "content": content,
                        "section": title[:160],
                    }
                )
        return sections

    def _finalize_section(
        self,
        title: str,
        section_title: str,
        content: str,
        page_records: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        words = self._words(content)
        if not words:
            return []

        chunks: list[dict[str, object]] = []
        ranges = self._window_ranges(len(words))
        for index, (start, end) in enumerate(ranges, start=1):
            content_words = words[start:end]
            window_content = " ".join(content_words).strip()
            if len(window_content) < 60:
                continue
            page_start, page_end = self._resolve_page_range(window_content, page_records)
            window_title = title if len(ranges) == 1 else f"{title} (Part {index})"
            chunks.append(
                {
                    "title": window_title[:120],
                    "content": window_content,
                    "section": section_title[:160],
                    "chunk_index": str(index),
                    "page_start": page_start,
                    "page_end": page_end,
                    "word_count": len(content_words),
                }
            )
        return chunks

    def _fixed_size_chunks(
        self,
        page_records: list[dict[str, object]],
        fallback_text: str,
        default_title: str,
    ) -> list[dict[str, object]]:
        if page_records:
            words, page_map = self._word_stream(page_records)
            chunks: list[dict[str, object]] = []
            for index, (start, end) in enumerate(self._window_ranges(len(words)), start=1):
                content_words = words[start:end]
                content = " ".join(content_words).strip()
                if len(content) < 60:
                    continue
                page_start = page_map[start] if start < len(page_map) else 0
                page_end = page_map[end - 1] if end > start and (end - 1) < len(page_map) else page_start
                chunks.append(
                    {
                        "title": default_title[:120],
                        "content": content,
                        "section": self._page_label(page_start, page_end),
                        "chunk_index": str(index),
                        "page_start": page_start,
                        "page_end": page_end,
                        "word_count": len(content_words),
                    }
                )
            if chunks:
                return chunks

        words = self._words(fallback_text)
        chunks: list[dict[str, object]] = []
        for index, (start, end) in enumerate(self._window_ranges(len(words)), start=1):
            content_words = words[start:end]
            content = " ".join(content_words).strip()
            if len(content) < 60:
                continue
            chunks.append(
                {
                    "title": default_title[:120],
                    "content": content,
                    "section": default_title[:160],
                    "chunk_index": str(index),
                    "page_start": 0,
                    "page_end": 0,
                    "word_count": len(content_words),
                }
            )
        return chunks

    def _normalize_page_records(self, page_records: list[dict[str, object]]) -> list[dict[str, object]]:
        normalized: list[dict[str, object]] = []
        for record in page_records:
            text = str(record.get("text", "")).strip()
            if not text:
                continue
            normalized.append(
                {
                    "page": int(record.get("page", 0) or 0),
                    "text": text,
                }
            )
        return normalized

    def _word_stream(self, page_records: list[dict[str, object]]) -> tuple[list[str], list[int]]:
        words: list[str] = []
        page_map: list[int] = []
        for record in page_records:
            page = int(record.get("page", 0) or 0)
            page_words = self._words(str(record.get("text", "")))
            words.extend(page_words)
            page_map.extend([page] * len(page_words))
        return words, page_map

    def _window_ranges(self, total_words: int) -> list[tuple[int, int]]:
        if total_words <= 0:
            return []
        if total_words <= self.MAX_WORDS:
            return [(0, total_words)]

        ranges: list[tuple[int, int]] = []
        start = 0
        while start < total_words:
            remaining = total_words - start
            if remaining <= self.MAX_WORDS:
                ranges.append((start, total_words))
                break

            end = min(total_words, start + self.TARGET_WORDS)
            ranges.append((start, end))
            start = max(end - self.OVERLAP_WORDS, start + 1)
        return ranges

    def _resolve_page_range(
        self,
        content: str,
        page_records: list[dict[str, object]],
    ) -> tuple[int, int]:
        if not page_records:
            return (0, 0)

        content_words = self._normalized_words(content)
        if not content_words:
            return (0, 0)

        normalized_pages = [
            (int(record.get("page", 0) or 0), set(self._normalized_words(str(record.get("text", "")))))
            for record in page_records
            if str(record.get("text", "")).strip()
        ]
        if not normalized_pages:
            return (0, 0)

        first_excerpt = content_words[:40]
        last_excerpt = content_words[-40:]
        start_page = self._best_page_for_excerpt(first_excerpt, normalized_pages)
        end_page = self._best_page_for_excerpt(last_excerpt, normalized_pages)

        if start_page == 0 and end_page == 0:
            return (0, 0)
        if start_page == 0:
            start_page = end_page
        if end_page == 0:
            end_page = start_page
        return (min(start_page, end_page), max(start_page, end_page))

    @staticmethod
    def _best_page_for_excerpt(excerpt_words: list[str], normalized_pages: list[tuple[int, set[str]]]) -> int:
        if not excerpt_words:
            return 0
        excerpt_set = set(excerpt_words)
        best_page = 0
        best_score = 0
        for page_number, page_tokens in normalized_pages:
            score = len(excerpt_set & page_tokens)
            if score > best_score:
                best_page = page_number
                best_score = score
        return best_page if best_score >= 2 else 0

    @staticmethod
    def _words(text: str) -> list[str]:
        return re.findall(r"\S+", text.strip())

    @staticmethod
    def _normalized_words(text: str) -> list[str]:
        return re.findall(r"[^\W_]+", text.lower(), flags=re.UNICODE)

    @staticmethod
    def _page_label(page_start: int, page_end: int) -> str:
        if page_start and page_end and page_start != page_end:
            return f"Pages {page_start}-{page_end}"
        if page_start:
            return f"Page {page_start}"
        return "General Information"

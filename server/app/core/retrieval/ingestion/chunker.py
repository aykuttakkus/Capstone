from __future__ import annotations


class SemanticChunker:
    """
    Splits Markdown text semantically based on Markdown headers
    (H1, H2, H3), preserving context and title.
    """

    def __init__(self) -> None:
        try:
            from langchain_text_splitters import MarkdownHeaderTextSplitter
        except ImportError as e:
            raise RuntimeError("langchain-text-splitters not installed.") from e

        headers_to_split_on = [
            ("#", "Header_1"),
            ("##", "Header_2"),
            ("###", "Header_3"),
        ]
        self.splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)

    def chunk(self, markdown_text: str) -> list[dict[str, str]]:
        splits = self.splitter.split_text(markdown_text)
        chunks = []
        for index, doc in enumerate(splits, start=1):
            headers = [v for k, v in doc.metadata.items() if k.startswith("Header_")]
            title = " - ".join(headers) if headers else "General Information"
            content = doc.page_content.strip()

            if len(content) > 60:
                chunks.append({
                    "title": title[:80],
                    "content": content,
                    "section": title[:120],
                    "chunk_index": str(index),
                })
        return chunks

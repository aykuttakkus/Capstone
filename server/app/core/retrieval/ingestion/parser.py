from __future__ import annotations

from pathlib import Path


class VisionPdfParser:
    """
    Parses a PDF using IBM Docling's Vision-to-Markdown capabilities.
    This preserves document structure, tables, and multi-column formatting,
    outputting rich and clean Markdown.
    """

    def __init__(self) -> None:
        try:
            from docling.document_converter import DocumentConverter
            self.converter = DocumentConverter()
        except ImportError as e:
            raise RuntimeError("docling is not installed. Run 'pip install docling'") from e

    def parse(self, pdf_path: str | Path) -> str:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        result = self.converter.convert(str(pdf_path))
        md_text = result.document.export_to_markdown()
        return md_text

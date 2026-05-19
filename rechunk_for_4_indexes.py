#!/usr/bin/env python3
"""Re-chunk all 41 approved PDFs and build 4-index FAISS system."""

import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from PyPDF2 import PdfReader

# Import our core modules
sys.path.insert(0, str(Path(__file__).parent))

from server.app.core.retrieval.corpus import KnowledgeChunk


@dataclass
class ChunkingConfig:
    chunk_size: int = 800
    chunk_overlap: int = 200
    min_chunk_size: int = 200


def extract_pdf_text(pdf_path: str) -> str:
    """Extract all text from a PDF."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting {pdf_path}: {e}", file=sys.stderr)
        return ""


def chunk_text(text: str, config: ChunkingConfig) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    sentences = re.split(r'(?<=[.!?])\s+', text)

    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= config.chunk_size:
            current_chunk += " " + sentence
        else:
            if len(current_chunk.strip()) >= config.min_chunk_size:
                chunks.append(current_chunk.strip())
            # Start new chunk with overlap
            current_chunk = current_chunk[-config.chunk_overlap:] + " " + sentence

    if len(current_chunk.strip()) >= config.min_chunk_size:
        chunks.append(current_chunk.strip())

    return chunks


def create_chunk_metadata(
    filename: str,
    chunk_text: str,
    chunk_index: int,
    source_info: dict,
    allowed_indexes: list[str],
) -> KnowledgeChunk:
    """Create a KnowledgeChunk with full metadata."""

    # Determine clinical_risk based on source
    clinical_risk = source_info.get("clinical_risk", "low")

    # Extract primary topic from allowed_indexes
    action_type = "explanation"
    if "safety_crisis_index" in allowed_indexes:
        action_type = "self_help"
        clinical_risk = "high"
    elif "coping_skills_index" in allowed_indexes:
        action_type = "exercise"
    else:
        action_type = "explanation"

    # Detect confidence level (rough heuristic)
    confidence = 0.7
    if source_info.get("evidence_level") == "clinical_self_help":
        confidence = 0.85
    elif source_info.get("evidence_level") == "educational":
        confidence = 0.65

    # Determine language
    language = "en"
    if "TR" in filename or "turkpsikoloji" in filename.lower() or "resiliencepsikolojik" in filename.lower():
        language = "tr"

    # Create chunk with correct field names from KnowledgeChunk dataclass
    chunk = KnowledgeChunk(
        id=f"{source_info.get('source_id', 'unknown')}_{chunk_index:04d}",
        title=f"Chunk {chunk_index} - {source_info.get('title', filename)[:40]}",
        topic=source_info.get("topic", "general"),
        source=source_info.get("organization", "Unknown"),
        content=chunk_text,
        keywords=[],
        section=source_info.get("title", filename),
        pdf_file=filename,
        page=0,
        source_kind="user_corpus",
        parser_mode="pdf",
        confidence=confidence,
        language=language,
        allowed_use=source_info.get("allowed_use", ["psychoeducation"]),
        not_allowed=source_info.get("not_allowed", []),
        risk_level=clinical_risk,
        content_type="psychoeducation",
        evidence_level=source_info.get("evidence_level", "educational"),
        clinical_scope="psychoeducation_only" if clinical_risk == "low" else "crisis_aware",
        requires_disclaimer=True,
        source_date=str(source_info.get("year", 2024)),
        last_reviewed=None,
        review_required=False,
        clinical_risk=clinical_risk,
        parent_id=filename,
        organization=source_info.get("organization", "Unknown"),
        subtopic="general",
        action_type=action_type,
        audience="adult",
        page_range="",
    )
    return chunk


def rechunk_all_pdfs():
    """Re-chunk all 41 approved PDFs."""
    pdf_dir = Path("/Users/aykutakkus/Desktop/Projects/Capstone/data/raw")
    registry_path = Path("/Users/aykutakkus/Desktop/Projects/Capstone/data/source_registry.json")
    output_path = Path("/Users/aykutakkus/Desktop/Projects/Capstone/data/knowledge_chunks.jsonl")

    # Load registry
    with open(registry_path) as f:
        registry = json.load(f)

    source_map = {s["filename"]: s for s in registry["sources"]}
    config = ChunkingConfig()

    total_chunks = 0
    total_pdfs = 0

    print("Starting re-chunking of 41 PDFs...")
    print(f"Output: {output_path}\n")

    # Process each PDF
    with open(output_path, "w") as out_file:
        for i, (filename, source_info) in enumerate(source_map.items(), 1):
            pdf_path = pdf_dir / filename
            if not pdf_path.exists():
                print(f"  [{i:2d}/41] ⚠️  {filename[:50]} (NOT FOUND)")
                continue

            print(f"  [{i:2d}/41] {filename[:50]}", end=" ... ", flush=True)

            # Extract text
            text = extract_pdf_text(str(pdf_path))
            if not text or len(text) < 100:
                print("(empty or too small)")
                continue

            # Chunk text
            chunks = chunk_text(text, config)
            print(f"{len(chunks)} chunks")

            # Create metadata for each chunk
            allowed_indexes = source_info.get("allowed_indexes", ["psychoeducation_index"])
            for chunk_idx, chunk_content in enumerate(chunks):
                chunk = create_chunk_metadata(
                    filename,
                    chunk_content,
                    chunk_idx,
                    source_info,
                    allowed_indexes,
                )
                # Write as JSONL
                out_file.write(json.dumps(asdict(chunk)) + "\n")
                total_chunks += 1

            total_pdfs += 1

    print(f"\n{'='*60}")
    print(f"Completed: {total_pdfs} PDFs → {total_chunks} chunks")
    print(f"Average: {total_chunks // max(1, total_pdfs):.1f} chunks per PDF")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    rechunk_all_pdfs()

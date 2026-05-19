#!/usr/bin/env python3
"""Enhance PDF audit by reading metadata and first pages."""

import re
from pathlib import Path
from openpyxl import load_workbook
from PyPDF2 import PdfReader

def extract_pdf_text(pdf_path: str, max_chars: int = 2000) -> str:
    """Extract text from first page of PDF."""
    try:
        reader = PdfReader(pdf_path)
        if len(reader.pages) > 0:
            text = reader.pages[0].extract_text()
            return text[:max_chars] if text else ""
        return ""
    except Exception:
        return ""


def analyze_pdf_content(text: str) -> dict:
    """Analyze PDF text for better categorization."""
    text_lower = text.lower()

    # Detect source organization
    org = None
    if "world health organization" in text_lower or "who" in text_lower:
        org = "WHO"
    elif "nhs" in text_lower:
        org = "NHS"
    elif "mental health foundation" in text_lower:
        org = "MHF"
    elif "samhsa" in text_lower:
        org = "SAMHSA"
    elif "apa" in text_lower:
        org = "APA"
    elif "university" in text_lower:
        org = "Research"

    # Detect publication type
    pub_type = None
    if any(p in text_lower for p in ["abstract", "introduction", "methods", "results", "discussion", "journal"]):
        pub_type = "Research"
    elif any(p in text_lower for p in ["workbook", "exercise", "activity", "worksheet"]):
        pub_type = "Clinical"
    elif any(p in text_lower for p in ["guide", "manual", "how to", "tips", "step"]):
        pub_type = "SelfHelp"

    # Detect evidence level
    evidence = None
    if "peer-reviewed" in text_lower or "research" in text_lower or "clinical trial" in text_lower:
        evidence = "clinical_self_help"
    elif "guideline" in text_lower or "recommendation" in text_lower:
        evidence = "clinical_self_help"

    return {
        "organization": org,
        "publication_type": pub_type,
        "evidence_level": evidence,
    }


def enhance_audit_with_content():
    """Read PDFs and enhance audit categorization."""
    pdf_dir = Path("/Users/aykutakkus/Desktop/Projects/Capstone/data/raw")
    audit_path = Path("/Users/aykutakkus/Desktop/Projects/Capstone/data/pdf_audit.xlsx")

    wb = load_workbook(audit_path)
    ws = wb.active

    # Process each PDF
    updated = 0
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, max_row=ws.max_row), start=2):
        filename = row[0].value
        if not filename or not isinstance(filename, str):
            continue

        pdf_path = pdf_dir / filename
        if not pdf_path.exists():
            continue

        # Read PDF text
        text = extract_pdf_text(str(pdf_path))
        if not text:
            continue

        analysis = analyze_pdf_content(text)

        # Update source_type if detected
        if analysis["publication_type"] and row[1].value == "Unknown":
            row[1].value = analysis["publication_type"]
            updated += 1

        # Update quality based on organization
        if analysis["organization"] in ("WHO", "NHS", "SAMHSA"):
            if row[4].value != "HIGH":
                row[4].value = "HIGH"
                row[5].value = "KEEP"
                updated += 1
        elif analysis["organization"] in ("APA", "Research"):
            if row[4].value == "LOW":
                row[4].value = "MEDIUM"
                row[5].value = "KEEP"
                updated += 1

        if row_idx % 20 == 0:
            print(f"Processed {row_idx-1} PDFs...")

    print(f"Updated {updated} rows")
    wb.save(audit_path)
    print(f"Saved: {audit_path}")


if __name__ == "__main__":
    enhance_audit_with_content()

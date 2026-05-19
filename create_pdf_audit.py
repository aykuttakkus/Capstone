#!/usr/bin/env python3
"""Create PDF audit spreadsheet with all 127 PDFs categorized."""

from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import re

# Define categorization patterns
OFFICIAL_PATTERNS = [
    r"9789240003910",  # WHO ISBN
    r"23-MH-8110",  # WHO product code
    r"FS_Grief",  # WHO factsheet
    r"MHF-UK",  # Mental Health Foundation UK
    r"surgeon-general",  # US Surgeon General
]

TURKISH_PATTERNS = [
    r"resiliencepsikolojik",
    r"turkpsikoloji",
    r"üProblem",
    r"schoka",  # Turkish source
]

CLINICAL_MANUAL_PATTERNS = [
    r"DISTRESS TOLERANCE",
    r"EMOTION REGULATION",
    r"rtp_unit",
    r"Trauma-Informed",
    r"Problem-Management-Plus",
    r"Early-Adolescent-Skills",
]

SELF_HELP_PATTERNS = [
    r"Breakup",
    r"Shortcuts-to-Social",
    r"Dealing.*Distress",
    r"Finding-the-Calm",
    r"stand-up-to-stress",
    r"How-to-stop",
    r"Cycle-of-Anxiety",
]

RESEARCH_PATTERNS = [
    r"10\.\d+",  # DOI numbers
    r"Roos_uncc",
    r"Acharya",
    r"Joeng\.personality",
    r"mikulincer",
    r"cogsci",
]

TOPIC_PATTERNS = {
    "anxiety": [r"anxiety", r"anxious", r"panic", r"worry"],
    "depression": [r"depression", r"depressed", r"mood"],
    "stress": [r"stress", r"stressed", r"burnout"],
    "coping": [r"coping", r"distress tolerance", r"emotion regulation", r"skills"],
    "loneliness": [r"loneliness", r"isolation", r"social"],
    "relationships": [r"relationship", r"romantic", r"breakup", r"attachment"],
    "self_esteem": [r"self-esteem", r"self-worth", r"body image"],
    "sleep": [r"sleep", r"insomnia"],
    "trauma": [r"trauma", r"ptsd", r"post-traumatic"],
    "psychosis": [r"psychosis"],
    "rumination": [r"rumination", r"overthinking"],
    "grief": [r"grief", r"loss"],
    "ocd": [r"obsessive", r"ocd"],
    "eating": [r"eating", r"disorder"],
    "bipolar": [r"bipolar"],
    "general": [],  # catch-all
}


def categorize_pdf(filename: str) -> dict:
    """Analyze filename and return categorization."""
    name_lower = filename.lower()

    # Detect source type
    source_type = "Unknown"
    if any(re.search(p, name_lower) for p in OFFICIAL_PATTERNS):
        source_type = "Official"
    elif any(re.search(p, name_lower) for p in TURKISH_PATTERNS):
        source_type = "Turkish"
    elif any(re.search(p, name_lower) for p in CLINICAL_MANUAL_PATTERNS):
        source_type = "Clinical"
    elif any(re.search(p, name_lower) for p in SELF_HELP_PATTERNS):
        source_type = "SelfHelp"
    elif any(re.search(p, name_lower) for p in RESEARCH_PATTERNS):
        source_type = "Research"

    # Detect language
    language = "EN"
    if any(re.search(p, filename) for p in TURKISH_PATTERNS):
        language = "TR"
    elif re.search(r"-eng\.pdf", filename):
        language = "EN"

    # Detect topic
    topic = "general"
    for t, patterns in TOPIC_PATTERNS.items():
        if any(re.search(p, name_lower) for p in patterns):
            topic = t
            break

    # Assign quality tier based on source type
    quality = "LOW"
    if source_type == "Official":
        quality = "HIGH"
    elif source_type in ("Clinical", "Research"):
        quality = "MEDIUM"
    elif source_type == "SelfHelp":
        quality = "MEDIUM"
    elif source_type == "Turkish":
        quality = "MEDIUM"
    else:
        quality = "LOW"

    # Assign action (KEEP high-quality, DELETE low-quality, UNCLEAR for borderline)
    action = "KEEP" if quality in ("HIGH", "MEDIUM") else "DELETE"
    if source_type == "Unknown":
        action = "UNCLEAR"

    # Assign index type
    index_type = "none"
    if source_type == "Unknown":
        index_type = "none"
    elif re.search(r"methodology|research|ai|rag|benchmark", name_lower):
        index_type = "methodology_index"
    elif re.search(r"crisis|suicide|safety|emergency", name_lower):
        index_type = "safety_crisis_index"
    elif re.search(r"skill|technique|exercise|coping|distress|emotion", name_lower):
        index_type = "coping_skills_index"
    else:
        index_type = "psychoeducation_index"

    return {
        "filename": filename,
        "source_type": source_type,
        "topic": topic,
        "language": language,
        "quality": quality,
        "action": action,
        "index_type": index_type,
        "notes": "",
    }


def create_audit_spreadsheet():
    """Create Excel audit spreadsheet."""
    # Get all PDFs
    pdf_dir = Path("/Users/aykutakkus/Desktop/Projects/Capstone/data/raw")
    pdfs = sorted([f.name for f in pdf_dir.glob("*.pdf")])

    print(f"Found {len(pdfs)} PDFs")

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "PDF_Audit"

    # Headers
    headers = ["filename", "source_type", "topic", "language", "quality", "action", "index_type", "notes"]
    ws.append(headers)

    # Style headers
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    header_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.border = header_border
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Add PDF data
    for pdf in pdfs:
        cat = categorize_pdf(pdf)
        ws.append([
            cat["filename"],
            cat["source_type"],
            cat["topic"],
            cat["language"],
            cat["quality"],
            cat["action"],
            cat["index_type"],
            cat["notes"],
        ])

    # Set column widths and alignment
    ws.column_dimensions["A"].width = 60
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 12
    ws.column_dimensions["F"].width = 12
    ws.column_dimensions["G"].width = 22
    ws.column_dimensions["H"].width = 30

    # Center align columns B-G
    for row in ws.iter_rows(min_row=2, max_row=len(pdfs)+1, min_col=2, max_col=7):
        for cell in row:
            cell.alignment = Alignment(horizontal="center", vertical="top")

    # Add borders to all cells
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    for row in ws.iter_rows(min_row=2, max_row=len(pdfs)+1, min_col=1, max_col=8):
        for cell in row:
            cell.border = thin_border

    # Add summary stats
    summary_row = len(pdfs) + 3
    ws[f"A{summary_row}"] = "SUMMARY"
    ws[f"A{summary_row}"].font = Font(bold=True)

    # Count by action
    action_row = summary_row + 1
    ws[f"A{action_row}"] = "KEEP:"
    ws[f"B{action_row}"] = f"=COUNTIF(F2:F{len(pdfs)+1},\"KEEP\")"

    action_row += 1
    ws[f"A{action_row}"] = "DELETE:"
    ws[f"B{action_row}"] = f"=COUNTIF(F2:F{len(pdfs)+1},\"DELETE\")"

    action_row += 1
    ws[f"A{action_row}"] = "UNCLEAR:"
    ws[f"B{action_row}"] = f"=COUNTIF(F2:F{len(pdfs)+1},\"UNCLEAR\")"

    action_row += 1
    ws[f"A{action_row}"] = "TOTAL:"
    ws[f"B{action_row}"] = f"=COUNTA(A2:A{len(pdfs)+1})"

    # Save
    output_path = Path("/Users/aykutakkus/Desktop/Projects/Capstone/data/pdf_audit.xlsx")
    wb.save(output_path)
    print(f"Created: {output_path}")

    # Summary by action
    keep_count = sum(1 for p in pdfs if categorize_pdf(p)["action"] == "KEEP")
    delete_count = sum(1 for p in pdfs if categorize_pdf(p)["action"] == "DELETE")
    unclear_count = sum(1 for p in pdfs if categorize_pdf(p)["action"] == "UNCLEAR")

    print(f"\nInitial Categorization:")
    print(f"  KEEP: {keep_count}")
    print(f"  DELETE: {delete_count}")
    print(f"  UNCLEAR: {unclear_count}")
    print(f"  Total: {keep_count + delete_count + unclear_count}")


if __name__ == "__main__":
    create_audit_spreadsheet()

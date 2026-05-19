#!/usr/bin/env python3
"""Aggressively prune to exactly 40 high-quality PDFs."""

from openpyxl import load_workbook

# Strategic selection for 40-PDF target
DEFINITE_KEEP = {
    # Official sources (5)
    "9789240003910-eng.pdf",  # WHO stress
    "23-MH-8110-Understanding-Psychosis.pdf",  # WHO
    "FS_GriefInAdults_EN_2025.pdf",  # WHO grief
    "surgeon-general-social-connection-advisory.pdf",  # US Surgeon General
    "clinical-research-trials-you-questions-answers.pdf",  # Clinical trials info

    # Clinical manuals & workbooks (8)
    "EMOTION REGULATION SKILLS MANUAL.pdf",
    "DISTRESS TOLERANCE SKILLS MANUAL e-version.pdf",
    "rtp_unit-2-workbook.pdf",
    "helping-children-and-adolescents-cope-with-traumatic-events.pdf",
    "stand-up-to-stress-coloring-activity-book.pdf",
    "Trauma-Informed-Behaviour-Support-A-Practical-Guide-to-Developing-Resilient-Learners-1673306765.pdf",
    "tips-for-talking-with-a-health-care-provider-about-your-mental-health_1.pdf",
    "Fundamentals-of-Psychological-Disorders.pdf",

    # Turkish sources (3)
    "turkpsikoloji.1515430.pdf",
    "resiliencepsikolojik-dayaniklilik.pdf",
    "1002672446-schoka.pdf",

    # Key research papers on major topics (24)
    # Anxiety (3)
    "social-anxiety-challenging-anxious-thinking.pdf",
    "Anxiety_Sensitivity_and_Catastrophizing.pdf",
    "HO15_ThnkngAbtThnkng.pdf",

    # Depression & Mood (3)
    "perinatal-depression.pdf",
    "Learned-Helplessness.pdf",
    "annurev-psych-010418-102813.pdf",

    # Relationships & Attachment (4)
    "Attachment Style and Dissolution of Romantic Relationships.pdf",
    "Implications of Rejection Sensitivity for Intimate Relationships.pdf",
    "baumeister and leary.pdf",
    "Avoiding more than Intimacy_ Avoidant Attachment and the Avoidanc.pdf",

    # Emotion Regulation & Coping (3)
    "Emotion_Regulation_through_Cognitive_Strategies.pdf",
    "Emotion_regulation.pdf",
    "Self-Compassion, Self-Esteem, and Well-Being.pdf",

    # Trauma & Stress (3)
    "post-traumatic-stress-disorder_1.pdf",
    "Self-harm and PTSD among a sample of women in Turkey the role of self.pdf",
    "repetitive-negative-thinking-rumination.pdf",

    # Cognitive patterns (3)
    "Thinking Errors and Self Defeating Beliefs-Anxiety and Depression.pdf",
    "Cognitive-Distortions.pdf",
    "cognitive-distortions (2).pdf",

    # Body image & Self-esteem (2)
    "Body Image - How we think and feel about our bodies.pdf",
    "Self-Esteem, Social Comparison, and Facebook Use.pdf",

    # Loneliness (2)
    "Psychology_of_Loneliness.pdf",
    "Isolation-and-loneliness-an-overview-of-literature.pdf",

    # Behavior & Disorders (2)
    "obsessive-compulsive-disorder-508.pdf",
    "bipolar-disorder.pdf",
}


def aggressive_prune():
    """Update spreadsheet to exactly 40 PDFs."""
    audit_path = "/Users/aykutakkus/Desktop/Projects/Capstone/data/pdf_audit.xlsx"
    wb = load_workbook(audit_path)
    ws = wb.active

    keep_count = 0
    delete_count = 0
    total_rows = 0

    # Find actual data range (skip summary)
    max_actual_row = ws.max_row
    for row in ws.iter_rows(min_row=ws.max_row - 5, max_row=ws.max_row):
        if row[0].value and "SUMMARY" in str(row[0].value):
            max_actual_row = row[0].row - 2
            break

    # Mark all PDFs
    for row in ws.iter_rows(min_row=2, max_row=max_actual_row):
        filename = row[0].value
        if not filename or not isinstance(filename, str):
            continue

        total_rows += 1

        # Decisively classify
        if filename in DEFINITE_KEEP:
            row[5].value = "KEEP"
            keep_count += 1
        else:
            row[5].value = "DELETE"
            delete_count += 1

    # Save
    wb.save(audit_path)

    print(f"Aggressive prune ({total_rows} PDFs):")
    print(f"  KEEP: {keep_count}")
    print(f"  DELETE: {delete_count}")
    print(f"\nSaved: {audit_path}")

    if keep_count > 40:
        print(f"\n⚠️  Still {keep_count - 40} PDFs over target")
    elif keep_count < 40:
        print(f"\n⚠️  Need {40 - keep_count} more PDFs")


if __name__ == "__main__":
    aggressive_prune()

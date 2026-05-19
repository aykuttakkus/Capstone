from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_active_prompts_do_not_claim_clinician_identity() -> None:
    prompts = (ROOT / "server/app/config/prompts.yaml").read_text()

    forbidden = [
        "You are a PhD Clinical Psychologist",
        "You are a Clinical Psychologist with a PhD",
        "PhD Psychologist Tone",
        "clinical formulation",
    ]

    for phrase in forbidden:
        assert phrase not in prompts


def test_generation_prompt_contains_boundary_rules() -> None:
    prompts = (ROOT / "server/app/config/prompts.yaml").read_text()

    assert "You are Calma, a psychological psychoeducation and information-support assistant." in prompts
    assert "You are not a therapist, psychologist, psychiatrist, doctor" in prompts
    assert "You do not diagnose, treat, prescribe, manage medication" in prompts
    assert "replace professional care" in prompts


def test_frontend_does_not_present_intake_as_phd_clinician() -> None:
    app = (ROOT / "client/src/App.jsx").read_text()

    assert "PhD Clinical Psychologist" not in app
    assert "PhD Assistant" not in app
    assert "The clinical assistant is currently unavailable" not in app
    assert "Calma Support Intake" in app or "${APP_NAME} Support Intake" in app

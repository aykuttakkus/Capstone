from __future__ import annotations

"""
Conversational Clinical Intake Engine — PhD Psychologist Edition
================================================================
A highly professional, empathetic intake flow led by a PhD-level 
clinical personality. Includes reflective acknowledgments between steps.
"""

import json
from dataclasses import dataclass
from typing import Any

from server.app.core.generation.llm import OllamaClient
from server.app.utils.prompts import render_prompt


@dataclass(frozen=True, slots=True)
class IntakeChatStep:
    phase: str
    question: str
    extract_fields: list[str]


# ---------------------------------------------------------------------------
# PhD Level Clinical Questions
# ---------------------------------------------------------------------------

INTAKE_CHAT_STEPS: list[IntakeChatStep] = [
    IntakeChatStep(
        phase="name",
        question=(
            "Welcome. I'm glad you've taken this step for your well-being. "
            "To begin our journey together, how would you like me to address you?"
        ),
        extract_fields=["preferred_name"],
    ),
    IntakeChatStep(
        phase="concern",
        question=(
            "Thank you, {name}. To help me understand your world, could you share "
            "what is the primary concern or weight on your mind that brought you here today? "
            "Please feel free to speak openly."
        ),
        extract_fields=["main_issue"],
    ),
    IntakeChatStep(
        phase="timeline",
        question=(
            "I appreciate your openness. Could you tell me more about the timeline of these "
            "experiences, and how they might be influencing your daily life—perhaps in your "
            "relationships, your work, or your sense of self?"
        ),
        extract_fields=["duration", "impact"],
    ),
    IntakeChatStep(
        phase="support",
        question=(
            "That provides important context, {name}. Are you currently navigating this with "
            "professional support, or perhaps through personal coping practices that you've "
            "found helpful when things feel particularly challenging?"
        ),
        extract_fields=["therapy_status", "coping_style", "support_system"],
    ),
    IntakeChatStep(
        phase="narrative",
        question=(
            "We are nearing the start of our regular sessions. As a final piece of our "
            "initial meeting: if you could describe your life as it stands today—your "
            "typical routines, what sustains your resilience, and what you hope might "
            "shift—what would that look like?"
        ),
        extract_fields=["life_narrative"],
    ),
]

PHASE_ORDER = [step.phase for step in INTAKE_CHAT_STEPS]
_STEP_MAP = {step.phase: step for step in INTAKE_CHAT_STEPS}


@dataclass(slots=True)
class IntakeStepResult:
    current_phase: str
    next_phase: str | None
    next_question: str | None
    reflection: str | None  # PhD level reflection on the answer
    extracted: dict[str, str]
    complete: bool


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _extract_name(answer: str) -> str:
    cleaned = answer.strip().strip('"').strip("'").strip(".")
    if len(cleaned.split()) > 5:
        cleaned = " ".join(cleaned.split()[:3])
    return cleaned.title() if cleaned else "Friend"


def _extract_therapy_status(answer: str) -> str:
    lower = answer.lower()
    if any(w in lower for w in ["yes", "yeah", "seeing", "therapist", "counselor", "psychiatrist", "currently"]):
        return "Yes"
    if any(w in lower for w in ["no", "nope", "not", "never", "haven't", "don't"]):
        return "No"
    return "Unknown"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class IntakeChatEngine:
    def __init__(self, llm_client: OllamaClient | None = None):
        self.llm_client = llm_client or OllamaClient()

    def get_first_question(self) -> IntakeStepResult:
        step = INTAKE_CHAT_STEPS[0]
        return IntakeStepResult(
            current_phase="",
            next_phase=step.phase,
            next_question=step.question,
            reflection=None,
            extracted={},
            complete=False,
        )

    async def _generate_reflection(self, phase: str, answer: str, signals: dict[str, Any]) -> str:
        """Uses the LLM to generate a brief, PhD-level clinical reflection."""
        try:
            prompt = render_prompt(
                "agents.intake_reflector",
                PHASE=phase,
                SIGNALS=json.dumps(signals),
                ANSWER=answer,
            )
            result = self.llm_client.generate(prompt)
            if result.available and result.text:
                return result.text.strip()
        except Exception:
            pass
        return ""

    async def _generate_summary(self, signals: dict[str, Any]) -> str:
        """Generates a final case formulation summary at the end of intake."""
        try:
            prompt = render_prompt(
                "agents.intake_summarizer",
                SIGNALS=json.dumps(signals),
            )
            result = self.llm_client.generate(prompt)
            if result.available and result.text:
                return result.text.strip()
        except Exception:
            pass
        return "Thank you for sharing your story with me. I now have a much clearer picture of your situation."

    async def process_step(
        self,
        phase: str,
        answer: str,
        accumulated: dict[str, str] | None = None,
    ) -> IntakeStepResult:
        accumulated = accumulated or {}
        step = _STEP_MAP.get(phase)
        if step is None:
            summary = await self._generate_summary(accumulated)
            return IntakeStepResult(
                current_phase=phase,
                next_phase=None,
                next_question=None,
                reflection=summary,
                extracted=accumulated,
                complete=True,
            )

        extracted = dict(accumulated)

        # Basic rule-based extraction for reliability
        if phase == "name":
            extracted["preferred_name"] = _extract_name(answer)
        elif phase == "concern":
            extracted["main_issue"] = answer.strip()
        elif phase == "timeline":
            extracted["duration_raw"] = answer.strip()
            # Basic impact detection
            lower = answer.lower()
            if any(w in lower for w in ["severe", "struggling", "can't function"]):
                extracted["impact"] = "Severe_I_am_struggling_to_function"
            else:
                extracted["impact"] = "Moderate_It_is_making_daily_tasks_difficult"
        elif phase == "support":
            extracted["therapy_status"] = _extract_therapy_status(answer)
        elif phase == "narrative":
            extracted["life_narrative"] = answer.strip()

        # Determine next phase
        current_idx = PHASE_ORDER.index(phase)
        if current_idx + 1 < len(PHASE_ORDER):
            # Generate PhD level reflection for intermediate steps
            reflection = await self._generate_reflection(phase, answer, extracted)
            next_step = INTAKE_CHAT_STEPS[current_idx + 1]
            name = extracted.get("preferred_name", "there")
            next_question = next_step.question.replace("{name}", name)
            return IntakeStepResult(
                current_phase=phase,
                next_phase=next_step.phase,
                next_question=next_question,
                reflection=reflection,
                extracted=extracted,
                complete=False,
            )

        # Final step completed: generate summary
        summary = await self._generate_summary(extracted)
        return IntakeStepResult(
            current_phase=phase,
            next_phase=None,
            next_question=None,
            reflection=summary,
            extracted=extracted,
            complete=True,
        )


intake_chat_engine = IntakeChatEngine()

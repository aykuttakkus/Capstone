from __future__ import annotations

from dataclasses import dataclass

from server.app.core.agents.response_planner import ResponsePlan


@dataclass(slots=True)
class SentimentProfile:
    label: str
    urgency: int
    empathy_required: bool
    rationale: str
from server.app.core.generation.llm import OllamaClient
from server.app.core.retrieval.retriever import ScoredChunk
from server.app.core.safety.policy import SafetyDecision
from server.app.services.flows.topics import topic_label
from server.app.services.session import compose_memory_context
from server.app.utils.prompts import render_prompt
from server.app.utils.text import split_sentences


def _excerpt(content: str, max_sentences: int = 2) -> str:
    sentences = split_sentences(content)
    return " ".join(sentences[:max_sentences])


@dataclass(slots=True)
class GeneratedPayload:
    status: str
    answer: str
    summary: str
    follow_up: list[str]
    route: str


class AnswerGenerator:
    def __init__(self, llm_client: OllamaClient | None = None) -> None:
        self.llm_client = llm_client or OllamaClient()

    def _build_prompt(
        self,
        message: str,
        topic: str,
        retrievals: list[ScoredChunk],
        intent_label: str,
        clinical_nugget: str | None = None,
        screening: dict[str, str | int | bool] | None = None,
        sentiment: SentimentProfile | None = None,
        session_memory: str | None = None,
        memory: str | None = None,
        planner: ResponsePlan | None = None,
        profile_snapshot: str | None = None,
        mood_summary: str | None = None,
        journal_summary: str | None = None,
    ) -> str:
        # Step 2: Use synthesized nugget for minimal context
        context_block = f"\n[CLINICAL EVIDENCE: {clinical_nugget}]" if clinical_nugget else ""
        
        system_rules = render_prompt("generation.answer_system_rules")
        
        # Simplified context components
        screening_info = f"\n[Assessment: {screening.get('severity') if screening else 'None'}]"
        sentiment_info = f"\n[User Sentiment: {sentiment.label if sentiment else 'Neutral'}]"
        memory_info = f"\n[Key History: {memory[:200] if memory else ''}]"
        
        return "\n\n".join(
            [
                system_rules + context_block + screening_info + sentiment_info + memory_info,
                f"User Message: {message}",
                render_prompt("generation.answer_output_format"),
            ]
        )

    def build_special(self, safety: SafetyDecision, topic: str, intent_label: str) -> GeneratedPayload:
        if safety.mode == "crisis_support":
            return GeneratedPayload(status="crisis", answer=(f"{safety.message} If you can, move closer to a trusted person and use local emergency support now."), summary="crisis routing", follow_up=["Seek immediate human support", "Use local emergency services"], route=safety.mode)

        if safety.mode == "risk_clarification":
            return GeneratedPayload(
                status="clarification",
                answer=(
                    f"{safety.message} If you are in immediate danger, contact local emergency support now. "
                    "If not, reply with 'safe' and we can keep talking here."
                ),
                summary="risk clarification",
                follow_up=["Confirm whether you are safe", "Ask for immediate help if needed"],
                route=safety.mode,
            )

        if safety.mode == "medication_refusal":
            return GeneratedPayload(status="refusal", answer=(f"{safety.message} I can still explain general information about {topic_label(topic).lower()}."), summary="medication refusal", follow_up=["Ask for general psychoeducation", "Ask about trusted sources"], route=safety.mode)

        if safety.mode == "diagnosis_refusal":
            return GeneratedPayload(status="refusal", answer=(f"{safety.message} I can explain general signs and concepts related to {topic_label(topic).lower()} instead."), summary="diagnosis refusal", follow_up=["Ask for a general explanation", "Ask for source-backed information"], route=safety.mode)

        if safety.mode == "off_domain":
            return GeneratedPayload(status="off_domain", answer=safety.message, summary="off-domain request", follow_up=["Ask about stress or anxiety", "Ask about low mood or burnout", "Ask about how to seek professional support"], route=safety.mode)

        if safety.mode == "prompt_injection_blocked":
            return GeneratedPayload(status="blocked", answer=safety.message, summary="prompt injection blocked", follow_up=["Ask a general mental health question"], route=safety.mode)

        return GeneratedPayload(status="refusal", answer=safety.message, summary=intent_label, follow_up=["Check immediate safety", "Ask a general question"], route=safety.mode)

    def build_insufficient(self, topic: str, intent_label: str) -> GeneratedPayload:
        if topic == "general":
            return GeneratedPayload(
                status="general_fallback",
                answer=(
                    "I can give you a general psychoeducational overview. "
                    "What would you like to understand more specifically?"
                ),
                summary=intent_label,
                follow_up=[
                    "Ask about stress",
                    "Ask about anxiety",
                    "Ask about burnout or sleep",
                ],
                route="topic:general",
            )

        return GeneratedPayload(status="insufficient_evidence", answer=(f"I do not have enough reliable evidence for a confident answer on {topic_label(topic).lower()}. If you want, I can still offer a general explanation or switch to a better-covered topic."), summary=intent_label, follow_up=["Switch to a related topic", "Ask for a simpler general explanation"], route="evidence_gate")

    def build_grounded(
        self,
        message: str,
        topic: str,
        retrievals: list[ScoredChunk],
        intent_label: str,
        clinical_nugget: str | None = None,
        screening: dict[str, str | int | bool] | None = None,
        sentiment: SentimentProfile | None = None,
        session_memory: str | None = None,
        memory: str | None = None,
        planner: ResponsePlan | None = None,
        profile_snapshot: str | None = None,
        mood_summary: str | None = None,
        journal_summary: str | None = None,
    ) -> GeneratedPayload:
        llm_result = self.llm_client.generate(
            self._build_prompt(
                message,
                topic,
                retrievals,
                intent_label,
                clinical_nugget=clinical_nugget,
                screening=screening,
                sentiment=sentiment,
                session_memory=session_memory,
                memory=memory,
                planner=planner,
                profile_snapshot=profile_snapshot,
                mood_summary=mood_summary,
                journal_summary=journal_summary,
            )
        )

        if llm_result.available and llm_result.text:
            raw_answer = llm_result.text.strip()
            
            # ADIM 3: MEKANİK DOZAJLAMA (RESPONSE CHUNKING)
            sentences = split_sentences(raw_answer)
            
            if len(sentences) > 4:
                truncated = " ".join(sentences[:3])
                last_q = sentences[-1] if "?" in sentences[-1] else "Would you like me to elaborate on a specific part of this?"
                final_answer = f"{truncated}\n\n{last_q}"
            else:
                final_answer = raw_answer

            return GeneratedPayload(
                status="grounded",
                answer=final_answer,
                summary=intent_label,
                follow_up=[],
                route=f"topic:{topic}",
            )

        return self.build_insufficient(topic, intent_label)

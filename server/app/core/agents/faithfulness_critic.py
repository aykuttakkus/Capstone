from __future__ import annotations

from dataclasses import dataclass, field

from server.app.core.agents.response_planner import ResponsePlan
from server.app.core.retrieval.retriever import ScoredChunk


@dataclass(slots=True)
class FaithfulnessCriticResult:
    passed: bool = True
    unsupported_claims: list[str] = field(default_factory=list)
    source_misuse: list[str] = field(default_factory=list)
    rewrite_required: bool = False
    rewrite_instructions: list[str] = field(default_factory=list)


class FaithfulnessCritic:
    STRONG_CLAIM_MARKERS = [
        "research proves",
        "studies prove",
        "it is proven",
        "definitely",
        "always",
        "never",
        "guaranteed",
        "will cure",
        # Extended over-confidence markers (spec M4)
        "100% effective",
        "100% safe",
        "it is certain",
        "without a doubt",
        "this will definitely",
        "this always works",
        "this never fails",
        "will fix",
        "will solve",
        "scientifically proven",
        "clinically proven",
        "universally accepted",
        "there is no risk",
        "completely safe",
        "absolutely certain",
        "you will feel better",
        "this is the only",
        "the best treatment",
        "the only way",
    ]
    DIAGNOSIS_MARKERS = [
        "you have depression",
        "you have anxiety disorder",
        "you have ocd",
        "you have ptsd",
        "you are depressed",
        "this is depression",
        "this is ocd",
    ]
    MEDICATION_MARKERS = [
        "you should take",
        "you should stop taking",
        "increase your dose",
        "decrease your dose",
        "start medication",
        "stop medication",
    ]

    def critique(
        self,
        draft_response: str,
        retrieved_chunks: list[ScoredChunk],
        response_plan: ResponsePlan,
        retrieval_confidence: float,
    ) -> FaithfulnessCriticResult:
        result = FaithfulnessCriticResult()
        response_lower = draft_response.lower()

        self._check_boundaries(response_lower, response_plan, result)
        self._check_retrieval_support(response_lower, retrieved_chunks, response_plan, retrieval_confidence, result)
        self._check_source_scope(retrieved_chunks, response_plan, result)

        if result.unsupported_claims or result.source_misuse:
            result.passed = False
            result.rewrite_required = True
        return result

    def _check_boundaries(
        self,
        response_lower: str,
        response_plan: ResponsePlan,
        result: FaithfulnessCriticResult,
    ) -> None:
        if not response_plan.diagnosis_allowed:
            for marker in self.DIAGNOSIS_MARKERS:
                if marker in response_lower:
                    result.unsupported_claims.append(f"diagnosis_language:{marker}")
                    result.rewrite_instructions.append("Remove diagnostic claims and use non-diagnostic psychoeducation.")
                    break

        if not response_plan.medication_advice_allowed:
            for marker in self.MEDICATION_MARKERS:
                if marker in response_lower:
                    result.unsupported_claims.append(f"medication_advice:{marker}")
                    result.rewrite_instructions.append("Remove medication instructions and redirect to a qualified medical professional.")
                    break

    def _check_retrieval_support(
        self,
        response_lower: str,
        retrieved_chunks: list[ScoredChunk],
        response_plan: ResponsePlan,
        retrieval_confidence: float,
        result: FaithfulnessCriticResult,
    ) -> None:
        has_strong_claim = any(marker in response_lower for marker in self.STRONG_CLAIM_MARKERS)
        if response_plan.source_required and not retrieved_chunks:
            result.unsupported_claims.append("source_required_but_no_retrieval")
            result.rewrite_instructions.append("Avoid factual claims because no reliable retrieval is available.")
        if has_strong_claim and retrieval_confidence < 0.5:
            result.unsupported_claims.append("strong_claim_with_low_retrieval_confidence")
            result.rewrite_instructions.append("Replace strong certainty with lower-confidence language.")

    def _check_source_scope(
        self,
        retrieved_chunks: list[ScoredChunk],
        response_plan: ResponsePlan,
        result: FaithfulnessCriticResult,
    ) -> None:
        if response_plan.response_mode != "crisis":
            crisis_chunks = [chunk.chunk.id for chunk in retrieved_chunks if chunk.chunk.clinical_scope == "crisis_support_only"]
            if crisis_chunks:
                result.source_misuse.append(f"crisis_sources_used_outside_crisis:{','.join(crisis_chunks)}")
                result.rewrite_instructions.append("Remove crisis-only source use from non-crisis response.")

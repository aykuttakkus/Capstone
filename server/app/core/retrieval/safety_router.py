from __future__ import annotations

from dataclasses import dataclass, field


PSYCHOEDUCATION_COLLECTION = "calma_psychoeducation"
COPING_COLLECTION = "calma_coping"
CRISIS_SAFETY_COLLECTION = "calma_crisis_safety"
MEDICATION_BOUNDARY_COLLECTION = "calma_medication_boundary"
METHODOLOGY_COLLECTION = "calma_methodology"


@dataclass(slots=True)
class RetrievalScope:
    name: str
    allowed_use: list[str]
    clinical_scope: str | None
    min_evidence_level: str
    risk_level: str
    use_rag: bool
    collection_hint: str
    reason_tags: list[str] = field(default_factory=list)


def select_retrieval_scope(intent: str, risk_level: str, safety_mode: str) -> RetrievalScope:
    normalized_intent = _normalize_intent(intent)
    normalized_risk = _normalize_risk(risk_level, safety_mode)

    if safety_mode in {"crisis", "crisis_support"} or normalized_intent == "crisis" or normalized_risk == "crisis":
        return RetrievalScope(
            name="crisis_safety",
            allowed_use=["crisis"],
            clinical_scope="crisis_support_only",
            min_evidence_level="clinical_self_help",
            risk_level="crisis",
            use_rag=False,
            collection_hint=CRISIS_SAFETY_COLLECTION,
            reason_tags=["scope:crisis_safety", "rag:disabled_for_crisis"],
        )

    if safety_mode == "medication_refusal":
        return RetrievalScope(
            name="medication_boundary",
            allowed_use=["medication_boundary"],
            clinical_scope="medication_boundary_only",
            min_evidence_level="educational",
            risk_level=normalized_risk,
            use_rag=False,
            collection_hint=MEDICATION_BOUNDARY_COLLECTION,
            reason_tags=["scope:medication_boundary", "rag:disabled_for_medication"],
        )

    if normalized_intent == "off_scope" or safety_mode in {"off_domain", "prompt_injection_blocked"}:
        return RetrievalScope(
            name="off_scope",
            allowed_use=[],
            clinical_scope=None,
            min_evidence_level="educational",
            risk_level=normalized_risk,
            use_rag=False,
            collection_hint=METHODOLOGY_COLLECTION,
            reason_tags=["scope:off_scope", "rag:disabled_for_scope"],
        )

    if normalized_intent == "coping_strategy":
        return RetrievalScope(
            name="coping",
            allowed_use=["coping_strategy"],
            clinical_scope="psychoeducation_only",
            min_evidence_level="clinical_self_help",
            risk_level=normalized_risk,
            use_rag=True,
            collection_hint=COPING_COLLECTION,
            reason_tags=["scope:coping", "rag:coping_safe"],
        )

    if normalized_intent == "symptom_exploration":
        return RetrievalScope(
            name="symptom_exploration",
            allowed_use=["symptom_exploration", "psychoeducation"],
            clinical_scope="psychoeducation_only",
            min_evidence_level="educational",
            risk_level=normalized_risk,
            use_rag=True,
            collection_hint=PSYCHOEDUCATION_COLLECTION,
            reason_tags=["scope:symptom_exploration", "rag:psychoeducation_safe"],
        )

    if normalized_intent == "emotional_support":
        return RetrievalScope(
            name="emotional_support",
            allowed_use=["emotional_support", "psychoeducation"],
            clinical_scope="psychoeducation_only",
            min_evidence_level="educational",
            risk_level=normalized_risk,
            use_rag=normalized_risk in {"medium", "high"},
            collection_hint=PSYCHOEDUCATION_COLLECTION,
            reason_tags=["scope:emotional_support", "rag:limited_support"],
        )

    return RetrievalScope(
        name="psychoeducation",
        allowed_use=["psychoeducation"],
        clinical_scope="psychoeducation_only",
        min_evidence_level="educational",
        risk_level=normalized_risk,
        use_rag=True,
        collection_hint=PSYCHOEDUCATION_COLLECTION,
        reason_tags=["scope:psychoeducation", "rag:psychoeducation_safe"],
    )


def _normalize_intent(intent: str) -> str:
    intent_map = {
        "educational_request": "psychoeducation",
        "general_query": "psychoeducation",
        "medical_info": "psychoeducation",
        "symptom_search": "symptom_exploration",
        "venting": "emotional_support",
        "clarification": "clarification_needed",
    }
    return intent_map.get(intent, intent or "emotional_support")


def _normalize_risk(risk_level: str, safety_mode: str) -> str:
    if safety_mode in {"crisis", "crisis_support"}:
        return "crisis"
    if risk_level in {"none", "low", "medium", "high", "crisis"}:
        return risk_level
    return "none"

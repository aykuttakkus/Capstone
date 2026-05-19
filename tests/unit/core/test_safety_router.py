from __future__ import annotations

from server.app.core.retrieval.safety_router import select_retrieval_scope


def test_safety_router_selects_psychoeducation_scope() -> None:
    scope = select_retrieval_scope("psychoeducation", "none", "normal")

    assert scope.name == "psychoeducation"
    assert scope.use_rag is True
    assert scope.allowed_use == ["psychoeducation"]
    assert scope.clinical_scope == "psychoeducation_only"
    assert scope.collection_hint == "calma_psychoeducation"


def test_safety_router_selects_coping_scope() -> None:
    scope = select_retrieval_scope("coping_strategy", "low", "normal")

    assert scope.name == "coping"
    assert scope.allowed_use == ["coping_strategy"]
    assert scope.min_evidence_level == "clinical_self_help"
    assert scope.collection_hint == "calma_coping"


def test_safety_router_disables_normal_rag_for_crisis() -> None:
    scope = select_retrieval_scope("crisis", "crisis", "crisis_support")

    assert scope.name == "crisis_safety"
    assert scope.use_rag is False
    assert scope.allowed_use == ["crisis"]
    assert scope.clinical_scope == "crisis_support_only"
    assert scope.collection_hint == "calma_crisis_safety"


def test_safety_router_disables_normal_rag_for_medication_boundary() -> None:
    scope = select_retrieval_scope("psychoeducation", "none", "medication_refusal")

    assert scope.name == "medication_boundary"
    assert scope.use_rag is False
    assert scope.allowed_use == ["medication_boundary"]
    assert scope.clinical_scope == "medication_boundary_only"

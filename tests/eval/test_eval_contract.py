from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.eval.run_eval import EvalResult, build_report_data


pytestmark = [pytest.mark.eval]


def test_eval_dataset_and_schema_expose_required_fields() -> None:
    eval_dir = Path(__file__).resolve().parent
    dataset = json.loads((eval_dir / "golden_dataset.json").read_text(encoding="utf-8"))
    schema = json.loads((eval_dir / "eval_results_schema.json").read_text(encoding="utf-8"))

    assert dataset
    assert all("query" in item for item in dataset)
    assert all("expected_route" in item for item in dataset)
    assert all("eval_type" in item for item in dataset)
    assert any(item.get("eval_type") == "personalization" for item in dataset)
    assert "summary" in schema
    assert "subset_metrics" in schema
    assert "detailed_results" in schema


def test_build_report_data_matches_expected_shape() -> None:
    report = build_report_data(
        [
            EvalResult(
                query="Tell me about stress",
                target_topic="stress_anxiety",
                eval_type="retrieval",
                detected_route="topic:stress_anxiety",
                detected_safety="normal",
                detected_status="grounded",
                latency_ms=10.0,
                sources_found=2,
                top_score=0.91,
                pass_target_route=True,
                pass_target_safety=True,
                keyword_match_count=1,
                source_match_count=1,
                personalization_applied=True,
                expected_personalization_applied=True,
                pass_personalization=True,
            )
        ]
    )

    assert report["summary"]["total_samples"] == 1
    assert report["summary"]["route_accuracy"] == 1.0
    assert report["summary"]["source_match_rate"] == 1.0
    assert report["summary"]["personalization_accuracy"] == 1.0
    assert report["subset_metrics"]["retrieval"]["route_accuracy"] == 1.0
    assert report["detailed_results"][0]["detected_route"] == "topic:stress_anxiety"

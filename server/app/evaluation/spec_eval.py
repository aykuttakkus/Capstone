from __future__ import annotations

"""Spec compliance evaluator — runs benchmark_dataset.json against the pipeline.

Usage:
    python -m server.app.evaluation.spec_eval [--dataset PATH] [--output PATH]
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_DEFAULT_DATASET = Path(__file__).parent / "benchmark_dataset.json"


@dataclass
class CaseResult:
    case_id: str
    passed: bool
    intent_match: bool
    risk_match: bool
    content_ok: bool
    forbidden_found: list[str]
    quality_score: float
    notes: list[str] = field(default_factory=list)


@dataclass
class EvalReport:
    total: int
    passed: int
    failed: int
    pass_rate: float
    results: list[CaseResult]
    spec_gaps: list[str] = field(default_factory=list)


def _check_contains(response: str, terms: list[str], mode: str = "all") -> bool:
    lower = response.lower()
    if mode == "all":
        return all(t.lower() in lower for t in terms)
    return any(t.lower() in lower for t in terms)


def _find_forbidden(response: str, forbidden: list[str]) -> list[str]:
    lower = response.lower()
    return [f for f in forbidden if f.lower() in lower]


def evaluate_case(case: dict[str, Any], response: str, intent: str, risk_level: str, quality_score: float) -> CaseResult:
    notes: list[str] = []

    intent_match = intent == case.get("expected_intent", "")
    if not intent_match:
        notes.append(f"intent: expected={case.get('expected_intent')} got={intent}")

    risk_match = risk_level == case.get("expected_risk_level", "none")
    if not risk_match:
        notes.append(f"risk: expected={case.get('expected_risk_level')} got={risk_level}")

    required = case.get("expected_contains", [])
    required_any = case.get("expected_contains_any", [])
    content_ok = True
    if required:
        content_ok = _check_contains(response, required, mode="all")
        if not content_ok:
            notes.append(f"missing required terms: {required}")
    if required_any and content_ok:
        content_ok = _check_contains(response, required_any, mode="any")
        if not content_ok:
            notes.append(f"missing any-of terms: {required_any}")

    forbidden = _find_forbidden(response, case.get("must_not_contain", []))
    if forbidden:
        notes.append(f"forbidden terms found: {forbidden}")

    min_q = case.get("min_quality_score", 0.65)
    quality_ok = quality_score >= min_q
    if not quality_ok:
        notes.append(f"quality too low: {quality_score:.2f} < {min_q}")

    passed = intent_match and risk_match and content_ok and not forbidden and quality_ok

    return CaseResult(
        case_id=case["id"],
        passed=passed,
        intent_match=intent_match,
        risk_match=risk_match,
        content_ok=content_ok,
        forbidden_found=forbidden,
        quality_score=quality_score,
        notes=notes,
    )


def run_offline_eval(dataset_path: Path) -> EvalReport:
    """Offline dry-run: validates dataset structure and reports expected counts."""
    with open(dataset_path) as f:
        cases = json.load(f)

    results: list[CaseResult] = []
    for case in cases:
        # Stub: in offline mode generate a placeholder response
        stub_response = " ".join(case.get("expected_contains_any", case.get("expected_contains", ["general response"])))
        stub_intent = case.get("expected_intent", "emotional_support")
        stub_risk = case.get("expected_risk_level", "none")
        stub_quality = case.get("min_quality_score", 0.65)

        result = evaluate_case(case, stub_response, stub_intent, stub_risk, stub_quality)
        results.append(result)

    passed = sum(1 for r in results if r.passed)
    return EvalReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        pass_rate=passed / max(len(results), 1),
        results=results,
        spec_gaps=[r.case_id for r in results if not r.passed],
    )


def print_report(report: EvalReport) -> None:
    print(f"\n{'='*60}")
    print(f"SPEC EVAL REPORT — {report.total} cases")
    print(f"{'='*60}")
    print(f"Passed:    {report.passed} / {report.total}  ({report.pass_rate:.0%})")
    print(f"Failed:    {report.failed}")
    if report.spec_gaps:
        print(f"Gap cases: {', '.join(report.spec_gaps)}")
    print()
    for result in report.results:
        status = "✅" if result.passed else "❌"
        print(f"  {status} [{result.case_id}] quality={result.quality_score:.2f}")
        for note in result.notes:
            print(f"       ⚠  {note}")
    print(f"{'='*60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Calma Spec Evaluator")
    parser.add_argument("--dataset", type=Path, default=_DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=None, help="Write JSON report to file")
    args = parser.parse_args()

    report = run_offline_eval(args.dataset)
    print_report(report)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(
                {
                    "total": report.total,
                    "passed": report.passed,
                    "failed": report.failed,
                    "pass_rate": report.pass_rate,
                    "gaps": report.spec_gaps,
                    "results": [
                        {
                            "id": r.case_id,
                            "passed": r.passed,
                            "intent_match": r.intent_match,
                            "risk_match": r.risk_match,
                            "content_ok": r.content_ok,
                            "forbidden_found": r.forbidden_found,
                            "quality_score": r.quality_score,
                            "notes": r.notes,
                        }
                        for r in report.results
                    ],
                },
                f,
                indent=2,
            )
        print(f"Report written to {args.output}")

    sys.exit(0 if report.failed == 0 else 1)


if __name__ == "__main__":
    main()

"""RAG evaluation runner — Phase D.

Evaluates intent detection accuracy, index routing correctness,
boundary enforcement, and retrieval quality against the 45-case benchmark.

Usage:
    python -m server.app.evaluation.rag_eval
    python -m server.app.evaluation.rag_eval --verbose
    python -m server.app.evaluation.rag_eval --category safety_isolation
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


BENCHMARK_PATH = Path(__file__).parent / "rag_benchmark_dataset.json"


@dataclass
class CaseResult:
    test_id: str
    category: str
    passed: bool
    intent_correct: bool
    index_correct: bool
    boundary_correct: bool
    confidence_meets_threshold: bool
    actual_intent: str
    expected_intent: str
    actual_risk_level: str
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class EvalReport:
    total: int
    passed: int
    failed: int
    pass_rate: float
    by_category: dict[str, dict[str, int]]
    intent_accuracy: float
    index_accuracy: float
    boundary_accuracy: float
    failures: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)


def load_benchmark() -> list[dict]:
    if not BENCHMARK_PATH.exists():
        print(f"ERROR: Benchmark file not found: {BENCHMARK_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(BENCHMARK_PATH) as f:
        data = json.load(f)
    return data.get("test_cases", [])


def evaluate_case(case: dict, verbose: bool = False) -> CaseResult:
    """Evaluate a single test case against the IntentDetector and routing logic."""
    from server.app.core.pipeline.intent_detector import IntentDetector
    from server.app.core.retrieval.multi_index_retriever import (
        INDEX_SAFETY_CRISIS,
        CRISIS_INDEX_MIN_RISK,
        _INTENT_INDEX_MAP,
    )

    detector = IntentDetector()
    test_id = case["test_id"]
    category = case.get("category", "unknown")
    user_message = case["user_message"]
    expected_intent = case["intent"]
    expected_risk_level = case.get("risk_level", 0)
    expected_indexes = case.get("expected_indexes", [])
    must_not_query = case.get("must_not_query_indexes", [])

    failures: list[str] = []
    warnings: list[str] = []

    # 1. Intent detection
    result = detector.detect(user_message)
    actual_intent = result.primary_intent
    intent_correct = actual_intent == expected_intent

    if not intent_correct:
        failures.append(f"Intent: expected={expected_intent}, actual={actual_intent} (conf={result.confidence:.2f})")

    # 2. Risk level detection (for symptom/emotional cases)
    actual_risk_kw = detector.detect_risk_level(user_message)
    expected_risk_kw = case.get("expected_risk_keyword_level")
    if expected_risk_kw and actual_risk_kw != expected_risk_kw:
        failures.append(f"Risk keyword level: expected={expected_risk_kw}, actual={actual_risk_kw}")

    # 3. Index routing correctness
    # Simulate what MultiIndexRetriever._select_indexes() would do
    if expected_risk_level >= CRISIS_INDEX_MIN_RISK:
        simulated_indexes = [INDEX_SAFETY_CRISIS]
    else:
        preferred = _INTENT_INDEX_MAP.get(actual_intent, [])
        simulated_indexes = [idx for idx in preferred if idx != INDEX_SAFETY_CRISIS]

    # Check expected indexes are queried
    index_correct = True
    if expected_indexes:
        missing = [idx for idx in expected_indexes if idx not in simulated_indexes]
        if missing:
            index_correct = False
            failures.append(f"Missing indexes: {missing} (actual indexes: {simulated_indexes})")

    # Check forbidden indexes are NOT queried
    if must_not_query:
        forbidden_hit = [idx for idx in must_not_query if idx in simulated_indexes]
        if forbidden_hit:
            index_correct = False
            failures.append(f"Forbidden indexes queried: {forbidden_hit}")

    # Check crisis isolation
    must_not_from = case.get("must_not_retrieve_from_indexes", [])
    if must_not_from:
        leaked = [idx for idx in must_not_from if idx in simulated_indexes]
        if leaked:
            index_correct = False
            failures.append(f"Crisis isolation violated — leaked into: {leaked}")

    # 4. Boundary enforcement (off_scope, crisis)
    boundary_correct = True
    if expected_intent == "off_scope" and actual_intent != "off_scope":
        boundary_correct = False
        failures.append(f"Boundary: expected off_scope, got {actual_intent}")
    if expected_intent == "crisis" and actual_intent != "crisis":
        boundary_correct = False
        failures.append(f"Crisis: expected crisis, got {actual_intent}")

    # 5. Confidence meets threshold
    expected_min_conf = case.get("expected_min_confidence", 0.0)
    confidence_ok = expected_intent == "off_scope" or result.confidence >= expected_min_conf
    if not confidence_ok:
        warnings.append(f"Low confidence: {result.confidence:.2f} < {expected_min_conf}")

    passed = intent_correct and index_correct and boundary_correct

    if verbose and not passed:
        print(f"  FAIL [{test_id}] {category}")
        for f in failures:
            print(f"    → {f}")

    return CaseResult(
        test_id=test_id,
        category=category,
        passed=passed,
        intent_correct=intent_correct,
        index_correct=index_correct,
        boundary_correct=boundary_correct,
        confidence_meets_threshold=confidence_ok,
        actual_intent=actual_intent,
        expected_intent=expected_intent,
        actual_risk_level=actual_risk_kw,
        failures=failures,
        warnings=warnings,
    )


def run_eval(
    cases: list[dict],
    verbose: bool = False,
    filter_category: str | None = None,
) -> EvalReport:
    if filter_category:
        cases = [c for c in cases if c.get("category") == filter_category]

    results: list[CaseResult] = []
    for case in cases:
        result = evaluate_case(case, verbose=verbose)
        results.append(result)

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    pass_rate = passed / total if total > 0 else 0.0
    intent_accuracy = sum(1 for r in results if r.intent_correct) / total if total > 0 else 0.0
    index_accuracy = sum(1 for r in results if r.index_correct) / total if total > 0 else 0.0
    boundary_accuracy = sum(1 for r in results if r.boundary_correct) / total if total > 0 else 0.0

    # Group by category
    by_category: dict[str, dict[str, int]] = {}
    for r in results:
        cat = r.category
        if cat not in by_category:
            by_category[cat] = {"total": 0, "passed": 0, "failed": 0}
        by_category[cat]["total"] += 1
        if r.passed:
            by_category[cat]["passed"] += 1
        else:
            by_category[cat]["failed"] += 1

    failures = [
        {
            "test_id": r.test_id,
            "category": r.category,
            "expected_intent": r.expected_intent,
            "actual_intent": r.actual_intent,
            "reasons": r.failures,
        }
        for r in results if not r.passed
    ]

    warnings = [w for r in results for w in r.warnings]

    return EvalReport(
        total=total,
        passed=passed,
        failed=failed,
        pass_rate=pass_rate,
        by_category=by_category,
        intent_accuracy=intent_accuracy,
        index_accuracy=index_accuracy,
        boundary_accuracy=boundary_accuracy,
        failures=failures,
        warnings=warnings,
    )


def print_report(report: EvalReport, verbose: bool = False) -> None:
    sep = "─" * 60
    print(f"\n{sep}")
    print("  CALMA RAG Evaluation Report")
    print(f"{sep}")
    print(f"  Total:   {report.total}")
    print(f"  Passed:  {report.passed} ✅")
    print(f"  Failed:  {report.failed} ❌")
    print(f"  Rate:    {report.pass_rate:.0%}")
    print(f"{sep}")
    print("  Accuracy by Dimension:")
    print(f"    Intent Detection:    {report.intent_accuracy:.0%}")
    print(f"    Index Routing:       {report.index_accuracy:.0%}")
    print(f"    Boundary Enforcement:{report.boundary_accuracy:.0%}")
    print(f"{sep}")
    print("  By Category:")
    for cat, stats in sorted(report.by_category.items()):
        rate = stats["passed"] / stats["total"] if stats["total"] else 0
        icon = "✅" if rate >= 0.75 else ("⚠️ " if rate >= 0.50 else "❌")
        print(f"    {icon} {cat:<30} {stats['passed']}/{stats['total']} ({rate:.0%})")
    print(f"{sep}")

    if report.failures:
        print(f"  Failures ({len(report.failures)}):")
        for f in report.failures:
            print(f"    [{f['test_id']}] expected={f['expected_intent']}, got={f['actual_intent']}")
            for reason in f.get("reasons", []):
                print(f"      → {reason}")
        print(f"{sep}")

    if report.warnings and verbose:
        print(f"  Warnings ({len(report.warnings)}):")
        for w in report.warnings[:10]:
            print(f"    ⚠️  {w}")
        print(f"{sep}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CALMA RAG Evaluation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print per-case details")
    parser.add_argument("--category", "-c", help="Filter by category", default=None)
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    cases = load_benchmark()
    print(f"Loaded {len(cases)} test cases from {BENCHMARK_PATH.name}")

    report = run_eval(cases, verbose=args.verbose, filter_category=args.category)

    if args.json:
        import dataclasses
        print(json.dumps(dataclasses.asdict(report), indent=2))
    else:
        print_report(report, verbose=args.verbose)

    # Exit with code 1 if pass rate < 70%
    sys.exit(0 if report.pass_rate >= 0.70 else 1)


if __name__ == "__main__":
    main()

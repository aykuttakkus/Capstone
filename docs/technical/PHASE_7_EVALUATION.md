# Phase 7: Evaluation Harness

## Goal

Measure routing, safety, retrieval, source transparency, and personalization with a fixed gold set.

## What Changed

1. Expanded the golden evaluation dataset to include retrieval, Turkish typo handling, safety, and personalization samples.
2. Added source matching and personalization metrics to the evaluation report.
3. Added subset metrics so each scenario family can be checked separately.
4. Extended the evaluation schema to describe the richer report shape.

## Keep / Replace / Remove

### Keep

1. The single evaluation script.
2. JSON-based dataset and report outputs.
3. Unit-testable report computation.

### Replace

1. Route-only evaluation with multi-metric evaluation.
2. Flat sample list metrics with subset-aware metrics.

### Remove

1. Ambiguous evaluation output that does not separate retrieval from safety or personalization.

## Validation

The phase is validated by the evaluation contract tests. The script can also be run directly to produce `baseline_report.json`.

## Notes

1. The dataset is intentionally small so it can run locally and be reviewed quickly.
2. The evaluation output is designed to be readable by both humans and automated agents.

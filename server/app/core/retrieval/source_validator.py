"""Source registry validator — spec Phase A §A3.

Enforces the rule: No PDF enters the vector database without being
in the approved source registry with a valid review date.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path


_REGISTRY_PATH = Path("data/source_registry.json")


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    source_id: str | None
    reason: str
    warnings: list[str]


class SourceValidator:
    """Validates PDF sources against source_registry.json before ingestion."""

    def __init__(self, registry_path: Path | None = None) -> None:
        self._registry_path = registry_path or _REGISTRY_PATH
        self._registry = self._load_registry()

    def validate(self, filename: str, *, strict: bool = False) -> ValidationResult:
        """Check if a PDF file is approved for ingestion.

        Args:
            filename: PDF filename (basename only, e.g. "anxiety_guide.pdf")
            strict: If True, reject unregistered sources instead of warning.
        """
        if not self._registry:
            return ValidationResult(
                is_valid=True,
                source_id=None,
                reason="Registry unavailable — skipping validation",
                warnings=["source_registry.json could not be loaded"],
            )

        source = self._find_source(filename)

        if source is None:
            if strict:
                return ValidationResult(
                    is_valid=False,
                    source_id=None,
                    reason=f"Unregistered source: {filename}",
                    warnings=[],
                )
            return ValidationResult(
                is_valid=True,
                source_id=None,
                reason="Source not in registry — allowed (non-strict mode)",
                warnings=[f"{filename} is not in source_registry.json"],
            )

        source_id = source.get("source_id", "unknown")
        warnings: list[str] = []

        # Review date check
        review_warning = self._check_review_date(source)
        if review_warning:
            warnings.append(review_warning)

        # Approval status
        if source.get("review_status") != "approved":
            return ValidationResult(
                is_valid=False,
                source_id=source_id,
                reason=f"Source not approved: status={source.get('review_status')}",
                warnings=warnings,
            )

        return ValidationResult(
            is_valid=True,
            source_id=source_id,
            reason="Source approved",
            warnings=warnings,
        )

    def get_metadata(self, filename: str) -> dict:
        """Return registry metadata for a filename, or empty dict."""
        source = self._find_source(filename)
        return source or {}

    def list_approved_indexes(self, filename: str) -> list[str]:
        """Return the allowed_indexes for a registered source."""
        source = self._find_source(filename)
        if not source:
            return []
        return source.get("allowed_indexes", [])

    def list_allowed_use(self, filename: str) -> list[str]:
        """Return allowed_use list for a registered source."""
        source = self._find_source(filename)
        if not source:
            return []
        return source.get("allowed_use", [])

    # ── Private ────────────────────────────────────────────────────────────────

    def _find_source(self, filename: str) -> dict | None:
        filename_lower = filename.lower()
        for entry in self._registry.get("sources", []):
            registered = entry.get("filename", "").lower()
            if registered == filename_lower or registered in filename_lower:
                return entry
        return None

    def _check_review_date(self, source: dict) -> str | None:
        next_review_str = source.get("next_review")
        if not next_review_str:
            return f"Source '{source.get('source_id')}' has no next_review date set"
        try:
            next_review = date.fromisoformat(next_review_str)
            if date.today() > next_review:
                return (
                    f"Source '{source.get('source_id')}' is overdue for review "
                    f"(next_review={next_review_str})"
                )
        except ValueError:
            return f"Invalid next_review date: {next_review_str}"
        return None

    def _load_registry(self) -> dict:
        try:
            if self._registry_path.exists():
                with open(self._registry_path) as f:
                    return json.load(f)
        except Exception:
            pass
        return {}


# Module-level singleton
source_validator = SourceValidator()

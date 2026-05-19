from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DependencyCriticResult:
    is_safe: bool
    violations: list[str]
    severity: str
    recommendation: str


class DependencyCritic:
    DEPENDENCY_RED_FLAGS = {
        "always_available": [
            "i will always be here", "i'll be here for you", "whenever you need me",
            "24/7", "anytime", "her zaman yanındayım", "ne zaman ihtiyaç duysan"
        ],
        "only_i_understand": [
            "only i understand", "nobody else gets you", "i'm the only one",
            "only i can help", "sadece ben anlıyorum", "kimse seni anlamıyor"
        ],
        "isolation_from_support": [
            "don't trust anyone else", "others will hurt you", "can't rely on anyone",
            "keep this between us", "başkasına söyleme", "kimseye güvenme"
        ],
        "therapist_implication": [
            "i am your therapist", "this is therapy", "i am a doctor",
            "licensed to treat", "mental health professional", "terapeütim", "doktor"
        ],
        "rescue_fantasy": [
            "i will fix everything", "i will solve your problems", "leave it to me",
            "don't worry about it", "hepsini çözerim", "endişelenme"
        ]
    }

    BOUNDARY_VIOLATIONS = {
        "clinical_scope": [
            "you have", "you suffer from", "diagnosis", "prescription", "medication",
            "mental illness", "disorder", "teşhis", "ilaç"
        ],
        "relationship_blurring": [
            "we are friends", "our friendship", "personal connection", "close to me",
            "arkadaş", "yakın", "özel ilişki"
        ],
        "romantic_implication": [
            "i care about you", "i love you", "special person", "attracted",
            "seni önemsiyor", "seviyorum", "özel"
        ],
        "over_involvement": [
            "i will help you", "let me help", "i can handle this", "leave it to me",
            "yardım edeceğim", "bunu hallederim"
        ]
    }

    def critique(self, draft_response: str, context: dict | None = None) -> DependencyCriticResult:
        result = DependencyCriticResult(
            is_safe=True,
            violations=[],
            severity="none",
            recommendation=""
        )

        if not draft_response:
            return result

        normalized = draft_response.lower()

        # Check dependency red flags
        for category, red_flags in self.DEPENDENCY_RED_FLAGS.items():
            for flag in red_flags:
                if flag.lower() in normalized:
                    result.is_safe = False
                    result.violations.append(
                        f"Dependency risk ({category}): '{flag}' detected in response"
                    )
                    result.severity = "high"
                    break

        # Check boundary violations
        for category, violations in self.BOUNDARY_VIOLATIONS.items():
            for violation in violations:
                if violation.lower() in normalized:
                    result.is_safe = False
                    result.violations.append(
                        f"Boundary violation ({category}): '{violation}' detected"
                    )
                    if result.severity != "high":
                        result.severity = "medium"

        # Set recommendation based on violations
        if result.violations:
            if result.severity == "high":
                result.recommendation = "Rewrite: Remove all dependency-creating language. Use third-person support resources instead."
            else:
                result.recommendation = "Revise: Clarify professional boundaries and encourage outside support."
        else:
            result.recommendation = "Response is appropriate. No dependency or boundary concerns detected."

        return result

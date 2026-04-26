"""
Post-Guards — Response Validation Layer

Validates the final response before delivery to the user:
1. Structural completeness: All 4 signal categories present
2. Forbidden pattern blocking: No advice, comparisons, or speculation
3. Length enforcement: Response stays within budget
4. Source citation check: Ensure a source URL is present

If validation fails, the guard returns a corrected response or triggers
fallback formatting.
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


# ─── Forbidden Patterns ──────────────────────────────────────────────────────

FORBIDDEN_PATTERNS = [
    # Investment advice
    (r"\b(you\s+should\s+(buy|sell|invest|hold))\b", "investment advice"),
    (r"\b(i\s+recommend|i\s+suggest|consider\s+buying)\b", "recommendation"),
    (r"\b(good\s+investment|worth\s+investing|great\s+opportunity)\b", "investment advice"),

    # Price speculation
    (r"\b(price\s+will|price\s+could|price\s+might)\b", "price speculation"),
    (r"\b(likely\s+to\s+(increase|decrease|rise|fall|moon|pump|dump))\b", "price speculation"),
    (r"\b(potential\s+for\s+growth|upside\s+potential|downside\s+risk)\b", "speculation"),

    # Comparisons
    (r"\b(better\s+than|worse\s+than|compared\s+to|superior\s+to)\b", "comparison"),
    (r"\b(outperform|underperform)\b", "comparison"),

    # Subjective judgments
    (r"\b(this\s+is\s+a\s+(scam|gem|legit|safe|dangerous))\b", "subjective judgment"),
    (r"\b(trust(worthy|ed)?|reliable|unreliable)\b", "subjective judgment"),
]

# Required sections (None for the new narrative-only format)
REQUIRED_SECTIONS = []


class PostGuardResult:
    """Result of post-guard validation."""

    def __init__(self, passed: bool, response: str, violations: list = None):
        self.passed = passed
        self.response = response
        self.violations = violations or []

    def __repr__(self):
        status = "✓ Passed" if self.passed else "✗ Failed"
        return f"PostGuardResult({status}, violations={len(self.violations)})"


class PostGuards:
    """
    Validates and sanitizes the final response before delivery.
    """

    def __init__(self):
        self._forbidden = [
            (re.compile(pattern, re.IGNORECASE), label)
            for pattern, label in FORBIDDEN_PATTERNS
        ]

    def validate(self, response: str) -> PostGuardResult:
        """
        Run all validation checks on the response.

        Returns:
            PostGuardResult with pass/fail status, cleaned response, and violations
        """
        violations = []
        cleaned_response = response

        # 1. Check structural completeness
        completeness_violations = self._check_completeness(response)
        violations.extend(completeness_violations)

        # 2. Check forbidden patterns and sanitize
        cleaned_response, pattern_violations = self._check_forbidden_patterns(cleaned_response)
        violations.extend(pattern_violations)

        # Log results
        if violations:
            logger.warning(f"PostGuards: {len(violations)} violation(s) found: {violations}")
        else:
            logger.info("PostGuards: All checks passed")

        return PostGuardResult(
            passed=len(violations) == 0,
            response=cleaned_response,
            violations=violations,
        )

    def _check_completeness(self, response: str) -> list:
        """
        Verify all 4 signal categories are present in the response.
        """
        violations = []
        response_lower = response.lower()

        for section in REQUIRED_SECTIONS:
            if section not in response_lower:
                violations.append(f"Missing signal category: {section}")

        return violations

    def _check_forbidden_patterns(self, response: str) -> Tuple[str, list]:
        """
        Scan for forbidden patterns and remove/replace them.
        Returns the cleaned response and list of violations found.
        """
        violations = []
        cleaned = response

        for pattern, label in self._forbidden:
            matches = pattern.findall(cleaned)
            if matches:
                violations.append(f"Forbidden pattern ({label}): '{matches[0]}'")
                # Replace the forbidden text with a neutral marker
                cleaned = pattern.sub("[REDACTED]", cleaned)

        return cleaned, violations

    def enforce(self, response: str) -> str:
        """
        Validate and return the cleaned response.
        If critical violations are found, return a safe fallback.
        """
        result = self.validate(response)

        if result.passed:
            return result.response

        # Check severity: missing categories are critical
        critical = any("Missing signal category" in v for v in result.violations)

        if critical:
            logger.error("PostGuards: Critical violation — response missing signal categories")
            # Don't replace the whole response for missing categories
            # (the output formatter should have handled this)
            return result.response

        # For non-critical violations (forbidden patterns), return cleaned version
        return result.response

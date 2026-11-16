"""Content guardrails service — rule-based regex and Llama Guard path."""

import logging
import re
from dataclasses import dataclass
from typing import List

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Common prompt injection patterns
INJECTION_PATTERNS: List[str] = [
    r"(?i)ignore\s+(all\s+)?previous\s+instructions",
    r"(?i)ignore\s+(all\s+)?above\s+instructions",
    r"(?i)disregard\s+(all\s+)?previous",
    r"(?i)forget\s+(all\s+)?(your\s+)?instructions",
    r"(?i)you\s+are\s+now\s+(a\s+)?(?:DAN|jailbreak|unrestricted)",
    r"(?i)system\s*:\s*you\s+are",
    r"(?i)override\s+(system|safety)\s+(prompt|instructions|rules)",
    r"(?i)act\s+as\s+if\s+you\s+have\s+no\s+(restrictions|rules|guidelines)",
    r"(?i)pretend\s+you\s+(are|can|have)\s+no\s+(limitations|restrictions)",
    r"(?i)\bdo\s+anything\s+now\b",
    r"(?i)\bbypass\s+(safety|content|moderation)\s+(filters?|checks?|rules?)\b",
    r"(?i)reveal\s+(your|the|system)\s+(system\s+)?(prompt|instructions)",
    r"(?i)what\s+(is|are)\s+your\s+(system\s+)?(prompt|instructions)",
    r"(?i)<\s*script\s*>",
    r"(?i)javascript\s*:",
    r"(?i)\bon\s*(error|load|click|mouse)\s*=",
]

# Compile patterns once at module load
_COMPILED_PATTERNS = [re.compile(p) for p in INJECTION_PATTERNS]


@dataclass
class GuardrailResult:
    """Result of a guardrail content check."""

    safe: bool
    reason: str


class GuardrailsService:
    """Content safety guardrails with rule-based and Llama Guard modes."""

    def __init__(self, mode: str = ""):
        """
        Initialize guardrails service.

        Args:
            mode: 'rule_based' for regex checks, 'llama_guard' for LLM-based checks.
        """
        self.mode = mode or settings.GUARDRAIL_MODE
        logger.info("GuardrailsService initialized in '%s' mode", self.mode)

    def check_content(self, content: str) -> GuardrailResult:
        """
        Check content for prompt injection and unsafe patterns.

        Args:
            content: The text content to check.

        Returns:
            GuardrailResult indicating whether the content is safe.
        """
        if not content or not content.strip():
            return GuardrailResult(safe=False, reason="Content is empty.")

        if self.mode == "llama_guard":
            return self._check_llama_guard(content)

        return self._check_rule_based(content)

    def _check_rule_based(self, content: str) -> GuardrailResult:
        """Rule-based guardrail using regex pattern matching."""
        for i, pattern in enumerate(_COMPILED_PATTERNS):
            match = pattern.search(content)
            if match:
                matched_text = match.group(0)
                logger.warning(
                    "Guardrail triggered: pattern #%d matched '%s' in content",
                    i,
                    matched_text,
                )
                return GuardrailResult(
                    safe=False,
                    reason=f"Content matched injection pattern: '{matched_text}'",
                )

        logger.debug("Content passed rule-based guardrail check.")
        return GuardrailResult(safe=True, reason="Content passed all rule-based checks.")

    def _check_llama_guard(self, content: str) -> GuardrailResult:
        """
        Llama Guard based content safety check.

        In production, this would call a Llama Guard model endpoint.
        Currently runs rule-based checks as a baseline and logs the mode.
        """
        logger.info("Running Llama Guard mode guardrail check.")

        # Run rule-based checks as baseline even in llama_guard mode
        rule_result = self._check_rule_based(content)
        if not rule_result.safe:
            return rule_result

        # Llama Guard LLM check would go here in production.
        # For now, content that passes rule-based checks is considered safe.
        logger.info(
            "Llama Guard mode: content passed baseline checks. "
            "Full LLM-based safety analysis would run in production."
        )
        return GuardrailResult(
            safe=True,
            reason="Content passed Llama Guard baseline checks.",
        )


# Module-level instance for convenience
_guardrails_service = GuardrailsService()


def check_content_safety(content: str) -> GuardrailResult:
    """Module-level convenience function for checking content safety."""
    return _guardrails_service.check_content(content)

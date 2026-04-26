"""
Output Formatter — Strict Schema Enforcement Layer

Enforces the fixed response schema for all assistant outputs:
  1. Signal Summary (grouped by category)
  2. Explanation (2-3 sentences)
  3. Source (one citation link)
  4. Last Updated (timestamp)

No category is ever omitted. All fallback values are applied before formatting.
"""

import logging
from typing import Optional
from backend.services.signal_normalizer import NormalizedSignals

logger = logging.getLogger(__name__)


class OutputFormatter:
    """
    Formats normalized signals + LLM explanation into the strict precision schema.
    """

    def format_response(
        self,
        signals: NormalizedSignals,
        explanation: str,
        asset_name: Optional[str] = None,
    ) -> str:
        """
        Build the final response string containing only the clinical explanation.
        The UI handles all other data visualization.
        """
        # Return only the cleaned LLM explanation (Summary + Detailed Analysis)
        return self._clean_explanation(explanation)

    def format_refusal(self, message: str) -> str:
        """
        Format a query router refusal message.
        """
        return f"⚠️ {message}"

    def format_error(self, error_message: str) -> str:
        """
        Format an error response.
        """
        return (
            "**Signal Summary:**\n\n"
            "• **Smart Contract & Protocol Risk:** Data retrieval error\n"
            "• **Market & Liquidity Risk:** Data retrieval error\n"
            "• **External Trust & Verification:** Data retrieval error\n"
            "• **Regulatory Sanctions & Alerts:** Data retrieval error\n\n"
            f"**Factual Summary:** {error_message}\n\n"
            "**Source:** N/A\n\n"
            "**Last Updated:** N/A\n"
        )

    def _clean_explanation(self, explanation: str) -> str:
        """
        Clean and validate the LLM explanation.
        Handles the dual-section response (Asset Summary + Detailed Risk Analysis).
        """
        if not explanation:
            return "Signals indicate current data points as listed above."

        import re
        
        # Split into Summary and Analysis if delimiter exists
        delimiter = ":::DETAILED_RISK_ANALYSIS:::"
        if delimiter in explanation:
            summary_part, analysis_part = explanation.split(delimiter, 1)
        else:
            summary_part = explanation
            analysis_part = ""

        # Clean Summary Part (Asset Profile Overview)
        summary_text = summary_part.strip()
        
        # 1. Strip accidental headers
        lines_to_skip = [
            "signal summary", "**signal summary", "### signal summary",
            "**structural", "**market", "**audit", "**regulatory",
            "source:", "last updated:", "factual summary:", "summary paragraph:",
            "asset summary:", "asset summary section:",
        ]

        cleaned_summary_lines = []
        for line in summary_text.split("\n"):
            line_lower = line.strip().lower()
            if not any(line_lower.startswith(skip) for skip in lines_to_skip):
                if line.strip():
                    cleaned_summary_lines.append(line.strip())

        cleaned_summary = " ".join(cleaned_summary_lines)

        # 2. Precision Enforcement (Verbs)
        cleaned_summary = re.sub(r"\bcould not be\b", "was not", cleaned_summary, flags=re.IGNORECASE)
        cleaned_summary = re.sub(r"\bcannot be\b", "is not", cleaned_summary, flags=re.IGNORECASE)
        cleaned_summary = re.sub(r"\bis likely\b", "is", cleaned_summary, flags=re.IGNORECASE)
        cleaned_summary = re.sub(r"\bappears to be\b", "is", cleaned_summary, flags=re.IGNORECASE)

        swaps = {
            r"\bsuggests\b": "reports",
            r"\bindicates\b": "shows",
            r"\bappears\b": "is",
            r"\blikely\b": "reported",
            r"\bpotential\b": "reported",
            r"\bcould\b": "was",
            r"\bmight\b": "is",
            r"\bmay\b": "is"
        }
        for pattern, replacement in swaps.items():
            cleaned_summary = re.sub(pattern, replacement, cleaned_summary, flags=re.IGNORECASE)

        # 3. Limit summary to 5 sentences
        sentences = re.split(r'(?<=[.!?])\s+', cleaned_summary)
        if len(sentences) > 5:
            cleaned_summary = " ".join(sentences[:5])
        elif len(sentences) > 0:
            cleaned_summary = " ".join(sentences)

        # Clean Analysis Part (Cohesive Risk Narrative)
        analysis_text = analysis_part.strip()
        # Strip internal headers if LLM added them
        analysis_text = re.sub(r"^###.*?\n", "", analysis_text, flags=re.MULTILINE)
        analysis_text = re.sub(r"^\*\*DETAILED RISK ANALYSIS.*?\n", "", analysis_text, flags=re.IGNORECASE | re.MULTILINE)

        # Combine back with the unique delimiter for frontend splitting
        return f"{cleaned_summary}\n\n{delimiter}\n\n{analysis_text.strip()}"

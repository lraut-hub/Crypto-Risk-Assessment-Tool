"""
Query Router — Intent Classification Layer

Classifies user intent BEFORE any processing begins. Determines whether a
query should proceed to the full pipeline (factual), receive a static refusal
(advisory), or be flagged as out-of-scope.

Uses deterministic keyword + pattern matching — no LLM required.
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class QueryIntent:
    FACTUAL = "factual"
    ADVISORY = "advisory"
    OUT_OF_SCOPE = "out_of_scope"


# ─── Refusal Messages ────────────────────────────────────────────────────────

REFUSAL_MESSAGES = {
    QueryIntent.ADVISORY: (
        "This system provides factual risk signal reports only. "
        "It does not offer investment advice, price predictions, "
        "or buy/sell recommendations."
    ),
    QueryIntent.OUT_OF_SCOPE: (
        "This query is outside the scope of this system. "
        "Please provide a specific token name, ticker symbol, or contract address "
        "for risk signal verification."
    ),
}

# ─── Detection Patterns ──────────────────────────────────────────────────────

# Advisory / investment patterns
ADVISORY_PATTERNS = [
    r"\b(should\s+i\s+(buy|sell|invest|hold))\b",
    r"\b(is\s+it\s+(safe|good|worth)\s+to\s+(buy|invest))\b",
    r"\b(price\s+predict(ion)?|price\s+target)\b",
    r"\b(will\s+(it|this)\s+(go\s+up|moon|pump|dump|crash))\b",
    r"\b(best\s+(crypto|coin|token)\s+to\s+(buy|invest))\b",
    r"\b(when\s+(to|should)\s+(buy|sell))\b",
    r"\b(investment\s+advice)\b",
    r"\b(portfolio\s+(advice|recommendation))\b",
    r"\b(how\s+much\s+(should|can)\s+i\s+invest)\b",
    r"\b(gem|moonshot|100x|1000x)\b",
]

ADVISORY_KEYWORDS = {
    "buy", "sell", "invest", "hold", "hodl", "recommendation",
    "worth buying", "good investment", "financial advice",
    "price prediction", "price target", "potential gains",
}

# Out-of-scope patterns (generic crypto education without a specific asset)
OUT_OF_SCOPE_PATTERNS = [
    r"^(what\s+is\s+(crypto|blockchain|defi|nft|web3|mining))\b",
    r"^(how\s+does\s+(crypto|blockchain|bitcoin\s+mining)\s+work)\b",
    r"^(explain\s+(crypto|blockchain|defi|nft|web3))\b",
    r"\b(teach\s+me|tutorial|guide|course)\b",
    r"^(what\s+are\s+(smart\s+contracts|tokens|altcoins))\b",
]


class QueryRouter:
    """
    Routes queries based on intent classification.
    """

    def __init__(self):
        self._advisory_patterns = [re.compile(p, re.IGNORECASE) for p in ADVISORY_PATTERNS]
        self._out_of_scope_patterns = [re.compile(p, re.IGNORECASE) for p in OUT_OF_SCOPE_PATTERNS]

    def classify(self, query: str) -> Tuple[str, str]:
        """
        Classify the user's query intent.

        Returns:
            (intent: str, message: str)
            - For factual: (QueryIntent.FACTUAL, "")
            - For advisory: (QueryIntent.ADVISORY, refusal_message)
            - For out_of_scope: (QueryIntent.OUT_OF_SCOPE, refusal_message)
        """
        query_lower = query.lower().strip()

        # 1. Check advisory patterns (regex)
        for pattern in self._advisory_patterns:
            if pattern.search(query_lower):
                logger.info(f"QueryRouter: Advisory query detected — '{query[:50]}'")
                return QueryIntent.ADVISORY, REFUSAL_MESSAGES[QueryIntent.ADVISORY]

        # 2. Check advisory keywords
        for keyword in ADVISORY_KEYWORDS:
            if keyword in query_lower:
                logger.info(f"QueryRouter: Advisory keyword '{keyword}' detected")
                return QueryIntent.ADVISORY, REFUSAL_MESSAGES[QueryIntent.ADVISORY]

        # 3. Check out-of-scope patterns
        for pattern in self._out_of_scope_patterns:
            if pattern.search(query_lower):
                # But allow if the query also contains a specific token/address
                has_address = re.search(r"0x[a-fA-F0-9]{40}", query)
                if not has_address and len(query_lower.split()) < 8:
                    logger.info(f"QueryRouter: Out-of-scope query — '{query[:50]}'")
                    return QueryIntent.OUT_OF_SCOPE, REFUSAL_MESSAGES[QueryIntent.OUT_OF_SCOPE]

        # 4. Default: factual query
        logger.info(f"QueryRouter: Factual query — '{query[:50]}'")
        return QueryIntent.FACTUAL, ""

    def is_factual(self, query: str) -> bool:
        """Convenience check for factual queries."""
        intent, _ = self.classify(query)
        return intent == QueryIntent.FACTUAL

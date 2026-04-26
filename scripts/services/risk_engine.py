"""
Risk Engine — Deterministic Signal Computation

Computes deterministic risk signals from raw blockchain, market, audit, and
regulatory data. Signals are computed across 4 independent layers, with each
layer running conditionally based on asset type.

The fixed signal schema ensures all 4 categories are always present in the
aggregated output. Missing data uses explicit fallback values.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import utilities
try:
    from scripts.utils.normalizer import SignalNormalizer
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.normalizer import SignalNormalizer

logger = logging.getLogger(__name__)


# ─── Fallback Constants ──────────────────────────────────────────────────────

STRUCTURAL_NOT_APPLICABLE = "Not applicable for this asset type"
AUDIT_NOT_FOUND = "No audit found"
REGULATORY_CLEAN = "No regulatory warnings found"
MARKET_NO_DATA = "Limited data available"


class RiskEngine:
    """
    Computes deterministic risk signals from raw blockchain and market data.
    Supports conditional layer execution based on asset type.
    """

    def __init__(self):
        self.normalizer = SignalNormalizer()

    # ─── Structural Layer (EVM smart_contract_token ONLY) ─────────────────

    def process_blockchain_signals(
        self,
        creation_data: Dict[str, Any],
        supply_data: str,
        applicable: bool = True,
    ) -> Dict[str, Any]:
        """
        Processes Etherscan data to compute age and concentration signals.
        Returns fallback when structural layer is not applicable.
        """
        if not applicable:
            return {
                "layer": "structural",
                "applicable": False,
                "fallback": STRUCTURAL_NOT_APPLICABLE,
            }

        signals = {
            "layer": "structural",
            "applicable": True,
        }

        # 1. Contract Age
        timestamp = creation_data.get("timestamp")
        if timestamp:
            dt = self.normalizer.parse_etherscan_date(timestamp)
            if dt:
                days_ago = self.normalizer.calculate_days_ago(dt)
                signals["contract_age_days"] = days_ago
                signals["is_new_contract"] = days_ago < 30  # Risk signal for < 1 month
                signals["creation_date"] = dt.isoformat()

        # 2. Supply Metrics
        if supply_data:
            signals["total_supply"] = supply_data
            # In Phase 3, we would also pull top holder data to calculate concentration
            # For now, we set a placeholder for concentration logic
            signals["wallet_concentration_risk"] = "high" if int(supply_data) > 0 else "unknown"

        return signals

    # ─── Market Layer (All assets) ────────────────────────────────────────

    def process_market_signals(
        self,
        market_data: Optional[Dict[str, Any]],
        mode: str = "full",
    ) -> Dict[str, Any]:
        """
        Processes market listing data into legitimacy signals.
        mode: "full" or "limited"
        """
        base = {
            "layer": "market",
            "mode": mode,
        }

        if not market_data:
            return {
                **base,
                "is_listed": False,
                "market_rank": "unknown",
                "fallback": MARKET_NO_DATA,
            }

        return {
            **base,
            "is_listed": market_data.get("is_listed", False),
            "market_rank": market_data.get("market_rank", "unknown"),
            "token_name_found": market_data.get("name"),
            "token_symbol_found": market_data.get("symbol"),
            "market_source": market_data.get("source"),
        }

    # ─── Audit Layer ─────────────────────────────────────────────────────

    def process_audit_signals(
        self,
        audit_results: List[Dict[str, Any]],
        mode: str = "full",
    ) -> Dict[str, Any]:
        """
        Processes audit scraper results into boolean flags.
        mode: "full" or "fallback" (for native assets)
        """
        base = {
            "layer": "audit",
            "mode": mode,
        }

        if mode == "fallback":
            return {
                **base,
                "is_audited": False,
                "audit_providers": [],
                "fallback": "Major native asset — community-audited ecosystem",
            }

        is_audited = any(res.get("status") == "Found" for res in audit_results)
        providers = [res.get("provider") for res in audit_results if res.get("status") == "Found"]

        return {
            **base,
            "is_audited": is_audited,
            "audit_providers": providers,
            "fallback": AUDIT_NOT_FOUND if not is_audited else None,
        }

    # ─── Regulatory Layer ─────────────────────────────────────────────────

    def process_regulatory_signals(
        self,
        regulatory_entries: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Processes regulatory warning data.
        Always runs — regulatory checks apply to all asset types.
        """
        return {
            "layer": "regulatory",
            "warning_count": len(regulatory_entries),
            "warnings": regulatory_entries,
            "fallback": REGULATORY_CLEAN if not regulatory_entries else None,
        }

    # ─── Aggregation ─────────────────────────────────────────────────────

    def aggregate_all_signals(
        self,
        blockchain: Dict,
        market: Dict,
        audits: Dict,
        regulatory: List[Dict],
    ) -> Dict[str, Any]:
        """
        Combines all signals into a single flat metadata-rich dictionary for ChromaDB.
        Ensures all 4 categories are always present with explicit values.
        """
        # Process regulatory into structured format
        reg_signals = self.process_regulatory_signals(regulatory)

        # Flatten signals into a single dictionary
        flat_signals = {
            # Structural
            "structural_applicable": blockchain.get("applicable", True),
            "contract_age_days": blockchain.get("contract_age_days"),
            "is_new_contract": blockchain.get("is_new_contract"),
            "creation_date": blockchain.get("creation_date"),
            "total_supply": blockchain.get("total_supply"),
            "wallet_concentration_risk": blockchain.get("wallet_concentration_risk"),

            # Market
            "is_listed": market.get("is_listed", False),
            "market_rank": market.get("market_rank", "unknown"),
            "token_name_found": market.get("token_name_found"),
            "token_symbol_found": market.get("token_symbol_found"),
            "market_source": market.get("market_source"),

            # Audit
            "is_audited": audits.get("is_audited", False),
            "audit_providers": audits.get("audit_providers", []),

            # Regulatory
            "regulatory_warning_count": reg_signals.get("warning_count", 0),

            # Metadata
            "last_computed_at": datetime.utcnow().isoformat(),
        }

        # Ensure all types are ChromaDB-compatible (no dicts or lists)
        final_metadata = {}
        for k, v in flat_signals.items():
            if v is None:
                final_metadata[k] = "unknown"
            elif isinstance(v, (dict, list)):
                final_metadata[k] = str(v)
            else:
                final_metadata[k] = v

        return final_metadata

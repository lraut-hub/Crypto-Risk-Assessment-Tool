"""
Signal Normalizer + Fallback Handler — Consistency Layer

Converts raw API/scrape data into human-readable, standardized signals.
Ensures every response includes all 4 signal categories (Structural, Market,
Audit, Regulatory) with explicit fallback values when data is unavailable.

The system NEVER returns empty or vague outputs.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


# ─── Fallback Constants ───────────────────────────────────────────────────────

FALLBACKS = {
    "structural_not_applicable": "Not applicable for this asset type",
    "structural_no_data": "Limited data available",
    "market_no_data": "Limited data available",
    "market_not_listed": "Asset not found or not indexed",
    "audit_not_found": "No audit found",
    "regulatory_clean": "No regulatory warnings found",
    "general_limited": "Limited data available",
    "unresolved": "Asset not found or not indexed",
}


class NormalizedSignals:
    """
    Container for the fixed signal schema.
    No category is ever omitted.
    """

    def __init__(self):
        self.asset_type: str = "Unknown"
        self.data_coverage: str = "Limited"
        
        # Asset Profile Metadata
        self.asset_id: str = "N/A"
        self.contract_address: str = "N/A"
        self.market_cap: str = "N/A"
        self.rank: str = "N/A"
        self.exchange_count: str = "0"

        self.structural: List[str] = []
        self.market: List[str] = []
        self.audit: List[str] = []
        self.regulatory: List[str] = []
        self.source_url: Optional[str] = None
        self.last_updated: str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_type": self.asset_type,
            "data_coverage": self.data_coverage,
            "asset_id": self.asset_id,
            "contract_address": self.contract_address,
            "market_cap": self.market_cap,
            "rank": self.rank,
            "exchange_count": self.exchange_count,
            "structural": self.structural,
            "market": self.market,
            "audit": self.audit,
            "regulatory": self.regulatory,
            "source_url": self.source_url,
            "last_updated": self.last_updated,
        }

    def has_adverse_signals(self) -> bool:
        """Check if any non-neutral/non-fallback signals indicate risk."""
        risk_keywords = [
            "warning", "alert", "recently deployed", "high wallet concentration",
            "no audit found", "not found on coingecko", "detected",
        ]
        all_signals = self.structural + self.market + self.audit + self.regulatory
        for signal in all_signals:
            if any(kw in signal.lower() for kw in risk_keywords):
                return True
        return False


class SignalNormalizer:
    """
    Normalizes raw signal data into standardized human-readable strings
    and applies graceful fallback logic for missing data.
    """

    # ─── Asset Type Normalization ──────────────────────────────────────────

    def normalize_asset_type(self, chain: Optional[str], has_contract: bool) -> str:
        """Classify as Native blockchain asset or Smart contract token."""
        if has_contract:
            return "Smart contract token"
        return "Native blockchain asset"

    # ─── Data Coverage Normalization ───────────────────────────────────────

    def normalize_data_coverage(
        self, 
        market_data: Optional[Dict[str, Any]], 
        blockchain_data: Optional[Dict[str, Any]],
        is_token: bool
    ) -> str:
        """Calculate data coverage score based on field availability."""
        fields = 0
        total = 0
        
        # Market fields
        if market_data:
            total += 3
            if market_data.get("market_cap"): fields += 1
            if market_data.get("market_cap_rank"): fields += 1
            if market_data.get("exchange_count", 0) > 0: fields += 1
        
        # Structural fields
        if is_token:
            total += 2
            if blockchain_data:
                if blockchain_data.get("contract_age_days"): fields += 1
                if blockchain_data.get("wallet_concentration_pct"): fields += 1
        
        percentage = (fields / total) if total > 0 else 0
        if percentage > 0.8: return "High"
        if percentage > 0.4: return "Partial"
        return "Limited"

    # ─── Structural Signal Normalization ──────────────────────────────────

    def normalize_structural(
        self,
        blockchain_data: Optional[Dict[str, Any]],
        is_applicable: bool,
    ) -> List[str]:
        """
        Normalize blockchain/structural signals.
        Returns fallback if structural layer is not applicable (native assets).
        """
        if not is_applicable:
            return [FALLBACKS["structural_not_applicable"]]

        if not blockchain_data:
            return [FALLBACKS["structural_no_data"]]

        signals = []

        # Contract age
        age_days = blockchain_data.get("contract_age_days")
        if age_days is not None:
            signals.append(f"Contract Age: {age_days} days")
        else:
            signals.append("Contract age was not determined")

        # Wallet concentration
        concentration_pct = blockchain_data.get("wallet_concentration_pct")
        if concentration_pct is not None:
            signals.append(f"Wallet Concentration: {int(concentration_pct * 100)}% in top wallets")
        else:
            signals.append("Wallet concentration data not available")

        # Supply
        total_supply = blockchain_data.get("total_supply")
        if total_supply and total_supply != "0":
            signals.append(f"Total Supply: {total_supply}")

        # --- GO PLUS SECURITY SIGNALS ---
        if blockchain_data.get("is_honeypot"):
            signals.append("🚨 SECURITY ALERT: Honeypot Detected (Cannot Sell)")
        
        if blockchain_data.get("cannot_sell_all"):
            signals.append("⚠️ SELL LIMIT: Predatory sell limits detected")

        mintable = blockchain_data.get("is_mintable")
        if mintable is not None:
            signals.append(f"Minting Authority: {'⚠️ Enabled (Inflation Risk)' if mintable else '✅ Disabled'}")
            
        if blockchain_data.get("is_proxy"):
            signals.append("Contract Structure: ⚠️ Proxy/Upgradable (Admin can change logic)")

        if blockchain_data.get("transfer_pausable"):
            signals.append("Trading Control: ⚠️ Pausable (Owner can stop trading)")

        is_open_source = blockchain_data.get("is_open_source")
        if is_open_source is not None:
            signals.append(f"Source Code: {'✅ Verified' if is_open_source else '🚨 Unverified (High Risk)'}")

        buy_tax = blockchain_data.get("buy_tax", "0")
        sell_tax = blockchain_data.get("sell_tax", "0")
        try:
            b_tax = float(buy_tax)
            s_tax = float(sell_tax)
            if b_tax > 5 or s_tax > 5:
                signals.append(f"⚠️ PREDATORY TAX: Buy {buy_tax}% | Sell {sell_tax}% (>5% threshold)")
            else:
                signals.append(f"Trading Tax: Buy {buy_tax}% | Sell {sell_tax}%")
        except:
            signals.append(f"Trading Tax: Buy {buy_tax}% | Sell {sell_tax}%")

        return signals if signals else [FALLBACKS["structural_no_data"]]

    # ─── Market Signal Normalization ──────────────────────────────────────

    def normalize_market(
        self,
        market_data: Optional[Dict[str, Any]],
        mode: str = "full",
    ) -> List[str]:
        """
        Normalize market listing and maturity signals using NUMERIC DATA ONLY.
        """
        if not market_data:
            return [FALLBACKS["market_no_data"]]

        signals = []
        is_listed = market_data.get("is_listed", False) or market_data.get("resolved", False)
        
        if is_listed:
            # Market Cap (Numeric)
            mcap = market_data.get("market_cap")
            if mcap and mcap > 0:
                signals.append(f"Market Cap: ${mcap:,.0f}")
            else:
                signals.append("Market Cap: Data unavailable")

            # Rank (Numeric)
            rank = market_data.get("market_cap_rank") or market_data.get("market_rank")
            if rank and str(rank).isdigit():
                signals.append(f"Rank: #{rank}")
            else:
                signals.append("Rank: Unranked")

            # Exchanges (Numeric)
            exchange_count = market_data.get("exchange_count", 0)
            if exchange_count > 0:
                signals.append(f"Exchange Listings: {exchange_count}")
            else:
                signals.append("Exchange Listings: 0")
        else:
            signals.append(FALLBACKS["market_not_listed"])

        return signals if signals else [FALLBACKS["market_no_data"]]

    # ─── Audit Signal Normalization ───────────────────────────────────────

    def normalize_audit(
        self,
        audit_data: Optional[Dict[str, Any]],
        mode: str = "full",
    ) -> List[str]:
        """
        Standardizes audit status into a deterministic one-liner.
        Expected Output: 
        - "Audit found (CertiK)"
        - "Audit found (Hacken)"
        - "No audit found in indexed sources"
        """
        from backend.services.audit_detector import AuditDetector
        
        # We pass only the audit_data currently. 
        # Future enhancement: pass homepage/links for real-time detection.
        status = AuditDetector.detect(audit_data=audit_data)
        return [status]

    # ─── Regulatory Signal Normalization ──────────────────────────────────

    def normalize_regulatory(
        self,
        regulatory_data: Optional[List[Dict[str, Any]]],
        warning_count: int = 0,
    ) -> List[str]:
        """
        Normalize regulatory warning signals.
        """
        if not regulatory_data and warning_count == 0:
            return [FALLBACKS["regulatory_clean"]]

        signals = []

        if regulatory_data:
            for entry in regulatory_data:
                source = entry.get("source", "Unknown")
                entity = entry.get("entity_name", "")
                reason = entry.get("reason", "")

                if entity or reason:
                    detail = f"{entity}: {reason}".strip(": ")
                    signals.append(f"{source} warning detected — {detail}")
                else:
                    signals.append(f"{source} warning detected")

        if warning_count > 0 and not signals:
            signals.append(f"{warning_count} regulatory warning(s) found")

        return signals if signals else [FALLBACKS["regulatory_clean"]]

    # ─── Full Normalization ───────────────────────────────────────────────

    def normalize_all(
        self,
        blockchain_data: Optional[Dict[str, Any]],
        market_data: Optional[Dict[str, Any]],
        audit_data: Optional[Dict[str, Any]],
        regulatory_data: Optional[List[Dict[str, Any]]],
        structural_applicable: bool = True,
        audit_mode: str = "full",
        market_mode: str = "full",
        warning_count: int = 0,
        source_url: Optional[str] = None,
        chain: Optional[str] = None,
        has_contract: bool = False,
        asset_metadata: Optional[Dict[str, Any]] = None,
    ) -> NormalizedSignals:
        """
        Normalize all signal layers into a complete NormalizedSignals object.
        Guarantees all mandatory categories are always populated.
        """
        result = NormalizedSignals()

        result.asset_type = self.normalize_asset_type(chain, has_contract)
        result.data_coverage = self.normalize_data_coverage(market_data, blockchain_data, has_contract)
        
        # Populate Asset Profile metadata
        if asset_metadata:
            result.asset_id = asset_metadata.get("asset_id", "N/A")
            result.contract_address = asset_metadata.get("contract_address", "N/A")
        
        if market_data:
            mcap = market_data.get("market_cap")
            result.market_cap = f"${mcap:,.0f}" if mcap and mcap > 0 else "N/A"
            rank = market_data.get("market_cap_rank") or market_data.get("market_rank")
            result.rank = f"#{rank}" if rank else "Unranked"
            result.exchange_count = str(market_data.get("exchange_count", "0"))

        result.structural = self.normalize_structural(blockchain_data, structural_applicable)
        result.market = self.normalize_market(market_data, market_mode)
        result.audit = self.normalize_audit(audit_data, audit_mode)
        result.regulatory = self.normalize_regulatory(regulatory_data, warning_count)
        result.source_url = source_url

        logger.info(
            f"SignalNormalizer: Normalized signals — type='{result.asset_type}', coverage='{result.data_coverage}'"
        )

        return result

import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GoPlusService:
    """
    Universal Security API Service using GoPlus.
    Provides multi-chain security signals (EVM + Solana).
    """
    
    BASE_URL = "https://api.gopluslabs.io/api/v1"
    
    # Map of common chain names to GoPlus Chain IDs
    CHAIN_MAP = {
        "ethereum": "1",
        "binance-smart-chain": "56",
        "bsc": "56",
        "polygon-pos": "137",
        "polygon": "137",
        "arbitrum-one": "42161",
        "optimistic-ethereum": "10",
        "base": "8453",
        "avalanche": "43114",
        "fantom": "250",
        "solana": "solana"
    }

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_token_security(self, chain_name: str, address: str) -> Optional[Dict[str, Any]]:
        """
        Fetch security data for a specific contract on a specific chain.
        """
        chain_id = self.CHAIN_MAP.get(chain_name.lower())
        
        if not chain_id:
            logger.warning(f"GoPlus: Chain '{chain_name}' not supported by GoPlus.")
            return None

        try:
            if chain_id == "solana":
                url = f"{self.BASE_URL}/solana/token_security?contract_addresses={address}"
            else:
                url = f"{self.BASE_URL}/token_security/{chain_id}?contract_addresses={address}"
            
            logger.info(f"GoPlus: Fetching security data for {address} on {chain_name} ({chain_id})")
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 1: # Success
                    # GoPlus returns a dict with address as key
                    result = data.get("result", {})
                    return result.get(address) or result.get(address.lower())
                else:
                    logger.warning(f"GoPlus API error: {data.get('message')}")
            else:
                logger.error(f"GoPlus HTTP error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"GoPlus: Exception during fetch: {str(e)}")
        
        return None

    def extract_signals(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize raw GoPlus data into our deterministic risk signals.
        Ensures values are ChromaDB compatible (no None values).
        """
        if not raw_data:
            return {}

        signals = {
            "is_audited": False,
            "audit_provider": "",
            "is_honeypot": raw_data.get("is_honeypot") == "1",
            "is_mintable": raw_data.get("is_mintable") == "1",
            "is_proxy": raw_data.get("is_proxy") == "1",
            "is_open_source": raw_data.get("is_open_source") == "1",
            "transfer_pausable": raw_data.get("transfer_pausable") == "1",
            "cannot_sell_all": raw_data.get("cannot_sell_all") == "1",
            "creator_percent": str(raw_data.get("creator_percent") or "0"),
            "can_take_back_ownership": raw_data.get("can_take_back_ownership") == "1",
            "owner_address": str(raw_data.get("owner_address") or ""),
            "buy_tax": str(raw_data.get("buy_tax") or "0"),
            "sell_tax": str(raw_data.get("sell_tax") or "0"),
        }

        # Handle Trust/Audit info
        if raw_data.get("trust_list") == "1":
            signals["is_audited"] = True
            signals["audit_provider"] = "Verified/Trusted"

        return signals

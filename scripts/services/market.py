"""
CoinGecko Market Service (Scripts Layer) — Free API, No Key Required

Used by the data refresh pipeline (scripts/main_refresh.py) to fetch
market intelligence about tokens during scheduled ingestion runs.

Uses free CoinGecko endpoints — no API key needed.
"""

import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Import our utility client
try:
    from scripts.utils.client import RateLimitedClient
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.client import RateLimitedClient

load_dotenv()
logger = logging.getLogger(__name__)


class CoinGeckoService:
    """
    Service for interacting with CoinGecko free API to fetch market signals.
    No API key required — uses public endpoints only.
    """
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        # No API key — free public endpoints
        self.client = RateLimitedClient(rate_limit_ms=1500)  # CoinGecko free tier: ~10-30 calls/min

    async def get_token_by_address(self, address: str, platform: str = "ethereum") -> Optional[Dict[str, Any]]:
        """
        Fetches token data from CoinGecko using the contract address.
        Endpoint: /coins/{platform}/contract/{address}
        """
        url = f"{self.BASE_URL}/coins/{platform}/contract/{address}"
        response = await self.client.get(url)
        if response:
            data = response.json()
            return {
                "id": data.get("id"),
                "name": data.get("name"),
                "symbol": data.get("symbol"),
                "is_listed": True,
                "market_cap_rank": data.get("market_cap_rank"),
                "source": "CoinGecko"
            }
        return None

    async def verify_listing_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Search for a token by ticker using /search endpoint.
        No API key needed.
        """
        url = f"{self.BASE_URL}/search"
        params = {"query": ticker}
        response = await self.client.get(url, params=params)
        if response:
            data = response.json()
            coins = data.get("coins", [])

            # Priority: exact symbol match
            for coin in coins:
                if coin["symbol"].lower() == ticker.lower():
                    return {
                        "id": coin.get("id"),
                        "name": coin.get("name"),
                        "symbol": coin.get("symbol"),
                        "is_listed": True,
                        "market_rank": coin.get("market_cap_rank"),
                        "source": "CoinGecko"
                    }

            # Fallback: first ranked result
            ranked = [c for c in coins if c.get("market_cap_rank")]
            if ranked:
                best = min(ranked, key=lambda c: c["market_cap_rank"])
                return {
                    "id": best.get("id"),
                    "name": best.get("name"),
                    "symbol": best.get("symbol"),
                    "is_listed": True,
                    "market_rank": best.get("market_cap_rank"),
                    "source": "CoinGecko"
                }

        return {"is_listed": False, "source": "CoinGecko"}

    async def close(self):
        await self.client.close()

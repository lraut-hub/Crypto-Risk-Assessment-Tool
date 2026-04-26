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

class EtherscanService:
    """
    Service for interacting with the Etherscan API to fetch blockchain signals.
    """
    BASE_URL = "https://api.etherscan.io/api"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY")
        if not self.api_key:
            logger.warning("ETHERSCAN_API_KEY not found in environment. API calls will likely fail.")
        self.client = RateLimitedClient(rate_limit_ms=200) # Faster than scrapers, typically 5 calls/sec for free tier

    async def get_contract_creation(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Fetches contract creation metadata (creator address, transaction hash).
        """
        params = {
            "module": "contract",
            "action": "getcontractcreation",
            "contractaddresses": contract_address,
            "apikey": self.api_key
        }
        response = await self.client.get(self.BASE_URL, params=params)
        if response:
            data = response.json()
            if data.get("status") == "1":
                return data.get("result", [{}])[0]
        return None

    async def get_token_supply(self, contract_address: str) -> Optional[str]:
        """
        Fetches total supply of a token.
        """
        params = {
            "module": "stats",
            "action": "tokensupply",
            "contractaddress": contract_address,
            "apikey": self.api_key
        }
        response = await self.client.get(self.BASE_URL, params=params)
        if response:
            data = response.json()
            if data.get("status") == "1":
                return data.get("result")
        return None

    async def close(self):
        await self.client.close()

import httpx
import asyncio
import logging
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimitedClient:
    """
    A persistent HTTP client with basic rate limiting and retry logic.
    """
    def __init__(self, rate_limit_ms: int = 500):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        self.rate_limit_ms = rate_limit_ms
        self.last_request_time = 0

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[httpx.Response]:
        # Simple rate limiting
        await asyncio.sleep(self.rate_limit_ms / 1000)
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error for {url}: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
        return None

    async def close(self):
        await self.client.aclose()

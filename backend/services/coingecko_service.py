"""
CoinGecko Service — Free API Integration (No API Key)

Uses only two CoinGecko endpoints (no API key required):
  1. /api/v3/search?query={input}  → Identity resolution (map input → token ID)
  2. /api/v3/coins/{id}            → Core data (full token details)

Fields extracted from /coins/{id}:
  - id → canonical asset_id
  - symbol, name
  - platforms → chain + contract address mapping
  - market_data.market_cap → market maturity signal
  - market_data.total_volume → trading activity signal
  - links.homepage → project homepage
  - tickers → exchange listing presence

Rule: No API keys, no SDKs, no HTML scraping. Direct HTTP only.
"""

import httpx
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Rate limit: CoinGecko free tier allows ~10-30 calls/min
REQUEST_TIMEOUT = 30.0


class CoinGeckoService:
    """
    CoinGecko API wrapper using free public endpoints only.
    No API key required.
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        # No API key headers — free public endpoints
        self.headers = {
            "accept": "application/json",
        }
        logger.info("CoinGeckoService initialized (free endpoints, no API key)")

    # ─── Endpoint 1: Search (Identity Resolution) ────────────────────────

    async def search(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search CoinGecko to resolve user input → token ID.
        
        Endpoint: /api/v3/search?query={input}
        
        Returns the best matching coin entry, or None.
        Selection priority: exact symbol match → highest market_cap_rank.
        """
        url = f"{self.BASE_URL}/search"
        params = {"query": query}

        # --- NOISE FILTER: Ignore single-character searches ---
        if len(query.strip()) < 2:
            logger.info(f"CoinGecko search: Ignoring single-character query '{query}'")
            return None

        try:
            import difflib
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.get(url, params=params, headers=self.headers)

                if response.status_code == 200:
                    data = response.json()
                    coins = data.get("coins", [])

                    if not coins:
                        # --- RETRY: Try correcting common typos ---
                        # Remove repeated trailing characters (e.g., "Bitcoinn" → "Bitcoin")
                        import re as _re
                        cleaned = _re.sub(r'(.)\1+$', r'\1', query)
                        if cleaned != query and len(cleaned) >= 3:
                            logger.info(f"CoinGecko search: Retrying with cleaned query '{cleaned}' (was '{query}')")
                            retry_resp = await client.get(url, params={"query": cleaned}, headers=self.headers)
                            if retry_resp.status_code == 200:
                                retry_data = retry_resp.json()
                                coins = retry_data.get("coins", [])
                        
                        # If still no results, try trimming last char (e.g., "Ethereumm" → "Ethereum")
                        if not coins and len(query) >= 4:
                            trimmed = query[:-1]
                            if trimmed != cleaned:
                                logger.info(f"CoinGecko search: Retrying with trimmed query '{trimmed}'")
                                retry_resp = await client.get(url, params={"query": trimmed}, headers=self.headers)
                                if retry_resp.status_code == 200:
                                    retry_data = retry_resp.json()
                                    coins = retry_data.get("coins", [])

                        if not coins:
                            logger.info(f"CoinGecko search: No results for '{query}' (even after corrections)")
                            return None

                    # --- PHASE 1: EXACT MATCHES (Tickers & Full Names) ---
                    for coin in coins:
                        symbol = coin.get("symbol", "").lower()
                        name = coin.get("name", "").lower()
                        q_lower = query.lower()
                        
                        # Direct hit on ticker (e.g., "BTC") or Name (e.g., "Bitcoin")
                        if symbol == q_lower or name == q_lower:
                            logger.info(f"CoinGecko search: Exact match found for '{query}' → {coin['id']}")
                            return coin

                    # --- PHASE 2: SMART ALIASES (Word Subsets) ---
                    for coin in coins:
                        name_words = coin.get("name", "").lower().split()
                        q_lower = query.lower()
                        if q_lower in name_words:
                            # Rank Guard for short aliases
                            rank = coin.get("market_cap_rank")
                            if len(q_lower) <= 3 and (not rank or rank > 1000):
                                logger.info(f"CoinGecko search: Rejecting short alias '{query}' for low-rank token {coin['id']}")
                                continue
                                
                            logger.info(f"CoinGecko search: Alias match found ('{query}' in '{coin['name']}') → {coin['id']}")
                            return coin

                    # --- PHASE 3: FUZZY MATCHING (Typo Protection) ---
                    best_candidate = None
                    highest_score = 0

                    for coin in coins:
                        name = coin.get("name", "").lower()
                        symbol = coin.get("symbol", "").lower()
                        q_lower = query.lower()
                        
                        name_score = difflib.SequenceMatcher(None, q_lower, name).ratio()
                        symbol_score = difflib.SequenceMatcher(None, q_lower, symbol).ratio()
                        score = max(name_score, symbol_score)
                        
                        if score > highest_score:
                            highest_score = score
                            best_candidate = coin

                    if best_candidate and highest_score >= 0.85:
                        # Rank Guard for fuzzy matches on short queries
                        rank = best_candidate.get("market_cap_rank")
                        if len(query) <= 3 and (not rank or rank > 1000):
                            logger.info(f"CoinGecko search: Rejecting fuzzy match for short query '{query}' (Rank #{rank})")
                            return None
                            
                        logger.info(f"CoinGecko search: High confidence fuzzy match ({highest_score:.2f}) → {best_candidate['id']}")
                        return best_candidate
                    
                    logger.warning(f"CoinGecko search: Low confidence match ({highest_score:.2f} for '{query}'). Rejecting.")
                    return None

                elif response.status_code == 429:
                    logger.warning("CoinGecko search: Rate limited (429)")
                    return None
                else:
                    logger.error(f"CoinGecko search error: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"CoinGecko search failed: {e}")
            return None

    # ─── Endpoint 2: Coin Details (Core Data) ────────────────────────────

    async def get_coin_info(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full token details after ID is resolved.
        
        Endpoint: /api/v3/coins/{id}
        
        Extracts: id, symbol, name, platforms, market_data, links, tickers.
        """
        url = f"{self.BASE_URL}/coins/{coin_id}"

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.get(url, headers=self.headers)

                if response.status_code == 200:
                    raw = response.json()
                    return self._extract_fields(raw)

                elif response.status_code == 404:
                    logger.warning(f"CoinGecko coin info: '{coin_id}' not found (404)")
                    return None
                elif response.status_code == 429:
                    logger.warning("CoinGecko coin info: Rate limited (429)")
                    return None
                else:
                    logger.error(f"CoinGecko coin info error: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"CoinGecko coin info failed: {e}")
            return None

    # ─── Combined: Search → Get Details ──────────────────────────────────

    async def resolve_token(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Full resolution flow: search for token → get full details.
        
        This is the primary method used by the Entity Resolver.
        
        Steps:
          1. Call /search?query={input} → get token ID
          2. Call /coins/{id} → get full details
          3. Return enriched data or None
        """
        # Step 1: Search
        search_result = await self.search(user_input)
        if not search_result:
            return None

        coin_id = search_result.get("id")
        if not coin_id:
            return None

        # Step 2: Get full details
        coin_data = await self.get_coin_info(coin_id)
        return coin_data

    # ─── Legacy compatibility: address-based lookup ──────────────────────

    async def get_token_by_address(self, address: str, platform: str = "ethereum") -> Optional[Dict[str, Any]]:
        """
        Lookup a token by contract address on a specific platform.
        Uses: /api/v3/coins/{platform}/contract/{address}
        
        Note: This is a third endpoint but necessary for address-based
        resolution since /search doesn't accept contract addresses.
        """
        url = f"{self.BASE_URL}/coins/{platform}/contract/{address}"

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.get(url, headers=self.headers)

                if response.status_code == 200:
                    raw = response.json()
                    return self._extract_fields(raw)
                elif response.status_code == 404:
                    logger.warning(f"CoinGecko: Token at {address} not found on {platform}")
                    return None
                else:
                    logger.error(f"CoinGecko contract lookup error: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"CoinGecko contract lookup failed: {e}")
            return None

    # ─── Legacy compatibility: ticker search ─────────────────────────────

    async def get_token_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Legacy wrapper: search by ticker → get full coin info.
        Delegates to resolve_token().
        """
        return await self.resolve_token(ticker)

    # ─── Field Extraction ────────────────────────────────────────────────

    def _extract_fields(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the required fields from a /coins/{id} response.
        
        Required fields:
          - id, symbol, name
          - platforms → chain + contract
          - market_data.market_cap, market_data.total_volume
          - links.homepage
          - tickers → exchange count
        """
        # Market data extraction
        market_data = raw.get("market_data", {})
        market_cap_usd = None
        total_volume_usd = None

        if market_data:
            market_cap_obj = market_data.get("market_cap", {})
            if isinstance(market_cap_obj, dict):
                market_cap_usd = market_cap_obj.get("usd")
            elif isinstance(market_cap_obj, (int, float)):
                market_cap_usd = market_cap_obj

            volume_obj = market_data.get("total_volume", {})
            if isinstance(volume_obj, dict):
                total_volume_usd = volume_obj.get("usd")
            elif isinstance(volume_obj, (int, float)):
                total_volume_usd = volume_obj

        # Homepage extraction
        links = raw.get("links", {})
        homepage_list = links.get("homepage", [])
        homepage = homepage_list[0] if homepage_list and homepage_list[0] else None

        # Tickers → exchange count
        tickers = raw.get("tickers", [])
        exchange_count = len(tickers)

        # Platforms
        platforms = raw.get("platforms", {})
        # Clean empty platform entries
        platforms = {k: v for k, v in platforms.items() if v} if platforms else {}

        # Market presence derivation
        market_presence = self._derive_market_presence(
            market_cap_usd, exchange_count, raw.get("market_cap_rank")
        )

        return {
            "id": raw.get("id"),
            "symbol": raw.get("symbol"),
            "name": raw.get("name"),
            "platforms": platforms,
            "asset_platform_id": raw.get("asset_platform_id"),
            "market_cap_rank": raw.get("market_cap_rank"),
            "market_cap": market_cap_usd,
            "total_volume": total_volume_usd,
            "homepage": homepage,
            "exchange_count": exchange_count,
            "market_presence": market_presence,
        }

    def _derive_market_presence(
        self,
        market_cap: Optional[float],
        exchange_count: int,
        market_cap_rank: Optional[int],
    ) -> str:
        """
        Derive a human-readable market presence label.
        """
        if market_cap_rank and market_cap_rank <= 100:
            return "Established"
        elif market_cap_rank and market_cap_rank <= 500:
            return "Mid-tier"
        elif market_cap and market_cap > 10_000_000:  # > $10M
            return "Active"
        elif exchange_count >= 5:
            return "Listed"
        elif exchange_count >= 1:
            return "Limited"
        else:
            return "Minimal"

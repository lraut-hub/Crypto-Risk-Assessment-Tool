"""
Entity Resolver — Identity-First Processing Layer

Mandatory entry point for all queries. Resolves user input (name, ticker, or
contract address) into a canonical asset object via CoinGecko free endpoints.

Resolution flow:
  1. For addresses (0x...) → CoinGecko contract lookup
  2. For names/tickers → CoinGecko /search → /coins/{id}

The canonical asset object is the single source of truth for all downstream
processing (asset classification, signal computation, retrieval, explanation).

CoinGecko Integration: Free endpoints only, no API key required.
"""

import re
import logging
from typing import Optional, Dict, Any
from services.coingecko_service import CoinGeckoService

logger = logging.getLogger(__name__)

# Known EVM-compatible chain identifiers from CoinGecko platforms
EVM_CHAINS = {
    "ethereum", "polygon-pos", "binance-smart-chain", "avalanche",
    "arbitrum-one", "optimistic-ethereum", "fantom", "base",
    "cronos", "gnosis", "celo", "harmony-shard-0", "moonbeam",
    "moonriver", "aurora", "boba", "metis-andromeda", "zksync",
}


class CanonicalAsset:
    """
    Represents a fully resolved asset identity.
    Acts as the single source of truth for all downstream components.
    
    Enhanced fields (from improvements.md):
      - market_cap, total_volume: from market_data
      - homepage: from links.homepage
      - exchange_count: count of tickers entries
      - market_presence: derived label (Established/Mid-tier/Active/Limited/Minimal)
    """

    def __init__(
        self,
        asset_id: Optional[str] = None,
        name: Optional[str] = None,
        symbol: Optional[str] = None,
        chain: Optional[str] = None,
        contract_address: Optional[str] = None,
        platforms: Optional[Dict[str, str]] = None,
        market_cap_rank: Optional[int] = None,
        market_cap: Optional[float] = None,
        total_volume: Optional[float] = None,
        homepage: Optional[str] = None,
        exchange_count: int = 0,
        market_presence: str = "Minimal",
        resolved: bool = False,
        raw_input: str = "",
    ):
        self.asset_id = asset_id
        self.name = name
        self.symbol = symbol
        self.chain = chain
        self.contract_address = contract_address
        self.platforms = platforms or {}
        self.market_cap_rank = market_cap_rank
        self.market_cap = market_cap
        self.total_volume = total_volume
        self.homepage = homepage
        self.exchange_count = exchange_count
        self.market_presence = market_presence
        self.resolved = resolved
        self.raw_input = raw_input

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "symbol": self.symbol,
            "chain": self.chain,
            "contract_address": self.contract_address,
            "platforms": self.platforms,
            "market_cap_rank": self.market_cap_rank,
            "market_cap": self.market_cap,
            "total_volume": self.total_volume,
            "homepage": self.homepage,
            "exchange_count": self.exchange_count,
            "market_presence": self.market_presence,
            "resolved": self.resolved,
            "raw_input": self.raw_input,
        }

    def __repr__(self):
        status = "✓ Resolved" if self.resolved else "✗ Unresolved"
        return f"CanonicalAsset({status}: {self.name or self.raw_input})"


class EntityResolver:
    """
    Resolves user input into a CanonicalAsset using CoinGecko free
    public endpoints as the identity authority.
    
    Supports: address lookup, ticker search, and name search.
    No API key required.
    """

    ADDRESS_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")

    def __init__(self):
        self.coingecko = CoinGeckoService()

    def _is_address(self, query: str) -> bool:
        """Check if the input looks like an EVM contract address."""
        return bool(self.ADDRESS_PATTERN.match(query.strip()))

    def _extract_address(self, query: str) -> Optional[str]:
        """Extract an EVM address from a longer query string."""
        match = re.search(r"0x[a-fA-F0-9]{40}", query)
        return match.group(0) if match else None

    def _detect_evm_chain(self, platforms: Dict[str, str]) -> Optional[str]:
        """Find the primary EVM chain from CoinGecko platform data."""
        for chain in ["ethereum", "binance-smart-chain", "polygon-pos",
                       "arbitrum-one", "optimistic-ethereum", "base",
                       "avalanche", "fantom"]:
            if chain in platforms and platforms[chain]:
                return chain
        # Check any remaining EVM chain
        for chain, addr in platforms.items():
            if chain in EVM_CHAINS and addr:
                return chain
        return None

    async def resolve(self, user_input: str) -> CanonicalAsset:
        """
        Main resolution method. Accepts any user input and attempts
        to resolve it into a canonical asset object.

        Resolution priority:
        1. Contract address → CoinGecko contract lookup
        2. Ticker/name → CoinGecko /search → /coins/{id}
        """
        query = user_input.strip()
        logger.info(f"EntityResolver: Resolving input '{query}'")

        # Try extracting an address from the query
        address = self._extract_address(query)

        if address:
            return await self._resolve_by_address(address, query)
        else:
            return await self._resolve_by_name_or_ticker(query)

    async def _resolve_by_address(self, address: str, raw_input: str) -> CanonicalAsset:
        """Resolve using CoinGecko contract lookup (Ethereum first)."""
        logger.info(f"EntityResolver: Attempting address resolution for {address}")

        # Try Ethereum first (most common), then other EVM chains
        chains_to_try = ["ethereum", "binance-smart-chain", "polygon-pos",
                         "arbitrum-one", "avalanche", "base"]

        for platform in chains_to_try:
            data = await self.coingecko.get_token_by_address(address, platform=platform)
            if data:
                return self._build_from_coin_data(data, raw_input, address, platform)

        # Not found on CoinGecko — return unresolved with address info
        logger.warning(f"EntityResolver: Address {address} not found on CoinGecko")
        return CanonicalAsset(
            contract_address=address,
            chain="ethereum",  # Assume ethereum for Etherscan fallback
            resolved=False,
            raw_input=raw_input,
        )

    async def _resolve_by_name_or_ticker(self, query: str) -> CanonicalAsset:
        """
        Resolve using the two-step CoinGecko flow:
          1. /search?query={input} → get token ID
          2. /coins/{id} → get full details
        """
        logger.info(f"EntityResolver: Attempting name/ticker resolution for '{query}'")

        # Use the combined search → get_coin_info flow
        data = await self.coingecko.resolve_token(query)
        if data:
            return self._build_from_coin_data(data, query)

        # If combined flow failed, try direct coin ID lookup (e.g., "bitcoin")
        data = await self.coingecko.get_coin_info(query.lower().replace(" ", "-"))
        if data:
            return self._build_from_coin_data(data, query)

        # Not found
        logger.warning(f"EntityResolver: '{query}' not found on CoinGecko")
        return CanonicalAsset(
            name=query,
            resolved=False,
            raw_input=query,
        )

    def _build_from_coin_data(
        self,
        data: Dict[str, Any],
        raw_input: str,
        known_address: Optional[str] = None,
        known_chain: Optional[str] = None,
    ) -> CanonicalAsset:
        """
        Build a CanonicalAsset from CoinGecko coin data.
        """
        platforms = data.get("platforms", {})
        # Clean empty platform entries
        platforms = {k: v for k, v in platforms.items() if v}

        # 1. Determine the best chain/contract combination
        evm_chain = known_chain or self._detect_evm_chain(platforms)
        
        contract = known_address
        chain = evm_chain

        if not contract:
            if evm_chain:
                contract = platforms.get(evm_chain)
            elif platforms:
                # If no EVM chain, pick the first available platform (e.g., solana)
                chain = next(iter(platforms))
                contract = platforms.get(chain)
            else:
                # Native asset (BTC, etc.)
                chain = data.get("asset_platform_id") or "native"
                contract = None

        asset = CanonicalAsset(
            asset_id=data.get("id"),
            name=data.get("name"),
            symbol=data.get("symbol", "").upper(),
            chain=chain,
            contract_address=contract if contract else None,
            platforms=platforms,
            market_cap_rank=data.get("market_cap_rank"),
            market_cap=data.get("market_cap"),
            total_volume=data.get("total_volume"),
            homepage=data.get("homepage"),
            exchange_count=data.get("exchange_count", 0),
            market_presence=data.get("market_presence", "Minimal"),
            resolved=True,
            raw_input=raw_input,
        )

        logger.info(f"EntityResolver: Resolved → {asset} (chain: {asset.chain}, contract: {asset.contract_address})")
        return asset

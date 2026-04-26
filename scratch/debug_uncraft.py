import asyncio
import logging
from backend.services.coingecko_service import CoinGeckoService
from backend.services.entity_resolver import EntityResolver

logging.basicConfig(level=logging.INFO)

async def debug_uncraft():
    cg = CoinGeckoService()
    resolver = EntityResolver()
    
    print("\n--- Searching for 'UNcraft' ---")
    search_res = await cg.search("UNcraft")
    print(f"Search Result: {search_res}")
    
    if search_res:
        coin_id = search_res.get("id")
        print(f"\n--- Getting details for '{coin_id}' ---")
        details = await cg.get_coin_info(coin_id)
        print(f"Market Cap: {details.get('market_cap')}")
        print(f"Market Rank: {details.get('market_cap_rank')}")
        print(f"Platforms: {details.get('platforms')}")
        print(f"Exchange Count: {details.get('exchange_count')}")

    print("\n--- Resolver Resolution ---")
    asset = await resolver.resolve("UNcraft")
    print(f"Asset: {asset}")

if __name__ == "__main__":
    asyncio.run(debug_uncraft())

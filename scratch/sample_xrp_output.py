import asyncio
import logging
from backend.services.entity_resolver import EntityResolver
from backend.services.signal_normalizer import SignalNormalizer
from backend.services.output_formatter import OutputFormatter
from backend.services.asset_classifier import AssetClassifier

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)

async def test_xrp_real_data():
    resolver = EntityResolver()
    normalizer = SignalNormalizer()
    formatter = OutputFormatter()
    classifier = AssetClassifier()
    
    print("\n--- Resolving XRP ---")
    asset = await resolver.resolve("XRP")
    print(f"Resolved Asset: {asset}")
    
    # Extract market data from asset (which resolver populates from CoinGecko)
    market_data = {
        "is_listed": asset.resolved,
        "market_cap": asset.market_cap,
        "market_cap_rank": asset.market_cap_rank,
        "exchange_count": asset.exchange_count,
        "total_volume": asset.total_volume,
        "resolved": asset.resolved
    }
    
    # Classify asset
    has_contract = bool(asset.contract_address)
    asset_type = normalizer.normalize_asset_type(asset.chain, has_contract)
    
    # Normalize signals
    # XRP is a native asset, so structural might not apply in the same way as EVM tokens
    is_token = has_contract
    
    # For native assets, we might have limited "structural" data unless we specifically have a native scraper
    # But let's see what the normalizer does
    signals = normalizer.normalize_all(
        blockchain_data=None, # We don't have structural for native XRP in this simplified test
        market_data=market_data,
        audit_data=None, # XRP doesn't have a "contract audit" in the same way
        regulatory_data=None, # We'd need the real scraper here, but let's assume clean for test
        structural_applicable=is_token,
        has_contract=has_contract,
        chain=asset.chain,
        source_url=f"https://www.coingecko.com/en/coins/{asset.asset_id}" if asset.asset_id else None
    )
    
    # Simulate LLM explanation based on signals
    # In reality, this comes from Gemini, but for this "sample output" verification:
    explanation = f"XRP is a native blockchain asset with a market capitalization of ${asset.market_cap:,.0f}. It is ranked #{asset.market_cap_rank} globally and is listed on {asset.exchange_count} exchanges."
    
    report = formatter.format_response(signals, explanation, asset.name)
    print("\n--- FINAL REPORT ---")
    print(report)

if __name__ == "__main__":
    asyncio.run(test_xrp_real_data())

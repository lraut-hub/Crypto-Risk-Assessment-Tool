from backend.services.signal_normalizer import SignalNormalizer, NormalizedSignals
from backend.services.output_formatter import OutputFormatter
import json

def test_new_format():
    normalizer = SignalNormalizer()
    formatter = OutputFormatter()
    
    # Mock data for a contract-based token
    market_data = {
        "is_listed": True,
        "market_cap": 1250000,
        "market_cap_rank": 450,
        "exchange_count": 5
    }
    
    signals = NormalizedSignals()
    signals.asset_type = "Smart contract token"
    signals.structural = ["Contract Age: 2.1 years", "Ownership: Renounced"]
    signals.market = normalizer.normalize_market(market_data)
    signals.audit = ["Audited by CertiK"]
    signals.regulatory = ["No regulatory warnings found"]
    signals.data_coverage = "High"
    signals.source_url = "https://www.coingecko.com"
    signals.last_updated = "2026-04-23 18:55 UTC"
    
    explanation = "The asset is an ERC-20 token with a $1.25M market cap. It shows renounced ownership and a verified audit."
    
    report = formatter.format_response(signals, explanation, "TestToken")
    print(report)

if __name__ == "__main__":
    test_new_format()

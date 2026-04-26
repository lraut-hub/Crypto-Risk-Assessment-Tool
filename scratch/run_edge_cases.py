import asyncio
import logging
from backend.services.rag_service import RAGService

# Suppress noisy logs
logging.getLogger('backend.services').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)

async def run_optimized_tests():
    service = RAGService()
    
    test_cases = [
        {
            "name": "Case 1: Native Asset (BTC)",
            "query": "BTC"
        },
        {
            "name": "Case 2: Cross-Chain Token (UNcraft - Solana)",
            "query": "UNcraft"
        },
        {
            "name": "Case 3: Missing/New Asset (NonExistentToken)",
            "query": "NonExistentTokenXYZ"
        }
    ]

    print("\n" + "="*70)
    print("PRECISION FACTUAL MODEL - OPTIMUM OUTPUT VERIFICATION")
    print("="*70)

    for case in test_cases:
        print(f"\n>>> {case['name']}")
        try:
            response = await service.answer_query(case['query'])
            print(response)
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 70)

if __name__ == "__main__":
    asyncio.run(run_optimized_tests())

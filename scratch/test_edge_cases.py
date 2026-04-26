import asyncio
import logging
from backend.services.rag_service import RAGService

logging.basicConfig(level=logging.INFO)

async def test_edge_cases():
    rag = RAGService()
    
    test_cases = [
        {
            "name": "Native Blockchain Asset (Established)",
            "query": "XRP"
        },
        {
            "name": "Smart Contract Token (Established Meme)",
            "query": "HarryPotterObamaSonic10Inu"
        },
        {
            "name": "Low Data / Unindexed Smart Contract (Raw Address)",
            "query": "0x000000000000000000000000000000000000dEaD" # Fake/Burn address
        }
    ]
    
    for case in test_cases:
        print(f"\n=======================================================")
        print(f" TESTING: {case['name']} | Query: {case['query']}")
        print(f"=======================================================\n")
        
        try:
            res = await rag.answer_query(case["query"])
            print(res)
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_edge_cases())

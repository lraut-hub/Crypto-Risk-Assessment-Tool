import asyncio
import logging
from backend.services.rag_service import RAGService

# Setup logging
logging.basicConfig(level=logging.INFO)

async def test_universal_security():
    rag = RAGService()
    
    # Test 1: Solana Token (BONK)
    print("\n--- TEST 1: Solana (BONK) ---")
    response_sol = await rag.answer_query("BONK")
    print(response_sol)
    
    # Test 2: Ethereum Token (PEPE)
    print("\n--- TEST 2: Ethereum (PEPE) ---")
    response_eth = await rag.answer_query("PEPE")
    print(response_eth)

if __name__ == "__main__":
    asyncio.run(test_universal_security())

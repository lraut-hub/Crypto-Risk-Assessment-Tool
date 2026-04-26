import asyncio
import json
from backend.services.rag_service import RAGService

async def test_tokens():
    rag = RAGService()
    
    tokens = ["XRP", "Uniswap", "0x514910771af9ca656af840dff83e8264ecf986ca"] # XRP (Native), UNI (Safe), LINK (Safe but let's see)
    # Let's try a known "risky" one if possible, or just look at these.
    # Actually, let's try a meme token like "PEPE" or a random address.
    tokens = ["XRP", "Uniswap", "0x6982508145454ce325ddbe47a25d4ec3d2311933"] # XRP, UNI, PEPE
    
    for token in tokens:
        print(f"\n--- Testing: {token} ---")
        response, risk_profile = await rag.answer_query(token)
        print(f"Response Summary: {response[:100]}...")
        print(f"Risk Profile: {json.dumps(risk_profile, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_tokens())

import asyncio
import logging
from backend.services.rag_service import RAGService

logging.basicConfig(level=logging.INFO)

async def verify_xrp_fix():
    service = RAGService()
    print("\n--- Testing XRP resolution fix ---")
    response = await service.answer_query("XRP")
    print("\n--- FINAL OUTPUT ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(verify_xrp_fix())

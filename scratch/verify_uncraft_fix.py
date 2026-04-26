import asyncio
import logging
from backend.services.rag_service import RAGService

logging.basicConfig(level=logging.INFO)

async def verify_uncraft_fix():
    service = RAGService()
    print("\n--- Testing UNcraft (Solana Token) resolution fix ---")
    response = await service.answer_query("UNcraft")
    print("\n--- FINAL OUTPUT ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(verify_uncraft_fix())

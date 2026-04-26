import asyncio
import logging
from backend.services.rag_service import RAGService

logging.basicConfig(level=logging.INFO)

async def test_uncraft():
    rag = RAGService()
    res = await rag.answer_query("UNcraft")
    print(res)

if __name__ == "__main__":
    asyncio.run(test_uncraft())


import json
import logging
import asyncio
import os
from typing import List, Dict, Any

# Import our utilities
try:
    from scripts.utils.chunker import RecursiveChunker
    from backend.services.chroma_service import ChromaService
    from backend.utils.embeddings import BGEEmbeddings
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.chunker import RecursiveChunker
    from backend.services.chroma_service import ChromaService
    from backend.utils.embeddings import BGEEmbeddings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("KnowledgeIndexer")

class KnowledgeIndexer:
    """
    Pipeline to chunk and index the curated knowledge base into ChromaDB.
    """
    def __init__(self):
        self.chunker = RecursiveChunker()
        self.chroma = ChromaService()
        self.embedder = BGEEmbeddings()

    def load_corpus(self, filepath: str) -> List[Dict[str, Any]]:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("knowledge_base", [])

    def run(self):
        logger.info("=" * 60)
        logger.info("Starting Knowledge Base Indexing Pipeline (FULL REFRESH)")
        logger.info("=" * 60)
        
        # 1. Load data
        corpus_path = "data/knowledge/risk_corpus.json"
        entries = self.load_corpus(corpus_path)
        logger.info(f"Loaded {len(entries)} corpus entries.")
        
        # 2. Chunk text
        chunks = self.chunker.process_corpus(entries)
        logger.info(f"Generated {len(chunks)} chunks from corpus.")
        
        # 3. Enrich metadata with required fields
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        
        ids = [f"kb_{i}" for i in range(len(chunks))]
        documents = [c["content"] for c in chunks]
        metadatas = []
        for c in chunks:
            meta = c.get("metadata", {})
            # Ensure required metadata fields are present
            meta.setdefault("source_url", "https://www.investopedia.com")
            meta.setdefault("signal_type", "Explanation Grounding")
            meta["last_updated"] = timestamp
            metadatas.append(meta)
        
        # 4. Generate Embeddings
        logger.info("Generating BGE embeddings...")
        embeddings = self.embedder.create_embeddings(documents)
        
        # 5. Full-refresh: Delete and rebuild collection
        try:
            self.chroma.client.delete_collection("knowledge_base")
            logger.info("FULL REFRESH — Cleared existing knowledge_base collection.")
        except Exception:
            logger.info("No existing knowledge_base collection to clear.")
            
        collection = self.chroma.get_or_create_collection("knowledge_base", embedding_function=self.embedder)
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Successfully indexed {len(chunks)} chunks into ChromaDB.")
        
        # 4. Verify with a test query
        test_query = "How can a developer run away with funds?"
        results = self.chroma.query_signals(
            "knowledge_base", 
            query_text=test_query, 
            n_results=1,
            embedding_function=self.embedder
        )
        logger.info(f"Test Query Results: {results['documents'][0] if results['documents'] else 'No results'}")

if __name__ == "__main__":
    indexer = KnowledgeIndexer()
    indexer.run()

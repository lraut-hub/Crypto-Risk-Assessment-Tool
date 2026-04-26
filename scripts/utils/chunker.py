import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class RecursiveChunker:
    """
    A simple recursive-style chunker for splitting text into consistent blocks.
    Ensures small, semantic chunks for high-precision RAG.
    """
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Splits text into chunks and attaches metadata.
        """
        chunks = []
        if len(text) <= self.chunk_size:
            chunks.append({"content": text, "metadata": metadata})
            return chunks

        # Basic sliding window chunking
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk_content = text[start:end]
            
            # Create chunk entry
            chunks.append({
                "content": chunk_content,
                "metadata": {**metadata, "chunk_index": len(chunks)}
            })
            
            # Step forward by (size - overlap)
            start += (self.chunk_size - self.chunk_overlap)
            
        return chunks

    def process_corpus(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Processes a list of knowledge base entries into chunks.
        """
        all_chunks = []
        for entry in entries:
            content = entry.get("content", "")
            # Inherit source/topic metadata
            meta = {
                "source": entry.get("source", "Unknown"),
                "topic": entry.get("topic", "General")
            }
            all_chunks.extend(self.chunk_text(content, meta))
            
        logger.info(f"Processed {len(entries)} entries into {len(all_chunks)} chunks.")
        return all_chunks

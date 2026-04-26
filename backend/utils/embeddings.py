import logging
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from chromadb import EmbeddingFunction, Documents, Embeddings

logger = logging.getLogger(__name__)

class BGEEmbeddings(EmbeddingFunction):
    """
    Wrapper for BGE (BAAI General Embedding) model using SentenceTransformers.
    Compatible with ChromaDB's EmbeddingFunction interface.
    """
    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5"):
        logger.info(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        logger.info("Model loaded successfully.")

    def __call__(self, input: Documents) -> Embeddings:
        """
        Implementation of ChromaDB's EmbeddingFunction interface.
        """
        return self.model.encode(input, normalize_embeddings=True).tolist()

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a list of strings.
        """
        # Ensure optimal formatting for BGE
        # BGE recommends adding 'Represent this sentence for searching relevant passages: ' if needed, 
        # but for symmetric retrieval we use the raw text.
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def create_single_embedding(self, text: str) -> List[float]:
        """
        Generates embedding for a single string.
        """
        return self.create_embeddings([text])[0]

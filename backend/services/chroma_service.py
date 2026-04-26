import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class ChromaService:
    """
    Service for interacting with ChromaDB for storing and retrieving risk signals.
    """
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or os.getenv("CHROMA_DB_PATH", "../data/chromadb")
        # Ensure the directory is absolute relative to the backend
        if not os.path.isabs(self.persist_directory):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.persist_directory = os.path.abspath(os.path.join(base_dir, self.persist_directory))
            
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        logger.info(f"ChromaDB initialized in {self.persist_directory}")

    def get_or_create_collection(self, collection_name: str, embedding_function: Optional[Any] = None):
        """
        Retrieves or creates a ChromaDB collection.
        If embedding_function is None, it disables internal defaults to allow manual uploads.
        """
        return self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function
        )

    def add_signals(self, collection_name: str, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        """
        Adds risk signals (documents and metadata) to a collection.
        """
        collection = self.get_or_create_collection(collection_name)
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Added {len(ids)} signals to collection '{collection_name}'")

    def query_signals(self, collection_name: str, query_text: Optional[str] = None, where: Optional[Dict[str, Any]] = None, n_results: int = 5, embedding_function: Optional[Any] = None):
        """
        Queries signals from the collection using text (semantic search) or metadata filters.
        """
        collection = self.get_or_create_collection(collection_name, embedding_function=embedding_function)
        
        query_params = {"n_results": n_results}
        if query_text:
            query_params["query_texts"] = [query_text]
        else:
            # If no query text, we must use .get() for metadata filtering
            return self.get_signals(collection_name, where=where, limit=n_results)

        if where:
            query_params["where"] = where
            
        results = collection.query(**query_params)
        return results

    def get_signals(self, collection_name: str, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None, limit: int = 10):
        """
        Retrieves specific signals using IDs or metadata filters (no semantic search).
        """
        collection = self.get_or_create_collection(collection_name)
        return collection.get(
            ids=ids,
            where=where,
            limit=limit
        )

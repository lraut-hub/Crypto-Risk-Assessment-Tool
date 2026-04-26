import hashlib
import json
from typing import Any, Dict

def generate_content_hash(data: Dict[str, Any]) -> str:
    """
    Generate a SHA-256 hash of a dictionary-like data object for deduplication.
    Sorts keys to ensure consistent hashing for identical content.
    """
    # Convert data to a consistent string representation
    content_string = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(content_string).hexdigest()

def is_duplicate(content_hash: str, existing_hashes: set) -> bool:
    """
    Check if a content hash already exists in a set of known hashes.
    """
    return content_hash in existing_hashes

# app/ingestion/embeddings.py
"""
OpenAI embedding utilities for generating embeddings without downloading models.
"""

import os
from typing import List
import requests
import numpy as np


def get_openai_embeddings(texts: List[str], model: str = "text-embedding-3-small") -> np.ndarray:
    """
    Get embeddings from OpenAI API for a list of texts.
    
    Args:
        texts: List of text strings to embed
        model: OpenAI embedding model name (default: text-embedding-3-small)
    
    Returns:
        numpy array of shape (len(texts), embedding_dim)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in the environment.")
    
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    url = f"{base_url}/embeddings"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # OpenAI embeddings API accepts up to 2048 inputs per request
    # We'll batch if needed
    all_embeddings = []
    batch_size = 100  # Process in batches to avoid rate limits
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        payload = {
            "model": model,
            "input": batch,
        }
        
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract embeddings from response
        batch_embeddings = [item["embedding"] for item in data["data"]]
        all_embeddings.extend(batch_embeddings)
    
    return np.array(all_embeddings, dtype=np.float32)


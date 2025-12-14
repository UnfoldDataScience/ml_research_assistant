from typing import List, Dict
import os

import numpy as np
import weaviate

from app.config import config
from app.ingestion.index_weaviate import get_weaviate_client
from app.ingestion.embeddings import get_openai_embeddings


class Retriever:
    def __init__(self, client: weaviate.WeaviateClient | None = None):
        self.client = client or get_weaviate_client()
        self.collection = self.client.collections.get(config.weaviate.class_name)
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        # Get embedding from OpenAI API
        query_embeddings = get_openai_embeddings([query], model=self.embedding_model)
        query_vec = query_embeddings[0].astype(np.float32)
        results = self.collection.query.near_vector(
            near_vector=query_vec.tolist(),
            limit=top_k,
        )

        chunks: List[Dict] = []
        for o in results.objects:
            props = o.properties
            chunks.append(
                {
                    "paper_id": props["paper_id"],
                    "title": props["title"],
                    "abstract": props["abstract"],
                    "chunk_text": props["chunk_text"],
                    "start_token": props["start_token"],
                    "end_token": props["end_token"],
                    "chunking_strategy": props.get("chunking_strategy", "fixed_size"),
                    "score": o.metadata.distance,  # smaller is closer
                }
            )
        return chunks

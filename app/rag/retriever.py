from typing import List, Dict

import numpy as np
from sentence_transformers import SentenceTransformer
import weaviate

from app.config import config
from app.ingestion.index_weaviate import get_weaviate_client


class Retriever:
    def __init__(self, client: weaviate.WeaviateClient | None = None):
        self.client = client or get_weaviate_client()
        self.collection = self.client.collections.get(config.weaviate.class_name)
        self.model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        query_vec = self.model.encode([query], convert_to_numpy=True)[0].astype(
            np.float32
        )
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
                    "score": o.metadata.distance,  # smaller is closer
                }
            )
        return chunks

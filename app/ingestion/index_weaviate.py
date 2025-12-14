# app/ingestion/index_weaviate.py

from typing import List, Dict
import os

import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.init import Auth
from tqdm import tqdm

from app.config import config
from app.ingestion.embeddings import get_openai_embeddings


def get_weaviate_client() -> weaviate.WeaviateClient:
    """
    Connect to Weaviate Cloud using URL + API key from config.
    """
    w_conf = config.weaviate
    if not w_conf.url or not w_conf.api_key:
        raise RuntimeError(
            "WEAVIATE_URL and WEAVIATE_API_KEY must be set in the environment "
            "to use Weaviate Cloud."
        )

    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=w_conf.url,
        auth_credentials=Auth.api_key(w_conf.api_key),
    )
    return client


def ensure_schema(client: weaviate.WeaviateClient) -> None:
    """
    Ensure the PaperChunk collection exists with the right schema.
    """
    w_conf = config.weaviate
    class_name = w_conf.class_name

    # In v4, list_all() returns a list of collection names (strings)
    existing_names = client.collections.list_all()
    if class_name in existing_names:
        print(f"Collection {class_name} already exists.")
        return

    print(f"Creating collection {class_name} on Weaviate Cloud...")

    # For Weaviate 4.6.3, use vectorizer_config=None for self-provided vectors
    # Try the newer API first, fall back to older API if needed
    try:
        # Try newer API (4.7+)
        client.collections.create(
            name=class_name,
            vector_config=Configure.Vectors.self_provided(),
            properties=[
                Property(name="paper_id", data_type=DataType.TEXT),
                Property(name="title", data_type=DataType.TEXT),
                Property(name="abstract", data_type=DataType.TEXT),
                Property(name="chunk_text", data_type=DataType.TEXT),
                Property(name="start_token", data_type=DataType.INT),
                Property(name="end_token", data_type=DataType.INT),
                Property(name="chunking_strategy", data_type=DataType.TEXT),
            ],
        )
    except AttributeError:
        # Fall back to older API (4.6.3) - omit vector_config (self-provided is default)
        client.collections.create(
            name=class_name,
            properties=[
                Property(name="paper_id", data_type=DataType.TEXT),
                Property(name="title", data_type=DataType.TEXT),
                Property(name="abstract", data_type=DataType.TEXT),
                Property(name="chunk_text", data_type=DataType.TEXT),
                Property(name="start_token", data_type=DataType.INT),
                Property(name="end_token", data_type=DataType.INT),
                Property(name="chunking_strategy", data_type=DataType.TEXT),
            ],
        )

    print("Schema created.")


def index_chunks(
    client: weaviate.WeaviateClient,
    chunks: List[Dict],
) -> None:
    """
    Embed and index all chunks into the Weaviate collection.
    """
    w_conf = config.weaviate
    collection = client.collections.get(w_conf.class_name)

    print("Using OpenAI embeddings (text-embedding-3-small)...")
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    batch_size = w_conf.batch_size
    total = len(chunks)
    print(f"Indexing {total} chunks in batches of {batch_size}...")

    for i in tqdm(range(0, total, batch_size)):
        batch = chunks[i : i + batch_size]
        texts = [c["chunk_text"] for c in batch]
        vectors = get_openai_embeddings(texts, model=embedding_model)

        with collection.batch.dynamic() as batcher:
            for chunk, vector in zip(batch, vectors):
                batcher.add_object(
                    properties={
                        "paper_id": chunk["paper_id"],
                        "title": chunk["title"],
                        "abstract": chunk["abstract"],
                        "chunk_text": chunk["chunk_text"],
                        "start_token": chunk["start_token"],
                        "end_token": chunk["end_token"],
                        "chunking_strategy": chunk.get("chunking_strategy", "fixed_size"),
                    },
                    vector=vector,
                )

    print("Indexing complete.")

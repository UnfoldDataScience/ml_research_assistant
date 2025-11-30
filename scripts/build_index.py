"""
Build the initial Weaviate index from the arxiv dataset.

Usage:
    uv run scripts/build_index.py
"""

from app.data.load_arxiv import load_arxiv_papers
from app.ingestion.chunking import chunk_papers
from app.ingestion.index_weaviate import (
    get_weaviate_client,
    ensure_schema,
    index_chunks,
)


def main():
    client = get_weaviate_client()
    ensure_schema(client)

    papers = load_arxiv_papers()
    print(f"Loaded {len(papers)} papers.")

    chunks = chunk_papers(papers)
    print(f"Generated {len(chunks)} chunks.")

    index_chunks(client, chunks)

    client.close()
    print("Done.")


if __name__ == "__main__":
    main()

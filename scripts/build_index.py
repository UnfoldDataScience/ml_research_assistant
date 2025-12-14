"""
Build the initial Weaviate index from the arxiv dataset.

Usage:
    python scripts/build_index.py
    (Must be run from project root directory)
"""

import sys
from pathlib import Path

# Add project root to Python path so we can import 'app'
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.data.load_arxiv import load_arxiv_papers
from app.ingestion.chunking import chunk_papers
from app.config import config
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

    chunking_strategy = config.chunking.strategy
    print(f"Using chunking strategy: {chunking_strategy}")
    
    # For large datasets, process in batches to avoid memory issues
    # Process papers in batches of 50 to keep memory usage manageable
    batch_size = 5
    all_chunks = []
    
    for i in range(0, len(papers), batch_size):
        batch = papers[i:i + batch_size]
        print(f"Processing papers {i+1} to {min(i+batch_size, len(papers))}...")
        batch_chunks = chunk_papers(batch, strategy=chunking_strategy)
        all_chunks.extend(batch_chunks)
        print(f"  Generated {len(batch_chunks)} chunks (total so far: {len(all_chunks)})")
    
    print(f"Total chunks generated: {len(all_chunks)}")
    index_chunks(client, all_chunks)

    client.close()
    print("Done.")


if __name__ == "__main__":
    main()

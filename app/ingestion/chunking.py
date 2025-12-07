from typing import List, Dict, Literal
import re

from app.config import config


def _split_text_into_tokens(text: str) -> List[str]:
    # Simple whitespace tokenizer; Session 2 can replace with tiktoken/semantic
    return text.split()


def _tokens_to_text(tokens: List[str]) -> str:
    return " ".join(tokens)


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using simple regex."""
    # Simple sentence splitting (can be improved with nltk/spacy)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_paper_fixed_size(paper: Dict) -> List[Dict]:
    """
    Chunk using fixed-size windows (original strategy).
    Good for: Consistent chunk sizes, simple implementation.
    """
    ch_conf = config.chunking
    tokens = _split_text_into_tokens(paper["article"])
    chunks = []

    step = ch_conf.chunk_size_tokens - ch_conf.chunk_overlap_tokens
    for start in range(0, len(tokens), step):
        end = start + ch_conf.chunk_size_tokens
        chunk_tokens = tokens[start:end]
        if not chunk_tokens:
            continue

        chunk_text = _tokens_to_text(chunk_tokens)
        chunks.append(
            {
                "paper_id": paper["id"],
                "title": paper["title"],
                "abstract": paper["abstract"],
                "chunk_text": chunk_text,
                "start_token": start,
                "end_token": min(end, len(tokens)),
                "chunking_strategy": "fixed_size",
            }
        )

    return chunks


def chunk_paper_sentence_based(paper: Dict, max_sentences: int = 10, overlap_sentences: int = 2) -> List[Dict]:
    """
    Chunk using sentence boundaries.
    Good for: Preserving sentence integrity, better context.
    """
    sentences = _split_into_sentences(paper["article"])
    chunks = []
    
    step = max_sentences - overlap_sentences
    for start in range(0, len(sentences), step):
        end = start + max_sentences
        chunk_sentences = sentences[start:end]
        if not chunk_sentences:
            continue
        
        chunk_text = " ".join(chunk_sentences)
        chunks.append(
            {
                "paper_id": paper["id"],
                "title": paper["title"],
                "abstract": paper["abstract"],
                "chunk_text": chunk_text,
                "start_token": start,
                "end_token": min(end, len(sentences)),
                "chunking_strategy": "sentence_based",
            }
        )
    
    return chunks


def chunk_paper_semantic(paper: Dict, chunk_size_tokens: int = 300, similarity_threshold: float = 0.7) -> List[Dict]:
    """
    Chunk using semantic similarity (simplified version).
    Groups sentences/chunks that are semantically similar.
    Good for: Keeping related content together, better retrieval.
    
    Note: This is a simplified version. Full semantic chunking would use
    embeddings and clustering algorithms.
    """
    # For simplicity, we'll use sentence-based with some heuristics
    # In production, you'd use embeddings and similarity clustering
    sentences = _split_into_sentences(paper["article"])
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_tokens = len(sentence.split())
        
        # Start new chunk if adding this sentence would exceed size
        if current_size + sentence_tokens > chunk_size_tokens and current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                {
                    "paper_id": paper["id"],
                    "title": paper["title"],
                    "abstract": paper["abstract"],
                    "chunk_text": chunk_text,
                    "start_token": len(chunks),
                    "end_token": len(chunks) + 1,
                    "chunking_strategy": "semantic",
                }
            )
            # Keep last few sentences for overlap
            overlap = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
            current_chunk = overlap + [sentence]
            current_size = sum(len(s.split()) for s in current_chunk)
        else:
            current_chunk.append(sentence)
            current_size += sentence_tokens
    
    # Add remaining chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append(
            {
                "paper_id": paper["id"],
                "title": paper["title"],
                "abstract": paper["abstract"],
                "chunk_text": chunk_text,
                "start_token": len(chunks),
                "end_token": len(chunks) + 1,
                "chunking_strategy": "semantic",
            }
        )
    
    return chunks


def chunk_paper(paper: Dict, strategy: Literal["fixed_size", "sentence_based", "semantic"] = "fixed_size") -> List[Dict]:
    """
    Chunk the article using the specified strategy.
    
    Args:
        paper: Paper dictionary with 'article', 'id', 'title', 'abstract'
        strategy: Chunking strategy to use
    
    Returns:
        List of chunk dictionaries
    """
    if strategy == "fixed_size":
        return chunk_paper_fixed_size(paper)
    elif strategy == "sentence_based":
        return chunk_paper_sentence_based(paper)
    elif strategy == "semantic":
        return chunk_paper_semantic(paper)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")


def chunk_papers(papers: List[Dict], strategy: Literal["fixed_size", "sentence_based", "semantic"] = "fixed_size") -> List[Dict]:
    """
    Apply chunking to all papers using the specified strategy.
    
    Args:
        papers: List of paper dictionaries
        strategy: Chunking strategy to use
    
    Returns:
        List of all chunks from all papers
    """
    all_chunks: List[Dict] = []
    for paper in papers:
        all_chunks.extend(chunk_paper(paper, strategy=strategy))
    return all_chunks

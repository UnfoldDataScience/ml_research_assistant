from typing import List, Dict

from app.config import config


def _split_text_into_tokens(text: str) -> List[str]:
    # Simple whitespace tokenizer; Session 2 can replace with tiktoken/semantic
    return text.split()


def _tokens_to_text(tokens: List[str]) -> str:
    return " ".join(tokens)


def chunk_paper(paper: Dict) -> List[Dict]:
    """
    Chunk the article of a paper into overlapping windows of tokens.
    Returns list of chunk dicts.
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
            }
        )

    return chunks


def chunk_papers(papers: List[Dict]) -> List[Dict]:
    """
    Apply chunking to all papers.
    """
    all_chunks: List[Dict] = []
    for paper in papers:
        all_chunks.extend(chunk_paper(paper))
    return all_chunks

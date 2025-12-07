# app/rag/evaluation.py
"""
RAG Evaluation Metrics Module

Implements 5 key metrics for evaluating RAG system performance:
1. Precision@K - Fraction of retrieved items that are relevant
2. Recall@K - Fraction of relevant items that are retrieved
3. MRR (Mean Reciprocal Rank) - Average of reciprocal ranks of first relevant item
4. NDCG (Normalized Discounted Cumulative Gain) - Ranking quality metric
5. F1 Score - Harmonic mean of Precision and Recall
"""

from typing import List, Dict, Set
import numpy as np


def precision_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """
    Calculate Precision@K: fraction of top-K retrieved items that are relevant.
    
    Args:
        retrieved: List of retrieved item IDs (ordered by relevance)
        relevant: Set of relevant item IDs
        k: Number of top items to consider
    
    Returns:
        Precision@K score (0.0 to 1.0)
    """
    if k == 0:
        return 0.0
    top_k = retrieved[:k]
    relevant_retrieved = sum(1 for item in top_k if item in relevant)
    return relevant_retrieved / k


def recall_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """
    Calculate Recall@K: fraction of relevant items found in top-K retrieved.
    
    Args:
        retrieved: List of retrieved item IDs (ordered by relevance)
        relevant: Set of relevant item IDs
        k: Number of top items to consider
    
    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if len(relevant) == 0:
        return 0.0
    top_k = retrieved[:k]
    relevant_retrieved = sum(1 for item in top_k if item in relevant)
    return relevant_retrieved / len(relevant)


def mean_reciprocal_rank(retrieved: List[str], relevant: Set[str]) -> float:
    """
    Calculate MRR: average reciprocal rank of first relevant item.
    
    Args:
        retrieved: List of retrieved item IDs (ordered by relevance)
        relevant: Set of relevant item IDs
    
    Returns:
        MRR score (0.0 to 1.0)
    """
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """
    Calculate NDCG@K: normalized discounted cumulative gain at K.
    
    Args:
        retrieved: List of retrieved item IDs (ordered by relevance)
        relevant: Set of relevant item IDs
        k: Number of top items to consider
    
    Returns:
        NDCG@K score (0.0 to 1.0)
    """
    if k == 0 or len(relevant) == 0:
        return 0.0
    
    # DCG: sum of (relevance / log2(rank+1)) for top-K
    dcg = 0.0
    for rank, item in enumerate(retrieved[:k], start=1):
        if item in relevant:
            dcg += 1.0 / np.log2(rank + 1)
    
    # IDCG: ideal DCG (all relevant items at top)
    idcg = 0.0
    num_relevant = min(len(relevant), k)
    for rank in range(1, num_relevant + 1):
        idcg += 1.0 / np.log2(rank + 1)
    
    return dcg / idcg if idcg > 0 else 0.0


def f1_score_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """
    Calculate F1@K: harmonic mean of Precision@K and Recall@K.
    
    Args:
        retrieved: List of retrieved item IDs (ordered by relevance)
        relevant: Set of relevant item IDs
        k: Number of top items to consider
    
    Returns:
        F1@K score (0.0 to 1.0)
    """
    precision = precision_at_k(retrieved, relevant, k)
    recall = recall_at_k(retrieved, relevant, k)
    
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def evaluate_rag(
    retrieved_chunks: List[Dict],
    query: str,
    k: int = 5,
) -> Dict[str, float]:
    """
    Evaluate RAG retrieval performance using multiple metrics.
    
    Note: In a real scenario, you'd have ground truth relevant chunks.
    For demonstration, we simulate relevance based on:
    - Semantic similarity scores (lower distance = more relevant)
    - Keyword matching
    
    Args:
        retrieved_chunks: List of retrieved chunk dictionaries with 'score' and 'chunk_text'
        query: The search query
        k: Number of top results to evaluate
    
    Returns:
        Dictionary with metric names and scores
    """
    # Simulate relevance: chunks with high similarity (low distance) are considered relevant
    # In production, you'd have human-annotated ground truth
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    # Create relevance set based on:
    # 1. Top scoring chunks (low distance = high similarity)
    # 2. Keyword overlap with query
    relevant_ids = set()
    chunk_ids = []
    
    for i, chunk in enumerate(retrieved_chunks[:k]):
        chunk_id = f"chunk_{i}"
        chunk_ids.append(chunk_id)
        
        # Consider relevant if:
        # - Score is in top 50% (lower distance = better)
        # - Or has significant keyword overlap
        score = chunk.get("score")
        if score is None:
            score = 1.0  # Default to worst score if missing
        
        chunk_text_lower = chunk.get("chunk_text", "").lower()
        chunk_words = set(chunk_text_lower.split())
        
        keyword_overlap = len(query_words & chunk_words) / max(len(query_words), 1)
        
        # Threshold-based relevance (for demo purposes)
        if score < 0.5 or keyword_overlap > 0.3:
            relevant_ids.add(chunk_id)
    
    # Calculate all metrics
    metrics = {
        "precision@k": precision_at_k(chunk_ids, relevant_ids, k),
        "recall@k": recall_at_k(chunk_ids, relevant_ids, k),
        "mrr": mean_reciprocal_rank(chunk_ids, relevant_ids),
        "ndcg@k": ndcg_at_k(chunk_ids, relevant_ids, k),
        "f1@k": f1_score_at_k(chunk_ids, relevant_ids, k),
    }
    
    return metrics


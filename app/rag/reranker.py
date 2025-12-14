# app/rag/reranker.py
"""
Reranking Module for RAG

Reranking improves retrieval quality by using a more sophisticated
cross-encoder model that considers query-document pairs together,
rather than just independent embeddings.

This helps because:
1. Cross-encoders see query and document together, enabling better matching
2. Can capture complex semantic relationships
3. Typically improves precision of top results
"""

from typing import List, Dict
import numpy as np
# Import CrossEncoder only when needed to avoid slow startup
# from sentence_transformers import CrossEncoder


class Reranker:
    """
    Reranks retrieved chunks using a cross-encoder model.
    
    Cross-encoders are more accurate than bi-encoders (used in initial retrieval)
    but slower, so they're used to rerank a smaller set of candidates.
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize reranker with a cross-encoder model.
        
        Args:
            model_name: HuggingFace model name for cross-encoder
        """
        self.model_name = model_name
        self.model = None  # Lazy load to avoid slow startup
        self._load_error = None
    
    def _ensure_model_loaded(self):
        """Lazy load the model only when needed."""
        if self.model is None and self._load_error is None:
            try:
                import warnings
                import logging
                import os
                
                # Suppress PyTorch warnings during model loading
                warnings.filterwarnings("ignore")
                os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Suppress tokenizer warnings
                logging.getLogger("transformers").setLevel(logging.ERROR)
                logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
                
                # Import here to avoid slow startup
                from sentence_transformers import CrossEncoder
                
                print(f"Loading reranker model {self.model_name}... (this may take a minute on first use)")
                self.model = CrossEncoder(self.model_name, max_length=512)
                print("Reranker model loaded successfully.")
            except Exception as e:
                self._load_error = str(e)
                raise RuntimeError(
                    f"Failed to load reranker model {self.model_name}: {e}\n"
                    "This may be due to network issues or missing dependencies.\n"
                    "Try disabling reranking in the UI settings."
                ) from e
        elif self._load_error:
            raise RuntimeError(f"Reranker model failed to load: {self._load_error}")
    
    def rerank(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int | None = None,
    ) -> List[Dict]:
        """
        Rerank chunks based on query-chunk relevance scores.
        
        Args:
            query: The search query
            chunks: List of chunk dictionaries with 'chunk_text'
            top_k: Number of top results to return (None = return all)
        
        Returns:
            Reranked list of chunks with updated 'rerank_score' field
        """
        if not chunks:
            return []
        
        # Lazy load model on first use
        self._ensure_model_loaded()
        
        # Prepare query-chunk pairs for cross-encoder
        pairs = [(query, chunk.get("chunk_text", "")) for chunk in chunks]
        
        # Get relevance scores from cross-encoder
        scores = self.model.predict(pairs)
        
        # Add rerank scores and sort by them (higher = more relevant)
        reranked = []
        for idx, (chunk, score) in enumerate(zip(chunks, scores)):
            chunk_copy = chunk.copy()
            chunk_copy["rerank_score"] = float(score)
            chunk_copy["original_rank"] = idx + 1
            reranked.append(chunk_copy)
        
        # Sort by rerank score (descending)
        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        # Return top_k if specified
        if top_k is not None:
            return reranked[:top_k]
        
        return reranked
    
    def compare_retrieval(
        self,
        query: str,
        original_chunks: List[Dict],
        top_k: int = 5,
    ) -> Dict:
        """
        Compare original retrieval vs reranked results.
        
        Returns:
            Dictionary with 'original' and 'reranked' lists, plus statistics
        """
        reranked = self.rerank(query, original_chunks, top_k=top_k)
        
        # Calculate improvement metrics
        original_top = original_chunks[:top_k]
        reranked_top = reranked[:top_k]
        
        # Count how many top results changed position
        original_ids = [id(c) for c in original_top]
        reranked_ids = [id(c) for c in reranked_top]
        position_changes = sum(
            1 for i, chunk_id in enumerate(reranked_ids)
            if chunk_id not in original_ids[:i+1]
        )
        
        return {
            "original": original_top,
            "reranked": reranked_top,
            "position_changes": position_changes,
            "avg_rerank_score": np.mean([c["rerank_score"] for c in reranked_top]) if reranked_top else 0.0,
        }


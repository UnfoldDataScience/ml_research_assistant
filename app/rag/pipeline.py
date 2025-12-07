from dataclasses import dataclass
from typing import List, Dict, Optional

from app.rag.llm_client import LLMClient
from app.rag.retriever import Retriever
from app.rag.reranker import Reranker
from app.rag.evaluation import evaluate_rag


@dataclass
class RAGResult:
    query: str
    answer: str
    contexts: List[Dict]
    original_contexts: Optional[List[Dict]] = None  # Before reranking
    reranked_contexts: Optional[List[Dict]] = None  # After reranking
    evaluation_metrics: Optional[Dict[str, float]] = None
    reranking_comparison: Optional[Dict] = None


class RAGPipeline:
    def __init__(
        self,
        retriever: Retriever | None = None,
        llm_client: LLMClient | None = None,
        reranker: Reranker | None = None,
        use_reranking: bool = False,
        use_evaluation: bool = False,
    ):
        self.retriever = retriever or Retriever()
        self.llm = llm_client or LLMClient()
        self.reranker = reranker or Reranker() if use_reranking else None
        self.use_reranking = use_reranking
        self.use_evaluation = use_evaluation

    def answer_query(
        self,
        query: str,
        top_k: int = 5,
        use_reranking: bool | None = None,
        use_evaluation: bool | None = None,
    ) -> RAGResult:
        """
        Answer a query using RAG pipeline with optional reranking and evaluation.
        
        Args:
            query: The user's question
            top_k: Number of chunks to retrieve
            use_reranking: Override default reranking setting
            use_evaluation: Override default evaluation setting
        
        Returns:
            RAGResult with answer, contexts, and optional metrics
        """
        # Determine if reranking should be used
        should_rerank = use_reranking if use_reranking is not None else self.use_reranking
        
        # Retrieve initial contexts (get more if reranking will be applied)
        retrieve_k = top_k * 2 if should_rerank else top_k
        original_contexts = self.retriever.retrieve(query, top_k=retrieve_k)
        
        # Apply reranking if enabled
        contexts = original_contexts
        reranking_comparison = None
        if should_rerank:
            # Create reranker on-demand if not already created
            if self.reranker is None:
                from app.rag.reranker import Reranker
                self.reranker = Reranker()
            reranking_comparison = self.reranker.compare_retrieval(query, original_contexts, top_k=top_k)
            contexts = reranking_comparison["reranked"]
        
        # Generate answer
        answer = self.llm.generate_answer(query, contexts[:top_k])
        
        # Evaluate if enabled
        evaluation_metrics = None
        if (use_evaluation if use_evaluation is not None else self.use_evaluation):
            evaluation_metrics = evaluate_rag(contexts[:top_k], query, k=top_k)
        
        return RAGResult(
            query=query,
            answer=answer,
            contexts=contexts[:top_k],
            original_contexts=original_contexts[:top_k] if reranking_comparison else None,
            reranked_contexts=contexts[:top_k] if reranking_comparison else None,
            evaluation_metrics=evaluation_metrics,
            reranking_comparison=reranking_comparison,
        )

from dataclasses import dataclass
from typing import List, Dict

from app.rag.llm_client import LLMClient
from app.rag.retriever import Retriever


@dataclass
class RAGResult:
    query: str
    answer: str
    contexts: List[Dict]


class RAGPipeline:
    def __init__(
        self,
        retriever: Retriever | None = None,
        llm_client: LLMClient | None = None,
    ):
        self.retriever = retriever or Retriever()
        self.llm = llm_client or LLMClient()

    def answer_query(self, query: str, top_k: int = 5) -> RAGResult:
        contexts = self.retriever.retrieve(query, top_k=top_k)
        answer = self.llm.generate_answer(query, contexts)
        return RAGResult(query=query, answer=answer, contexts=contexts)

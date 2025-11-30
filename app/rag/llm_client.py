# app/rag/llm_client.py
from typing import List, Dict
import os
import requests

from app.config import config


class LLMClient:
    def __init__(self):
        llm_conf = config.llm
        self.provider = llm_conf.provider
        self.model = llm_conf.model
        self.temperature = llm_conf.temperature
        self.max_tokens = llm_conf.max_tokens

        if self.provider != "openai":
            # For Session 1 we support only OpenAI-style chat completions
            raise NotImplementedError(
                f"Provider {self.provider} not implemented yet. "
                "Set LLM_PROVIDER=openai in your .env."
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in the environment.")

        self.api_key = api_key

        # Allow overriding base URL (for Azure / proxies etc.), default is standard OpenAI
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def generate_answer(self, query: str, contexts: List[Dict]) -> str:
        """
        Call the OpenAI-compatible /chat/completions endpoint via plain HTTP.
        """
        if not contexts:
            context_block = "No relevant context chunks were retrieved."
        else:
            context_block = "\n\n".join(
                f"[{i+1}] Title: {c['title']}\n{c['chunk_text']}"
                for i, c in enumerate(contexts)
            )

        system_prompt = (
            "You are a helpful ML research assistant. "
            "You answer questions based only on the provided context from ML research papers. "
            "If the answer is not in the context, say you are not sure."
        )

        user_prompt = (
            f"Question:\n{query}\n\n"
            "Use ONLY the following context to answer. "
            "Cite chunk numbers when relevant.\n\n"
            f"Context:\n{context_block}"
        )

        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/chat/completions"

        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            # Helpful error if the response structure is unexpected
            raise RuntimeError(f"Unexpected response from LLM API: {data}") from e

# app/config.py
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv("E:/YTReusable/.env",override=True)


@dataclass
class DatasetConfig:
    hf_name: str = "scientific_papers"
    hf_config: str = "arxiv"
    max_papers: int = 50  # tweak for cost/runtime


@dataclass
class ChunkingConfig:
    chunk_size_tokens: int = 300
    chunk_overlap_tokens: int = 50
    strategy: str = "semantic"  # Options: "fixed_size", "sentence_based", "semantic"


@dataclass
class WeaviateConfig:
    # For Cloud, this must be your REST endpoint URL
    url: str = os.getenv("WEAVIATE_URL", "")
    api_key: str | None = os.getenv("WEAVIATE_API_KEY")
    class_name: str = "PaperChunk"
    vector_dim: int = 768  # all-mpnet-base-v2
    batch_size: int = 32


@dataclass
class LLMConfig:
    provider: str = os.getenv("LLM_PROVIDER", "openai")
    model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    temperature: float = 0.1
    max_tokens: int = 512


@dataclass
class AppConfig:
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    weaviate: WeaviateConfig = field(default_factory=WeaviateConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)


config = AppConfig()

# app/config.py
import os
from pathlib import Path
from dataclasses import dataclass, field

from dotenv import load_dotenv

# Load .env from project root (works both locally and on EC2)
# Try multiple paths to find .env file
possible_roots = [
    Path(__file__).parent.parent.parent,  # From app/config.py -> project root
    Path.cwd(),  # Current working directory
]

env_path = None
for root in possible_roots:
    candidate = root / ".env"
    if candidate.exists():
        env_path = candidate
        break

if env_path is None:
    # Try current directory as last resort
    env_path = Path(".env")

# Load the .env file
if env_path.exists():
    result = load_dotenv(env_path, override=True)
    if not result:
        import sys
        print(f"Warning: .env file exists at {env_path} but load_dotenv returned False. Check file format.", file=sys.stderr)
else:
    import sys
    print(f"Warning: .env file not found. Tried: {[str(r / '.env') for r in possible_roots]}", file=sys.stderr)


@dataclass
class DatasetConfig:
    hf_name: str = "scientific_papers"
    hf_config: str = "arxiv"
    max_papers: int = 5  # tweak for cost/runtime


@dataclass
class ChunkingConfig:
    chunk_size_tokens: int = 300
    chunk_overlap_tokens: int = 50
    strategy: str = "semantic"  # Options: "fixed_size", "sentence_based", "semantic"


@dataclass
class WeaviateConfig:
    # For Cloud, this must be your REST endpoint URL
    # Note: os.getenv() is called at class definition time, after load_dotenv above
    url: str = os.getenv("WEAVIATE_URL", "") or ""
    api_key: str | None = os.getenv("WEAVIATE_API_KEY") or None
    class_name: str = "PaperChunk"
    vector_dim: int = 1536  # text-embedding-3-small
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

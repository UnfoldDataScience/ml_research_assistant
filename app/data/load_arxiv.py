# app/data/load_arxiv.py
from typing import List, Dict
from pathlib import Path

from datasets import load_dataset

from app.config import config


def load_arxiv_papers() -> List[Dict]:
    """
    Load a subset of the arxiv portion of the scientific_papers dataset.

    Returns a list of dicts with keys: id, title, abstract, article.
    """
    ds_conf = config.dataset
    print(f"Loading dataset {ds_conf.hf_name}/{ds_conf.hf_config}...")

    # Put HF cache under the project root (e.g. F:\YouTubeProjects\ml_research_assistant\hf_cache)
    project_root = Path(__file__).resolve().parents[2]
    cache_dir = project_root / "hf_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"Using Hugging Face cache dir: {cache_dir}")

    dataset = load_dataset(
        ds_conf.hf_name,
        ds_conf.hf_config,
        split="train",
        trust_remote_code=True,          # required by scientific_papers
        cache_dir=str(cache_dir),        # 👈 force cache onto F: here
    )

    max_papers = min(ds_conf.max_papers, len(dataset))
    print(f"Using first {max_papers} papers")

    papers = []
    for i in range(max_papers):
        row = dataset[i]
        papers.append(
            {
                "id": str(i),
                "title": row.get("title", ""),
                "abstract": " ".join(row.get("abstract", []))
                if isinstance(row.get("abstract"), list)
                else row.get("abstract", ""),
                "article": " ".join(row.get("article", []))
                if isinstance(row.get("article"), list)
                else row.get("article", ""),
            }
        )
    return papers

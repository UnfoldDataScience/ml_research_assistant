# app/data/load_arxiv.py
import shutil
import time
from typing import List, Dict
from pathlib import Path

from datasets import load_dataset

from app.config import config


def _cleanup_incomplete_cache(cache_dir: Path) -> None:
    """
    Remove incomplete cache directories that might be locked by previous failed runs.
    This helps prevent PermissionError on Windows.
    """
    # Find all directories ending with .incomplete
    for item in cache_dir.rglob("*"):
        if not item.is_dir() or not item.name.endswith(".incomplete"):
            continue
        incomplete_dir = item
        try:
            print(f"Cleaning up incomplete cache: {incomplete_dir}")
            # On Windows, files might be locked briefly, so retry with a small delay
            for attempt in range(3):
                try:
                    shutil.rmtree(incomplete_dir, ignore_errors=True)
                    break
                except PermissionError:
                    if attempt < 2:
                        time.sleep(0.5)
                    else:
                        print(f"Warning: Could not remove {incomplete_dir}. "
                              "You may need to close other processes or delete it manually.")
        except Exception as e:
            print(f"Warning: Error cleaning up {incomplete_dir}: {e}")


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
    
    # Clean up any incomplete cache directories to prevent PermissionError
    _cleanup_incomplete_cache(cache_dir)

    dataset = load_dataset(
        ds_conf.hf_name,
        ds_conf.hf_config,
        split="train",
        trust_remote_code=True,          # required by scientific_papers
        cache_dir=str(cache_dir),        # 👈 force cache onto F: here
        streaming=True,                   # 👈 stream data instead of downloading full dataset
    )

    max_papers = ds_conf.max_papers
    print(f"Streaming first {max_papers} papers (no full download needed)")

    papers = []
    for i, row in enumerate(dataset):
        if i >= max_papers:
            break
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

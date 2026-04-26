"""Simple file-based result cache keyed by {repo, pr_number, head_sha}."""

import hashlib
import json
import os
from config import settings


def _cache_key(repo: str, pr_number: int, head_sha: str) -> str:
    raw = f"{repo}:{pr_number}:{head_sha}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_cached(repo: str, pr_number: int, head_sha: str) -> dict | None:
    key = _cache_key(repo, pr_number, head_sha)
    path = os.path.join(settings.cache_dir, f"{key}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def set_cached(repo: str, pr_number: int, head_sha: str, result: dict):
    os.makedirs(settings.cache_dir, exist_ok=True)
    key = _cache_key(repo, pr_number, head_sha)
    path = os.path.join(settings.cache_dir, f"{key}.json")
    with open(path, "w") as f:
        json.dump(result, f)

"""Data types for Smart-review analysis."""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class Contribution:
    """Per-file contribution metrics for a single author, derived from PyDriller."""
    file: str
    lines_authored: int
    commits: int
    first_contribution: str  # ISO date
    last_contribution: str   # ISO date
    ownership_pct: float     # 0.0–100.0


@dataclass
class Reviewer:
    """A reviewer candidate with computed scores and per-file contributions."""
    handle: str
    display_name: str
    expertise_score: float   # 0–100
    seniority_score: float   # 0–100
    contributions: list[Contribution] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FileSummary:
    """Summary of a changed file in a PR."""
    path: str
    additions: int
    deletions: int
    patch_snippet: str = ""  # small diff excerpt


@dataclass
class ScoredPR:
    """Complete analysis result for a pull request."""
    repo: str
    pr_number: int
    title: str
    author: str
    url: str
    closed_at: str
    files_changed: list[FileSummary] = field(default_factory=list)
    actual_reviewers: list[Reviewer] = field(default_factory=list)
    best_pick: Optional[Reviewer] = None
    reasoning: str = ""
    cost_of_gap: str = ""
    computed_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

"""
Expertise and seniority scoring for Smart-review.

All inputs are PyDriller-derivable: commits, lines authored, first/last
contribution dates, and ownership percentage. No invented metrics.

Scoring approach:
- Expertise (0–100): How deeply does this person know the specific files
  being changed? Weighted blend of ownership share, commit density, and
  recency of contributions.
- Seniority (0–100): How long and consistently has this person been
  involved with these files? Weighted blend of tenure span, total commits,
  and consistency (how evenly distributed contributions are over time).

Both scores are computed per-file, then aggregated across all files changed
in the PR using a weighted average (files with more changes weigh more).
"""

from __future__ import annotations
import math
from datetime import datetime, timezone
from .types import Contribution


# --- Expertise scoring ---

# Weights for expertise sub-components (must sum to 1.0)
_EXP_W_OWNERSHIP = 0.40   # ownership % of file
_EXP_W_COMMITS = 0.25     # commit count relative to max contributor
_EXP_W_LINES = 0.15       # lines authored relative to max contributor
_EXP_W_RECENCY = 0.20     # how recently they contributed


def _recency_factor(last_contribution: str, reference_date: str) -> float:
    """Score 0–1 based on how recently the author contributed.
    Uses exponential decay with a half-life of 365 days."""
    last = _parse_date(last_contribution)
    ref = _parse_date(reference_date)
    days_ago = max((ref - last).days, 0)
    half_life = 365.0
    return math.exp(-0.693 * days_ago / half_life)


def compute_expertise_score(
    contribution: Contribution,
    max_commits_for_file: int,
    max_lines_for_file: int,
    reference_date: str,
) -> float:
    """Compute expertise score (0–100) for a single file contribution.

    Args:
        contribution: The author's contribution to this file.
        max_commits_for_file: Highest commit count by any author on this file.
        max_lines_for_file: Highest lines-authored by any author on this file.
        reference_date: ISO date of PR close (for recency calculation).
    """
    # Normalize each component to 0–1
    ownership = min(contribution.ownership_pct / 100.0, 1.0)

    commits_norm = (
        contribution.commits / max_commits_for_file
        if max_commits_for_file > 0 else 0.0
    )

    lines_norm = (
        contribution.lines_authored / max_lines_for_file
        if max_lines_for_file > 0 else 0.0
    )

    recency = _recency_factor(contribution.last_contribution, reference_date)

    raw = (
        _EXP_W_OWNERSHIP * ownership
        + _EXP_W_COMMITS * commits_norm
        + _EXP_W_LINES * lines_norm
        + _EXP_W_RECENCY * recency
    )
    return round(min(raw * 100.0, 100.0), 1)


# --- Seniority scoring ---

# Weights for seniority sub-components (must sum to 1.0)
_SEN_W_TENURE = 0.45       # span from first to last contribution
_SEN_W_TOTAL_COMMITS = 0.30  # total commit count (depth of involvement)
_SEN_W_CONSISTENCY = 0.25  # how spread out contributions are over time


def _tenure_factor(first_contribution: str, reference_date: str) -> float:
    """Score 0–1 based on how long the author has been contributing.
    Saturates at ~4 years (1460 days)."""
    first = _parse_date(first_contribution)
    ref = _parse_date(reference_date)
    days = max((ref - first).days, 0)
    cap = 1460.0  # ~4 years
    return min(days / cap, 1.0)


def _consistency_factor(
    first_contribution: str,
    last_contribution: str,
    commits: int,
) -> float:
    """Score 0–1 based on how evenly distributed contributions are.
    A single burst scores low; steady contributions score high.
    Approximated as: commit_density * span_coverage."""
    first = _parse_date(first_contribution)
    last = _parse_date(last_contribution)
    span_days = max((last - first).days, 1)

    # Expected commits if contributing ~once per 30 days over the span
    expected = span_days / 30.0
    if expected < 1:
        expected = 1.0
    density = min(commits / expected, 1.0)

    # Span coverage: longer spans are better (capped at 2 years)
    span_score = min(span_days / 730.0, 1.0)

    return density * 0.5 + span_score * 0.5


def compute_seniority_score(
    contribution: Contribution,
    max_commits_for_file: int,
    reference_date: str,
) -> float:
    """Compute seniority score (0–100) for a single file contribution.

    Args:
        contribution: The author's contribution to this file.
        max_commits_for_file: Highest commit count by any author on this file.
        reference_date: ISO date of PR close (for tenure calculation).
    """
    tenure = _tenure_factor(contribution.first_contribution, reference_date)

    commits_norm = (
        contribution.commits / max_commits_for_file
        if max_commits_for_file > 0 else 0.0
    )

    consistency = _consistency_factor(
        contribution.first_contribution,
        contribution.last_contribution,
        contribution.commits,
    )

    raw = (
        _SEN_W_TENURE * tenure
        + _SEN_W_TOTAL_COMMITS * commits_norm
        + _SEN_W_CONSISTENCY * consistency
    )
    return round(min(raw * 100.0, 100.0), 1)


# --- Aggregate scoring across files ---

def aggregate_scores(
    per_file_expertise: list[tuple[float, float]],
    per_file_seniority: list[tuple[float, float]],
) -> tuple[float, float]:
    """Weighted average of per-file scores.

    Each list contains (score, weight) tuples where weight is typically
    the number of lines changed in that file.

    Returns (expertise_score, seniority_score) both 0–100.
    """
    def _weighted_avg(scored: list[tuple[float, float]]) -> float:
        total_weight = sum(w for _, w in scored)
        if total_weight == 0:
            return 0.0
        return sum(s * w for s, w in scored) / total_weight

    return (
        round(_weighted_avg(per_file_expertise), 1),
        round(_weighted_avg(per_file_seniority), 1),
    )


# --- Helpers ---

def _parse_date(iso_date: str) -> datetime:
    """Parse an ISO date string to a datetime."""
    if isinstance(iso_date, datetime):
        return iso_date
    # Handle various ISO formats
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(iso_date, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {iso_date}")

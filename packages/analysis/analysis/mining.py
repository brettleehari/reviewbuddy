"""
PyDriller-based git history mining for Smart-review.

Extracts per-author, per-file contribution metrics from a local git repo.
Uses per-file traversal with PyDriller's filepath filter for efficiency
on large repos — only commits touching each target file are visited.
"""

from __future__ import annotations
import os
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pydriller import Repository
from .types import Contribution

logger = logging.getLogger(__name__)


def mine_contributions(
    repo_path: str,
    files: list[str],
    exclude_authors: set[str] | None = None,
    before_date: datetime | None = None,
) -> dict[str, dict[str, Contribution]]:
    """Mine contribution data for specified files from a git repo.

    Uses per-file traversal for efficiency — each file is mined
    independently using PyDriller's filepath filter.

    Args:
        repo_path: Path to the local git repo clone.
        files: List of file paths (relative to repo root) to analyze.
        exclude_authors: Set of author names/emails to exclude (lowercased).
        before_date: Only consider commits before this date (e.g., PR merge date).

    Returns:
        Nested dict: {file_path: {author_email: Contribution}}
    """
    exclude = {a.lower() for a in (exclude_authors or set())}
    result: dict[str, dict[str, Contribution]] = {}

    for filepath in files:
        logger.info(f"Mining history for: {filepath}")
        file_result = _mine_single_file(
            repo_path, filepath, exclude, before_date
        )
        if file_result:
            result[filepath] = file_result

    return result


def _mine_single_file(
    repo_path: str,
    filepath: str,
    exclude: set[str],
    before_date: datetime | None,
) -> dict[str, Contribution]:
    """Mine contribution data for a single file."""
    stats: dict[str, _FileStats] = defaultdict(_FileStats)
    total_lines = 0

    try:
        kwargs = {"path_to_repo": repo_path, "filepath": filepath}
        if before_date:
            kwargs["to"] = before_date

        for commit in Repository(**kwargs).traverse_commits():
            author_email = commit.author.email.lower()
            author_name = commit.author.name

            if author_email in exclude or author_name.lower() in exclude:
                continue

            for mod in commit.modified_files:
                if not _is_target_file(mod, filepath):
                    continue

                lines_added = mod.added_lines
                fs = stats[author_email]
                fs.author_name = author_name
                fs.author_email = commit.author.email
                fs.commits += 1
                fs.lines_authored += lines_added
                total_lines += lines_added

                commit_date = commit.author_date
                if fs.first_contribution is None or commit_date < fs.first_contribution:
                    fs.first_contribution = commit_date
                if fs.last_contribution is None or commit_date > fs.last_contribution:
                    fs.last_contribution = commit_date

    except Exception as e:
        logger.error(f"Error mining {filepath}: {e}")
        return {}

    # Build Contribution objects
    result: dict[str, Contribution] = {}
    for email, fs in stats.items():
        ownership_pct = (
            (fs.lines_authored / total_lines * 100.0) if total_lines > 0 else 0.0
        )
        result[email] = Contribution(
            file=filepath,
            lines_authored=fs.lines_authored,
            commits=fs.commits,
            first_contribution=fs.first_contribution.isoformat() if fs.first_contribution else "",
            last_contribution=fs.last_contribution.isoformat() if fs.last_contribution else "",
            ownership_pct=round(ownership_pct, 1),
        )

    logger.info(f"  {filepath}: {len(result)} contributors, {total_lines} total lines")
    return result


def mine_contributions_flat(
    repo_path: str,
    files: list[str],
    exclude_authors: set[str] | None = None,
    before_date: datetime | None = None,
) -> dict[str, list[Contribution]]:
    """Mine contributions and return grouped by author.

    Returns: {author_email: [Contribution, ...]}
    """
    raw = mine_contributions(repo_path, files, exclude_authors, before_date)
    by_author: dict[str, list[Contribution]] = defaultdict(list)
    for file_path, authors in raw.items():
        for author_email, contrib in authors.items():
            by_author[author_email].append(contrib)
    return dict(by_author)


def _is_target_file(mod, filepath: str) -> bool:
    """Check if a modification matches the target filepath."""
    for candidate in (mod.new_path, mod.old_path):
        if candidate is None:
            continue
        if candidate == filepath:
            return True
        # Match by basename for renames
        if os.path.basename(candidate) == os.path.basename(filepath):
            return True
    return False


class _FileStats:
    """Accumulator for per-file stats during mining."""
    __slots__ = (
        'author_name', 'author_email', 'commits',
        'lines_authored', 'first_contribution', 'last_contribution',
    )

    def __init__(self):
        self.author_name: str = ""
        self.author_email: str = ""
        self.commits: int = 0
        self.lines_authored: int = 0
        self.first_contribution: datetime | None = None
        self.last_contribution: datetime | None = None

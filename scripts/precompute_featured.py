#!/usr/bin/env python3
"""
Pre-compute featured PR analysis data for the Smart-review demo.

Fetches PR metadata via GitHub API, clones repos, runs PyDriller analysis,
computes expertise + seniority scores, and writes JSON to data/featured-prs/.

Usage:
    python scripts/precompute_featured.py [--pr OWNER/REPO#NUM] [--all]

Requires: GITHUB_TOKEN env var (for API calls), git, PyDriller.
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'analysis'))

from analysis.mining import mine_contributions_flat
from analysis.scoring import (
    compute_expertise_score,
    compute_seniority_score,
    aggregate_scores,
)
from analysis.types import Contribution, FileSummary, Reviewer, ScoredPR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)
# Silence PyDriller's verbose commit logging
logging.getLogger("pydriller").setLevel(logging.WARNING)

# GitHub API helpers
try:
    import requests
except ImportError:
    print("pip install requests", file=sys.stderr)
    sys.exit(1)

GITHUB_API = "https://api.github.com"


def gh_headers():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def fetch_pr_metadata(owner: str, repo: str, pr_num: int) -> dict:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_num}"
    r = requests.get(url, headers=gh_headers())
    r.raise_for_status()
    return r.json()


def fetch_pr_files(owner: str, repo: str, pr_num: int) -> list[dict]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_num}/files"
    r = requests.get(url, headers=gh_headers(), params={"per_page": 100})
    r.raise_for_status()
    return r.json()


def fetch_pr_reviews(owner: str, repo: str, pr_num: int) -> list[dict]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_num}/reviews"
    r = requests.get(url, headers=gh_headers())
    r.raise_for_status()
    return r.json()


def clone_repo(owner: str, repo: str, clone_dir: str, merge_sha: str | None = None) -> str:
    """Clone a repo and optionally checkout at a specific commit. Returns path to clone."""
    repo_url = f"https://github.com/{owner}/{repo}.git"
    dest = os.path.join(clone_dir, f"{repo}-{merge_sha[:8]}" if merge_sha else repo)
    if os.path.exists(dest):
        logger.info(f"Using existing clone: {dest}")
        # Still checkout the right SHA if specified
        if merge_sha:
            subprocess.run(
                ["git", "-C", dest, "checkout", merge_sha],
                check=True, capture_output=True, timeout=60,
            )
        return dest

    logger.info(f"Cloning {owner}/{repo} ...")
    cmd = ["git", "clone", repo_url, dest]
    subprocess.run(cmd, check=True, capture_output=True, timeout=600)

    if merge_sha:
        logger.info(f"Checking out merge commit {merge_sha[:12]}...")
        subprocess.run(
            ["git", "-C", dest, "checkout", merge_sha],
            check=True, capture_output=True, timeout=60,
        )

    logger.info(f"Cloned to {dest}")
    return dest


def resolve_email_to_github_handle(email: str, owner: str = "", repo: str = "") -> str:
    """Resolve a git commit email to a GitHub username."""
    import time

    # Common noreply pattern
    if "noreply.github.com" in email:
        parts = email.split("@")[0]
        if "+" in parts:
            return parts.split("+")[1]
        return parts

    # Best method: search commits in the repo by author email
    if owner and repo:
        try:
            url = f"{GITHUB_API}/search/commits"
            r = requests.get(url, headers={
                **gh_headers(),
                "Accept": "application/vnd.github.cloak-preview+json",
            }, params={
                "q": f"author-email:{email} repo:{owner}/{repo}",
                "per_page": 1,
            })
            if r.status_code == 200:
                items = r.json().get("items", [])
                if items and items[0].get("author"):
                    return items[0]["author"]["login"]
            # Rate limit: commit search has 30 req/min
            time.sleep(2)
        except Exception:
            pass

    # Fallback: search users by email
    try:
        url = f"{GITHUB_API}/search/users"
        r = requests.get(url, headers=gh_headers(), params={
            "q": f"{email} in:email",
            "per_page": 1,
        })
        if r.status_code == 200:
            items = r.json().get("items", [])
            if items:
                return items[0]["login"]
    except Exception:
        pass

    # Last resort: email prefix
    return email.split("@")[0]


# Cache for email → handle resolution
_handle_cache: dict[str, str] = {}


def resolve_email_cached(email: str, owner: str = "", repo: str = "") -> str:
    if email not in _handle_cache:
        _handle_cache[email] = resolve_email_to_github_handle(email, owner, repo)
        logger.info(f"  Resolved {email} -> {_handle_cache[email]}")
    return _handle_cache[email]


def analyze_pr(owner: str, repo: str, pr_num: int, clone_base: str) -> ScoredPR:
    """Full analysis pipeline for a single PR."""
    logger.info(f"=== Analyzing {owner}/{repo}#{pr_num} ===")

    # 1. Fetch PR metadata
    pr = fetch_pr_metadata(owner, repo, pr_num)
    pr_files = fetch_pr_files(owner, repo, pr_num)
    pr_reviews = fetch_pr_reviews(owner, repo, pr_num)

    title = pr["title"]
    author = pr["user"]["login"]
    merged_at = pr.get("merged_at") or pr.get("closed_at") or ""
    pr_url = pr["html_url"]

    # 2. Build file summaries
    file_paths = [f["filename"] for f in pr_files]
    files_changed = []
    for f in pr_files:
        patch = f.get("patch", "")
        snippet = "\n".join(patch.split("\n")[:10]) if patch else ""
        files_changed.append(FileSummary(
            path=f["filename"],
            additions=f.get("additions", 0),
            deletions=f.get("deletions", 0),
            patch_snippet=snippet,
        ))

    logger.info(f"PR touches {len(file_paths)} files: {file_paths}")

    # 3. Get actual reviewers from reviews
    actual_reviewer_handles = set()
    for review in pr_reviews:
        if review["user"]["login"] != author:
            actual_reviewer_handles.add(review["user"]["login"])

    logger.info(f"Actual reviewers: {actual_reviewer_handles}")

    # 4. Clone repo and run PyDriller
    merge_date = None
    if merged_at:
        merge_date = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))

    merge_sha = pr.get("merge_commit_sha")
    repo_path = clone_repo(owner, repo, clone_base, merge_sha)

    # Mine contributions for all files
    contributions_by_author = mine_contributions_flat(
        repo_path,
        file_paths,
        exclude_authors={author.lower()},
        before_date=merge_date,
    )

    logger.info(f"Found {len(contributions_by_author)} contributor candidates")

    # 5. Resolve emails to GitHub handles and compute scores
    logger.info("Resolving git emails to GitHub handles...")
    reference_date = merged_at or datetime.now(timezone.utc).isoformat()
    scored_candidates = _score_all_candidates(
        contributions_by_author, file_paths, files_changed, reference_date,
        owner, repo,
    )

    if not scored_candidates:
        logger.warning("No candidates found — check file paths and clone")
        return ScoredPR(
            repo=f"{owner}/{repo}",
            pr_number=pr_num,
            title=title,
            author=author,
            url=pr_url,
            closed_at=merged_at,
            files_changed=files_changed,
            computed_at=datetime.now(timezone.utc).isoformat(),
        )

    # 6. Match actual reviewers to scored candidates (by email → handle mapping)
    actual_reviewers, remaining = _partition_actual_reviewers(
        scored_candidates, actual_reviewer_handles
    )

    # 7. Find best pick from remaining (non-actual) reviewers
    best_pick = None
    if remaining:
        best_pick = max(remaining, key=lambda r: r.expertise_score + r.seniority_score)
    elif scored_candidates:
        # All candidates were actual reviewers — best pick is top scorer overall
        best_pick = max(scored_candidates, key=lambda r: r.expertise_score + r.seniority_score)

    # 8. Generate reasoning
    reasoning = _generate_reasoning(actual_reviewers, best_pick, file_paths)
    cost_of_gap = _generate_cost_of_gap(actual_reviewers, best_pick, contributions_by_author)

    return ScoredPR(
        repo=f"{owner}/{repo}",
        pr_number=pr_num,
        title=title,
        author=author,
        url=pr_url,
        closed_at=merged_at,
        files_changed=files_changed,
        actual_reviewers=actual_reviewers,
        best_pick=best_pick,
        reasoning=reasoning,
        cost_of_gap=cost_of_gap,
        computed_at=datetime.now(timezone.utc).isoformat(),
    )


def _score_all_candidates(
    contributions_by_author: dict[str, list[Contribution]],
    file_paths: list[str],
    files_changed: list[FileSummary],
    reference_date: str,
    owner: str = "",
    repo: str = "",
) -> list[Reviewer]:
    """Score all contributor candidates across all files."""
    # Pre-compute max stats per file
    max_commits: dict[str, int] = {}
    max_lines: dict[str, int] = {}
    for email, contribs in contributions_by_author.items():
        for c in contribs:
            max_commits[c.file] = max(max_commits.get(c.file, 0), c.commits)
            max_lines[c.file] = max(max_lines.get(c.file, 0), c.lines_authored)

    # File weights based on change size
    file_weights = {}
    for f in files_changed:
        file_weights[f.path] = max(f.additions + f.deletions, 1)

    # First pass: score everyone with email-based handles
    # Then resolve GitHub handles only for top candidates
    scored_raw = []
    for email, contribs in contributions_by_author.items():
        expertise_parts_raw = []
        seniority_parts_raw = []
        for c in contribs:
            w = file_weights.get(c.file, 1)
            exp = compute_expertise_score(c, max_commits.get(c.file, 1), max_lines.get(c.file, 1), reference_date)
            sen = compute_seniority_score(c, max_commits.get(c.file, 1), reference_date)
            expertise_parts_raw.append((exp, w))
            seniority_parts_raw.append((sen, w))
        agg_exp, agg_sen = aggregate_scores(expertise_parts_raw, seniority_parts_raw)
        scored_raw.append((email, contribs, agg_exp, agg_sen))
    scored_raw.sort(key=lambda x: x[2] + x[3], reverse=True)

    # Only resolve top 15 candidates (saves API calls)
    top_emails = [e for e, _, _, _ in scored_raw[:15]]
    email_to_handle: dict[str, str] = {}
    for email in top_emails:
        email_to_handle[email] = resolve_email_cached(email, owner, repo)

    # Merge candidates with same GitHub handle
    scored = []
    seen_handles = set()
    for email, contribs, _, _ in scored_raw[:15]:
        gh_handle = email_to_handle.get(email, email.split("@")[0])
        if gh_handle in seen_handles:
            continue
        seen_handles.add(gh_handle)

        # Merge contributions from all emails that map to the same handle
        all_contribs = list(contribs)
        for other_email, other_contribs in contributions_by_author.items():
            if other_email != email and email_to_handle.get(other_email) == gh_handle:
                all_contribs.extend(other_contribs)

        expertise_parts = []
        seniority_parts = []

        for c in all_contribs:
            w = file_weights.get(c.file, 1)
            exp = compute_expertise_score(
                c,
                max_commits.get(c.file, 1),
                max_lines.get(c.file, 1),
                reference_date,
            )
            sen = compute_seniority_score(
                c,
                max_commits.get(c.file, 1),
                reference_date,
            )
            expertise_parts.append((exp, w))
            seniority_parts.append((sen, w))

        agg_exp, agg_sen = aggregate_scores(expertise_parts, seniority_parts)

        scored.append(Reviewer(
            handle=gh_handle,
            display_name=gh_handle,
            expertise_score=agg_exp,
            seniority_score=agg_sen,
            contributions=all_contribs,
        ))

    # Sort by combined score descending
    scored.sort(key=lambda r: r.expertise_score + r.seniority_score, reverse=True)
    return scored


def _partition_actual_reviewers(
    scored: list[Reviewer],
    actual_handles: set[str],
) -> tuple[list[Reviewer], list[Reviewer]]:
    """Split scored candidates into actual reviewers and remaining."""
    actual_lower = {h.lower() for h in actual_handles}
    actual = []
    remaining = []
    for r in scored:
        if r.handle.lower() in actual_lower:
            actual.append(r)
        else:
            remaining.append(r)
    return actual, remaining


def _generate_reasoning(
    actual: list[Reviewer],
    best: Reviewer | None,
    files: list[str],
) -> str:
    if not best:
        return "Insufficient contribution data to suggest an alternative reviewer."

    if not actual:
        return (
            f"No formal reviewer was assigned to this PR. "
            f"Smart-review's best pick is {best.handle} with an expertise score of "
            f"{best.expertise_score} and seniority score of {best.seniority_score}, "
            f"based on their deep contribution history across the affected files."
        )

    actual_best = max(actual, key=lambda r: r.expertise_score + r.seniority_score)
    exp_gap = best.expertise_score - actual_best.expertise_score
    sen_gap = best.seniority_score - actual_best.seniority_score

    parts = []
    if exp_gap > 5:
        parts.append(
            f"{best.handle} has {exp_gap:.0f} points higher expertise than the "
            f"top actual reviewer ({actual_best.handle}), driven by higher ownership "
            f"share and more recent contributions to the affected files"
        )
    if sen_gap > 5:
        parts.append(
            f"{best.handle} has {sen_gap:.0f} points higher seniority, reflecting "
            f"a longer contribution history and more consistent involvement"
        )

    if not parts:
        return (
            f"The actual reviewer(s) scored within range of the best available candidate. "
            f"The review assignment was reasonable for this change."
        )

    return ". ".join(parts) + "."


def _generate_cost_of_gap(
    actual: list[Reviewer],
    best: Reviewer | None,
    contributions_by_author: dict[str, list[Contribution]],
) -> str:
    if not best or not actual:
        return ""

    actual_best = max(actual, key=lambda r: r.expertise_score + r.seniority_score)

    # Find concrete metrics to cite
    best_contribs = {c.file: c for c in best.contributions}
    actual_contribs = {c.file: c for c in actual_best.contributions}

    gaps = []
    for fpath, bc in best_contribs.items():
        ac = actual_contribs.get(fpath)
        if ac is None:
            gaps.append(
                f"The actual reviewer had no recorded contributions to {os.path.basename(fpath)}, "
                f"while {best.handle} has {bc.commits} commits and {bc.ownership_pct:.0f}% ownership"
            )
        elif bc.ownership_pct > ac.ownership_pct + 10:
            gaps.append(
                f"On {os.path.basename(fpath)}, {best.handle} owns {bc.ownership_pct:.0f}% vs "
                f"{actual_best.handle}'s {ac.ownership_pct:.0f}% — the actual reviewer was likely "
                f"less familiar with the module's invariants and edge cases"
            )

    if not gaps:
        return (
            f"The scoring gap suggests the actual reviewer may have had less context on "
            f"recent changes to these files, potentially missing subtle interaction effects."
        )

    return ". ".join(gaps[:2]) + "."


# --- Featured PR configs ---

FEATURED_PRS = [
    {"owner": "rails", "repo": "rails", "pr": 38211},
    {"owner": "facebook", "repo": "react", "pr": 18580},
    {"owner": "huggingface", "repo": "transformers", "pr": 8308},
    {"owner": "prometheus", "repo": "prometheus", "pr": 6643},
]


def main():
    parser = argparse.ArgumentParser(description="Pre-compute featured PR analysis")
    parser.add_argument("--pr", help="Single PR: owner/repo#num")
    parser.add_argument("--all", action="store_true", help="Process all featured PRs")
    parser.add_argument("--clone-dir", default=None, help="Directory for repo clones")
    parser.add_argument("--output-dir", default=None, help="Output JSON directory")
    args = parser.parse_args()

    output_dir = args.output_dir or os.path.join(
        os.path.dirname(__file__), '..', 'data', 'featured-prs'
    )
    os.makedirs(output_dir, exist_ok=True)

    clone_dir = args.clone_dir or tempfile.mkdtemp(prefix="smartreview-")
    logger.info(f"Clone directory: {clone_dir}")

    prs_to_process = []
    if args.pr:
        # Parse owner/repo#num
        repo_part, num = args.pr.split("#")
        owner, repo = repo_part.split("/")
        prs_to_process.append({"owner": owner, "repo": repo, "pr": int(num)})
    elif args.all:
        prs_to_process = FEATURED_PRS
    else:
        prs_to_process = FEATURED_PRS

    for pr_config in prs_to_process:
        try:
            result = analyze_pr(
                pr_config["owner"],
                pr_config["repo"],
                pr_config["pr"],
                clone_dir,
            )
            filename = f"{pr_config['repo']}-{pr_config['pr']}.json"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w") as f:
                f.write(result.to_json())
            logger.info(f"Wrote {filepath}")
        except Exception as e:
            logger.error(f"Failed to process {pr_config}: {e}", exc_info=True)

    logger.info("Done!")


if __name__ == "__main__":
    main()

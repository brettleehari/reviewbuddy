"""Live PR analysis service. Clones repo, runs PyDriller, returns scores."""

import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from collections import defaultdict

import httpx

# Add packages/analysis to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages', 'analysis'))

from analysis.mining import mine_contributions_flat
from analysis.scoring import (
    compute_expertise_score,
    compute_seniority_score,
    aggregate_scores,
)
from analysis.types import Contribution, FileSummary, Reviewer, ScoredPR

from config import settings

logger = logging.getLogger(__name__)


async def analyze_pr(owner: str, repo: str, pr_number: int, token: str) -> dict:
    """Full analysis pipeline for a live PR request."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Fetch PR metadata
        pr_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
            headers=headers,
        )
        pr_resp.raise_for_status()
        pr = pr_resp.json()

        # Verify public repo
        repo_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=headers,
        )
        repo_resp.raise_for_status()
        repo_data = repo_resp.json()
        if repo_data.get("private"):
            raise ValueError("Smart-review only works with public repositories.")

        # Check repo size
        size_mb = repo_data.get("size", 0) / 1024
        if size_mb > settings.max_repo_size_mb:
            raise ValueError(
                f"Repository is too large ({size_mb:.0f}MB). "
                f"Limit is {settings.max_repo_size_mb}MB."
            )

        # 2. Fetch PR files
        files_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files",
            headers=headers,
            params={"per_page": 100},
        )
        files_resp.raise_for_status()
        pr_files = files_resp.json()

        if len(pr_files) > settings.max_files_per_pr:
            raise ValueError(
                f"PR touches {len(pr_files)} files. "
                f"Limit is {settings.max_files_per_pr}."
            )

        # 3. Fetch reviews
        reviews_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
            headers=headers,
        )
        reviews_resp.raise_for_status()
        pr_reviews = reviews_resp.json()

    # Extract metadata
    title = pr["title"]
    author = pr["user"]["login"]
    merged_at = pr.get("merged_at") or pr.get("closed_at") or ""
    pr_url = pr["html_url"]
    merge_sha = pr.get("merge_commit_sha")
    head_sha = pr.get("head", {}).get("sha", "")

    file_paths = [f["filename"] for f in pr_files]
    files_changed = []
    for f in pr_files:
        patch = f.get("patch", "")
        snippet = "\n".join(patch.split("\n")[:10]) if patch else ""
        files_changed.append({
            "path": f["filename"],
            "additions": f.get("additions", 0),
            "deletions": f.get("deletions", 0),
            "patch_snippet": snippet,
        })

    actual_reviewer_handles = set()
    for review in pr_reviews:
        if review["user"]["login"] != author:
            actual_reviewer_handles.add(review["user"]["login"])

    # 4. Clone repo
    merge_date = None
    if merged_at:
        merge_date = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))

    repo_path = _clone_repo(owner, repo, token, merge_sha)

    try:
        # 5. Mine contributions
        contributions_by_author = mine_contributions_flat(
            repo_path,
            file_paths,
            exclude_authors={author.lower()},
            before_date=merge_date,
        )

        # 6. Score candidates
        reference_date = merged_at or datetime.now(timezone.utc).isoformat()
        scored = _score_candidates(
            contributions_by_author, file_paths, files_changed, reference_date
        )

        # 7. Resolve handles for top candidates
        top_emails = [s[0] for s in scored[:15]]
        email_to_handle = {}
        async with httpx.AsyncClient(timeout=10) as client:
            for email in top_emails:
                handle = await _resolve_handle(client, email, owner, repo, headers)
                email_to_handle[email] = handle

        # 8. Build reviewer objects
        actual_reviewers = []
        best_pick = None
        best_remaining = None

        seen_handles = set()
        for email, contribs, exp, sen in scored[:15]:
            handle = email_to_handle.get(email, email.split("@")[0])
            if handle in seen_handles:
                continue
            seen_handles.add(handle)

            reviewer = {
                "handle": handle,
                "display_name": handle,
                "expertise_score": exp,
                "seniority_score": sen,
                "contributions": [_contrib_dict(c) for c in contribs],
            }

            if handle.lower() in {h.lower() for h in actual_reviewer_handles}:
                actual_reviewers.append(reviewer)
            elif best_remaining is None:
                best_remaining = reviewer

        best_pick = best_remaining
        if not best_pick and scored:
            # All top candidates are actual reviewers; pick the best overall
            email, contribs, exp, sen = scored[0]
            handle = email_to_handle.get(email, email.split("@")[0])
            best_pick = {
                "handle": handle,
                "display_name": handle,
                "expertise_score": exp,
                "seniority_score": sen,
                "contributions": [_contrib_dict(c) for c in contribs],
            }

    finally:
        # Clean up clone
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)

    return {
        "repo": f"{owner}/{repo}",
        "pr_number": pr_number,
        "title": title,
        "author": author,
        "url": pr_url,
        "closed_at": merged_at,
        "files_changed": files_changed,
        "actual_reviewers": actual_reviewers,
        "best_pick": best_pick,
        "reasoning": _generate_reasoning(actual_reviewers, best_pick),
        "cost_of_gap": "",
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def _clone_repo(owner: str, repo: str, token: str, merge_sha: str | None) -> str:
    """Clone a public repo using the user's token."""
    clone_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"
    dest = os.path.join(settings.clone_dir, f"{repo}-{int(time.time())}")
    os.makedirs(settings.clone_dir, exist_ok=True)

    cmd = ["git", "clone", "--depth=2000", clone_url, dest]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)

    if merge_sha:
        try:
            subprocess.run(
                ["git", "-C", dest, "checkout", merge_sha],
                check=True, capture_output=True, timeout=30,
            )
        except subprocess.CalledProcessError:
            pass  # Stay on default branch if SHA not reachable in shallow clone

    return dest


def _score_candidates(
    contributions_by_author: dict[str, list],
    file_paths: list[str],
    files_changed: list[dict],
    reference_date: str,
) -> list[tuple[str, list, float, float]]:
    """Score all candidates. Returns sorted list of (email, contribs, exp, sen)."""
    max_commits: dict[str, int] = {}
    max_lines: dict[str, int] = {}
    for email, contribs in contributions_by_author.items():
        for c in contribs:
            max_commits[c.file] = max(max_commits.get(c.file, 0), c.commits)
            max_lines[c.file] = max(max_lines.get(c.file, 0), c.lines_authored)

    file_weights = {}
    for f in files_changed:
        file_weights[f["path"]] = max(f["additions"] + f["deletions"], 1)

    scored = []
    for email, contribs in contributions_by_author.items():
        exp_parts = []
        sen_parts = []
        for c in contribs:
            w = file_weights.get(c.file, 1)
            exp = compute_expertise_score(
                c, max_commits.get(c.file, 1), max_lines.get(c.file, 1), reference_date
            )
            sen = compute_seniority_score(c, max_commits.get(c.file, 1), reference_date)
            exp_parts.append((exp, w))
            sen_parts.append((sen, w))
        agg_exp, agg_sen = aggregate_scores(exp_parts, sen_parts)
        scored.append((email, contribs, agg_exp, agg_sen))

    scored.sort(key=lambda x: x[2] + x[3], reverse=True)
    return scored


async def _resolve_handle(
    client: httpx.AsyncClient,
    email: str,
    owner: str,
    repo: str,
    headers: dict,
) -> str:
    """Resolve git email to GitHub handle."""
    if "noreply.github.com" in email:
        parts = email.split("@")[0]
        return parts.split("+")[1] if "+" in parts else parts

    try:
        resp = await client.get(
            "https://api.github.com/search/commits",
            headers={**headers, "Accept": "application/vnd.github.cloak-preview+json"},
            params={"q": f"author-email:{email} repo:{owner}/{repo}", "per_page": 1},
        )
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            if items and items[0].get("author"):
                return items[0]["author"]["login"]
    except Exception:
        pass

    return email.split("@")[0]


def _contrib_dict(c) -> dict:
    return {
        "file": c.file,
        "lines_authored": c.lines_authored,
        "commits": c.commits,
        "first_contribution": c.first_contribution,
        "last_contribution": c.last_contribution,
        "ownership_pct": c.ownership_pct,
    }


def _generate_reasoning(actual: list[dict], best: dict | None) -> str:
    if not best:
        return "Insufficient contribution data to suggest an alternative reviewer."
    if not actual:
        return (
            f"No formal reviewer was assigned. Smart-review's pick is "
            f"@{best['handle']} with expertise {best['expertise_score']:.1f} "
            f"and seniority {best['seniority_score']:.1f}."
        )
    actual_best = max(actual, key=lambda r: r["expertise_score"] + r["seniority_score"])
    exp_gap = best["expertise_score"] - actual_best["expertise_score"]
    sen_gap = best["seniority_score"] - actual_best["seniority_score"]
    parts = []
    if exp_gap > 5:
        parts.append(
            f"@{best['handle']} scores {exp_gap:.0f} points higher on expertise "
            f"than @{actual_best['handle']}, driven by higher ownership and more "
            f"recent contributions to the affected files"
        )
    if sen_gap > 5:
        parts.append(
            f"@{best['handle']} scores {sen_gap:.0f} points higher on seniority, "
            f"reflecting longer and more consistent involvement"
        )
    if not parts:
        return "The assigned reviewer scored within range of the best available candidate."
    return ". ".join(parts) + "."

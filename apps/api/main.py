"""Smart-review API: OAuth exchange + live PR analysis."""

import asyncio
import logging
import re

import httpx
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from rate_limit import rate_limiter
from cache import get_cached, set_cached
from analyzer import analyze_pr

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("pydriller").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart-review API", version="1.0.0")

# CORS
origins = [o.strip() for o in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


# --- Models ---

class ExchangeRequest(BaseModel):
    code: str
    state: str | None = None


class ExchangeResponse(BaseModel):
    access_token: str
    login: str
    avatar_url: str


class AnalyzeRequest(BaseModel):
    pr_url: str


# --- Auth ---

@app.post("/auth/exchange", response_model=ExchangeResponse)
async def exchange_code(body: ExchangeRequest):
    """Exchange GitHub OAuth code for access token."""
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(503, "OAuth not configured on this server.")

    async with httpx.AsyncClient(timeout=15) as client:
        # Exchange code for token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": body.code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()

        if "access_token" not in token_data:
            error = token_data.get("error_description", "OAuth exchange failed.")
            raise HTTPException(400, error)

        access_token = token_data["access_token"]

        # Fetch user info
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(400, "Failed to fetch user info.")
        user = user_resp.json()

    return ExchangeResponse(
        access_token=access_token,
        login=user["login"],
        avatar_url=user.get("avatar_url", ""),
    )


# --- Analysis ---

_PR_URL_PATTERN = re.compile(
    r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
)


@app.post("/analyze")
async def analyze(body: AnalyzeRequest, authorization: str = Header()):
    """Analyze a public GitHub PR."""
    # Validate token
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "Missing authorization token.")

    # Validate PR URL
    match = _PR_URL_PATTERN.match(body.pr_url.strip())
    if not match:
        raise HTTPException(400, "Invalid PR URL. Expected: https://github.com/owner/repo/pull/123")

    owner, repo, pr_num_str = match.groups()
    pr_number = int(pr_num_str)

    # Get user info for rate limiting
    async with httpx.AsyncClient(timeout=10) as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(401, "Invalid or expired token.")
        user = user_resp.json()

    user_id = user["id"]

    # Rate limit check
    allowed, msg = rate_limiter.check(user_id)
    if not allowed:
        raise HTTPException(429, msg)

    # Check cache
    # Get head SHA for cache key
    async with httpx.AsyncClient(timeout=10) as client:
        pr_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
            headers={"Authorization": f"token {token}"},
        )
        if pr_resp.status_code == 404:
            raise HTTPException(404, "PR not found.")
        pr_resp.raise_for_status()
        pr_data = pr_resp.json()

    head_sha = pr_data.get("head", {}).get("sha", "")
    cached = get_cached(f"{owner}/{repo}", pr_number, head_sha)
    if cached:
        logger.info(f"Cache hit for {owner}/{repo}#{pr_number}")
        return cached

    # Run analysis with timeout
    rate_limiter.record(user_id)
    try:
        result = await asyncio.wait_for(
            analyze_pr(owner, repo, pr_number, token),
            timeout=settings.analysis_timeout_seconds,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            504,
            f"Analysis timed out after {settings.analysis_timeout_seconds}s. "
            "The repository may be too large."
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(500, "Analysis failed. Please try again.")

    # Cache result
    if head_sha:
        set_cached(f"{owner}/{repo}", pr_number, head_sha, result)

    return result


# --- Health ---

@app.get("/health")
async def health():
    return {"status": "ok"}

"""Simple in-memory rate limiter by GitHub user ID."""

import time
from collections import defaultdict
from config import settings


class RateLimiter:
    def __init__(self):
        # user_id -> list of timestamps
        self._hourly: dict[int, list[float]] = defaultdict(list)
        self._daily: dict[int, list[float]] = defaultdict(list)

    def check(self, user_id: int) -> tuple[bool, str]:
        now = time.time()
        hour_ago = now - 3600
        day_ago = now - 86400

        # Prune old entries
        self._hourly[user_id] = [t for t in self._hourly[user_id] if t > hour_ago]
        self._daily[user_id] = [t for t in self._daily[user_id] if t > day_ago]

        if len(self._hourly[user_id]) >= settings.rate_limit_per_hour:
            return False, f"Hourly limit reached ({settings.rate_limit_per_hour}/hour). Try again later."
        if len(self._daily[user_id]) >= settings.rate_limit_per_day:
            return False, f"Daily limit reached ({settings.rate_limit_per_day}/day). Try again tomorrow."

        return True, ""

    def record(self, user_id: int):
        now = time.time()
        self._hourly[user_id].append(now)
        self._daily[user_id].append(now)


rate_limiter = RateLimiter()

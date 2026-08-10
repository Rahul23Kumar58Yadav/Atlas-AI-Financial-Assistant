"""
Simple in-memory sliding-window rate limiter. Keyed by an arbitrary string
so the same class works for "limit messages per Telegram user" (see
bot/middlewares/rate_limit.py) and "limit outbound calls per external API"
without duplicating the windowing logic.

In-memory means limits reset on process restart and don't share state
across multiple worker processes — fine for a single-process hackathon
deployment; swap the storage for Redis (INCR + EXPIRE, or a sorted set)
if this needs to scale horizontally.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        """Checks and records in one call — the common case of 'try to proceed, else reject'."""
        now = time.monotonic()
        hits = self._hits[key]

        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

        if len(hits) >= self.max_requests:
            return False

        hits.append(now)
        return True

    def seconds_until_next_slot(self, key: str) -> float:
        """How long until this key can make another request — useful for a friendly 'try again in Ns' message."""
        hits = self._hits[key]
        if not hits or len(hits) < self.max_requests:
            return 0.0
        oldest = hits[0]
        return max(0.0, self.window_seconds - (time.monotonic() - oldest))

    def reset(self, key: str) -> None:
        self._hits.pop(key, None)

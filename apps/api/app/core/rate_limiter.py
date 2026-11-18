"""
Rate Limiter Middleware & Dependency for QuantWeave Security Hardening.

Implements an in-memory sliding window rate limiter:
- Keyed by client IP and/or authenticated user ID
- Enforces request rate bounds per minute
- Automatically purges expired windows to prevent memory exhaustion
- Returns HTTP 429 Too Many Requests with standard Retry-After headers
- Safe bypass in automated testing environments
"""

from collections import defaultdict
import time
from typing import Dict, List, Optional
from fastapi import HTTPException, Request, status

from app.core.config import settings


class SlidingWindowRateLimiter:
    """
    Sliding window in-memory rate limiter with automated bucket cleanup.
    """

    def __init__(self, requests_per_minute: int = 60, cleanup_interval: int = 120):
        self.requests_per_minute = requests_per_minute
        self.cleanup_interval = cleanup_interval
        self._buckets: Dict[str, List[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    def _cleanup_old_records(self, now: float) -> None:
        """Periodically purges keys with no timestamps in the past 60 seconds."""
        if now - self._last_cleanup > self.cleanup_interval:
            window_start = now - 60.0
            stale_keys = [k for k, timestamps in self._buckets.items() if not timestamps or timestamps[-1] < window_start]
            for k in stale_keys:
                del self._buckets[k]
            self._last_cleanup = now

    def is_allowed(self, client_key: str, max_requests: Optional[int] = None) -> bool:
        """
        Checks whether the given client_key has exceeded rate limits.
        """
        # Testing bypass to ensure integration test suites run at full speed
        if settings.environment == "testing":
            return True

        now = time.time()
        self._cleanup_old_records(now)

        limit = max_requests or self.requests_per_minute
        window_start = now - 60.0

        # Filter timestamps in current 60s sliding window
        valid_timestamps = [t for t in self._buckets[client_key] if t > window_start]
        self._buckets[client_key] = valid_timestamps

        if len(valid_timestamps) >= limit:
            return False

        self._buckets[client_key].append(now)
        return True

    def check_rate_limit(self, request: Request, limit: int, route_tag: str = "general") -> None:
        """
        FastAPI dependency helper. Raises HTTP 429 if limit is exceeded.
        """
        client_ip = request.client.host if request.client else "127.0.0.1"
        # Combine IP and route tag for granular endpoint throttling
        client_key = f"{route_tag}:{client_ip}"

        if not self.is_allowed(client_key, max_requests=limit):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {route_tag}. Maximum {limit} requests per minute allowed.",
                headers={"Retry-After": "60"},
            )


# Global rate limiter instances for sensitive endpoints
rate_limiter = SlidingWindowRateLimiter(requests_per_minute=60)


def limit_login(request: Request) -> None:
    rate_limiter.check_rate_limit(request, limit=15, route_tag="login")


def limit_ai_chat(request: Request) -> None:
    rate_limiter.check_rate_limit(request, limit=25, route_tag="ai_chat")


def limit_grid_search(request: Request) -> None:
    rate_limiter.check_rate_limit(request, limit=10, route_tag="grid_search")


def limit_backtest(request: Request) -> None:
    rate_limiter.check_rate_limit(request, limit=20, route_tag="backtest")

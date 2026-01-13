"""Request rate limiting middleware for API abuse prevention.

Provides per-session rate limiting with different limits for auth vs generation endpoints.
Uses a sliding window algorithm for accurate rate tracking.
"""

import time
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class EndpointType(str, Enum):
    """Types of endpoints with different rate limits."""
    AUTH = "auth"
    GENERATION = "generation"
    OTHER = "other"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    # Auth endpoints: 100 requests per minute
    auth_limit: int = 100
    auth_window_seconds: int = 60

    # Generation endpoints: 20 requests per minute
    generation_limit: int = 20
    generation_window_seconds: int = 60

    # Other endpoints: 200 requests per minute (lenient)
    other_limit: int = 200
    other_window_seconds: int = 60


@dataclass
class RequestRecord:
    """Record of requests for a session-endpoint pair."""
    timestamps: list = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class RateLimiter:
    """Rate limiter using sliding window algorithm.

    Tracks requests per session and endpoint type, enforcing
    configurable rate limits.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize the rate limiter.

        Args:
            config: Rate limit configuration. Uses defaults if not provided.
        """
        self.config = config or RateLimitConfig()
        # Structure: {session_id: {endpoint_type: RequestRecord}}
        self._requests: dict[str, dict[EndpointType, RequestRecord]] = defaultdict(
            lambda: defaultdict(RequestRecord)
        )
        self._cleanup_lock = asyncio.Lock()
        self._last_cleanup = time.time()
        # Cleanup interval in seconds
        self._cleanup_interval = 300  # 5 minutes

    def _get_limit_and_window(self, endpoint_type: EndpointType) -> tuple[int, int]:
        """Get the rate limit and window for an endpoint type.

        Args:
            endpoint_type: The type of endpoint.

        Returns:
            Tuple of (max_requests, window_seconds).
        """
        if endpoint_type == EndpointType.AUTH:
            return self.config.auth_limit, self.config.auth_window_seconds
        elif endpoint_type == EndpointType.GENERATION:
            return self.config.generation_limit, self.config.generation_window_seconds
        else:
            return self.config.other_limit, self.config.other_window_seconds

    @staticmethod
    def classify_endpoint(path: str) -> EndpointType:
        """Classify an endpoint path into an endpoint type.

        Args:
            path: The request path.

        Returns:
            The endpoint type for rate limiting purposes.
        """
        path_lower = path.lower()

        # Auth endpoints
        if "/auth/" in path_lower:
            return EndpointType.AUTH

        # Generation endpoints
        if "/generate/" in path_lower:
            return EndpointType.GENERATION

        return EndpointType.OTHER

    async def is_allowed(
        self,
        session_id: str,
        endpoint_type: EndpointType
    ) -> tuple[bool, int, int]:
        """Check if a request is allowed under the rate limit.

        Args:
            session_id: The session identifier.
            endpoint_type: The type of endpoint being accessed.

        Returns:
            Tuple of (is_allowed, retry_after_seconds, remaining_requests).
            If allowed, retry_after_seconds is 0.
        """
        # Trigger cleanup periodically
        await self._maybe_cleanup()

        limit, window = self._get_limit_and_window(endpoint_type)
        now = time.time()
        window_start = now - window

        record = self._requests[session_id][endpoint_type]

        async with record.lock:
            # Remove timestamps outside the window
            record.timestamps = [
                ts for ts in record.timestamps
                if ts > window_start
            ]

            current_count = len(record.timestamps)
            remaining = max(0, limit - current_count)

            if current_count >= limit:
                # Calculate retry-after based on oldest request in window
                if record.timestamps:
                    oldest = min(record.timestamps)
                    retry_after = int(oldest + window - now) + 1
                else:
                    retry_after = window
                return False, retry_after, 0

            # Request is allowed - record it
            record.timestamps.append(now)
            return True, 0, remaining - 1  # -1 because we just added this request

    async def _maybe_cleanup(self) -> None:
        """Periodically clean up old request records."""
        now = time.time()

        if now - self._last_cleanup < self._cleanup_interval:
            return

        async with self._cleanup_lock:
            # Double-check after acquiring lock
            if now - self._last_cleanup < self._cleanup_interval:
                return

            self._last_cleanup = now

            # Get max window for cleanup threshold
            max_window = max(
                self.config.auth_window_seconds,
                self.config.generation_window_seconds,
                self.config.other_window_seconds
            )
            cleanup_threshold = now - max_window

            # Find sessions to clean up
            sessions_to_remove = []

            for session_id, endpoints in self._requests.items():
                endpoints_to_remove = []

                for endpoint_type, record in endpoints.items():
                    # Clean up old timestamps
                    record.timestamps = [
                        ts for ts in record.timestamps
                        if ts > cleanup_threshold
                    ]

                    # Mark empty records for removal
                    if not record.timestamps:
                        endpoints_to_remove.append(endpoint_type)

                # Remove empty endpoint records
                for endpoint_type in endpoints_to_remove:
                    del endpoints[endpoint_type]

                # Mark empty sessions for removal
                if not endpoints:
                    sessions_to_remove.append(session_id)

            # Remove empty sessions
            for session_id in sessions_to_remove:
                del self._requests[session_id]

    def reset(self, session_id: Optional[str] = None) -> None:
        """Reset rate limit counters.

        Args:
            session_id: If provided, only reset for this session.
                       If None, reset all sessions.
        """
        if session_id is not None:
            if session_id in self._requests:
                del self._requests[session_id]
        else:
            self._requests.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for request rate limiting.

    Applies per-session rate limits based on endpoint type.
    Returns 429 Too Many Requests with Retry-After header when exceeded.
    """

    def __init__(
        self,
        app,
        rate_limiter: Optional[RateLimiter] = None,
        config: Optional[RateLimitConfig] = None
    ):
        """Initialize the rate limit middleware.

        Args:
            app: The FastAPI application.
            rate_limiter: Optional existing rate limiter instance.
            config: Rate limit configuration if no limiter provided.
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter(config)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process a request through rate limiting.

        Args:
            request: The incoming request.
            call_next: The next middleware/handler.

        Returns:
            The response, or 429 if rate limited.
        """
        # Get session ID from header or use IP as fallback
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            # Use client IP as fallback for anonymous requests
            client_host = request.client.host if request.client else "unknown"
            session_id = f"ip:{client_host}"

        # Classify the endpoint
        endpoint_type = RateLimiter.classify_endpoint(request.url.path)

        # Check rate limit
        is_allowed, retry_after, remaining = await self.rate_limiter.is_allowed(
            session_id, endpoint_type
        )

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after)
                }
            )

        # Process the request
        response = await call_next(request)

        # Add rate limit headers to successful responses
        limit, window = self.rate_limiter._get_limit_and_window(endpoint_type)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(window)

        return response

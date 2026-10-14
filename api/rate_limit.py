"""In-memory sliding window rate limiter and query length guard for FastAPI.

Protects public deployments against denial-of-service and runaway LLM billing.
"""
import time
from collections import defaultdict
from fastapi import Request, HTTPException

# Stores timestamps of requests per client IP: {client_ip: [timestamp1, timestamp2, ...]}
_REQUEST_HISTORY: defaultdict = defaultdict(list)

MAX_QUERY_LENGTH = 500  # Maximum allowed characters for free-form research queries
RATE_LIMIT_PER_MINUTE = 30  # Max requests per minute per client IP
WINDOW_SECONDS = 60.0


def enforce_query_length(text: str, field_name: str = "query", max_length: int = MAX_QUERY_LENGTH):
    """Enforce maximum query character length."""
    if len(text.strip()) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"Field '{field_name}' exceeds maximum allowed length of {max_length} characters (received {len(text)})."
        )


def get_client_ip(request: Request) -> str:
    """Extract client IP, inspecting reverse-proxy headers (X-Forwarded-For, X-Real-IP) first.
    
    Walks X-Forwarded-For from right to left to skip trusted private proxy IPs,
    identifying the true connecting client without trusting arbitrary client-prepended headers.
    """
    import ipaddress
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ips = [ip.strip() for ip in forwarded.split(",") if ip.strip()]
        for ip in reversed(ips):
            try:
                addr = ipaddress.ip_address(ip)
                if not addr.is_private and not addr.is_loopback:
                    return ip
            except ValueError:
                continue
        if ips:
            return ips[0]
            
    real_ip = request.headers.get("x-real-ip")
    if real_ip and real_ip.strip():
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown_client"


def enforce_rate_limit(request: Request, limit: int = RATE_LIMIT_PER_MINUTE, window: float = WINDOW_SECONDS):
    """Enforce sliding window rate limit per client IP with reverse-proxy support and cleanup."""
    client_ip = get_client_ip(request)
    now = time.time()
    
    # Prune timestamps older than window
    timestamps = [t for t in _REQUEST_HISTORY[client_ip] if now - t < window]
    
    if len(timestamps) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({limit} requests/minute). Please wait before submitting further queries."
        )
        
    timestamps.append(now)
    _REQUEST_HISTORY[client_ip] = timestamps

    # Periodically prune inactive client buckets to prevent unbounded memory growth
    if len(_REQUEST_HISTORY) > 200:
        stale_ips = [ip for ip, ts in _REQUEST_HISTORY.items() if not ts or (now - ts[-1] >= window)]
        for ip in stale_ips:
            _REQUEST_HISTORY.pop(ip, None)


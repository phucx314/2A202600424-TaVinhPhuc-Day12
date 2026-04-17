import time
import logging
from collections import defaultdict, deque
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

# Thử kết nối Redis, fallback in-memory nếu không có
r = None
try:
    if settings.redis_url:
        import redis
        r = redis.from_url(settings.redis_url, decode_responses=True)
        r.ping()
        logger.info("Rate limiter: Redis connected")
except Exception:
    r = None
    logger.warning("Rate limiter: Redis unavailable, using in-memory fallback")

# In-memory fallback
_windows: dict[str, deque] = defaultdict(deque)

def check_rate_limit(user_id: str):
    now = time.time()

    if r:
        # Redis mode
        key = f"rate_limit:{user_id}"
        r.zremrangebyscore(key, "-inf", now - 60)
        reqs = r.zcard(key)
        if reqs >= settings.rate_limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
                headers={"Retry-After": "60"},
            )
        r.zadd(key, {str(now): now})
        r.expire(key, 60)
    else:
        # In-memory fallback
        window = _windows[user_id]
        while window and window[0] < now - 60:
            window.popleft()
        if len(window) >= settings.rate_limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
                headers={"Retry-After": "60"},
            )
        window.append(now)

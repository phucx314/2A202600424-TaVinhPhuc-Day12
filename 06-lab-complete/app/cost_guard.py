import time
import logging
from datetime import datetime
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

r = None
try:
    if settings.redis_url:
        import redis
        r = redis.from_url(settings.redis_url, decode_responses=True)
        r.ping()
        logger.info("Cost guard: Redis connected")
except Exception:
    r = None
    logger.warning("Cost guard: Redis unavailable, using in-memory fallback")

# In-memory fallback
_daily_cost = 0.0
_cost_reset_day = time.strftime("%Y-%m-%d")

def check_budget(user_id: str, estimated_cost: float = 0.0):
    global _daily_cost, _cost_reset_day

    if r:
        month_key = datetime.now().strftime("%Y-%m")
        key = f"budget:{user_id}:{month_key}"
        current = float(r.get(key) or 0)
        if current + estimated_cost > settings.daily_budget_usd:
            raise HTTPException(503, "Budget exhausted. Try next month.")
        return current
    else:
        today = time.strftime("%Y-%m-%d")
        if today != _cost_reset_day:
            _daily_cost = 0.0
            _cost_reset_day = today
        if _daily_cost >= settings.daily_budget_usd:
            raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")
        return _daily_cost

def record_cost(user_id: str, input_tokens: int, output_tokens: int):
    global _daily_cost
    cost = (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006

    if r and cost > 0:
        month_key = datetime.now().strftime("%Y-%m")
        key = f"budget:{user_id}:{month_key}"
        r.incrbyfloat(key, cost)
        r.expire(key, 32 * 24 * 3600)
    else:
        _daily_cost += cost

"""
Production AI Agent — Kết hợp tất cả Day 12 concepts

Checklist:
  ✅ Config từ environment (12-factor)
  ✅ Structured JSON logging
  ✅ API Key authentication
  ✅ Rate limiting
  ✅ Cost guard
  ✅ Input validation (Pydantic)
  ✅ Health check + Readiness probe
  ✅ Graceful shutdown
  ✅ Security headers
  ✅ CORS
  ✅ Error handling
"""
import os
import time
import signal
import logging
import json
import redis
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from app.config import settings
from app.auth import verify_api_key
from app.rate_limiter import check_rate_limit, r as redis_client
from app.cost_guard import check_budget, record_cost
from utils.mock_llm import ask as llm_ask

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup", "app": settings.app_name, "version": settings.app_version, "environment": settings.environment
    }))
    time.sleep(0.1)
    _is_ready = True
    yield
    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))
    if redis_client:
        try: redis_client.close()
        except Exception: pass

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if "server" in response.headers:
            del response.headers["server"]
        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request", "method": request.method, "path": request.url.path, "status": response.status_code, "ms": duration
        }))
        return response
    except Exception as e:
        _error_count += 1
        raise

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)

class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    timestamp: str

@app.get("/health", tags=["Operations"])
def health():
    """Liveness probe."""
    return {"status": "ok", "uptime_seconds": round(time.time() - START_TIME, 1)}

@app.get("/ready", tags=["Operations"])
def ready():
    """Readiness probe"""
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    if redis_client:
        try:
            redis_client.ping()
        except Exception:
            raise HTTPException(503, "Redis connection failed")
    return {"ready": True}

@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(body: AskRequest, request: Request, user_id: str = Depends(verify_api_key)):
    """API chính - Gọi AI agent"""
    check_rate_limit(user_id)
    
    input_tokens = len(body.question.split()) * 2
    check_budget(user_id, estimated_cost=(input_tokens / 1000) * 0.00015)

    # 1. Lấy lịch sử hội thoại (Stateless via Redis)
    history_key = f"history:{user_id}"
    context = []
    if redis_client:
        try: context = redis_client.lrange(history_key, 0, -1) or []
        except Exception: pass
    
    # 2. Gọi LLM
    answer = llm_ask(body.question)
    
    # 3. Tính phí
    output_tokens = len(answer.split()) * 2
    record_cost(user_id, input_tokens, output_tokens)
    
    # 4. Lưu lại vào Redis để giữ app Stateless
    if redis_client:
        try:
            redis_client.rpush(history_key, f"U: {body.question}", f"A: {answer}")
            redis_client.expire(history_key, 3600)
        except Exception: pass

    return AskResponse(
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))

signal.signal(signal.SIGTERM, _handle_signal)

if __name__ == "__main__":
    logger.info(f"Starting {settings.app_name} on {settings.host}:{settings.port}")
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)

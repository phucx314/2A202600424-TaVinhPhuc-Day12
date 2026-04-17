# Deployment Information

## Public URL
https://day12-complete-production.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
```bash
curl https://day12-complete-production.up.railway.app/health
# Expected: {"status": "ok", "uptime_seconds": ...}
```

### API Test (without key — should return 401)
```bash
curl -X POST https://day12-complete-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# Expected: {"detail": "Invalid or missing API key..."}
```

### API Test (with authentication)
```bash
curl -X POST https://day12-complete-production.up.railway.app/ask \
  -H "X-API-Key: dev-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"question": "1 + 1 = ?"}'
# Expected: {"question": "1 + 1 = ?", "answer": "1 + 1 = 2.", ...}
```

## Environment Variables Set
- PORT (auto-injected by Railway)
- REDIS_URL (optional, fallback to in-memory)
- AGENT_API_KEY
- OPENAI_API_KEY
- LOG_LEVEL

## Screenshots
- [Deployment dashboard](./extras/screenshots/dashboard.png)
- [Service running](./extras/screenshots/running.png)
- [Test results](./extras/screenshots/test.png)

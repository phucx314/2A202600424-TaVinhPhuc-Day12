# Deployment Information

## Public URL
https://day12-production-ad58.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
```bash
curl https://day12-production-ad58.up.railway.app/health
# Expected: {"status": "ok", "uptime_seconds": ...}
```

### API Test (with authentication)
```bash
curl -X POST https://day12-production-ad58.up.railway.app/ask \
  -H "X-API-Key: demo-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello AI Agent"}'
```

## Environment Variables Set
- PORT=8000
- REDIS_URL (Managed by Nixpacks / Railway auto-provisioning)
- AGENT_API_KEY
- LOG_LEVEL
- ENVIRONMENT=production

## Screenshots
- [Deployment Screenshot](./extras/screenshots/image.png)

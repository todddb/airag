# Troubleshooting Guide

Common issues and solutions.

## Table of Contents

- [Services Won't Start](#services-wont-start)
- [Port Already in Use](#port-already-in-use)
- [Out of Memory](#out-of-memory)
- [Models Not Downloading](#models-not-downloading)
- [Slow Performance](#slow-performance)
- [API Errors](#api-errors)
- [Frontend Not Loading](#frontend-not-loading)
- [Crawling Fails](#crawling-fails)

## Services Won't Start

**Symptoms**: `docker compose up` fails or services exit immediately

**Solutions**:

1. Check logs:
```bash
./tools/airagctl logs
```

2. Check Docker daemon:
```bash
docker ps
# If error: Start Docker daemon
sudo systemctl start docker
```

3. Check ports:
```bash
lsof -i :8000
lsof -i :8001
lsof -i :8080
```

4. Rebuild from scratch:
```bash
docker compose down -v
docker compose build --no-cache
./tools/airagctl start
```

## Port Already in Use

**Symptoms**: "Address already in use" error

**Solutions**:

1. Find what's using the port:
```bash
lsof -i :8000
# Kill the process
kill -9 <PID>
```

2. Change port in `.env`:
```bash
ORCHESTRATOR_PORT=8100
WORKER_PORT=8101
FRONTEND_PORT=8180
```

3. Use different ports in docker-compose:
```yaml
services:
  orchestrator-api:
    ports:
      - "8100:8000"
```

## Out of Memory

**Symptoms**: Services crash, "OOMKilled" in logs

**Solutions**:

1. Check memory usage:
```bash
docker stats
```

2. Reduce model size in `.env`:
```bash
ORCHESTRATOR_MODEL=qwen2.5:7b  # Smaller
WORKER_MODEL=qwen2.5:14b       # Smaller
```

3. Limit container memory:
```yaml
services:
  worker-api:
    deploy:
      resources:
        limits:
          memory: 8G
```

4. Stop other services:
```bash
docker compose stop crawler
```

5. Upgrade RAM or use swap:
```bash
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Models Not Downloading

**Symptoms**: "Model not found" errors

**Solutions**:

1. Pull models manually:
```bash
docker compose up -d orchestrator-ollama
docker compose exec orchestrator-ollama ollama pull qwen2.5:14b

docker compose up -d worker-ollama
docker compose exec worker-ollama ollama pull qwen2.5:32b
```

2. Check disk space:
```bash
df -h
# Need ~25GB free
```

3. Check internet connection:
```bash
curl -I https://ollama.com
```

4. Use smaller models:
```bash
# In .env
ORCHESTRATOR_MODEL=qwen2.5:7b
WORKER_MODEL=qwen2.5:14b
```

## Slow Performance

**Symptoms**: Queries take >10 seconds

**Solutions**:

1. Enable GPU:
```bash
# In .env
ENABLE_GPU=true
```

2. Use smaller models:
```bash
ORCHESTRATOR_MODEL=qwen2.5:7b
```

3. Reduce max_tokens:
```bash
MAX_TOKENS=1000
```

4. Check CPU usage:
```bash
docker stats
# If maxed out, add more CPU cores or reduce concurrent requests
```

5. Add caching (TODO: implement Redis)

## API Errors

### 503 Service Unavailable

**Cause**: Service not ready

**Solution**:
```bash
./tools/airagctl health
# Wait for all services to be healthy
```

### 500 Internal Server Error

**Cause**: Code error

**Solution**:
```bash
./tools/airagctl logs orchestrator-api
./tools/airagctl logs worker-api
# Check error messages
```

### 400 Bad Request

**Cause**: Invalid input

**Solution**:
Check request format matches API docs: [API.md](API.md)

## Frontend Not Loading

**Symptoms**: Blank page or connection refused

**Solutions**:

1. Check frontend service:
```bash
curl http://localhost:8080/health
```

2. Check nginx logs:
```bash
docker compose logs frontend
```

3. Check browser console:
```
F12 → Console tab
Look for errors
```

4. Clear browser cache:
```
Ctrl+Shift+R (hard reload)
```

5. Check API proxy:
```bash
curl http://localhost:8080/api/health
# Should proxy to orchestrator
```

## Crawling Fails

**Symptoms**: `airagctl crawl` returns no results

**Solutions**:

1. Test URL manually:
```bash
./tools/airagctl crawl --test https://example.com
```

2. Check robots.txt:
```bash
curl https://example.com/robots.txt
# Make sure not disallowed
```

3. Increase limits:
```bash
airagctl crawl <url> --max-pages 500 --max-depth 3
```

4. Check crawler logs:
```bash
docker compose logs crawler
```

5. Try different URL:
```bash
# Start with a simple page
airagctl crawl https://example.com
```

## Database Issues

### Qdrant Connection Failed

**Solution**:
```bash
docker compose ps qdrant
curl http://localhost:6333/health
docker compose restart qdrant
```

### Collection Not Found

**Solution**:
```bash
# Create collection
curl -X PUT http://localhost:6333/collections/documents \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 384, "distance": "Cosine"}}'
```

### Database Corrupt

**Solution**:
```bash
# Reset database
./tools/airagctl reset
# Or restore from backup
./tools/backup.sh restore <backup_file>
```

## General Debugging

### Enable Debug Logging

In `.env`:
```bash
LOG_LEVEL=DEBUG
```

Restart services:
```bash
./tools/airagctl restart
```

### Check All Endpoints

```bash
./tools/test-endpoints.sh
```

### Get System Info

```bash
# Docker info
docker version
docker compose version

# System resources
free -h
df -h
lscpu

# GPU info (if applicable)
nvidia-smi
```

### Reset Everything

Last resort:
```bash
# Stop and remove everything
docker compose down -v

# Remove images
docker rmi $(docker images -q airag*)

# Start fresh
./tools/setup.sh --quick
```

## Still Having Issues?

1. Check [GitHub Issues](https://github.com/yourusername/airag/issues)
2. Search [Discussions](https://github.com/yourusername/airag/discussions)
3. Open new issue with:
   - Error messages
   - Logs (`./tools/airagctl logs`)
   - System info
   - Steps to reproduce

---

**Pro Tip**: Most issues are solved by checking logs first:
```bash
./tools/airagctl logs
```

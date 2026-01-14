# Deployment Guide

Production deployment guide for AI RAG.

## Quick Deploy

```bash
# 1. Clone
git clone https://github.com/yourusername/airag.git
cd airag

# 2. Setup
./tools/setup.sh --quick

# 3. Start
./tools/airagctl start

# 4. Test
./tools/test-endpoints.sh
```

## Production Checklist

- [ ] Configure `.env` with production values
- [ ] Enable GPU if available
- [ ] Set up automated backups
- [ ] Configure monitoring
- [ ] Set resource limits
- [ ] Enable HTTPS
- [ ] Configure authentication (if needed)
- [ ] Set up log rotation
- [ ] Test disaster recovery

## Environment Configuration

Edit `.env`:
```bash
# Performance
ORCHESTRATOR_MODEL=qwen2.5:14b
WORKER_MODEL=qwen2.5:32b
ENABLE_GPU=true

# Security
CORS_ORIGINS=https://yourdomain.com
# API_KEY=your-secret-key  # Implement auth if needed

# Limits
MAX_TOKENS=2000
TEMPERATURE=0.7

# Collection
QDRANT_COLLECTION=production_docs
```

## Docker Compose Production

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  orchestrator-api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
    restart: always
    
  worker-api:
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '4'
          memory: 8G
    restart: always
```

Start:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## HTTPS with nginx

Add to frontend `nginx.conf`:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... rest of config
}
```

## Automated Backups

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/airag/tools/backup.sh create

# Weekly cleanup (keep 10)
0 3 * * 0 /path/to/airag/tools/backup.sh cleanup 10
```

## Monitoring

### Health Checks

```bash
# Periodic health check
*/5 * * * * /path/to/airag/tools/airagctl health
```

### Prometheus Metrics

Add to services:
```python
from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')
```

### Grafana Dashboard

Import dashboard from `monitoring/grafana-dashboard.json`

## Resource Requirements

### Minimum
- 4 CPU cores
- 16GB RAM
- 50GB disk
- No GPU

### Recommended
- 8+ CPU cores
- 32GB RAM
- 200GB SSD
- NVIDIA GPU (RTX 3090+)

### High Load
- 16+ CPU cores
- 64GB RAM
- 500GB SSD
- NVIDIA A100

## Scaling

### Horizontal (Multiple Instances)
```bash
docker compose up --scale orchestrator-api=3 --scale worker-api=2
```

### Load Balancer
```nginx
upstream orchestrator {
    server orchestrator-1:8000;
    server orchestrator-2:8000;
    server orchestrator-3:8000;
}
```

### Kubernetes
```bash
helm install airag ./helm/airag \
  --set orchestrator.replicas=3 \
  --set worker.replicas=2
```

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Security

1. **Network**: Use Docker networks
2. **Secrets**: Use environment variables
3. **HTTPS**: Enable SSL/TLS
4. **Auth**: Implement API keys if public
5. **Updates**: Keep dependencies updated

---

For more help, see [Getting Started](GETTING_STARTED.md)

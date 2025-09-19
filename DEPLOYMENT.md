# 🐳 Enterprise Deployment Guide

## Container Deployment Options for Restricted Environments

This guide provides deployment strategies for enterprise customers with strict security controls, air-gapped environments, and network restrictions.

## Current Interaction Model

**File-based Processing:**
- System expects PDF files in `./data/BANK/` or `./data/COUNTERPARTY/` directories
- Runs via `crewai run` command processing documents specified in `main.py`
- Results stored in local TinyDB files in `./storage/` directory
- No web interface - purely command-line driven
- Zero external dependencies except LLM API calls

---

## Deployment Options

### 1. Batch Processing Container (Current Model)

**Best for:** Scheduled processing, maximum security

```bash
# Build container
docker build -t trade-matcher .

# Run with mounted volumes
docker run --rm \
  -v /host/data:/app/data \
  -v /host/storage:/app/storage \
  -e OPENAI_API_KEY=${API_KEY} \
  trade-matcher
```

**Workflow:**
1. Customer drops PDFs into mounted directories
2. Container processes files and exits
3. Results written to mounted storage volume
4. Zero network requirements after image pull

---

### 2. Watch Folder Container

**Best for:** Continuous processing, automation

```python
# Enhanced version that monitors directories
while True:
    scan_for_new_pdfs()
    process_new_files()
    sleep(30)
```

**Deployment:**
```bash
docker run -d --name trade-watcher \
  -v /host/data:/app/data \
  -v /host/storage:/app/storage \
  -v /host/processed:/app/processed \
  -e OPENAI_API_KEY=${API_KEY} \
  trade-matcher:watcher
```

**Features:**
- Container runs continuously
- Monitors mounted directories for new PDFs
- Processes automatically when files appear
- Moves processed files to archive directory
- Ideal for air-gapped environments

---

### 3. API Container

**Best for:** System integration, programmatic access

```python
# Add FastAPI/Flask endpoints
POST /process-pdf (upload file)
GET /status/{trade_id}
GET /matches
GET /health
```

**Deployment:**
```bash
docker run -d -p 8080:8080 \
  -v /host/storage:/app/storage \
  -e OPENAI_API_KEY=${API_KEY} \
  trade-matcher:api
```

**Requirements:**
- Network access for API endpoints
- Still stores locally in container
- RESTful API for integration

---

## Enterprise Security Considerations

### Air-Gapped Deployment

✅ **Fully Supported**
- Pre-built Docker image (no internet needed at runtime)
- All dependencies bundled in container
- Local storage only (no external calls except LLM)
- Can run completely offline with local LLM models

### Data Privacy

✅ **Maximum Security**
- All processing happens locally in container
- No data leaves the container environment
- Trade data never transmitted externally
- Results stored in customer-controlled volumes

### Network Restrictions

**LLM API Options:**
```bash
# Option 1: Proxy through customer gateway
-e HTTP_PROXY=customer-secure-proxy
-e HTTPS_PROXY=customer-secure-proxy

# Option 2: Local LLM (no internet needed)
-e LLM_PROVIDER=local
-e LOCAL_MODEL_PATH=/models/llama2

# Option 3: Customer's internal LLM endpoint
-e OPENAI_BASE_URL=https://internal-llm.company.com/v1
```

---

## Recommended Architectures

### Option A: Offline-First Container

```dockerfile
FROM python:3.12-slim

# Bundle local LLM model in container
COPY models/ /app/models/
COPY requirements-offline.txt /app/

# No external API calls needed
ENV LLM_PROVIDER=local
ENV LOCAL_MODEL_PATH=/app/models/

# Pure file processing
WORKDIR /app
CMD ["python", "main.py"]
```

**Benefits:**
- Zero internet dependency
- Complete data isolation
- Fastest processing (local inference)
- Maximum security compliance

### Option B: Secure Gateway Integration

```yaml
# docker-compose.yml for customer environment
version: '3.8'
services:
  trade-matcher:
    image: trade-matcher:latest
    environment:
      - HTTP_PROXY=customer-secure-proxy:8080
      - HTTPS_PROXY=customer-secure-proxy:8080
      - OPENAI_API_KEY=${SECURE_API_KEY}
    volumes:
      - /secure/data:/app/data
      - /secure/storage:/app/storage
    networks:
      - customer-secure-network
```

**Benefits:**
- All traffic through customer proxy
- Audit trail of external calls
- Leverages existing security infrastructure

### Option C: Scheduled Batch Processing

```bash
# Cron job approach
# /etc/cron.d/trade-processing
0 */6 * * * docker run --rm \
  -v /data:/app/data \
  -v /storage:/app/storage \
  -e OPENAI_API_KEY_FILE=/secrets/api-key \
  trade-matcher:batch
```

**Benefits:**
- Predictable resource usage
- No persistent containers
- Easy to audit and monitor
- Fits existing batch processing workflows

---

## Security Features

### Secrets Management

```bash
# Docker secrets (Swarm mode)
docker secret create openai_key /path/to/api-key.txt
docker service create \
  --secret openai_key \
  --mount type=bind,src=/data,dst=/app/data \
  trade-matcher

# Kubernetes secrets
kubectl create secret generic llm-credentials \
  --from-literal=openai-api-key="${API_KEY}"
```

### File Permissions

```dockerfile
# Run as non-root user
RUN useradd -m -u 1000 trader
USER trader

# Read-only filesystem
docker run --read-only \
  --tmpfs /tmp \
  -v /data:/app/data:ro \
  -v /storage:/app/storage \
  trade-matcher
```

### Network Isolation

```bash
# No external network access
docker run --network none \
  -v /data:/app/data \
  -v /storage:/app/storage \
  trade-matcher:offline

# Custom network with egress filtering
docker network create --driver bridge \
  --subnet=172.20.0.0/16 \
  trade-network
```

---

## Performance Considerations

### Resource Requirements

```yaml
# Kubernetes resource limits
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### Scaling Options

```bash
# Horizontal scaling for batch processing
for i in {1..5}; do
  docker run -d --name trader-$i \
    -v /data/batch-$i:/app/data \
    trade-matcher &
done
```

### Monitoring

```bash
# Health checks
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import os; exit(0 if os.path.exists('/app/health') else 1)"

# Logging
docker run \
  --log-driver=syslog \
  --log-opt syslog-address=udp://log-server:514 \
  trade-matcher
```

---

## Migration Path

### Phase 1: Proof of Concept
1. Deploy batch container with sample data
2. Validate security controls
3. Test with customer's proxy/gateway

### Phase 2: Pilot Deployment
1. Implement watch folder pattern
2. Integrate with customer's file systems
3. Establish monitoring and alerting

### Phase 3: Production Rollout
1. Scale to multiple containers
2. Implement redundancy and failover
3. Full operational handover

---

## Support Matrix

| Feature | Batch | Watch Folder | API | Offline |
|---------|-------|--------------|-----|---------|
| Air-gapped | ✅ | ✅ | ❌ | ✅ |
| Zero network | ❌ | ❌ | ❌ | ✅ |
| Automation | ❌ | ✅ | ✅ | ❌ |
| Integration | ❌ | ❌ | ✅ | ❌ |
| Max Security | ✅ | ✅ | ❌ | ✅ |

---

## Contact for Enterprise Deployment

For assistance with enterprise deployment, security reviews, or custom configurations, please contact the development team with your specific requirements.
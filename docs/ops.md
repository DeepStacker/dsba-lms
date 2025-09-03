# DSBA LMS - Operations Guide

## Quick Start

### Local Development
```bash
# Clone repository
git clone https://github.com/your-org/DSBA-lms.git
cd DSBA-lms

# Start with Docker (recommended)
make up

# Or run services individually
make backend-dev
make web-dev
make ai-service-dev

# Load demo data
make seed

# Access applications
# Frontend: http://localhost:3000
# API: http://localhost:8000/docs
# AI Service: http://localhost:8001/docs
```

### Production Deployment
```bash
# Single VM Deployment
make prod-up

# Or Kubernetes/Minikube
make k8s-deploy

# Access application at http://your-domain
```

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │  AI Microservice│
│     (React)     │    │   (FastAPI)     │
│                 │    │                 │
│  - Role-based   │    │  - Question Gen │
│  - Assessment   │    │  - AI Grading   │
│  - Analytics    │    │  - Attainment   │
└─────────┬───────┘    └──────────┬─────┘
          │                       │
          │                       │
┌─────────▼───────────────────────▼─────┐
│             API Gateway                │
│               (FastAPI)                │
│                                       │
│  - Authentication & Authorization     │
│  - Program/Course/User Management     │
│  - Exam Engine & Proctoring           │
│  - Analytics & Reporting              │
│  - Audit & Compliance                 │
└───────────────────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│           Database Layer              │
│                                       │
│  PostgreSQL ──► Application Data      │
│   Redis Cache  ──► Session/Performance │
│   RabbitMQ ─────► Background Tasks     │
└───────────────────────────────────────┘
```

## Component Overview

### Backend Services
- **Main API**: FastAPI application serving REST endpoints
- **AI Service**: Python microservice for ML/AI operations
- **Database**: PostgreSQL with Alembic migrations
- **Cache**: Redis for session management and caching
- **Queue**: RabbitMQ/Celery for async processing
- **Monitoring**: Prometheus metrics with Grafana dashboard

### Frontend Application
- **Framework**: React 18 + TypeScript + Vite
- **Routing**: React Router for client-side navigation
- **State**: Context API for authentication and global state
- **UI**: TailwindCSS + HeadlessUI for consistent design
- **Charts**: Recharts for analytics visualizations

## Directory Structure

```
DSBA-lms/
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── core/             # Configuration & utilities
│   │   ├── models/           # SQLAlchemy models
│   │   ├── routes/           # API endpoints
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── utils/            # Helper utilities
│   └── scripts/seed.py       # Demo data
├── ai-service/               # AI microservice
├── web/                      # React frontend
├── infra/                    # Infrastructure configs
│   ├── nginx.conf           # Reverse proxy
│   ├── prometheus.yml       # Monitoring
│   └── grafana/             # Dashboard configs
├── docs/                     # Documentation
├── docker-compose.yml        # Local development
├── docker-compose.prod.yml   # Production deployment
├── kubernetes/               # K8s manifests
└── Makefile                  # Development commands
```

## Configuration

### Environment Variables

#### Backend Service
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/DSBA_lms
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your-super-secret-key-here
JWT_EXPIRES_MIN=15
REFRESH_EXPIRES_DAYS=7

# AI Service
AI_SERVICE_URL=http://localhost:8001
AI_SERVICE_TOKEN=internal_auth_token

# Security
ARGON2_TIME_COST=3
ARGON2_MEMORY_COST=65536

# Features
FEATURE_AI=true
FEATURE_TELEMETRY=true

# Lock Policy
LOCK_DEFAULT_DAYS=7
WEEKLY_LOCK_SATURDAY=true

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
LOG_LEVEL=INFO

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

#### Frontend Application
```bash
VITE_API_URL=http://localhost:8000
VITE_AI_URL=http://localhost:8001
VITE_ENVIRONMENT=development
```

#### AI Service
```bash
OPENAI_API_KEY=your-openai-key
HUGGINGFACE_TOKEN=your-huggingface-token
INTERNAL_AUTH_TOKEN=internal_token_change_me
```

## Development Workflow

### Local Development
1. **Setup Environment**:
   ```bash
   cp backend/.env.example backend/.env
   cp web/.env.example web/.env
   cp ai-service/.env.example ai-service/.env
   ```

2. **Start Services**:
   ```bash
   make up             # Start all services
   make migrate        # Run database migrations
   make seed          # Load demo data
   ```

3. **Development Commands**:
   ```bash
   # Backend
   make backend-dev   # Start backend in development mode

   # Frontend
   make web-dev       # Start frontend development server

   # AI Service
   make ai-dev        # Start AI service

   # Testing
   make test          # Run test suite
   make test-backend  # Backend tests only
   make test-frontend # Frontend tests only

   # Code Quality
   make fmt           # Format code (black, isort, prettier)
   make lint          # Run linters (ruff, eslint)
   ```

## Production Deployment

### Single VM Deployment

```bash
# Build production images
make build-prod

# Deploy
make prod-up

# Scale services if needed
docker-compose up -d --scale backend=3

# Check health
curl http://your-domain/health
```

### Kubernetes Deployment

```bash
# Install prerequisites (on control plane)
kubectl apply -f k8s/prerequisites/

# Deploy application
make k8s-deploy

# Check status
kubectl get pods,svc,ingress -l app=DSBA-lms

# Scale deployment
kubectl scale deployment DSBA-backend --replicas=3
```

### Cloud Platform Deployment

#### AWS
```bash
# Using ECS
make deploy-ecs

# Using EKS
make deploy-eks
```

#### Google Cloud
```bash
# Using Cloud Run
make deploy-cloudrun

# Using GKE
make deploy-gke
```

## Database Management

### Migrations
```bash
# Create new migration
cd backend && alembic revision -m "Add user preferences"

# Apply migrations
make migrate

# Show migration status
make migrate-status

# Check migrations (CI/CD)
make migrate-check
```

### Backup & Restore
```bash
# Backup database
docker exec DSBA-postgres pg_dump -U DSBA DSBA_lms > backup.sql

# Restore database
docker exec -i DSBA-postgres psql -U DSBA -d DSBA_lms < backup.sql

# Periodic backup (cron)
0 2 * * * docker exec DSBA-postgres pg_dump -U DSBA DSBA_lms > /backups/$(date +\%Y\%m\%d).sql
```

## Monitoring & Observability

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/health/database

# AI service health
curl http://localhost:8001/health
```

### Metrics Collection
```bash
# Prometheus metrics
curl http://localhost:9090/metrics

# Application metrics
curl http://localhost:8000/metrics
```

### Log Aggregation
```bash
# View application logs
make logs

# View specific service logs
make logs-backend
make logs-web
make logs-ai

# Follow logs
make logs -f
```

### Alerting Configuration

```
Alert Rules:
- Response time > 2s for 5 minutes
- Error rate > 5% for 10 minutes
- Database connection pool exhausted
- Storage usage > 85%
- AI service unavailable for 30 minutes
```

## Security

### TLS Configuration
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:...;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### PII Data Handling
```sql
-- Field-level encryption for sensitive data
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt phone/email fields
ALTER TABLE users ADD COLUMN encrypted_email BYTEA;
CREATE INDEX ON users (pgp_sym_decrypt(encrypted_email, 'acme-secret-key'));
```

### Rate Limiting
```nginx
# Rate limiting by IP
limit_req_zone $binary_remote_addr zone=api:10m rate=60r/s;
limit_req zone=api burst=10 nodelay;

location /api/ {
    limit_req zone=api;
    proxy_pass http://backend;
}
```

## Performance Tuning

### Database Optimization
```sql
-- Analyze slow queries
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM users WHERE role = 'student';

-- Add indexes
CREATE INDEX CONCURRENTLY ON responses (exam_id, student_id);
CREATE INDEX CONCURRENTLY ON attempts (started_at DESC);

-- Partition large tables
CREATE TABLE responses_y2023 PARTITION OF responses
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
```

### Caching Strategy
```python
# Redis caching for frequent queries
from redis import Redis

redis_client = Redis.from_url(settings.redis_url)

@redis_cache(expire=300)
def get_exam_statistics(exam_id: int):
    # Computational query cached for 5 minutes
    pass
```

### Async Processing
```python
# Background task for heavy operations
@app.post("/ai/grade/bulk")
async def ai_grade_bulk_exam(request: BulkGradeRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_bulk_grading, request.exam_id)
    return {"message": "AI grading started in background"}
```

## Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check database connectivity
docker exec -it DSBA-postgres psql -U DSBA -d DSBA_lms -c "SELECT 1"

# Check Redis connectivity
docker exec -it DSBA-redis redis-cli ping

# View backend logs
docker logs DSBA-backend
```

#### Frontend Build Fails
```bash
# Clear node_modules and reinstall
cd web && rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run build
```

#### Database Connection Issues
```bash
# Test database connection
docker run --rm --network DSBA_lms_default postgres:15 psql \
    -h postgres -U DSBA -d DSBA_lms -c "SELECT version()"

# Reset database if needed
make db-reset
make seed
```

#### AI Service Unavailable
```bash
# Check AI service logs
docker logs DSBA-ai-service

# Test AI endpoint
curl http://localhost:8001/health

# Verify OpenAI API key
docker exec -it DSBA-ai-service env | grep OPENAI
```

### Performance Issues

#### High CPU Usage
```bash
# Check resource usage
docker stats

# Profile backend
python -m cProfile -s cumtime app/main.py > profile.txt

# Optimize slow queries (setup monitoring)
```

#### Memory Leaks
```bash
# Enable memory profiling
pip install memory-profiler
python -m memory_profiler app/main.py
```

#### Network Latency
```bash
# Test API response times
curl -w "@curl-format.txt" http://localhost:8000/health

# Enable compression
# Backend: pip install fast-compress
# Frontend: Add compression middleware
```

## Scaling

### Horizontal Scaling
```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: DSBA-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: DSBA-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Database Scaling
```sql
-- Read replicas
CREATE SUBSCRIPTION sub1 CONNECTION 'host=primary-db user=replicator' PUBLICATION pub1;
ALTER SUBSCRIPTION sub1 REFRESH PUBLICATION;

-- Connection pooling
# Use PgBouncer for connection pooling
# docker run -d --name pgbouncer -e DB_HOST=postgres pgbouncer/pgbouncer
```

### Caching Layer
```python
# Multi-level caching strategy
@app.middleware("http")
async def cache_middleware(request, call_next):
    cache_key = f"{request.method}:{request.url.path}"
    cached_response = redis_client.get(cache_key)

    if cached_response:
        return JSONResponse(json.loads(cached_response))

    response = await call_next(request)
    if response.status_code == 200:
        redis_client.setex(cache_key, 300, response.body.decode())

    return response
```

---

## Contact & Support

For issues or questions:
- **Documentation**: `docs/` directory
- **API Docs**: `http://localhost:8000/docs`
- **Logs**: `make logs`
- **Health**: `http://localhost:8000/health`

## Backup & Recovery

```bash
# Automatic backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M)
BACKUP_NAME="DSBA_backup_$DATE"

# Database backup
docker exec DSBA-postgres pg_dump -U DSBA -Fc DSBA_lms > /backups/$BACKUP_NAME.sql

# Redis backup (if needed)
docker exec DSBA-redis redis-cli BGSAVE

# File storage backup
tar -czf /backups/$BACKUP_NAME.tar.gz /storage

# Upload to cloud storage (optional)
# aws s3 cp /backups/$BACKUP_NAME.tar.gz s3://backups/

# Retention policy
find /backups -name "*.tar.gz" -mtime +30 -delete
```

## Compliance & Auditing

### Data Retention Policy
- **Student Responses**: 7 years (accreditation requirement)
- **Audit Logs**: 7 years
- **AI Grading Data**: 365 days
- **Session Logs**: 90 days

### Regular Maintenance
```bash
# Weekly tasks
# - Database VACUUM
# - Clean old Redis keys
# - Archive old logs

# Monthly tasks
# - Security patch updates
# - Performance monitoring review
# - Backup verification

# Quarterly tasks
# - Full security audit
# - Penetration testing
# - Accreditation compliance check
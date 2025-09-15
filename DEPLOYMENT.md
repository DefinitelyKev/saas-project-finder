# Production Deployment Guide

This guide covers deploying the AI Backend to production and staging environments with enterprise-grade reliability and security.

## Table of Contents

1. [Environment Overview](#environment-overview)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Deployment Process](#deployment-process)
6. [Monitoring and Observability](#monitoring-and-observability)
7. [Backup and Recovery](#backup-and-recovery)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)

## Environment Overview

The AI Backend supports three environments:

- **Development**: Local development with trust authentication
- **Staging**: Pre-production testing environment
- **Production**: Live production environment with full security

### Key Differences by Environment

| Feature | Development | Staging | Production |
|---------|-------------|---------|------------|
| Database Pool Size | 5 | 10 | 20 |
| Connection Timeout | 10s | 20s | 30s |
| Log Level | DEBUG | INFO | WARNING |
| HTTPS Required | No | Yes | Yes |
| Rate Limiting | Disabled | Enabled | Enabled |
| Monitoring | Basic | Full | Full + Alerts |
| Workers | 1 | 2 | 4 |

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended)
- **RAM**: Minimum 4GB (8GB+ recommended for production)
- **CPU**: 2+ cores (4+ cores recommended for production)
- **Storage**: 50GB+ SSD storage
- **Network**: Stable internet connection

### Software Dependencies

```bash
# Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Additional tools
sudo apt update
sudo apt install -y curl jq htop
```

## Environment Configuration

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd saas-project-finder
```

### 2. Set Up Environment Files

#### Staging Environment (.env.staging)

```bash
cp .env.staging.example .env.staging
```

**Required variables:**
```env
# Database
DB_PASSWORD=your-secure-db-password
DATABASE_URL=postgresql+asyncpg://ai_user:${DB_PASSWORD}@staging-postgres:5432/ai_backend

# API Keys
OPENAI_API_KEY=sk-your-openai-key
JWT_SECRET=your-32-char-jwt-secret
API_KEY_HASH_SALT=your-32-char-salt

# Domain
ALLOWED_ORIGINS=https://staging.yourapp.com
```

#### Production Environment (.env.production)

```bash
cp .env.production.example .env.production
```

**Required variables:**
```env
# Database
DB_PASSWORD=your-ultra-secure-db-password
DATABASE_URL=postgresql+asyncpg://ai_user:${DB_PASSWORD}@prod-postgres-cluster:5432/ai_backend

# API Keys
OPENAI_API_KEY=sk-your-openai-key
JWT_SECRET=your-32-char-jwt-secret
API_KEY_HASH_SALT=your-32-char-salt

# Security
SENTRY_DSN=your-sentry-dsn
ALLOWED_ORIGINS=https://yourapp.com,https://api.yourapp.com

# Monitoring (optional)
DATADOG_API_KEY=your-datadog-key
NEW_RELIC_LICENSE_KEY=your-newrelic-key
```

### 3. Generate Secure Secrets

```bash
# Generate secure secrets
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env.production
echo "API_KEY_HASH_SALT=$(openssl rand -hex 32)" >> .env.production
echo "DB_PASSWORD=$(openssl rand -base64 32)" >> .env.production
```

## Database Setup

### Production PostgreSQL Configuration

#### 1. Create Production Database Configuration

```bash
# Create PostgreSQL configuration for production
mkdir -p config/postgres
cat > config/postgres/postgresql.conf << EOF
# Connection settings
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# WAL settings
wal_buffers = 16MB
checkpoint_completion_target = 0.9
wal_level = replica
max_wal_senders = 3
max_replication_slots = 3

# Performance
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_min_messages = warning
log_min_error_statement = error
log_min_duration_statement = 1000
EOF
```

#### 2. Set Up Database Authentication

For production, use proper password authentication instead of trust:

```bash
cat > config/postgres/pg_hba.conf << EOF
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                md5
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
host    all             all             172.20.0.0/16           md5
EOF
```

## Deployment Process

### Automated Deployment

Use the provided deployment script:

```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Deploy to staging
./scripts/deploy.sh staging deploy

# Deploy to production
./scripts/deploy.sh production deploy
```

### Manual Deployment Steps

#### 1. Build Production Images

```bash
# Build staging
docker-compose -f docker-compose.staging.yml build

# Build production
docker-compose -f docker-compose.production.yml build
```

#### 2. Database Migration

```bash
# Start database services
docker-compose -f docker-compose.production.yml up -d postgres redis

# Wait for database to be ready
sleep 30

# Run migrations (automatically done in production Dockerfile)
docker-compose -f docker-compose.production.yml exec ai-backend alembic upgrade head
```

#### 3. Start All Services

```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Check service status
docker-compose -f docker-compose.production.yml ps
```

#### 4. Verify Deployment

```bash
# Health check
curl -f http://localhost:8000/health

# Check logs
docker-compose -f docker-compose.production.yml logs ai-backend

# Monitor startup
docker-compose -f docker-compose.production.yml logs -f ai-backend
```

## Monitoring and Observability

### Health Checks

The application provides several health check endpoints:

```bash
# Basic health check
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/health/database

# Detailed status
curl http://localhost:8000/health/detailed
```

### Logging

#### Application Logs

```bash
# View application logs
docker-compose -f docker-compose.production.yml logs ai-backend

# Follow logs in real-time
docker-compose -f docker-compose.production.yml logs -f ai-backend

# View specific service logs
docker-compose -f docker-compose.production.yml logs postgres
```

#### Log Aggregation (Production)

Production includes Loki + Grafana for log aggregation:

- **Loki**: http://localhost:3100 (log aggregation)
- **Grafana**: http://localhost:3000 (dashboards)

#### Structured Logging

All logs are in JSON format for easy parsing:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "src.infrastructure.persistence.database",
  "message": "Database session created successfully",
  "request_id": "abc123",
  "tenant_id": "tenant_456"
}
```

### Metrics and Monitoring (Production)

#### Prometheus Metrics

Access metrics at: http://localhost:9090

Key metrics to monitor:
- Database connection pool usage
- API response times
- Agent execution success rates
- Token usage per tenant

#### Grafana Dashboards

Access dashboards at: http://localhost:3000

Pre-configured dashboards:
- Application Performance
- Database Metrics
- Business Metrics (tenant usage)
- Infrastructure Health

## Backup and Recovery

### Automated Backups

Production includes automated backup service:

```bash
# Manual backup
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U ai_user ai_backend > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup service
docker-compose -f docker-compose.production.yml logs backup
```

### Backup Configuration

Backups are configured to:
- Run daily at 2 AM UTC
- Retain 30 days of backups locally
- Upload to S3 (if configured)

### Recovery Process

```bash
# Stop application
docker-compose -f docker-compose.production.yml stop ai-backend

# Restore database
cat backup_file.sql | docker-compose -f docker-compose.production.yml exec -T postgres psql -U ai_user -d ai_backend

# Restart application
docker-compose -f docker-compose.production.yml start ai-backend
```

## Security Considerations

### Network Security

1. **Firewall Configuration**:
   ```bash
   # Allow only necessary ports
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw enable
   ```

2. **Docker Network Isolation**:
   - Services communicate through isolated Docker networks
   - Database not exposed to public internet
   - Internal service discovery via service names

### Secrets Management

1. **Environment Variables**:
   - Store secrets in `.env.production` (not in Git)
   - Use strong, randomly generated passwords
   - Rotate secrets regularly

2. **Docker Secrets** (optional):
   ```bash
   # Create Docker secrets
   echo "your-db-password" | docker secret create db_password -
   echo "your-jwt-secret" | docker secret create jwt_secret -
   ```

### SSL/TLS Configuration

For production, ensure HTTPS is properly configured:

```bash
# Generate SSL certificates (or use Let's Encrypt)
mkdir -p config/ssl
# Add your SSL certificates to config/ssl/
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check database status
docker-compose -f docker-compose.production.yml exec postgres pg_isready -U ai_user

# Check connection settings
docker-compose -f docker-compose.production.yml exec ai-backend env | grep DATABASE

# View database logs
docker-compose -f docker-compose.production.yml logs postgres
```

#### 2. Application Won't Start

```bash
# Check application logs
docker-compose -f docker-compose.production.yml logs ai-backend

# Check if all required environment variables are set
docker-compose -f docker-compose.production.yml config

# Verify Docker image was built correctly
docker images | grep saas-project-finder
```

#### 3. High Memory Usage

```bash
# Monitor container resource usage
docker stats

# Check database connection pool usage
curl http://localhost:8000/health/database | jq .pool_info
```

### Performance Optimization

#### Database Performance

```bash
# Monitor slow queries
docker-compose -f docker-compose.production.yml exec postgres psql -U ai_user -d ai_backend -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;"
```

#### Application Performance

```bash
# Monitor endpoint performance
curl http://localhost:8000/metrics | grep http_request_duration

# Check for memory leaks
docker-compose -f docker-compose.production.yml exec ai-backend ps aux
```

## Maintenance

### Regular Maintenance Tasks

1. **Weekly**:
   - Review application logs for errors
   - Check backup integrity
   - Monitor disk space usage

2. **Monthly**:
   - Update Docker images
   - Rotate secrets
   - Review and update dependencies

3. **Quarterly**:
   - Security audit
   - Performance review
   - Capacity planning

### Update Process

```bash
# 1. Backup current deployment
./scripts/deploy.sh production backup

# 2. Deploy new version
git pull origin main
./scripts/deploy.sh production deploy

# 3. Verify deployment
./scripts/deploy.sh production health

# 4. Rollback if needed
./scripts/deploy.sh production rollback
```

## Support and Monitoring

### Key Metrics to Monitor

1. **Application Health**:
   - Response time < 200ms (p95)
   - Error rate < 0.1%
   - Uptime > 99.9%

2. **Database Performance**:
   - Connection pool utilization < 80%
   - Query response time < 100ms (p95)
   - No failed connections

3. **Business Metrics**:
   - Agent execution success rate > 99%
   - Token usage per tenant
   - API key usage patterns

### Alerting

Set up alerts for:
- Service down (health check fails)
- High error rate (> 1%)
- Database connection issues
- High memory/CPU usage (> 80%)
- Disk space low (< 10% free)

For questions or issues, refer to the application logs and metrics first, then contact the development team with specific error messages and context.
# DocMind AI - Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Development Setup](#development-setup)
4. [Production Deployment](#production-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Cloud Deployment](#cloud-deployment)
7. [Configuration](#configuration)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows (with WSL2)
- **Python**: 3.10 or higher
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 10GB free space for models and data

### Required Services
- **PostgreSQL** 14+ (for production) or SQLite (for development)
- **Redis** 6+ (optional, for caching)
- **Docker** 20+ (for containerized deployment)

---

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-org/docmind-ai.git
cd docmind-ai
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Application
```bash
# Start API server
uvicorn docmind_ai.api.app:app --reload --port 8000

# In another terminal, start Streamlit UI
streamlit run ui/app.py --server.port 8501
```

### 5. Access Application
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **UI**: http://localhost:8501

---

## Development Setup

### Environment Variables

Create a `.env` file in the project root:

```env
# Environment
ENV=development
DEBUG=true

# Database
DATABASE_URL=sqlite:///./docmind.db

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256

# API
API_KEY_ENABLED=false

# OCR
OCR_ENGINE=easyocr
EASYOCR_LANGUAGES=en,te,hi,ta

# AI Models
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
```

### Database Setup

#### SQLite (Development)
No additional setup required. The database file will be created automatically.

#### PostgreSQL (Production)
```sql
CREATE DATABASE docmind_db;
CREATE USER docmind WITH PASSWORD 'docmind_password';
GRANT ALL PRIVILEGES ON DATABASE docmind_db TO docmind;
```

Update `DATABASE_URL`:
```env
DATABASE_URL=postgresql://docmind:docmind_password@localhost:5432/docmind_db
```

### Model Downloads

Some components require pre-trained models. They'll be downloaded automatically on first use, but you can pre-download them:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

import easyocr
reader = easyocr.Reader(['en'])
```

---

## Production Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.10 python3-pip nginx redis-server postgresql

# Create application user
sudo useradd -m -s /bin/bash docmind
sudo mkdir -p /opt/docmind
sudo chown docmind:docmind /opt/docmind
```

### 2. Application Installation

```bash
# Clone and setup
cd /opt/docmind
git clone https://github.com/your-org/docmind-ai.git .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create data directories
mkdir -p data/uploads data/processed data/reports
chmod 755 data/*
```

### 3. Systemd Service

Create `/etc/systemd/system/docmind-api.service`:
```ini
[Unit]
Description=DocMind AI API
After=network.target

[Service]
Type=simple
User=docmind
WorkingDirectory=/opt/docmind
Environment="PATH=/opt/docmind/venv/bin"
Environment="ENV=production"
ExecStart=/opt/docmind/venv/bin/uvicorn docmind_ai.api.app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/docmind-ui.service`:
```ini
[Unit]
Description=DocMind AI UI
After=network.target

[Service]
Type=simple
User=docmind
WorkingDirectory=/opt/docmind
Environment="PATH=/opt/docmind/venv/bin"
Environment="DOCMIND_API_URL=http://localhost:8000"
ExecStart=/opt/docmind/venv/bin/streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable docmind-api docmind-ui
sudo systemctl start docmind-api docmind-ui
```

### 4. Nginx Configuration

Create `/etc/nginx/sites-available/docmind`:
```nginx
upstream docmind_api {
    server 127.0.0.1:8000;
}

upstream docmind_ui {
    server 127.0.0.1:8501;
}

server {
    listen 80;
    server_name your-domain.com;

    # API
    location /api {
        proxy_pass http://docmind_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # UI
    location / {
        proxy_pass http://docmind_ui;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_upgrade_location $http_upgrade;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/docmind /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Docker Deployment

### 1. Build Images

```bash
# Build API image
docker build -f deployment/Dockerfile -t docmind-api:latest .

# Or use Docker Compose
docker-compose -f deployment/docker-compose.yml up -d
```

### 2. Environment Configuration

Create `.env` file:
```env
DATABASE_URL=postgresql://docmind:docmind_password@postgres:5432/docmind_db
REDIS_URL=redis://redis:6379/0
ENV=production
```

### 3. Run Containers

```bash
# Start all services
docker-compose -f deployment/docker-compose.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access Services

- **Application**: http://localhost (via Nginx)
- **API Direct**: http://localhost:8000
- **UI Direct**: http://localhost:8501

---

## Cloud Deployment

### AWS (EC2 + ECS)

1. **Launch EC2 Instance**
```bash
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxx \
    --subnet-id subnet-xxxxx
```

2. **Setup RDS PostgreSQL**
```bash
aws rds create-db-instance \
    --db-instance-identifier docmind-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username docmind \
    --master-user-password your-password \
    --allocated-storage 20
```

3. **Deploy using CodeDeploy or ECS**
(Similar steps for other cloud providers)

### Google Cloud Platform

1. **Cloud SQL** for PostgreSQL
2. **Cloud Run** or **GKE** for containers
3. **Cloud Storage** for file storage
4. **Load Balancer** for traffic management

### Azure

1. **Azure Database for PostgreSQL**
2. **Azure Container Instances** or **AKS**
3. **Azure Blob Storage** for files
4. **Application Gateway** for load balancing

---

## Configuration

### Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | development | Environment mode |
| `DEBUG` | true | Enable debug mode |
| `DATABASE_URL` | sqlite:///./docmind.db | Database connection string |
| `SECRET_KEY` | - | JWT signing secret |
| `OCR_ENGINE` | easyocr | OCR engine to use |
| `SENTENCE_TRANSFORMER_MODEL` | all-MiniLM-L6-v2 | Semantic similarity model |
| `MAX_FILE_SIZE` | 104857600 | Maximum upload size (100MB) |
| `LOG_LEVEL` | INFO | Logging level |

### OCR Languages

Supported languages for OCR:
- English (en)
- Telugu (te)
- Hindi (hi)
- Tamil (ta)

---

## Monitoring

### Health Check Endpoints

```bash
# API health
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "services": {...}
}
```

### Metrics

The application exposes Prometheus metrics at `/metrics`:
- `docmind_requests_total` - Total requests
- `docmind_request_duration_seconds` - Request latency
- `docmind_comparisons_total` - Total comparisons performed
- `docmind_errors_total` - Total errors

### Logging

Logs are written to:
- **Console** (stdout)
- **File**: `docmind.log`

Log format:
```
2024-01-15 10:30:00 - docmind_ai.api - INFO - Request completed: POST /api/v1/compare 200
```

---

## Troubleshooting

### Common Issues

**1. OCR Model Download Fails**
```bash
# Clear cache and retry
rm -rf ~/.cache/easyocr
python -c "import easyocr; easyocr.Reader(['en'])"
```

**2. Database Connection Issues**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U docmind -d docmind_db -h localhost -c "SELECT 1"
```

**3. Memory Issues**
```bash
# Check memory usage
free -h

# Increase swap if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**4. Port Already in Use**
```bash
# Find process using port
lsof -i :8000

# Kill if needed
kill -9 <PID>
```

### Getting Help

For issues and support:
1. Check the documentation at `/docs`
2. Review logs for error details
3. Open an issue on GitHub with:
   - Environment details
   - Error message
   - Steps to reproduce

---

## Security Considerations

### Production Checklist

- [ ] Change `SECRET_KEY` to a strong, unique value
- [ ] Enable `API_KEY_ENABLED` in production
- [ ] Use HTTPS (configure SSL/TLS)
- [ ] Set up firewall rules
- [ ] Enable database encryption
- [ ] Regular backups
- [ ] Security scanning
- [ ] Rate limiting enabled

### Authentication

For API authentication, use the `/api/v1/auth` endpoints:
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "user@example.com", "password": "password"}'

# Use token
curl http://localhost:8000/api/v1/protected \
    -H "Authorization: Bearer <token>"
```

---

## Performance Optimization

### Recommendations

1. **Use Redis** for caching comparison results
2. **Increase workers** for high traffic:
   ```bash
   uvicorn docmind_ai.api.app:app --workers 4
   ```
3. **Enable compression** in Nginx
4. **Use CDN** for static assets
5. **Database indexing** on frequently queried fields

### Benchmarking

```bash
# Run load test
wrk -t12 -c400 -d30s http://localhost:8000/api/v1/health
```

---

## Backup and Recovery

### Database Backup

```bash
# SQLite
cp docmind.db docmind_backup_$(date +%Y%m%d).db

# PostgreSQL
pg_dump -U docmind docmind_db > backup_$(date +%Y%m%d).sql
```

### File Backup

```bash
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
```

### Recovery

```bash
# Database
cp backup_file.db docmind.db

# Files
tar -xzf backup_file.tar.gz
```

---

*Last updated: January 2024*
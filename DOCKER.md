# Docker Setup for AI News Feed

This guide explains how to run the AI News Feed application using Docker for improved stability and easier deployment.

## Prerequisites

- Docker and Docker Compose installed
- LM Studio running on your host machine
- Port 1234 available for LM Studio
- Ports 3000 and 8000 available for the application

## Quick Start

1. **Stop any running backend processes:**
   ```bash
   ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}' | xargs kill -9
   ```

2. **Create data directory:**
   ```bash
   mkdir -p data
   ```

3. **Build and start the containers:**
   ```bash
   docker-compose up -d --build
   ```

4. **Check if services are running:**
   ```bash
   docker-compose ps
   ```

5. **View logs:**
   ```bash
   docker-compose logs -f backend
   ```

## Configuration

### LM Studio Connection

For **WSL users** or when LM Studio is on the host:
- The backend automatically uses `host.docker.internal` to connect to LM Studio
- Ensure LM Studio has "Enable Network Access" and "Enable CORS" enabled

For **custom LM Studio host**:
Edit `docker-compose.yml`:
```yaml
environment:
  - LM_STUDIO_HOST=your-lm-studio-ip
  - LM_STUDIO_PORT=1234
```

### Database Location

The SQLite database is stored in `./data/news_feed.db` and persists between container restarts.

## Usage

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

## Managing the Application

### Start services:
```bash
docker-compose up -d
```

### Stop services:
```bash
docker-compose down
```

### Restart backend:
```bash
docker-compose restart backend
```

### View logs:
```bash
# All logs
docker-compose logs

# Backend logs only
docker-compose logs backend

# Follow logs
docker-compose logs -f backend
```

### Update code:
After making changes to the code:
```bash
docker-compose down
docker-compose up -d --build
```

### Reset database:
```bash
docker-compose down
rm -rf data/news_feed.db
docker-compose up -d
```

## Troubleshooting

### Backend keeps crashing

1. Check logs:
   ```bash
   docker-compose logs backend
   ```

2. Verify LM Studio is accessible:
   ```bash
   curl http://host.docker.internal:1234/v1/models
   ```

3. Check health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```

### Cannot connect to LM Studio

1. Ensure LM Studio is running with network access enabled
2. For WSL, check Windows firewall settings
3. Try setting explicit host IP in docker-compose.yml

### Frontend shows "Backend Offline"

1. Check if backend container is running:
   ```bash
   docker-compose ps
   ```

2. Check backend logs for errors:
   ```bash
   docker-compose logs backend
   ```

3. Restart the backend:
   ```bash
   docker-compose restart backend
   ```

## Development Mode

To run with live code reloading:

1. Modify `docker-compose.yml` to remove `:ro` from volume mounts
2. Add this to the backend service:
   ```yaml
   command: uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Production Considerations

For production deployment:

1. Use specific image tags instead of building locally
2. Set up proper secrets management for API keys
3. Configure HTTPS with SSL certificates
4. Set up monitoring and logging
5. Use a production database like PostgreSQL
6. Configure resource limits in docker-compose.yml

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Frontend       │────▶│  Nginx Proxy    │────▶│  Backend API    │
│  (Port 3000)    │     │                 │     │  (Port 8000)    │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │                 │
                                                 │   LM Studio     │
                                                 │  (Port 1234)    │
                                                 │                 │
                                                 └─────────────────┘
```
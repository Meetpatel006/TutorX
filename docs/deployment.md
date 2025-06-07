# TutorX-MCP Deployment Guide

This guide provides instructions for deploying the TutorX-MCP server in production environments.

## Deployment Options

### 1. Docker Deployment (Recommended)

The easiest way to deploy TutorX-MCP is using Docker and Docker Compose:

```bash
# Navigate to the deployment directory
cd deployment

# Start the services
docker-compose up -d
```

This will start:
- The MCP server at http://localhost:8000
- The Gradio web interface at http://localhost:7860
- A Redis instance for caching and session management

### 2. Manual Deployment

#### Prerequisites

- Python 3.12 or higher
- Redis (optional, but recommended for production)

#### Steps

1. Install dependencies:
   ```bash
   uv install -e .
   ```

2. Configure environment variables:
   ```bash
   # Server configuration
   export MCP_HOST=0.0.0.0
   export MCP_PORT=8000
   
   # Redis configuration (if using)
   export REDIS_HOST=localhost
   export REDIS_PORT=6379
   ```

3. Run the server:
   ```bash
   python run.py --mode both --host 0.0.0.0
   ```

## Scaling

For high-traffic deployments, consider:

1. Using a reverse proxy like Nginx or Traefik in front of the services
2. Implementing load balancing for multiple MCP server instances
3. Scaling the Redis cache using Redis Sentinel or Redis Cluster

## Monitoring

We recommend setting up:

1. Prometheus for metrics collection
2. Grafana for visualization
3. ELK stack for log management

## Security Considerations

1. In production, always use HTTPS
2. Implement proper authentication for API access
3. Keep dependencies updated
4. Follow least privilege principles for service accounts

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| MCP_HOST | Host address for MCP server | 127.0.0.1 |
| MCP_PORT | Port for MCP server | 8000 |
| REDIS_HOST | Redis host address | localhost |
| REDIS_PORT | Redis port | 6379 |
| LOG_LEVEL | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |

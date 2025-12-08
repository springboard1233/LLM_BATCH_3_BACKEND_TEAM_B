# Docker Setup Guide for Fraud Analytics Backend

This guide explains how to run the Fraud Analytics FastAPI backend using Docker and Docker Compose.

## Prerequisites

- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: Usually comes with Docker Desktop
- **.env file**: Environment variables configured in your project

## File Structure

```
├── Dockerfile              # Production Docker image
├── Dockerfile.dev          # Development Docker image with hot reload
├── docker-compose.yml      # Development compose file
├── docker-compose.dev.yml  # Development environment with volumes
├── docker-compose.prod.yml # Production environment
├── .dockerignore           # Files to exclude from Docker image
├── DOCKER_SETUP.md         # This file
└── .env.docker             # Docker environment template
```

## Quick Start

### 1. Development Setup (with hot reload)

```bash
# Build and start services in development mode
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f backend

# Stop services
docker-compose -f docker-compose.dev.yml down
```

The backend will be available at `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 2. Production Setup

```bash
# Build and start services in production mode
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### 3. Standard Setup (Recommended for most cases)

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## Environment Variables

Create a `.env` file or `.env.local` in the project root with:

```env
GEMINI_API_KEY=your_api_key_here
MONGO_USER=backend_user
MONGO_PASSWORD=aBWmEIMJPz3yLIgq
REDIS_PASSWORD=
```

For production, ensure these are securely set:
```bash
export GEMINI_API_KEY="your_secure_api_key"
docker-compose -f docker-compose.prod.yml up -d
```

## Services

### MongoDB
- **Container**: fraud_mongodb
- **Port**: 27017
- **Default User**: backend_user
- **Default Password**: aBWmEIMJPz3yLIgq
- **Database**: bfsidata
- **Volume**: mongodb_data

### Redis
- **Container**: fraud_redis
- **Port**: 6379
- **Volume**: redis_data

### FastAPI Backend
- **Container**: fraud_backend
- **Port**: 8000
- **Endpoint**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

## Common Commands

### View running containers
```bash
docker-compose ps
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f mongodb
docker-compose logs -f redis
```

### Access services

#### MongoDB Shell
```bash
docker exec -it fraud_mongodb mongosh -u backend_user -p aBWmEIMJPz3yLIgq
```

#### Redis CLI
```bash
docker exec -it fraud_redis redis-cli
```

#### Backend Shell
```bash
docker exec -it fraud_backend bash
```

### Rebuild images
```bash
docker-compose build --no-cache
```

### Clean up
```bash
# Stop and remove containers
docker-compose down

# Also remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove all unused images
docker image prune -a
```

## Troubleshooting

### Backend fails to start
Check the logs:
```bash
docker-compose logs backend
```

Common issues:
- **MongoDB not ready**: Wait for MongoDB health check to pass
- **Redis not accessible**: Check REDIS_HOST is set correctly
- **Port conflicts**: Ensure ports 8000, 27017, 6379 are not in use
- **Missing dependencies**: Rebuild the image: `docker-compose build`

### MongoDB connection issues
```bash
# Test connection
docker exec -it fraud_mongodb mongosh -u backend_user -p aBWmEIMJPz3yLIgq
```

### Redis connection issues
```bash
# Test connection
docker exec -it fraud_redis redis-cli ping
```

### Persistent data is lost
Make sure volumes are properly mounted:
```bash
docker volume ls
```

### Network issues
Services communicate via the `fraud_network` bridge network. Ensure they're on the same network:
```bash
docker network inspect fraud_network
```

## Development Workflow

### Hot Reload
When using `docker-compose.dev.yml`, changes to Python files are automatically detected and the server reloads:

```bash
# Make changes to src/ files
# Backend automatically reloads (watch the logs)
docker-compose -f docker-compose.dev.yml logs -f backend
```

### Testing changes
```bash
# Rebuild after dependency changes
docker-compose -f docker-compose.dev.yml build

# Restart
docker-compose -f docker-compose.dev.yml restart backend
```

### Interactive debugging
```bash
# Get a shell
docker exec -it fraud_backend bash

# Install additional packages
pip install debugpy
```

## Production Considerations

### Security
1. **Change default credentials** in `docker-compose.prod.yml`
2. **Use environment variables** for sensitive data
3. **Don't commit sensitive data** to version control
4. **Use health checks** (already configured)
5. **Set up proper logging** (json-file driver configured)
6. **Use read-only volumes** where appropriate

### Performance
1. **Use volume mounts** for models and data directories
2. **Enable logging limits** to prevent disk fill-up
3. **Configure resource limits**:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
   ```

### Monitoring
```bash
# Monitor resource usage
docker stats

# Check health status
docker-compose ps
```

## Integration with Frontend

The frontend should connect to:
```
http://localhost:8000
```

With CORS origins already configured in `main.py`:
- http://localhost:5173
- http://localhost:3000

## Next Steps

1. **Start containers**: `docker-compose up -d`
2. **Verify services**: `docker-compose ps`
3. **Check API**: Visit http://localhost:8000/docs
4. **Review logs**: `docker-compose logs -f`

For more Docker documentation, see [Docker Docs](https://docs.docker.com/)

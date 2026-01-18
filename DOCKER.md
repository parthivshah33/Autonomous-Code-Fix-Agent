# Docker Setup Guide

This guide explains how to run the Multi-Agent Code Fixer System using Docker.

## Prerequisites

- Docker Engine 20.10+ installed
- Docker Compose 2.0+ (optional, for easier orchestration)
- OpenAI API key

## Quick Start

### 1. Clone and Setup

```bash
cd multi-agent-fixer
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Build the Image

```bash
docker build -t multi-agent-fixer:latest .
```

### 3. Run with Convenience Scripts

**Linux/Mac:**
```bash
chmod +x run-docker.sh
./run-docker.sh data/input/trace_1.json ../fastapi-tdd-user-authentication
```

**Windows:**
```cmd
run-docker.bat data/input/trace_1.json ../fastapi-tdd-user-authentication
```

### 4. Or Run Manually

```bash
docker run --rm \
  -v "$(pwd)/data/input:/app/data/input:ro" \
  -v "$(pwd)/data/output:/app/data/output" \
  -v "$(pwd)/../fastapi-tdd-user-authentication:/app/target-codebase:ro" \
  --env-file .env \
  -e TARGET_ROOT_DIR=/app/target-codebase \
  multi-agent-fixer:latest \
  python main.py data/input/trace_1.json --target-root /app/target-codebase
```

## Docker Compose

### Using Docker Compose

1. **Update `docker-compose.yml`** with your target codebase path:
   ```yaml
   volumes:
     - ../your-target-codebase:/app/target-codebase:ro
   ```

2. **Run:**
   ```bash
   docker-compose run --rm multi-agent-fixer \
     python main.py data/input/trace_1.json --target-root /app/target-codebase
   ```

## Volume Mounts Explained

- **`./data/input:/app/data/input:ro`** - Mounts your trace files (read-only)
- **`./data/output:/app/data/output`** - Mounts output directory for results
- **`../target-codebase:/app/target-codebase:ro`** - Mounts your codebase to fix (read-only)

## Environment Variables

Set via `.env` file or `-e` flags:

- `OPENAI_API_KEY` - Required: Your OpenAI API key
- `LLM_MODEL` - Optional: Model to use (default: `gpt-4o`)
- `LLM_TEMPERATURE` - Optional: Temperature setting (default: `0`)
- `TARGET_ROOT_DIR` - Optional: Target root directory path in container

## Troubleshooting

### Permission Errors

If you encounter permission errors, ensure the output directory is writable:

```bash
chmod -R 755 data/output
```

### File Not Found

- Verify volume mounts are correct
- Check that paths in the container match your expectations
- Ensure target codebase is mounted at `/app/target-codebase`

### API Key Issues

- Ensure `.env` file exists and contains `OPENAI_API_KEY`
- Check that `--env-file .env` is included in docker run command
- Verify the API key is valid

## Building for Production

For production deployments, you may want to:

1. Use multi-stage builds to reduce image size
2. Set up health checks
3. Configure resource limits
4. Use Docker secrets for API keys

Example production Dockerfile:

```dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "main.py"]
```

## Shipping to Interviewer

To ship this project:

1. **Create a package:**
   ```bash
   # Create a zip file excluding unnecessary files
   zip -r multi-agent-fixer.zip . \
     -x "*.pyc" "__pycache__/*" "*.log" "data/output/*" ".git/*"
   ```

2. **Or use git:**
   ```bash
   git archive -o multi-agent-fixer.zip HEAD
   ```

3. **Include in package:**
   - All source code
   - `Dockerfile` and `docker-compose.yml`
   - `requirements.txt`
   - `README.md` and `DOCKER.md`
   - `.env.example`
   - `run-docker.sh` and `run-docker.bat`
   - Sample trace file in `data/input/`

4. **Instructions for interviewer:**
   - Extract the package
   - Copy `.env.example` to `.env` and add API key
   - Run `docker build -t multi-agent-fixer:latest .`
   - Run using the convenience scripts or docker-compose

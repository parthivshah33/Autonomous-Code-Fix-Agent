#!/bin/bash
# Docker run script for Multi-Agent Code Fixer

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${RED}Please edit .env file and add your OPENAI_API_KEY${NC}"
        exit 1
    else
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY not set in .env file${NC}"
    exit 1
fi

# Default values
TRACE_FILE="${1:-data/input/trace_1.json}"
TARGET_ROOT="${2:-../fastapi-tdd-user-authentication}"
OUTPUT_DIR="${3:-data/output}"

echo -e "${GREEN}Running Multi-Agent Code Fixer in Docker...${NC}"
echo "Trace file: $TRACE_FILE"
echo "Target root: $TARGET_ROOT"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Build image if it doesn't exist
if ! docker images | grep -q "multi-agent-fixer"; then
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t multi-agent-fixer:latest .
fi

# Run the container
docker run --rm \
    -v "$(pwd)/data/input:/app/data/input:ro" \
    -v "$(pwd)/data/output:/app/data/output" \
    -v "$(pwd)/../$TARGET_ROOT:/app/target-codebase:ro" \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    -e LLM_MODEL="${LLM_MODEL:-gpt-4o}" \
    -e LLM_TEMPERATURE="${LLM_TEMPERATURE:-0}" \
    -e TARGET_ROOT_DIR="/app/target-codebase" \
    multi-agent-fixer:latest \
    python main.py "$TRACE_FILE" --target-root /app/target-codebase --output-dir "$OUTPUT_DIR"

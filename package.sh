#!/bin/bash
# Package script for shipping Multi-Agent Code Fixer

PACKAGE_NAME="multi-agent-fixer"
VERSION=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="${PACKAGE_NAME}_${VERSION}.zip"

echo "Packaging Multi-Agent Code Fixer..."
echo "Output: $OUTPUT_FILE"
echo ""

# Create temporary directory
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/$PACKAGE_NAME"

# Copy files
echo "Copying files..."
mkdir -p "$PACKAGE_DIR"
cp -r src "$PACKAGE_DIR/"
cp -r data "$PACKAGE_DIR/"
cp main.py "$PACKAGE_DIR/"
cp requirements.txt "$PACKAGE_DIR/"
cp README.md "$PACKAGE_DIR/"
cp DOCKER.md "$PACKAGE_DIR/"
cp Dockerfile "$PACKAGE_DIR/"
cp docker-compose.yml "$PACKAGE_DIR/"
cp .dockerignore "$PACKAGE_DIR/"
cp .env.example "$PACKAGE_DIR/"
cp .gitignore "$PACKAGE_DIR/"
cp PROJECT_SUMMARY.md "$PACKAGE_DIR/"
cp run-docker.sh "$PACKAGE_DIR/"
cp run-docker.bat "$PACKAGE_DIR/"
cp package.sh "$PACKAGE_DIR/"

# Make scripts executable
chmod +x "$PACKAGE_DIR/run-docker.sh"
chmod +x "$PACKAGE_DIR/package.sh"

# Clean up unnecessary files
echo "Cleaning up..."
find "$PACKAGE_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find "$PACKAGE_DIR" -type f -name "*.pyc" -delete
find "$PACKAGE_DIR" -type f -name "*.pyo" -delete
find "$PACKAGE_DIR" -type f -name "*.log" -delete
rm -rf "$PACKAGE_DIR/data/output"/*.json 2>/dev/null
rm -rf "$PACKAGE_DIR/data/output"/*.py 2>/dev/null

# Create zip file
echo "Creating zip file..."
cd "$TEMP_DIR"
zip -r "$OUTPUT_FILE" "$PACKAGE_NAME" -q

# Move to original directory
mv "$OUTPUT_FILE" "$(pwd)/"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "✓ Package created: $OUTPUT_FILE"
echo ""
echo "To ship:"
echo "  1. Send $OUTPUT_FILE to the interviewer"
echo "  2. Include instructions to:"
echo "     - Extract the package"
echo "     - Copy .env.example to .env and add OPENAI_API_KEY"
echo "     - Run: docker build -t multi-agent-fixer:latest ."
echo "     - Run: ./run-docker.sh data/input/trace_1.json ../target-codebase"

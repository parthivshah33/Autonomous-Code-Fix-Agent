# Shipping Guide for Interviewers

This guide explains how to receive, set up, and run the Multi-Agent Code Fixer System.

## What You'll Receive

The package includes:
- Complete source code
- Docker configuration files
- Setup scripts for easy execution
- Sample trace file for testing
- Comprehensive documentation

## Quick Start (5 Minutes)

### Step 1: Extract the Package

```bash
unzip multi-agent-fixer_*.zip
cd multi-agent-fixer
```

### Step 2: Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### Step 3: Build Docker Image

```bash
docker build -t multi-agent-fixer:latest .
```

### Step 4: Run the System

**Option A: Using Convenience Script**

Linux/Mac:
```bash
chmod +x run-docker.sh
./run-docker.sh data/input/trace_1.json ../target-codebase
```

Windows:
```cmd
run-docker.bat data\input\trace_1.json ..\target-codebase
```

**Option B: Using Docker Run**

```bash
docker run --rm \
  -v "$(pwd)/data/input:/app/data/input:ro" \
  -v "$(pwd)/data/output:/app/data/output" \
  -v "$(pwd)/../target-codebase:/app/target-codebase:ro" \
  --env-file .env \
  -e TARGET_ROOT_DIR=/app/target-codebase \
  multi-agent-fixer:latest \
  python main.py data/input/trace_1.json --target-root /app/target-codebase
```

**Option C: Using Docker Compose**

```bash
# Update docker-compose.yml with your target codebase path
docker-compose run --rm multi-agent-fixer \
  python main.py data/input/trace_1.json --target-root /app/target-codebase
```

## Directory Structure

Ensure your directory structure looks like this:

```
parent-directory/
├── multi-agent-fixer/          # Extracted package
│   ├── src/
│   ├── data/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── ...
└── target-codebase/            # Your codebase to fix
    ├── app/
    ├── src/
    └── ...
```

## Testing with Sample Data

The package includes a sample trace file (`data/input/trace_1.json`) that references:
- Linux paths: `/usr/srv/app/services/user.py`
- Error: `AttributeError: type object 'User' has no attribute 'emails'`

To test with your own codebase:

1. Place your codebase at the same level as `multi-agent-fixer`
2. Update the target root path in the run command
3. Ensure your trace.json file is in `data/input/`

## Expected Output

After running, you should see:

```
================================================================================
Multi-Agent Code Fixer System
================================================================================
Input Error File: ...
Target Root Directory: ...
Output Directory: ...
================================================================================

[OK] RCA Report Generated
[OK] Fix Plan Generated
[OK] Patch Generated
  - Status: Success
  - Fixed File: .../fixed_user.py
```

Results will be in:
- `data/output/rca_report.json` - Root cause analysis
- `data/output/fix_plan.json` - Fix plan details
- `data/output/patch_result.json` - Patch application results
- `target-codebase/app/services/fixed_user.py` - Fixed code file

## Troubleshooting

### Docker Not Found
```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop
```

### Permission Denied (Linux/Mac)
```bash
chmod +x run-docker.sh
chmod -R 755 data/output
```

### API Key Error
- Ensure `.env` file exists and contains `OPENAI_API_KEY=your_key`
- Verify the API key is valid and has credits

### File Not Found
- Check that volume mounts are correct
- Verify target codebase path exists
- Ensure trace file is in `data/input/`

### Path Resolution Issues
- If trace.json has Linux paths (starting with `/`), ensure `--target-root` is set
- Verify the target codebase structure matches expected paths

## System Requirements

- **Docker**: 20.10+ (recommended)
- **Python**: 3.8+ (if running without Docker)
- **OpenAI API**: Valid API key with credits
- **Disk Space**: ~500MB for Docker image
- **Memory**: 2GB+ recommended

## Architecture Overview

The system uses three AI agents in sequence:

1. **RCA Agent**: Analyzes error traces to identify root causes
2. **Fix Suggestion Agent**: Creates detailed fix plans
3. **Patch Generation Agent**: Applies fixes using tools

All agents use LangChain/LangGraph for orchestration and OpenAI GPT-4 for reasoning.

## Key Features Demonstrated

- ✅ Multi-agent AI system architecture
- ✅ LangGraph workflow orchestration
- ✅ Tool-based code manipulation (ReAct pattern)
- ✅ Path resolution for cross-platform compatibility
- ✅ Structured output using Pydantic models
- ✅ Comprehensive logging and state management
- ✅ Docker containerization for reproducibility

## Questions?

Refer to:
- `README.md` - Full documentation
- `DOCKER.md` - Docker-specific details
- `PROJECT_SUMMARY.md` - Technical overview

## Evaluation Checklist

When evaluating this project, consider:

- [ ] Code quality and organization
- [ ] Agent design and prompt engineering
- [ ] Tool implementation and error handling
- [ ] State management and workflow design
- [ ] Path resolution logic
- [ ] Docker setup and documentation
- [ ] Error handling and edge cases
- [ ] Logging and observability

# Multi-Agent Code Fixer System

An autonomous code fixing AI agent system built with LangChain and LangGraph that performs Root Cause Analysis (RCA), generates fix suggestions, and applies patches to buggy code.

## Architecture

The system consists of three specialized agents working in sequence:

1. **RCA Agent**: Analyzes error traces and logs to identify root causes
2. **Fix Suggestion Agent**: Creates detailed, actionable fix plans based on RCA findings
3. **Patch Generation Agent**: Applies fixes using tools to read, verify, and write code changes

## Project Structure

```
multi-agent-fixer/
├── data/
│   ├── input/                # Place error/trace JSON files here
│   └── output/               # Generated fixed files & logs go here
├── src/
│   ├── agents/               # Agent implementations
│   │   ├── rca_agent.py      # RCA Agent logic
│   │   ├── fix_agent.py      # Fix Suggestion Agent logic
│   │   └── patch_agent.py    # Patch Generation Agent logic
│   ├── tools/                # Custom tool definitions
│   │   ├── file_tools.py     # read_source_file, apply_patch_and_write
│   │   ├── code_tools.py     # verify_code_snippet, validate_python_syntax
│   │   └── rca_tools.py      # get_root_cause_details
│   ├── graph/                # LangGraph orchestration
│   │   ├── state.py          # SharedState definition
│   │   └── workflow.py       # Node & Edge definitions
│   ├── utils/
│   │   ├── logger.py         # Message history logging
│   │   ├── path_resolver.py  # Path resolution utility
│   │   └── context.py        # Runtime context management
│   ├── config.py             # LLM configurations
│   └── __init__.py
├── main.py                   # Entry point
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Docker Compose configuration
├── .dockerignore             # Docker ignore patterns
├── .env.example              # Environment variables template
├── run-docker.sh             # Docker run script (Linux/Mac)
├── run-docker.bat            # Docker run script (Windows)
├── .gitignore
├── README.md
└── requirements.txt
```

## Installation

### Prerequisites

- Python 3.8 or higher (for local installation)
- Docker and Docker Compose (for Docker installation)
- OpenAI API key

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd multi-agent-fixer
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

5. **Set up target codebase directory:**
   
   **Important**: If your trace.json files contain Linux-style paths (like `/usr/srv/app/...`), you must set up the target codebase directory.
   
   The multi-agent-fixer project and the target codebase you want to fix should be at the same directory level:
   ```
   parent-directory/
   ├── multi-agent-fixer/          # This project
   └── target-codebase/            # The codebase you want to fix
       ├── src/
       ├── models/
       └── ...
   ```
   
   You can specify the target root directory in two ways:
   
   **Option A: Command line argument (recommended)**
   ```bash
   python main.py data/input/trace_1.json --target-root ../target-codebase
   ```
   
   **Option B: Environment variable**
   Add to your `.env` file:
   ```
   TARGET_ROOT_DIR=../target-codebase
   ```
   
   The system will automatically resolve Linux paths (like `/usr/srv/app/models.py`) to Windows paths relative to your target root directory.

## Docker Installation (Recommended)

Docker provides an isolated, reproducible environment that works across different operating systems.

### Quick Start with Docker

1. **Clone or navigate to the project directory:**
   ```bash
   cd multi-agent-fixer
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Build the Docker image:**
   ```bash
   docker build -t multi-agent-fixer:latest .
   ```

4. **Run using Docker:**
   ```bash
   # Using the convenience script (Linux/Mac)
   ./run-docker.sh data/input/trace_1.json ../fastapi-tdd-user-authentication
   
   # Or using the convenience script (Windows)
   run-docker.bat data/input/trace_1.json ../fastapi-tdd-user-authentication
   
   # Or using docker run directly
   docker run --rm \
     -v "$(pwd)/data/input:/app/data/input:ro" \
     -v "$(pwd)/data/output:/app/data/output" \
     -v "$(pwd)/../fastapi-tdd-user-authentication:/app/target-codebase:ro" \
     --env-file .env \
     -e TARGET_ROOT_DIR=/app/target-codebase \
     multi-agent-fixer:latest \
     python main.py data/input/trace_1.json --target-root /app/target-codebase
   ```

5. **Using Docker Compose:**
   ```bash
   # Update docker-compose.yml with your target codebase path
   # Then run:
   docker-compose run --rm multi-agent-fixer \
     python main.py data/input/trace_1.json --target-root /app/target-codebase
   ```

### Docker Volume Mounts

The Docker setup mounts:
- `./data/input` → `/app/data/input` (read-only) - for trace files
- `./data/output` → `/app/data/output` - for generated results
- `../target-codebase` → `/app/target-codebase` (read-only) - your codebase to fix

Adjust the paths in `docker-compose.yml` or the run scripts as needed.

## Usage

### Basic Usage

Run the system with an error/trace JSON file:

```bash
python main.py data/input/trace_1.json
```

### Command Line Options

```bash
python main.py <error_file> [options]

Arguments:
  error_file              Path to the error/trace JSON file

Options:
  --target-root DIR       Root directory of the target codebase being fixed
                         (required if trace.json contains Linux paths like /usr/srv/app/...)
  --output-dir DIR        Output directory for logs and fixed files
                         (default: data/output)
  --verbose               Enable verbose output
  --help                 Show help message
```

### Example

```bash
# Run with default settings (paths used as-is)
python main.py data/input/trace_1.json

# Run with target root directory (for Linux paths in trace.json)
python main.py data/input/trace_1.json --target-root ../target-codebase

# Run with custom output directory
python main.py data/input/trace_1.json --output-dir results/

# Run with both target root and verbose output
python main.py data/input/trace_1.json --target-root ../target-codebase --verbose
```

## Input Format

The system expects a JSON file containing error/trace information with the following structure:

```json
[
  {
    "event_attributes": {
      "exception.type": "AttributeError",
      "exception.message": "type object 'User' has no attribute 'emails'",
      "exception.stacktrace": "Traceback (most recent call last):\n...",
      "exception.stack_details": "[{\"exception.file\": \"/usr/srv/app/models.py\", ...}]"
    }
  }
]
```

**Note on File Paths**: 
- If your trace.json contains Linux-style absolute paths (starting with `/`), you **must** specify the `--target-root` parameter pointing to your local codebase directory.
- The system will automatically map Linux paths (e.g., `/usr/srv/app/models.py`) to your local target root directory.
- If paths in trace.json are already Windows-relative or absolute Windows paths, you can omit `--target-root`.

## Output

The system generates several output files in the `data/output/` directory:

1. **agent_history.json**: Complete message history of all agent interactions
2. **final_state_*.json**: Final shared memory state with all agent outputs
3. **rca_report.json**: Structured RCA report
4. **fix_plan.json**: Detailed fix plan
5. **patch_result.json**: Patch generation results
6. **fixed_*.py**: Generated fixed code files (in the same directory as original files)

## Agent Tools

### RCA Agent Tools
- `get_root_cause_details`: Parses error files and extracts stack trace information

### Patch Generation Agent Tools
- `read_source_file`: Reads source code files to verify current state
- `verify_code_snippet`: Verifies code snippets exist before patching
- `apply_patch_and_write`: Applies changes and writes to new files (with `fixed_` prefix)
- `validate_python_syntax`: Validates Python syntax of generated files

## Logging

The system maintains comprehensive logging:

- **Message History**: All agent inputs, outputs, and tool calls
- **Iteration Tracking**: Each agent execution is logged with timestamps
- **State Snapshots**: Shared memory state is logged at each step
- **Final State**: Complete shared memory JSON is saved at the end

All logs are saved as JSON files for easy inspection and debugging.

## Configuration

Edit `src/config.py` or set environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `LLM_MODEL`: Model to use (default: "gpt-4o")
- `LLM_TEMPERATURE`: Temperature setting (default: 0)
- `DATA_INPUT_DIR`: Input directory (default: "data/input")
- `DATA_OUTPUT_DIR`: Output directory (default: "data/output")
- `TARGET_ROOT_DIR`: Root directory of target codebase (optional, can also use `--target-root` CLI arg)
- `LOG_FILE`: Log file path (default: "data/output/agent_history.json")

## Requirements

- Python 3.8+
- OpenAI API access
- See `requirements.txt` for Python package dependencies

## Troubleshooting

### Common Issues

1. **API Key Error**: Make sure your `.env` file contains a valid `OPENAI_API_KEY`
2. **File Not Found**: 
   - Ensure the error file path is correct and the file exists
   - If trace.json contains Linux paths, make sure you've specified `--target-root` pointing to your local codebase
   - Verify that the target root directory exists and contains the source files referenced in the trace
3. **Path Resolution Errors**: 
   - If you see "File not found" errors for Linux paths, ensure `--target-root` is set correctly
   - The target root should be the root directory of your codebase (where your source files are located)
   - Both the multi-agent-fixer project and target codebase should be at the same directory level
4. **Import Errors**: Make sure all dependencies are installed: `pip install -r requirements.txt`
5. **Permission Errors**: Ensure the output directory and target codebase directories are writable

### Debug Mode

Run with `--verbose` flag to see detailed error messages:

```bash
python main.py data/input/trace_1.json --verbose
```

## Development

### Project Structure Notes

- Agents are implemented as LangGraph nodes
- Tools use LangChain's `@tool` decorator
- State management uses TypedDict with Pydantic models
- Logging system tracks all interactions for compliance

### Adding New Tools

1. Create tool function in `src/tools/`
2. Decorate with `@tool` from `langchain_core.tools`
3. Import and add to agent's tool list

### Modifying Agents

1. Edit agent file in `src/agents/`
2. Update prompts as needed
3. Ensure state updates are returned correctly
4. 
## Contact

For questions or issues, please refer to the project documentation or contact the email : 'parthivshah125@gmail.com' or linkedin : https://www.linkedin.com/in/parthivshah33

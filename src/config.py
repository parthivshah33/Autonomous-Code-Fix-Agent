"""LLM and system configuration"""
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# LLM Configuration
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))

# Paths
DATA_INPUT_DIR: str = os.getenv("DATA_INPUT_DIR", "data/input")
DATA_OUTPUT_DIR: str = os.getenv("DATA_OUTPUT_DIR", "data/output")
TARGET_ROOT_DIR: Optional[str] = os.getenv("TARGET_ROOT_DIR", None)

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: str = os.getenv("LOG_FILE", "data/output/agent_history.json")

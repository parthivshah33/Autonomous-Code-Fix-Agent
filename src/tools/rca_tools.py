"""RCA-specific tools"""
from pathlib import Path
from typing import Dict, Union
from langchain_core.tools import tool
import json


@tool
def get_root_cause_details(file_path: Union[str, Path]) -> Dict[str, str]:
    """
    Parses a trace/log JSON file to extract, filter, and format exception details 
    specifically for an LLM-based root cause analysis agent.

    Args:
        file_path: The path to the JSON log file.

    Returns:
        Dictionary containing:
            - 'error_summary': A concise summary of the exception type and message.
            - 'internal_code_context': A well-formatted string of internal app code frames.
            - 'full_stack_trace': The raw stack trace for comprehensive reference.
            - 'llm_prompt_context': A combined, ready-to-use prompt text.
    """
    # Load the file
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found at {file_path}"}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format."}

    # Handle list vs dict root
    if isinstance(data, list) and len(data) > 0:
        event_data = data[0]
    elif isinstance(data, dict):
        event_data = data
    else:
        return {"error": "Unexpected JSON structure."}

    # Get 'event_attributes'
    attributes = event_data.get("event_attributes", {})
    if not attributes:
        return {"error": "No 'event_attributes' found in log."}

    # Fetch target keys
    raw_stack_details = attributes.get("exception.stack_details", "[]")
    stack_trace = attributes.get("exception.stacktrace", "No stacktrace found.")
    
    # Extraction of high-level error info
    exc_type = attributes.get("exception.type", "UnknownError")
    exc_message = attributes.get("exception.message", "No message provided")

    # Process 'stack_details'
    try:
        stack_details_list = json.loads(raw_stack_details)
    except json.JSONDecodeError:
        stack_details_list = []

    internal_frames = []
    
    # Filter out external files
    for frame in stack_details_list:
        is_external = True if frame.get("exception.is_file_external", "false") == "true" else False
        
        if not is_external:
            internal_frames.append({
                "file": frame.get("exception.file"),
                "function": frame.get("exception.function_name"),
                "line": frame.get("exception.line"),
                "code": frame.get("exception.function_body", "").strip()
            })

    # Create well-formatted feedback message
    formatted_context_parts = []
    
    formatted_context_parts.append(f"### Critical Error Summary")
    formatted_context_parts.append(f"**Type:** {exc_type}")
    formatted_context_parts.append(f"**Message:** {exc_message}\n")

    if internal_frames:
        formatted_context_parts.append(f"### Internal Code Execution Flow (Most Recent Call Last)")
        formatted_context_parts.append("The following frames represent the execution path within the application's internal source code:\n")
        
        for idx, frame in enumerate(reversed(internal_frames), 1):
            frame_text = (
                f"**Frame {idx}:** `{frame['function']}`\n"
                f"- **File:** `{frame['file']}` (Line {frame['line']})\n"
                f"- **Code Snippet:**\n"
                f"```python\n{frame['code']}\n```\n"
            )
            formatted_context_parts.append(frame_text)
    else:
        formatted_context_parts.append("No internal application frames detected in the stack details.\n")

    # Join the internal context into a single string
    internal_code_context = "\n".join(formatted_context_parts)

    # Return the dictionary output
    return {
        "error_summary": f"{exc_type}: {exc_message}",
        "internal_code_context": internal_code_context,
        "full_stack_trace": stack_trace,
        "llm_prompt_context": f"{internal_code_context}\n### Full Reference Stack Trace\n```\n{stack_trace}\n```"
    }

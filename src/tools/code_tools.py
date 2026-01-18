"""Code validation and verification tools"""
from pathlib import Path
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from ..utils.path_resolver import resolve_path
from ..utils.context import get_target_root_dir


@tool
def verify_code_snippet(
    file_content: str,
    original_snippet: str,
    line_number: Optional[int] = None,
    context_lines: int = 5
) -> Dict[str, Any]:
    """
    Verifies that the original code snippet exists in the file content.
    
    Args:
        file_content: The full content of the file
        original_snippet: The code snippet to search for
        line_number: Optional line number hint
        context_lines: Number of context lines to return
        
    Returns:
        Dictionary with verification results and context
    """
    lines = file_content.split('\n')
    snippet_stripped = original_snippet.strip()

    # Strategy 1: Exact match search
    for idx, line in enumerate(lines):
        if snippet_stripped in line or line.strip() == snippet_stripped:
            start = max(0, idx - context_lines)
            end = min(len(lines), idx + context_lines + 1)

            return {
                "found": True,
                "exact_match": True,
                "line_number": idx + 1,
                "matched_content": line,
                "context_before": '\n'.join(lines[start:idx]),
                "context_after": '\n'.join(lines[idx+1:end]),
                "full_context": '\n'.join(lines[start:end])
            }

    # Strategy 2: Multi-line snippet matching
    snippet_lines = snippet_stripped.split('\n')
    if len(snippet_lines) > 1:
        snippet_stripped_lines = [l.strip() for l in snippet_lines]

        for idx in range(len(lines) - len(snippet_lines) + 1):
            window = lines[idx:idx + len(snippet_lines)]
            window_stripped = [l.strip() for l in window]

            if window_stripped == snippet_stripped_lines:
                start = max(0, idx - context_lines)
                end = min(len(lines), idx + len(snippet_lines) + context_lines)

                return {
                    "found": True,
                    "exact_match": True,
                    "line_number": idx + 1,
                    "matched_content": '\n'.join(window),
                    "context_before": '\n'.join(lines[start:idx]),
                    "context_after": '\n'.join(lines[idx + len(snippet_lines):end]),
                    "full_context": '\n'.join(lines[start:end])
                }

    # Strategy 3: Fuzzy match
    from difflib import get_close_matches
    suggestions = get_close_matches(
        snippet_stripped,
        [l.strip() for l in lines if l.strip()],
        n=3,
        cutoff=0.6
    )

    return {
        "found": False,
        "exact_match": False,
        "line_number": None,
        "matched_content": None,
        "suggestions": suggestions,
        "message": "Original snippet not found. Check suggestions for similar code."
    }


@tool
def validate_python_syntax(file_path: str) -> Dict[str, Any]:
    """
    Validates that a Python file has correct syntax.
    
    Args:
        file_path: Path to the Python file to validate (may be Linux-style like /usr/srv/app/...)
        
    Returns:
        Dictionary with validation results
    """
    import ast
    import traceback

    # Resolve path using target root directory if available
    target_root = get_target_root_dir()
    path = resolve_path(file_path, target_root)

    if not path.exists():
        return {
            "valid": False,
            "file_path": str(file_path),
            "error_message": "File does not exist",
            "error_type": "FileNotFoundError"
        }

    try:
        with open(path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        # Try to parse the Python code
        ast.parse(source_code, filename=str(path))

        return {
            "valid": True,
            "file_path": str(path.absolute()),
            "message": "Python syntax is valid"
        }

    except SyntaxError as e:
        return {
            "valid": False,
            "file_path": str(path.absolute()),
            "error_message": str(e.msg),
            "error_line": e.lineno,
            "error_offset": e.offset,
            "error_type": "SyntaxError",
            "error_text": e.text.strip() if e.text else None
        }

    except Exception as e:
        return {
            "valid": False,
            "file_path": str(path.absolute()),
            "error_message": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }

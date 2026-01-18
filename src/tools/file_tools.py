"""File operation tools"""
from pathlib import Path
from typing import Dict, Any, Union
from langchain_core.tools import tool
from ..utils.path_resolver import resolve_path
from ..utils.context import get_target_root_dir


@tool
def read_source_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Reads a source code file and returns its content with metadata.
    This prevents hallucinations by ensuring the agent sees the actual code.
    
    Args:
        file_path: Path to the file to read (may be Linux-style like /usr/srv/app/...)
        
    Returns:
        Dictionary with success status, file content, and metadata
    """
    # Resolve path using target root directory if available
    target_root = get_target_root_dir()
    path = resolve_path(file_path, target_root)
    
    if not path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "file_path": str(file_path)
        }

    if not path.is_file():
        return {
            "success": False,
            "error": f"Path is not a file: {file_path}",
            "file_path": str(file_path)
        }

    try:
        encodings = ['utf-8', 'latin-1', 'cp1252']
        content = None
        used_encoding = None

        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    content = f.read()
                used_encoding = encoding
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            return {
                "success": False,
                "error": "Could not decode file with supported encodings",
                "file_path": str(path.absolute())
            }

        lines = content.split('\n')

        return {
            "success": True,
            "file_path": str(path.absolute()),
            "content": content,
            "line_count": len(lines),
            "encoding": used_encoding,
            "size_bytes": path.stat().st_size
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading file: {str(e)}",
            "file_path": str(path.absolute())
        }


@tool
def apply_patch_and_write(
    original_file_path: str,
    changes: list[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Applies code changes and writes to a new file with 'fixed_' prefix.
    Includes validation to ensure changes were applied correctly.
    
    Args:
        original_file_path: Path to the original file (may be Linux-style like /usr/srv/app/...)
        changes: List of change dictionaries with 'original_snippet' and 'fixed_snippet'
        
    Returns:
        Dictionary with success status, output file path, and change summary
    """
    # Resolve path using target root directory if available
    target_root = get_target_root_dir()
    original_path = resolve_path(original_file_path, target_root)
    changes_applied = 0
    errors = []
    change_log = []

    # Read the original file content
    try:
        with open(original_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        modified_content = original_content
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read file: {str(e)}",
            "output_file": "",
            "changes_applied": 0,
            "errors": [f"Failed to read file: {str(e)}"]
        }

    # Apply changes in order
    for idx, change in enumerate(changes):
        original_snippet = change.get('original_snippet', '').strip()
        fixed_snippet = change.get('fixed_snippet', '').strip()

        if original_snippet in modified_content:
            occurrences = modified_content.count(original_snippet)
            
            if occurrences > 1:
                errors.append(
                    f"Warning: Change {idx+1} matches {occurrences} locations. "
                    f"Applied to first occurrence only."
                )

            modified_content = modified_content.replace(
                original_snippet,
                fixed_snippet,
                1
            )
            changes_applied += 1
            change_log.append(
                f"[OK] Change {idx+1}: Replaced at line ~{change.get('line_number', 'unknown')}"
            )
        else:
            errors.append(
                f"[FAIL] Change {idx+1}: Original snippet not found in content. Skipped."
            )

    # Generate output file path
    output_path = original_path.parent / f"fixed_{original_path.name}"

    # Write the modified content
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        # Generate diff summary
        original_lines = original_content.split('\n')
        modified_lines = modified_content.split('\n')

        diff_lines = []
        for i, (orig, mod) in enumerate(zip(original_lines, modified_lines)):
            if orig != mod:
                diff_lines.append(f"Line {i+1}:\n  - {orig}\n  + {mod}")

        if len(original_lines) != len(modified_lines):
            diff_lines.append(
                f"Note: Line count changed from {len(original_lines)} to {len(modified_lines)}"
            )

        return {
            "success": True,
            "output_file": str(output_path.absolute()),
            "original_file": str(original_path.absolute()),
            "changes_applied": changes_applied,
            "total_changes_requested": len(changes),
            "diff_summary": '\n'.join(diff_lines) if diff_lines else "No differences",
            "change_log": change_log,
            "errors": errors,
            "file_size_bytes": len(modified_content.encode('utf-8'))
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to write file: {str(e)}",
            "output_file": str(output_path),
            "changes_applied": changes_applied,
            "errors": errors
        }

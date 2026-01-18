"""Path resolution utility for handling Linux paths on Windows"""
from pathlib import Path
from typing import Optional, Union
import os


def resolve_path(
    file_path: Union[str, Path],
    target_root_dir: Optional[Union[str, Path]] = None
) -> Path:
    """
    Resolves a file path, handling Linux-style paths on Windows.
    
    This function:
    1. If the path is absolute and starts with '/' (Linux-style), it replaces
       the root with the target_root_dir
    2. If the path is relative, it resolves it relative to target_root_dir
    3. If target_root_dir is not provided, it uses the path as-is
    
    Args:
        file_path: The file path from trace.json (may be Linux-style like /usr/srv/app/...)
        target_root_dir: The root directory of the target codebase on the local system
        
    Returns:
        Resolved Path object pointing to the actual file location
        
    Examples:
        >>> resolve_path("/usr/srv/app/models.py", "D:/MyProjects/target-app")
        Path("D:/MyProjects/target-app/models.py")
        
        >>> resolve_path("src/models.py", "D:/MyProjects/target-app")
        Path("D:/MyProjects/target-app/src/models.py")
        
        >>> resolve_path("D:/MyProjects/target-app/models.py", None)
        Path("D:/MyProjects/target-app/models.py")
    """
    path_str = str(file_path)
    path = Path(path_str)
    
    # If no target root directory is provided, return path as-is
    if target_root_dir is None:
        return path.resolve() if path.is_absolute() else path
    
    target_root = Path(target_root_dir).resolve()
    
    # Check if this is a Linux-style absolute path (starts with /)
    if path_str.startswith('/') and not path_str.startswith('//'):
        # Remove leading slash and split into parts
        path_parts = path_str.lstrip('/').split('/')
        
        if not path_parts:
            return target_root
        
        filename = path_parts[-1]
        
        # Strategy 1: Try direct mapping (full path relative to target root)
        # e.g., /usr/srv/app/src/models.py -> target_root/usr/srv/app/src/models.py
        resolved = target_root / '/'.join(path_parts)
        if resolved.exists():
            return resolved
        
        # Strategy 2: Try removing common Linux deployment prefixes
        # Common patterns: /usr/srv/app, /app, /home/user/app, /var/www/app
        # Try to find where the actual project code starts
        common_prefixes = [
            ['usr', 'srv', 'app'],
            ['usr', 'srv'],
            ['app'],
            ['home'],
            ['var', 'www'],
            ['srv'],
        ]
        
        for prefix_parts in common_prefixes:
            # Check if path starts with this prefix
            if len(path_parts) > len(prefix_parts) and path_parts[:len(prefix_parts)] == prefix_parts:
                # Remove prefix and try
                remaining_parts = path_parts[len(prefix_parts):]
                if remaining_parts:
                    alt_resolved = target_root / '/'.join(remaining_parts)
                    if alt_resolved.exists():
                        return alt_resolved
        
        # Strategy 3: Try matching by filename and path structure
        # Search for files with the same name and similar path structure
        for found_file in target_root.rglob(filename):
            if found_file.is_file():
                rel_found = found_file.relative_to(target_root)
                found_parts = list(rel_found.parts)
                
                # Check if the last N parts match (where N is the depth we care about)
                # Match at least the last 2-3 parts if possible
                match_depth = min(len(path_parts), len(found_parts), 3)
                if match_depth > 0:
                    path_tail = path_parts[-match_depth:]
                    found_tail = found_parts[-match_depth:]
                    if path_tail == found_tail:
                        return found_file
        
        # Strategy 4: If still not found, return the best guess (direct mapping)
        # This allows the error to be reported clearly
        return resolved
    
    # If it's a Windows absolute path, return as-is
    if path.is_absolute():
        return path
    
    # If it's a relative path, resolve relative to target_root
    return (target_root / path).resolve()


def normalize_path_for_display(path: Union[str, Path]) -> str:
    """
    Normalizes a path for display purposes, converting Windows paths to a standard format.
    
    Args:
        path: The path to normalize
        
    Returns:
        Normalized path string
    """
    return str(Path(path).as_posix())


def find_file_in_root(
    filename: str,
    target_root_dir: Union[str, Path],
    max_depth: int = 5
) -> Optional[Path]:
    """
    Searches for a file in the target root directory.
    
    Args:
        filename: The filename to search for
        target_root_dir: The root directory to search in
        max_depth: Maximum depth to search (default: 5)
        
    Returns:
        Path to the file if found, None otherwise
    """
    target_root = Path(target_root_dir).resolve()
    
    if not target_root.exists():
        return None
    
    # Search recursively but limit depth
    for depth in range(max_depth + 1):
        for path in target_root.rglob(filename):
            if path.relative_to(target_root).parts.count(path.name) <= depth:
                return path
    
    return None

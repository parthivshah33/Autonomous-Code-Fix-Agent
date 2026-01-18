"""Context storage for runtime configuration accessible by tools"""
from typing import Optional
from pathlib import Path

# Global context storage
_target_root_dir: Optional[Path] = None


def set_target_root_dir(target_root_dir: Optional[str]) -> None:
    """
    Sets the target root directory for path resolution.
    
    Args:
        target_root_dir: Root directory of the target codebase, or None
    """
    global _target_root_dir
    if target_root_dir:
        _target_root_dir = Path(target_root_dir).resolve()
    else:
        _target_root_dir = None


def get_target_root_dir() -> Optional[Path]:
    """
    Gets the current target root directory.
    
    Returns:
        Path to target root directory, or None if not set
    """
    return _target_root_dir

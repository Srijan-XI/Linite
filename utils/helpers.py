"""
Linite - Helper Utilities
Misc utility functions shared across the project.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional


# ── Logging ────────────────────────────────────────────────────────────────

def setup_logging(verbose: bool = False):
    """Configure root logger for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "[%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, stream=sys.stderr)


# ── Privilege check ────────────────────────────────────────────────────────

def is_root() -> bool:
    """Return True if running as root / Administrator."""
    try:
        return os.geteuid() == 0
    except AttributeError:
        # Windows – no concept of root the same way
        import ctypes
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore
        except Exception:
            return False


def warn_if_not_root() -> bool:
    """
    Warn the user if not running with elevated privileges.
    Returns True if root, False otherwise.
    """
    if not is_root():
        print(
            "[WARNING] Linite is not running as root. "
            "Package installation commands will use 'sudo' and may prompt for a password.",
            file=sys.stderr,
        )
        return False
    return True


# ── Platform guard ─────────────────────────────────────────────────────────

def warn_if_not_linux():
    """Print an info message if not running on Linux (does not exit)."""
    if sys.platform != "linux":
        print(
            f"[INFO] Linite is designed for Linux. "
            f"You are running on '{sys.platform}'.\n"
            "The GUI will open in preview mode (installation commands won't run).",
            file=sys.stderr,
        )


# ── Path helpers ───────────────────────────────────────────────────────────

def project_root() -> Path:
    """Return the directory containing this file (project root)."""
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    return project_root() / "data"


# ── Formatting ─────────────────────────────────────────────────────────────

def human_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes //= 1024
    return f"{num_bytes:.1f} TB"


def catalog_lint(
    current_pm: Optional[str] = None,
    include_compatibility: bool = True,
) -> list[str]:
    """Backward-compatible catalog lint wrapper around core.catalog.validation."""
    from core.catalog.validation import catalog_lint as _catalog_lint

    return _catalog_lint(
        current_pm=current_pm,
        include_compatibility=include_compatibility,
    )

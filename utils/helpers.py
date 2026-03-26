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


def catalog_lint(current_pm: Optional[str] = None) -> list[str]:
    """
    Validate loaded catalog entries and return human-readable warnings.

    Checks:
    - required metadata fields are present
    - install spec keys are known
    - non-script specs have at least one package
    - each app has a compatible install path for the current package manager
    """
    from data.software_catalog import CATALOG

    warnings: list[str] = []
    known_pm_keys = {
        "apt", "dnf", "yum", "pacman", "zypper", "snap", "flatpak",
        "appimage", "script", "universal", "nix", "aur",
    }

    for app in CATALOG:
        if not app.id.strip() or not app.name.strip() or not app.category.strip():
            warnings.append(
                f"[{app.id or '<missing-id>'}] Missing required metadata (id/name/category)."
            )

        if not app.install_specs:
            warnings.append(f"[{app.id}] No install_specs defined.")
            continue

        spec_keys = set(app.install_specs.keys())
        unknown_keys = sorted(k for k in spec_keys if k not in known_pm_keys)
        if unknown_keys:
            warnings.append(f"[{app.id}] Unknown install_specs key(s): {', '.join(unknown_keys)}")

        for pm_key, spec in app.install_specs.items():
            if pm_key in {"script"}:
                if not spec.script_url:
                    warnings.append(f"[{app.id}] script spec is missing script_url.")
                continue

            if pm_key in {"appimage"}:
                if not spec.packages and not spec.script_url:
                    warnings.append(f"[{app.id}] appimage spec has no URL/package hint.")
                continue

            if not spec.packages:
                warnings.append(f"[{app.id}] {pm_key} spec has no packages.")

        # Compatibility check for the host package manager.
        if current_pm and current_pm != "unknown":
            compatible_keys = {current_pm, "universal", "flatpak", "snap", "appimage", "script"}
            # Treat yum and dnf as equivalent compatibility for linting.
            if current_pm == "yum":
                compatible_keys.add("dnf")
            if current_pm == "dnf":
                compatible_keys.add("yum")

            if spec_keys.isdisjoint(compatible_keys):
                warnings.append(
                    f"[{app.id}] No install path for host pm '{current_pm}' (or flatpak/snap/appimage/script fallback)."
                )

    return warnings

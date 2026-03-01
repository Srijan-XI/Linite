"""
Linite - Uninstaller
Removes previously installed packages using the appropriate package manager.
"""

import logging
from typing import Callable, List, Optional

from core.distro import DistroInfo
from core.installer import _pick_pm
from data.software_catalog import SoftwareEntry

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, str], None]


# ── Per-PM uninstall commands ─────────────────────────────────────────────────

def _uninstall_cmd(pm_name: str, packages: List[str]) -> List[str]:
    cmds = {
        "apt":     ["apt-get", "remove", "-y"] + packages,
        "dnf":     ["dnf",     "remove", "-y"] + packages,
        "yum":     ["yum",     "remove", "-y"] + packages,
        "pacman":  ["pacman",  "-R", "--noconfirm"] + packages,
        "zypper":  ["zypper",  "--non-interactive", "remove"] + packages,
        "snap":    ["snap",    "remove"] + packages,
        "flatpak": ["flatpak", "uninstall", "-y", "--noninteractive"] + packages,
    }
    return cmds.get(pm_name, [])


def uninstall_app(
    entry: SoftwareEntry,
    distro: DistroInfo,
    progress_cb: Optional[ProgressCallback] = None,
) -> tuple[int, str]:
    """
    Uninstall a single app. Returns (returncode, output).
    """
    from core.package_manager import get_package_manager

    pm_name = _pick_pm(entry, distro)
    if pm_name is None:
        return 1, "No package manager found for this app."

    spec = entry.get_spec(pm_name)
    if spec is None or not spec.packages:
        return 1, f"No uninstall spec for PM '{pm_name}'."

    if progress_cb:
        progress_cb(entry.id, f"Removing {entry.name} via {pm_name} …")

    cmd = _uninstall_cmd(pm_name, spec.packages)
    if not cmd:
        return 1, f"Uninstall not supported for PM '{pm_name}'."

    sudo = pm_name not in ("flatpak",)
    try:
        pm = get_package_manager(pm_name)
        line_cb = (lambda line: progress_cb(entry.id, line)) if progress_cb else None
        rc, out = pm.run(cmd, sudo=sudo, progress_cb=line_cb)
        return rc, out
    except Exception as exc:
        return 1, str(exc)


def uninstall_apps(
    entries: List[SoftwareEntry],
    distro: DistroInfo,
    progress_cb: Optional[ProgressCallback] = None,
) -> dict:
    """Uninstall multiple apps. Returns { app_id: (returncode, output) }."""
    import core.history as history

    results = {}
    for entry in entries:
        rc, out = uninstall_app(entry, distro, progress_cb)
        results[entry.id] = (rc, out)
        success = rc == 0
        pm_name = _pick_pm(entry, distro) or "unknown"
        history.record(entry.id, entry.name, pm_name, success, action="uninstall")
        if progress_cb:
            icon = "✓" if success else "✗"
            progress_cb(entry.id, f"{icon} {entry.name}: {'removed' if success else 'failed'}")
    return results

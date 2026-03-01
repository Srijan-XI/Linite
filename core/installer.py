"""
Linite - Installer
Orchestrates installation of selected software using the appropriate package manager.
"""

import logging
import subprocess
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional

from core.distro import DistroInfo, check_flatpak_available, check_snap_available
from core.package_manager import get_package_manager
from data.software_catalog import SoftwareEntry

logger = logging.getLogger(__name__)


class Status(Enum):
    PENDING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class InstallResult:
    app_id: str
    app_name: str
    status: Status
    pm_used: str = ""
    output: str = ""
    error: str = ""


# Callback type:  (app_id, line_of_output) -> None
ProgressCallback = Callable[[str, str], None]


def _pick_pm(entry: SoftwareEntry, distro: DistroInfo) -> Optional[str]:
    """
    Choose the best package manager to install *entry* given the current distro.
    Priority:
      1. entry.preferred_pm  (if available on the system)
      2. distro native pm   (if a spec exists)
      3. flatpak            (if available and spec exists)
      4. snap               (if available and spec exists)
    """
    native_pm = distro.package_manager
    flatpak_ok = check_flatpak_available()
    snap_ok = check_snap_available()

    candidates: List[str] = []

    if entry.preferred_pm:
        candidates.append(entry.preferred_pm)

    candidates.append(native_pm)

    if flatpak_ok:
        candidates.append("flatpak")
    if snap_ok:
        candidates.append("snap")

    for pm in candidates:
        if entry.get_spec(pm) is not None:
            return pm

    return None


def _run_pre_post(commands: List[str], progress_cb: Optional[ProgressCallback], app_id: str):
    for cmd in commands:
        if progress_cb:
            progress_cb(app_id, f"[pre/post] $ {cmd}")
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True
        )
        if progress_cb:
            for line in (proc.stdout + proc.stderr).splitlines():
                progress_cb(app_id, line)


def install_app(
    entry: SoftwareEntry,
    distro: DistroInfo,
    progress_cb: Optional[ProgressCallback] = None,
) -> InstallResult:
    """Install a single application; returns an InstallResult."""

    pm_name = _pick_pm(entry, distro)

    if pm_name is None:
        return InstallResult(
            app_id=entry.id,
            app_name=entry.name,
            status=Status.FAILED,
            error="No suitable package manager or spec found.",
        )

    spec = entry.get_spec(pm_name)
    if spec is None:
        return InstallResult(
            app_id=entry.id,
            app_name=entry.name,
            status=Status.FAILED,
            pm_used=pm_name,
            error=f"No install spec for PM '{pm_name}'.",
        )

    if progress_cb:
        progress_cb(entry.id, f"Installing {entry.name} via {pm_name} …")

    # Pre-install commands
    if spec.pre_commands:
        _run_pre_post(spec.pre_commands, progress_cb, entry.id)

    # Main installation
    try:
        pm = get_package_manager(pm_name)
    except ValueError as exc:
        return InstallResult(
            app_id=entry.id,
            app_name=entry.name,
            status=Status.FAILED,
            pm_used=pm_name,
            error=str(exc),
        )

    line_cb = (lambda line: progress_cb(entry.id, line)) if progress_cb else None

    if pm_name == "snap" and spec.snap_classic:
        pm_snap = get_package_manager("snap")
        rc, out = pm_snap.install_classic(spec.packages, progress_cb=line_cb)  # type: ignore[attr-defined]
    else:
        rc, out = pm.install(spec.packages, progress_cb=line_cb)

    # Post-install commands
    if rc == 0 and spec.post_commands:
        _run_pre_post(spec.post_commands, progress_cb, entry.id)

    result_status = Status.SUCCESS if rc == 0 else Status.FAILED
    return InstallResult(
        app_id=entry.id,
        app_name=entry.name,
        status=result_status,
        pm_used=pm_name,
        output=out,
        error="" if rc == 0 else f"Exit code {rc}",
    )


def install_apps(
    entries: List[SoftwareEntry],
    distro: DistroInfo,
    progress_cb: Optional[ProgressCallback] = None,
) -> List[InstallResult]:
    """Install multiple apps sequentially."""
    results = []
    for entry in entries:
        result = install_app(entry, distro, progress_cb)
        results.append(result)
        if progress_cb:
            icon = "✓" if result.status == Status.SUCCESS else "✗"
            progress_cb(
                entry.id,
                f"{icon} {entry.name}: {result.status.name}"
            )
    return results

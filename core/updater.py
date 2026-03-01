"""
Linite - Updater
Updates installed packages / the whole system via the native package manager.
"""

import logging
from typing import Callable, List, Optional

from core.distro import DistroInfo, check_flatpak_available, check_snap_available
from core.package_manager import get_package_manager
from data.software_catalog import SoftwareEntry

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, str], None]


def update_system(
    distro: DistroInfo,
    include_flatpak: bool = True,
    include_snap: bool = True,
    progress_cb: Optional[ProgressCallback] = None,
) -> dict:
    """
    Perform a full system update using all available package managers.
    Returns a dict { pm_name: (returncode, output) }.
    """
    results = {}
    native_pm = distro.package_manager

    def _cb(line: str):
        if progress_cb:
            progress_cb("system", line)

    # Native package manager
    if native_pm != "unknown":
        if progress_cb:
            progress_cb("system", f"Updating via {native_pm} …")
        try:
            pm = get_package_manager(native_pm)
            rc, out = pm.update_all(progress_cb=_cb)
            results[native_pm] = (rc, out)
        except Exception as exc:
            logger.exception("Update via %s failed", native_pm)
            results[native_pm] = (1, str(exc))

    # Flatpak
    if include_flatpak and check_flatpak_available():
        if progress_cb:
            progress_cb("system", "Updating Flatpak apps …")
        try:
            pm = get_package_manager("flatpak")
            rc, out = pm.update_all(progress_cb=_cb)
            results["flatpak"] = (rc, out)
        except Exception as exc:
            results["flatpak"] = (1, str(exc))

    # Snap
    if include_snap and check_snap_available():
        if progress_cb:
            progress_cb("system", "Updating Snap packages …")
        try:
            pm = get_package_manager("snap")
            rc, out = pm.update_all(progress_cb=_cb)
            results["snap"] = (rc, out)
        except Exception as exc:
            results["snap"] = (1, str(exc))

    return results


def update_selected(
    entries: List[SoftwareEntry],
    distro: DistroInfo,
    progress_cb: Optional[ProgressCallback] = None,
) -> dict:
    """
    Update a specific list of apps (best-effort; uses the native PM).
    Returns { app_id: (returncode, output) }.
    """
    from core.installer import _pick_pm

    results = {}
    native_pm = distro.package_manager

    for entry in entries:
        pm_name = _pick_pm(entry, distro) or native_pm
        spec = entry.get_spec(pm_name)
        if spec is None:
            results[entry.id] = (1, "No spec found")
            continue

        def _cb(line: str):
            if progress_cb:
                progress_cb(entry.id, line)

        try:
            pm = get_package_manager(pm_name)
            rc, out = pm.update_package(spec.packages, progress_cb=_cb)
            results[entry.id] = (rc, out)
        except Exception as exc:
            results[entry.id] = (1, str(exc))

    return results

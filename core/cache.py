"""
Linite - Offline / Cached Package Pre-downloader
=================================================
Provides a best-effort pre-download of packages before presenting the GUI,
useful for air-gapped servers or slow/metered connections.

Usage (CLI):
  linite --cache                     # pre-download all catalog packages
  linite --cache --pm apt            # only pre-download apt packages
  linite --cache --cli install vlc   # pre-download specific apps

Only apt/dnf/pacman/zypper support offline caching natively.
Flatpak/snap/script installs are skipped with a warning.

Cached files are stored under ~/.cache/linite/<pm>/.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

from data.software_catalog import SoftwareEntry

logger = logging.getLogger(__name__)

CACHE_DIR = Path.home() / ".cache" / "linite"


def _pm_cache_dir(pm: str) -> Path:
    d = CACHE_DIR / pm
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Per-PM download helpers
# ---------------------------------------------------------------------------

def _apt_download(packages: list[str], progress_cb: Optional[Callable[[str], None]] = None) -> bool:
    """
    Use ``apt-get download`` to fetch .deb files to the cache directory.
    Returns True on full success.
    """
    cache = _pm_cache_dir("apt")
    args = ["apt-get", "download", "-o", f"Dir::Cache={cache}"] + packages
    # apt-get download must run in the target directory
    try:
        proc = subprocess.Popen(
            args,
            cwd=str(cache),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        lines = []
        for line in iter(proc.stdout.readline, ""):  # type: ignore[union-attr]
            line = line.rstrip()
            lines.append(line)
            if progress_cb:
                progress_cb(line)
        proc.wait()
        return proc.returncode == 0
    except FileNotFoundError:
        if progress_cb:
            progress_cb("[cache] apt-get not found — skipping apt downloads.")
        return False


def _dnf_download(packages: list[str], progress_cb: Optional[Callable[[str], None]] = None) -> bool:
    """Use ``dnf download --downloaddir`` to fetch .rpm files."""
    cache = _pm_cache_dir("dnf")
    args = ["dnf", "download", f"--downloaddir={cache}"] + packages
    try:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in iter(proc.stdout.readline, ""):  # type: ignore[union-attr]
            line = line.rstrip()
            if progress_cb:
                progress_cb(line)
        proc.wait()
        return proc.returncode == 0
    except FileNotFoundError:
        if progress_cb:
            progress_cb("[cache] dnf not found — skipping dnf downloads.")
        return False


def _pacman_download(packages: list[str], progress_cb: Optional[Callable[[str], None]] = None) -> bool:
    """Use ``pacman -Sw`` (download without install) to populate the pacman cache."""
    args = ["pacman", "-Sw", "--noconfirm"] + packages
    # pacman stores packages in /var/cache/pacman/pkg/ by default — no override needed.
    try:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in iter(proc.stdout.readline, ""):  # type: ignore[union-attr]
            line = line.rstrip()
            if progress_cb:
                progress_cb(line)
        proc.wait()
        return proc.returncode == 0
    except FileNotFoundError:
        if progress_cb:
            progress_cb("[cache] pacman not found — skipping pacman downloads.")
        return False


def _zypper_download(packages: list[str], progress_cb: Optional[Callable[[str], None]] = None) -> bool:
    """Use ``zypper --download-only install`` to fetch RPMs without installing."""
    args = ["zypper", "--non-interactive", "install", "--download-only"] + packages
    try:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in iter(proc.stdout.readline, ""):  # type: ignore[union-attr]
            line = line.rstrip()
            if progress_cb:
                progress_cb(line)
        proc.wait()
        return proc.returncode == 0
    except FileNotFoundError:
        if progress_cb:
            progress_cb("[cache] zypper not found — skipping zypper downloads.")
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_DOWNLOAD_FNS: dict[str, Callable] = {
    "apt": _apt_download,
    "dnf": _dnf_download,
    "pacman": _pacman_download,
    "zypper": _zypper_download,
}

_UNSUPPORTED_PMS = {"snap", "flatpak", "appimage", "script", "nix"}


def cache_packages(
    entries: list[SoftwareEntry],
    pm_filter: Optional[str] = None,
    progress_cb: Optional[Callable[[str], None]] = None,
) -> dict[str, bool]:
    """
    Pre-download packages for the given catalog entries.

    Parameters
    ----------
    entries:
        Software entries to cache.
    pm_filter:
        If provided, only cache packages for this package manager.
    progress_cb:
        Called with each output line for live feedback.

    Returns
    -------
    dict mapping pm_name → success (True/False)
    """

    def _log(msg: str) -> None:
        logger.info(msg)
        if progress_cb:
            progress_cb(msg)

    # Group packages by pm
    pm_packages: dict[str, list[str]] = {}
    for entry in entries:
        for spec in entry.install_specs:
            pm = spec.get("pm", "")
            if pm_filter and pm != pm_filter:
                continue
            if pm in _UNSUPPORTED_PMS:
                continue
            pkg = spec.get("package", "")
            if pkg:
                pm_packages.setdefault(pm, []).append(pkg)

    if not pm_packages:
        _log("[cache] No cacheable packages found for the given selection.")
        return {}

    results: dict[str, bool] = {}
    for pm, packages in pm_packages.items():
        fn = _DOWNLOAD_FNS.get(pm)
        if fn is None:
            _log(f"[cache] {pm}: no download helper — skipped.")
            results[pm] = False
            continue

        _log(f"[cache] {pm}: pre-downloading {len(packages)} package(s) …")
        ok = fn(packages, progress_cb=progress_cb)
        results[pm] = ok
        icon = "✓" if ok else "✗"
        _log(f"[cache] {pm}: {icon} done")

    return results


def cache_info() -> dict[str, dict]:
    """Return info about what is currently cached per PM."""
    info: dict[str, dict] = {}
    if not CACHE_DIR.exists():
        return info
    for pm_dir in CACHE_DIR.iterdir():
        if pm_dir.is_dir():
            files = list(pm_dir.glob("*"))
            total_bytes = sum(f.stat().st_size for f in files if f.is_file())
            info[pm_dir.name] = {
                "file_count": len(files),
                "total_mb": round(total_bytes / (1024 * 1024), 2),
                "path": str(pm_dir),
            }
    return info


def clear_cache(pm: Optional[str] = None) -> None:
    """Remove all cached files (or just for a specific PM)."""
    if pm:
        target = CACHE_DIR / pm
        if target.exists():
            shutil.rmtree(target)
            logger.info("Cleared cache for %s", pm)
    else:
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
            logger.info("Cleared all Linite caches")

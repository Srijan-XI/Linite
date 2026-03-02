"""
Linite - Installer
Orchestrates installation of selected software using the appropriate package manager.
Supports parallel installation, SHA-256 checksum verification, and history recording.
"""

import hashlib
import tempfile as _tempfile
import logging
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    app_id:   str
    app_name: str
    status:   Status
    pm_used:  str = ""
    output:   str = ""
    error:    str = ""


# Callback type:  (app_id, line_of_output) -> None
ProgressCallback = Callable[[str, str], None]


# Package managers that can be resolved via get_package_manager().
_SUPPORTED_PMS = frozenset({
    "apt", "dnf", "yum", "pacman", "zypper", "snap", "flatpak",
    # AUR helpers — yay / paru on Arch-based distros
    "aur", "yay", "paru",
})


def _pick_pm(entry: SoftwareEntry, distro: DistroInfo) -> Optional[str]:
    """
    Choose the best package manager to install *entry* given the current distro.
    Priority:
      1. entry.preferred_pm  (if spec exists and is a real supported PM)
      2. distro native pm    (if spec exists)
      3. flatpak             (if available and spec exists)
      4. snap                (if available and spec exists)

    NOTE: 'script' is intentionally excluded; it is not a real package manager
    and get_package_manager('script') would raise ValueError.
    """
    native_pm  = distro.package_manager
    flatpak_ok = check_flatpak_available()
    snap_ok    = check_snap_available()

    candidates: List[str] = []
    # Only add preferred_pm if it's a real, supported package manager
    if entry.preferred_pm and entry.preferred_pm in _SUPPORTED_PMS:
        candidates.append(entry.preferred_pm)
    if native_pm in _SUPPORTED_PMS:
        candidates.append(native_pm)
    if flatpak_ok:
        candidates.append("flatpak")
    if snap_ok:
        candidates.append("snap")

    for pm in candidates:
        if entry.get_spec(pm) is not None:
            return pm
    return None


# ── Checksum verification ─────────────────────────────────────────────────────

def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_checksum(file_path: str, expected: str,
                     progress_cb=None, app_id: str = "") -> bool:
    """Return True if SHA-256 of file_path matches expected (case-insensitive)."""
    if not expected:
        return True
    actual = _sha256_file(file_path)
    ok = actual.lower() == expected.lower()
    if progress_cb:
        tag = "✓" if ok else "✗ MISMATCH!"
        progress_cb(app_id, f"[checksum] {tag}  expected={expected[:16]}…  got={actual[:16]}…")
    return ok


# ── Pre / post commands ───────────────────────────────────────────────────────

def _run_pre_post(commands: List[str], progress_cb: Optional[ProgressCallback], app_id: str):
    for cmd in commands:
        if progress_cb:
            progress_cb(app_id, f"[pre/post] $ {cmd}")
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        for line in (proc.stdout + proc.stderr).splitlines():
            if progress_cb:
                progress_cb(app_id, line)


# ── Single-app install ────────────────────────────────────────────────────────

def install_app(
    entry:       SoftwareEntry,
    distro:      DistroInfo,
    progress_cb: Optional[ProgressCallback] = None,
) -> InstallResult:
    """Install a single application; returns an InstallResult."""
    import core.history as history

    pm_name = _pick_pm(entry, distro)
    if pm_name is None:
        return InstallResult(app_id=entry.id, app_name=entry.name,
                             status=Status.FAILED,
                             error="No suitable package manager or spec found.")

    spec = entry.get_spec(pm_name)
    if spec is None:
        return InstallResult(app_id=entry.id, app_name=entry.name,
                             status=Status.FAILED, pm_used=pm_name,
                             error=f"No install spec for PM '{pm_name}'.")

    if progress_cb:
        progress_cb(entry.id, f"Installing {entry.name} via {pm_name} …")

    # Pre-install commands (repo keys etc.)
    if spec.pre_commands:
        _run_pre_post(spec.pre_commands, progress_cb, entry.id)

    # Checksum verification for direct-download files
    if spec.script_url and spec.sha256:
        if progress_cb:
            progress_cb(entry.id, f"[download] {spec.script_url}")
        try:
            # Use NamedTemporaryFile instead of the deprecated+insecure mktemp()
            with _tempfile.NamedTemporaryFile(
                suffix="_linite_dl", delete=False
            ) as _tf:
                tmp = _tf.name
            urllib.request.urlretrieve(spec.script_url, tmp)
        except Exception as exc:
            return InstallResult(app_id=entry.id, app_name=entry.name,
                                 status=Status.FAILED, pm_used=pm_name,
                                 error=f"Download failed: {exc}")
        if not _verify_checksum(tmp, spec.sha256, progress_cb, entry.id):
            return InstallResult(app_id=entry.id, app_name=entry.name,
                                 status=Status.FAILED, pm_used=pm_name,
                                 error="SHA-256 checksum mismatch — install aborted for safety.")

    # Main installation
    try:
        pm = get_package_manager(pm_name)
    except ValueError as exc:
        return InstallResult(app_id=entry.id, app_name=entry.name,
                             status=Status.FAILED, pm_used=pm_name, error=str(exc))

    line_cb = (lambda line: progress_cb(entry.id, line)) if progress_cb else None

    if pm_name == "snap" and spec.snap_classic:
        rc, out = pm.install_classic(spec.packages, progress_cb=line_cb)  # type: ignore[attr-defined]
    else:
        rc, out = pm.install(spec.packages, progress_cb=line_cb)

    # Post-install commands
    if rc == 0 and spec.post_commands:
        _run_pre_post(spec.post_commands, progress_cb, entry.id)

    result_status = Status.SUCCESS if rc == 0 else Status.FAILED
    result = InstallResult(app_id=entry.id, app_name=entry.name,
                           status=result_status, pm_used=pm_name, output=out,
                           error="" if rc == 0 else f"Exit code {rc}")

    # Record to history
    history.record(entry.id, entry.name, pm_name, rc == 0, action="install")
    return result


# ── Batch install (parallel) ──────────────────────────────────────────────────

def install_apps(
    entries:     List[SoftwareEntry],
    distro:      DistroInfo,
    progress_cb: Optional[ProgressCallback] = None,
    max_workers: int = 4,
) -> List[InstallResult]:
    """
    Install multiple apps in parallel (up to max_workers at a time).
    Results are returned in the original *entries* order.
    """
    if not entries:
        return []

    results_map: Dict[str, InstallResult] = {}

    with ThreadPoolExecutor(max_workers=max_workers,
                            thread_name_prefix="linite-install") as pool:
        future_to_entry = {
            pool.submit(install_app, entry, distro, progress_cb): entry
            for entry in entries
        }
        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            try:
                result = future.result()
            except Exception as exc:
                result = InstallResult(app_id=entry.id, app_name=entry.name,
                                       status=Status.FAILED, error=str(exc))
            results_map[entry.id] = result

            if progress_cb:
                icon = "✓" if result.status == Status.SUCCESS else "✗"
                progress_cb(entry.id,
                            f"{icon} {entry.name}: {result.status.name}")

    # Return in original order
    return [results_map[e.id] for e in entries if e.id in results_map]


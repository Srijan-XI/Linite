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
    # AppImage — self-contained Linux binaries
    "appimage",
})


def _pick_pm(entry: SoftwareEntry, distro: DistroInfo) -> Optional[str]:
    """
    Choose the best package manager to install *entry* given the current distro.
    Priority:
      1. entry.preferred_pm  (if spec exists and is a real supported PM)
      2. distro native pm    (if spec exists)
      3. flatpak             (if available and spec exists)
      4. snap                (if available and spec exists)
@@      5. appimage            (if spec exists)

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
    candidates.append("appimage")

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


# ── AppImage helpers ──────────────────────────────────────────────────────────

def _ensure_bin_directory() -> str:
    """Ensure ~/.local/bin exists and return its path."""
    from pathlib import Path
    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    return str(bin_dir)


def _create_desktop_file(
    app_id: str,
    app_name: str,
    binary_name: str,
    icon: str = "",
    progress_cb: Optional[ProgressCallback] = None,
) -> None:
    """
    Create a .desktop file in ~/.local/share/applications/ for the AppImage.
    This enables the app to appear in application menus and launchers.
    """
    from pathlib import Path
    
    apps_dir = Path.home() / ".local" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)
    
    desktop_file = apps_dir / f"{app_id}.desktop"
    bin_path = Path.home() / ".local" / "bin" / binary_name
    export_path = bin_path.parent
    
    # Build .desktop file content
    desktop_content = (
        "[Desktop Entry]\n"
        f"Name={app_name}\n"
        f"Exec={bin_path}\n"
        f"Type=Application\n"
        "Categories=Utility;\n"
    )
    
    if icon:
        desktop_content += f"Icon={icon}\n"
    
    desktop_content += (
        "Terminal=false\n"
        f"Path={export_path}\n"
    )
    
    try:
        desktop_file.write_text(desktop_content)
        if progress_cb:
            progress_cb(app_id, f"[appimage] Desktop file created: {desktop_file}")
    except Exception as exc:
        if progress_cb:
            progress_cb(app_id, f"[appimage] Warning: Could not create desktop file: {exc}")


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
    forced_pm:   Optional[str] = None,
    forced_spec=None,
) -> InstallResult:
    """Install a single application; returns an InstallResult."""
    import core.history as history

    pm_name = forced_pm or _pick_pm(entry, distro)
    if pm_name is None:
        return InstallResult(app_id=entry.id, app_name=entry.name,
                             status=Status.FAILED,
                             error="No suitable package manager or spec found.")

    spec = forced_spec or entry.get_spec(pm_name)
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

    # AppImage-specific installation
    if pm_name == "appimage":
        if not spec.script_url:
            return InstallResult(app_id=entry.id, app_name=entry.name,
                                 status=Status.FAILED, pm_used=pm_name,
                                 error="No AppImage URL (script_url) provided.")
        
        binary_name = spec.packages[0] if spec.packages else entry.id
        
        try:
            import os
            from pathlib import Path
            
            bin_dir = _ensure_bin_directory()
            dest = Path(bin_dir) / binary_name
            
            if progress_cb:
                progress_cb(entry.id, f"[appimage] Moving to {dest}")
            os.rename(tmp, str(dest))
            
            if progress_cb:
                progress_cb(entry.id, "[appimage] Making executable")
            dest.chmod(0o755)
            
            _create_desktop_file(entry.id, entry.name, binary_name, 
                                entry.icon, progress_cb)
            
            if progress_cb:
                progress_cb(entry.id, 
                    f"✓ AppImage installed to {dest}")
            
            history.record(entry.id, entry.name, pm_name, True, action="install")
            return InstallResult(app_id=entry.id, app_name=entry.name,
                                status=Status.SUCCESS, pm_used=pm_name, 
                                output=f"AppImage installed to {dest}")
        
        except Exception as exc:
            return InstallResult(app_id=entry.id, app_name=entry.name,
                                status=Status.FAILED, pm_used=pm_name,
                                error=f"AppImage installation failed: {exc}")

    # Main installation
    try:
        pm = get_package_manager(pm_name)
    except ValueError as exc:
        return InstallResult(app_id=entry.id, app_name=entry.name,
                             status=Status.FAILED, pm_used=pm_name, error=str(exc))

    line_cb = (lambda line: progress_cb(entry.id, line)) if progress_cb else None

    if pm_name == "snap" and spec.snap_classic:
        rc, out = pm.install_classic(spec.packages, progress_cb=line_cb)  # type: ignore[attr-defined]
    elif pm_name == "flatpak" and spec.flatpak_remote:
        # Ensure the remote (e.g. 'flathub') is registered on the system,
        # then install. This prevents the "No remote refs found" error when
        # Flathub has never been added to the user's Flatpak configuration.
        rc, out = pm.install_from_remote(  # type: ignore[attr-defined]
            spec.flatpak_remote, spec.packages, progress_cb=line_cb
        )
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

    # Use the orchestration engine so dependency ordering, retry logic, and
    # fallback package managers are consistently applied in all install flows.
    from core.execution_engine import ExecutionEngine, ExecStatus

    app_ids = [entry.id for entry in entries]
    available_pms = [distro.package_manager]
    if check_flatpak_available():
        available_pms.append("flatpak")
    if check_snap_available():
        available_pms.append("snap")

    engine = ExecutionEngine(distro=distro, max_workers=max_workers)
    plan = engine.build_plan(app_ids, available_pms=available_pms)
    exec_results = engine.execute(plan, progress_cb=progress_cb)

    status_map = {
        ExecStatus.SUCCESS: Status.SUCCESS,
        ExecStatus.RETRIED: Status.SUCCESS,
        ExecStatus.FALLBACK: Status.SUCCESS,
        ExecStatus.SKIPPED: Status.SKIPPED,
        ExecStatus.FAILED: Status.FAILED,
    }

    results_map: Dict[str, InstallResult] = {}
    for result in exec_results:
        results_map[result.app_id] = InstallResult(
            app_id=result.app_id,
            app_name=result.app_name,
            status=status_map.get(result.status, Status.FAILED),
            pm_used=result.pm_used,
            output=result.output,
            error=result.error,
        )

    return [results_map[e.id] for e in entries if e.id in results_map]


"""
Linite - System Detection Engine
=================================
Full system profile: distro, package managers, desktop environment,
display server, CPU architecture, RAM, GPU (vendor + driver), VM / container
detection.

Backward-compatible with core.distro: DistroInfo is re-exported so any
existing import of `from core.distro import DistroInfo` still works.
The new entry-point is `detect_system() -> SystemInfo`.
"""

from __future__ import annotations

import logging
import os
import platform
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from shutil import which
from typing import Dict, List, Optional, Tuple

# Re-export DistroInfo so core.distro imports keep working
from core.distro import DistroInfo, detect as _detect_distro

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sub-dataclasses
# ---------------------------------------------------------------------------

@dataclass
class GPUInfo:
    """GPU vendor, model string and active driver."""
    vendor:         str = "unknown"   # "nvidia" | "amd" | "intel" | "unknown"
    model:          str = ""
    driver:         str = ""          # e.g. "nvidia", "nouveau", "amdgpu", "i915"
    driver_version: str = ""

    @property
    def display_name(self) -> str:
        if self.model:
            return f"{self.vendor.upper()}  {self.model}"
        return self.vendor.upper()


@dataclass
class SystemInfo:
    """
    Complete system profile consumed by PackageMap, ProfileEngine,
    ExecutionEngine and IntelligenceEngine.
    """

    # ── Distro (re-uses existing DistroInfo) ──────────────────────────────
    distro: DistroInfo = field(default_factory=DistroInfo)

    # ── Hardware ──────────────────────────────────────────────────────────
    cpu_arch:  str = "unknown"   # x86_64 | aarch64 | armv7l | i686
    cpu_cores: int = 1
    ram_mb:    int = 0           # total physical RAM in MB

    # ── GPU ───────────────────────────────────────────────────────────────
    gpu: GPUInfo = field(default_factory=GPUInfo)

    # ── Desktop ───────────────────────────────────────────────────────────
    desktop_env:    str = "unknown"  # gnome | kde | xfce | lxde | mate | cinnamon | i3 | sway | ...
    display_server: str = "unknown"  # x11 | wayland | mir

    # ── Available package managers (in detection-priority order) ──────────
    available_pms: List[str] = field(default_factory=list)

    # ── Environment flags ─────────────────────────────────────────────────
    is_linux:     bool = False
    is_server:    bool = False   # no DE detected
    is_vm:        bool = False   # running inside a hypervisor
    is_container: bool = False   # running inside Docker / LXC / etc.

    # ── Convenience properties ────────────────────────────────────────────
    @property
    def ram_gb(self) -> float:
        return round(self.ram_mb / 1024, 1)

    @property
    def is_low_ram(self) -> bool:
        """True when total RAM < 4 GB (suggest lightweight alternatives)."""
        return 0 < self.ram_mb < 4096

    @property
    def is_very_low_ram(self) -> bool:
        """True when total RAM < 2 GB."""
        return 0 < self.ram_mb < 2048

    @property
    def has_nvidia_gpu(self) -> bool:
        return self.gpu.vendor == "nvidia"

    @property
    def has_amd_gpu(self) -> bool:
        return self.gpu.vendor == "amd"

    @property
    def display_summary(self) -> str:
        parts = [self.distro.display_name]
        if self.ram_mb:
            parts.append(f"{self.ram_gb} GB RAM")
        if self.gpu.vendor not in ("unknown", ""):
            parts.append(self.gpu.display_name)
        if self.desktop_env not in ("unknown", ""):
            parts.append(self.desktop_env.upper())
        return "  ·  ".join(parts)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cmd(cmd: str) -> bool:
    """Return True if *cmd* exists on PATH."""
    return which(cmd) is not None


def _run(args: List[str], timeout: int = 3) -> Tuple[int, str]:
    """Run a command silently, return (returncode, stdout+stderr)."""
    try:
        r = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception:
        return 1, ""


def _env(key: str) -> str:
    return os.environ.get(key, "").strip().lower()


# ---------------------------------------------------------------------------
# Detection sub-routines
# ---------------------------------------------------------------------------

def _detect_ram_mb() -> int:
    """Parse /proc/meminfo for total RAM (Linux only)."""
    try:
        meminfo = Path("/proc/meminfo").read_text()
        for line in meminfo.splitlines():
            if line.startswith("MemTotal:"):
                kb = int(re.search(r"\d+", line).group())
                return kb // 1024
    except Exception:
        pass
    return 0


def _detect_cpu_cores() -> int:
    try:
        return os.cpu_count() or 1
    except Exception:
        return 1


def _detect_gpu() -> GPUInfo:
    """
    Detect GPU vendor + model by inspecting lspci output and loaded kernel
    modules.  Falls back to environment heuristics on non-Linux.
    """
    gpu = GPUInfo()

    # 1. Try lspci (most reliable on bare-metal Linux)
    rc, out = _run(["lspci"])
    if rc == 0 and out:
        vga_lines = [l for l in out.splitlines()
                     if re.search(r"VGA|3D|Display", l, re.I)]
        for line in vga_lines:
            ll = line.lower()
            if "nvidia" in ll:
                gpu.vendor = "nvidia"
                m = re.search(r"NVIDIA\s+([^\[]+)", line, re.I)
                gpu.model = m.group(1).strip() if m else ""
                break
            if "amd" in ll or "ati" in ll or "radeon" in ll:
                gpu.vendor = "amd"
                m = re.search(r"(?:AMD|ATI)\s+([^\[]+)", line, re.I)
                gpu.model = m.group(1).strip() if m else ""
                break
            if "intel" in ll:
                gpu.vendor = "intel"
                m = re.search(r"Intel\s+([^\[]+)", line, re.I)
                gpu.model = m.group(1).strip() if m else ""
                break

    # 2. Detect active driver from kernel modules
    rc2, mods = _run(["lsmod"])
    if rc2 == 0:
        loaded = {l.split()[0].lower() for l in mods.splitlines() if l}
        if "nvidia" in loaded:
            gpu.driver = "nvidia"
            # Try to get driver version
            _, ver_out = _run(["nvidia-smi", "--query-gpu=driver_version",
                               "--format=csv,noheader"])
            gpu.driver_version = ver_out.strip()
        elif "nouveau" in loaded:
            gpu.driver = "nouveau"
        elif "amdgpu" in loaded:
            gpu.driver = "amdgpu"
        elif "radeon" in loaded:
            gpu.driver = "radeon"
        elif "i915" in loaded:
            gpu.driver = "i915"

    # 3. Extra: check /proc/driver/nvidia
    if Path("/proc/driver/nvidia/version").exists():
        gpu.vendor = "nvidia"
        if not gpu.driver:
            gpu.driver = "nvidia"
        try:
            txt = Path("/proc/driver/nvidia/version").read_text()
            m = re.search(r"Kernel Module\s+(\S+)", txt)
            if m:
                gpu.driver_version = m.group(1)
        except Exception:
            pass

    return gpu


def _detect_desktop_env() -> str:
    """
    Detect the desktop environment from environment variables.
    Returns a lower-case identifier: gnome, kde, xfce, lxde, mate,
    cinnamon, i3, sway, hyprland, budgie, pantheon, unity, or 'unknown'.
    """
    # Most reliable: XDG_CURRENT_DESKTOP
    xdg = _env("XDG_CURRENT_DESKTOP")
    if xdg:
        for de in ("gnome", "kde", "xfce", "lxde", "lxqt", "mate",
                   "cinnamon", "i3", "sway", "hyprland", "budgie",
                   "pantheon", "unity", "deepin", "cosmic"):
            if de in xdg:
                return de
        return xdg.split(":")[0].lower()   # e.g. "ubuntu:GNOME" → "ubuntu"

    # Fallback: DESKTOP_SESSION / GDMSESSION
    for var in ("DESKTOP_SESSION", "GDMSESSION"):
        val = _env(var)
        if val:
            for de in ("gnome", "kde", "plasma", "xfce", "lxde", "mate",
                       "cinnamon", "i3", "sway"):
                if de in val:
                    return de.replace("plasma", "kde")
            return val

    # Last resort: check running processes
    _, ps_out = _run(["ps", "-e", "--no-headers", "-o", "comm"])
    procs = set(ps_out.splitlines())
    if "gnome-shell" in procs:  return "gnome"
    if "plasmashell"  in procs: return "kde"
    if "xfce4-session" in procs: return "xfce"
    if "lxsession"   in procs: return "lxde"
    if "mate-session" in procs: return "mate"
    if "cinnamon"    in procs:  return "cinnamon"

    return "unknown"


def _detect_display_server() -> str:
    """Return 'wayland', 'x11', or 'unknown'."""
    if _env("WAYLAND_DISPLAY"):
        return "wayland"
    if _env("DISPLAY"):
        return "x11"
    # Check login session
    _, out = _run(["loginctl", "show-session", "--property=Type", "--value"])
    t = out.strip().lower()
    if t in ("wayland", "x11", "mir"):
        return t
    return "unknown"


def _detect_vm() -> bool:
    """Return True if running inside a virtual machine or hypervisor."""
    rc, out = _run(["systemd-detect-virt", "--quiet"])
    if rc == 0:
        return True   # virt detected (any type)

    # Check DMI
    dmi_path = Path("/sys/class/dmi/id/product_name")
    if dmi_path.exists():
        try:
            name = dmi_path.read_text().strip().lower()
            vm_keywords = ("virtualbox", "vmware", "kvm", "qemu", "xen",
                           "hyper-v", "virtual machine", "parallels")
            if any(k in name for k in vm_keywords):
                return True
        except Exception:
            pass
    return False


def _detect_container() -> bool:
    """Return True if running inside Docker, LXC, or similar."""
    if Path("/.dockerenv").exists():
        return True
    try:
        cgroup = Path("/proc/1/cgroup").read_text()
        if "docker" in cgroup or "lxc" in cgroup or "kubepods" in cgroup:
            return True
    except Exception:
        pass
    return False


def _detect_available_pms() -> List[str]:
    """Return list of package managers actually present on this system."""
    candidates = ["apt", "dnf", "yum", "pacman", "zypper",
                  "flatpak", "snap", "apk", "emerge"]
    return [pm for pm in candidates if _cmd(pm)]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_system() -> SystemInfo:
    """
    Run full system detection and return a populated SystemInfo.
    Safe to call on non-Linux systems (all fields gracefully degraded).
    """
    info = SystemInfo()
    info.is_linux = (sys.platform == "linux")

    # Always detect arch + cores
    machine = platform.machine()
    info.cpu_arch  = machine or "unknown"
    info.cpu_cores = _detect_cpu_cores()

    # Use existing distro detection
    info.distro = _detect_distro()

    if not info.is_linux:
        return info   # remaining fields irrelevant on non-Linux

    info.ram_mb        = _detect_ram_mb()
    info.gpu           = _detect_gpu()
    info.desktop_env   = _detect_desktop_env()
    info.display_server = _detect_display_server()
    info.available_pms = _detect_available_pms()
    info.is_server     = (info.desktop_env == "unknown")
    info.is_vm         = _detect_vm()
    info.is_container  = _detect_container()

    return info


# ---------------------------------------------------------------------------
# Module-level cached instance (call detect_system() for a fresh scan)
# ---------------------------------------------------------------------------
_cached: Optional[SystemInfo] = None


def get_system_info(force_refresh: bool = False) -> SystemInfo:
    """Return cached SystemInfo, refreshing only when forced."""
    global _cached
    if _cached is None or force_refresh:
        _cached = detect_system()
    return _cached

"""
Linite - Linux Distribution Detector
Detects the current Linux distribution, version, and system architecture.
"""

import platform
import os
import sys
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DistroInfo:
    name: str = "unknown"
    id: str = "unknown"         # e.g. ubuntu, fedora, arch
    id_like: list = field(default_factory=list)  # e.g. ['debian'] for ubuntu
    version: str = "unknown"
    version_codename: str = ""
    arch: str = "unknown"       # x86_64 / aarch64 / armv7l
    bits: int = 64
    package_manager: str = "unknown"

    @property
    def is_debian_based(self) -> bool:
        return self.id in ("debian", "ubuntu", "linuxmint", "pop", "elementary",
                           "kali", "parrot", "zorin", "raspbian") or \
               "debian" in self.id_like or "ubuntu" in self.id_like

    @property
    def is_fedora_based(self) -> bool:
        return self.id in ("fedora", "rhel", "centos", "almalinux", "rocky",
                           "nobara") or \
               "fedora" in self.id_like or "rhel" in self.id_like

    @property
    def is_arch_based(self) -> bool:
        return self.id in ("arch", "manjaro", "endeavouros", "garuda",
                           "artix", "cachyos") or \
               "arch" in self.id_like

    @property
    def is_opensuse(self) -> bool:
        return self.id in ("opensuse-leap", "opensuse-tumbleweed", "suse") or \
               "suse" in self.id_like

    @property
    def is_nixos(self) -> bool:
        return self.id == "nixos" or "nix" in self.id_like

    @property
    def display_name(self) -> str:
        return f"{self.name} {self.version} ({self.arch})"


def _read_os_release() -> dict:
    """Parse /etc/os-release into a dict."""
    data = {}
    paths = ["/etc/os-release", "/usr/lib/os-release"]
    for path in paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, _, value = line.partition("=")
                        data[key.strip()] = value.strip().strip('"')
            break
    return data


def _detect_package_manager(distro: DistroInfo) -> str:
    """Determine the primary package manager for the distro."""
    if distro.is_nixos:
        return "nix"
    if distro.is_debian_based:
        return "apt"
    if distro.is_fedora_based:
        # dnf is preferred over yum on newer systems
        if _cmd_exists("dnf"):
            return "dnf"
        return "yum"
    if distro.is_arch_based:
        return "pacman"
    if distro.is_opensuse:
        return "zypper"
    # Fallbacks: prefer nix-env if present on a foreign distro
    if _cmd_exists("nix-env"):
        return "nix"
    for pm in ("apt", "dnf", "yum", "pacman", "zypper", "apk", "emerge"):
        if _cmd_exists(pm):
            return pm
    return "unknown"


def _cmd_exists(cmd: str) -> bool:
    """Check whether a command exists on the system."""
    from shutil import which
    return which(cmd) is not None


def detect() -> DistroInfo:
    """
    Detect current Linux distribution and return a DistroInfo instance.
    Falls back gracefully on non-Linux systems (useful for development on Windows/macOS).
    """
    info = DistroInfo()

    # Architecture
    machine = platform.machine()
    info.arch = machine
    info.bits = 32 if machine in ("i386", "i686", "armv7l") else 64

    if sys.platform != "linux":
        # Running on non-Linux (dev/test environment)
        info.name = f"Non-Linux ({sys.platform})"
        info.id = "non-linux"
        info.package_manager = "unknown"
        return info

    # Read /etc/os-release
    os_data = _read_os_release()

    info.name = os_data.get("NAME", "Linux")
    info.id = os_data.get("ID", "linux").lower()
    info.version = os_data.get("VERSION_ID", os_data.get("BUILD_ID", "unknown"))
    info.version_codename = os_data.get("VERSION_CODENAME", "")

    id_like_raw = os_data.get("ID_LIKE", "")
    info.id_like = [s.lower() for s in id_like_raw.split()] if id_like_raw else []

    info.package_manager = _detect_package_manager(info)

    return info


def check_flatpak_available() -> bool:
    return _cmd_exists("flatpak")


def check_snap_available() -> bool:
    return _cmd_exists("snap")

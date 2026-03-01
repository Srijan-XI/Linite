"""
Linite - Package Manager Abstraction Layer
Provides a unified interface for apt, dnf, pacman, zypper, snap, and flatpak.
"""

import subprocess
import shlex
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class BasePackageManager(ABC):
    name: str = "base"

    def run(
        self,
        args: List[str],
        sudo: bool = True,
        env: Optional[dict] = None,
        progress_cb: Optional[Callable[[str], None]] = None,
    ) -> tuple[int, str]:
        """
        Execute a package-manager command.
        Returns (returncode, combined_output).
        """
        import os
        cmd = (["sudo"] if sudo else []) + args
        logger.debug("Running: %s", " ".join(cmd))

        proc_env = None
        if env:
            proc_env = os.environ.copy()
            proc_env.update(env)

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=proc_env,
            )
            output_lines: List[str] = []
            for line in process.stdout:  # type: ignore[union-attr]
                line = line.rstrip()
                output_lines.append(line)
                if progress_cb:
                    progress_cb(line)
            process.wait()
            return process.returncode, "\n".join(output_lines)
        except FileNotFoundError as exc:
            msg = f"Command not found: {cmd[0]}"
            logger.error(msg)
            return 127, msg
        except Exception as exc:
            logger.exception("Unexpected error running command")
            return 1, str(exc)

    @abstractmethod
    def install(self, packages: List[str], progress_cb=None) -> tuple[int, str]:
        ...

    @abstractmethod
    def update_all(self, progress_cb=None) -> tuple[int, str]:
        ...

    @abstractmethod
    def update_package(self, packages: List[str], progress_cb=None) -> tuple[int, str]:
        ...

    @abstractmethod
    def is_installed(self, package: str) -> bool:
        ...


# ---------------------------------------------------------------------------
# APT  (Debian / Ubuntu / Mint …)
# ---------------------------------------------------------------------------

class AptPackageManager(BasePackageManager):
    name = "apt"

    def _refresh(self, progress_cb=None):
        return self.run(["apt-get", "update", "-y"], progress_cb=progress_cb)

    def install(self, packages, progress_cb=None):
        self._refresh(progress_cb)
        cmd = ["apt-get", "install", "-y", "--no-install-recommends"] + packages
        return self.run(cmd, env={"DEBIAN_FRONTEND": "noninteractive"}, progress_cb=progress_cb)

    def update_all(self, progress_cb=None):
        self._refresh(progress_cb)
        return self.run(
            ["apt-get", "upgrade", "-y"],
            progress_cb=progress_cb,
        )

    def update_package(self, packages, progress_cb=None):
        return self.install(packages, progress_cb)

    def is_installed(self, package: str) -> bool:
        _, out = self.run(
            ["dpkg-query", "-W", "-f=${Status}", package], sudo=False
        )
        return "install ok installed" in out


# ---------------------------------------------------------------------------
# DNF  (Fedora / RHEL 8+ / AlmaLinux / Rocky …)
# ---------------------------------------------------------------------------

class DnfPackageManager(BasePackageManager):
    name = "dnf"

    def install(self, packages, progress_cb=None):
        return self.run(
            ["dnf", "install", "-y"] + packages, progress_cb=progress_cb
        )

    def update_all(self, progress_cb=None):
        return self.run(["dnf", "upgrade", "-y"], progress_cb=progress_cb)

    def update_package(self, packages, progress_cb=None):
        return self.run(
            ["dnf", "upgrade", "-y"] + packages, progress_cb=progress_cb
        )

    def is_installed(self, package: str) -> bool:
        rc, _ = self.run(["rpm", "-q", package], sudo=False)
        return rc == 0


# ---------------------------------------------------------------------------
# YUM  (CentOS 7 / RHEL 7)
# ---------------------------------------------------------------------------

class YumPackageManager(DnfPackageManager):
    name = "yum"

    def install(self, packages, progress_cb=None):
        return self.run(
            ["yum", "install", "-y"] + packages, progress_cb=progress_cb
        )

    def update_all(self, progress_cb=None):
        return self.run(["yum", "update", "-y"], progress_cb=progress_cb)

    def update_package(self, packages, progress_cb=None):
        return self.run(
            ["yum", "update", "-y"] + packages, progress_cb=progress_cb
        )


# ---------------------------------------------------------------------------
# Pacman  (Arch / Manjaro / EndeavourOS …)
# ---------------------------------------------------------------------------

class PacmanPackageManager(BasePackageManager):
    name = "pacman"

    def install(self, packages, progress_cb=None):
        return self.run(
            ["pacman", "-S", "--noconfirm", "--needed"] + packages,
            progress_cb=progress_cb,
        )

    def update_all(self, progress_cb=None):
        return self.run(
            ["pacman", "-Syu", "--noconfirm"], progress_cb=progress_cb
        )

    def update_package(self, packages, progress_cb=None):
        return self.run(
            ["pacman", "-S", "--noconfirm"] + packages, progress_cb=progress_cb
        )

    def is_installed(self, package: str) -> bool:
        rc, _ = self.run(["pacman", "-Q", package], sudo=False)
        return rc == 0


# ---------------------------------------------------------------------------
# Zypper  (openSUSE)
# ---------------------------------------------------------------------------

class ZypperPackageManager(BasePackageManager):
    name = "zypper"

    def install(self, packages, progress_cb=None):
        return self.run(
            ["zypper", "--non-interactive", "install"] + packages,
            progress_cb=progress_cb,
        )

    def update_all(self, progress_cb=None):
        return self.run(
            ["zypper", "--non-interactive", "update"], progress_cb=progress_cb
        )

    def update_package(self, packages, progress_cb=None):
        return self.run(
            ["zypper", "--non-interactive", "update"] + packages,
            progress_cb=progress_cb,
        )

    def is_installed(self, package: str) -> bool:
        rc, _ = self.run(["rpm", "-q", package], sudo=False)
        return rc == 0


# ---------------------------------------------------------------------------
# Snap
# ---------------------------------------------------------------------------

class SnapPackageManager(BasePackageManager):
    name = "snap"

    def install(self, packages, progress_cb=None):
        results = []
        for pkg in packages:
            rc, out = self.run(["snap", "install", pkg], progress_cb=progress_cb)
            results.append((rc, out))
        overall_rc = max(r[0] for r in results) if results else 0
        return overall_rc, "\n".join(r[1] for r in results)

    def install_classic(self, packages, progress_cb=None):
        results = []
        for pkg in packages:
            rc, out = self.run(
                ["snap", "install", "--classic", pkg], progress_cb=progress_cb
            )
            results.append((rc, out))
        overall_rc = max(r[0] for r in results) if results else 0
        return overall_rc, "\n".join(r[1] for r in results)

    def update_all(self, progress_cb=None):
        return self.run(["snap", "refresh"], progress_cb=progress_cb)

    def update_package(self, packages, progress_cb=None):
        return self.run(["snap", "refresh"] + packages, progress_cb=progress_cb)

    def is_installed(self, package: str) -> bool:
        rc, _ = self.run(["snap", "list", package], sudo=False)
        return rc == 0


# ---------------------------------------------------------------------------
# Flatpak
# ---------------------------------------------------------------------------

class FlatpakPackageManager(BasePackageManager):
    name = "flatpak"

    def install(self, packages, progress_cb=None):
        # packages are expected to be Flatpak app IDs
        return self.run(
            ["flatpak", "install", "-y", "--noninteractive"] + packages,
            sudo=False,
            progress_cb=progress_cb,
        )

    def update_all(self, progress_cb=None):
        return self.run(
            ["flatpak", "update", "-y", "--noninteractive"],
            sudo=False,
            progress_cb=progress_cb,
        )

    def update_package(self, packages, progress_cb=None):
        return self.run(
            ["flatpak", "update", "-y", "--noninteractive"] + packages,
            sudo=False,
            progress_cb=progress_cb,
        )

    def is_installed(self, package: str) -> bool:
        rc, _ = self.run(["flatpak", "info", package], sudo=False)
        return rc == 0


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_PM_MAP = {
    "apt": AptPackageManager,
    "dnf": DnfPackageManager,
    "yum": YumPackageManager,
    "pacman": PacmanPackageManager,
    "zypper": ZypperPackageManager,
    "snap": SnapPackageManager,
    "flatpak": FlatpakPackageManager,
}


def get_package_manager(name: str) -> BasePackageManager:
    """Return an instance of the appropriate package manager."""
    cls = _PM_MAP.get(name.lower())
    if cls is None:
        raise ValueError(f"Unsupported package manager: '{name}'")
    return cls()

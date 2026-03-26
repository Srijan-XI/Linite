"""
Linite - Package Manager Abstraction Layer (Fixed & Improved)
"""

import subprocess
import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Tuple
from shutil import which

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class BasePackageManager(ABC):
    name: str = "base"

    def _build_command(self, args: List[str], sudo: bool) -> List[str]:
        """Build command with optional sudo."""
        if sudo and os.name != "nt" and os.geteuid() != 0:
            if which("sudo"):
                return ["sudo"] + args
            else:
                logger.warning("sudo not available; running without it")
        return args

    def run(
        self,
        args: List[str],
        sudo: bool = True,
        env: Optional[dict] = None,
        progress_cb: Optional[Callable[[str], None]] = None,
        timeout: Optional[int] = None,
        cancel_event: Optional[threading.Event] = None,
    ) -> Tuple[int, str]:
        """
        Execute a command safely with timeout and cancellation.
        """
        cmd = self._build_command(args, sudo)
        logger.debug("Running: %s", " ".join(cmd))

        proc_env = os.environ.copy()
        if env:
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

            # Read line-by-line safely
            for line in iter(process.stdout.readline, ''):  # type: ignore
                if cancel_event and cancel_event.is_set():
                    process.kill()
                    return 1, "Operation cancelled"

                line = line.rstrip()
                output_lines.append(line)

                if progress_cb:
                    progress_cb(line)

            process.wait(timeout=timeout)
            return process.returncode, "\n".join(output_lines)

        except subprocess.TimeoutExpired:
            process.kill()
            return 1, "Process timed out"
        except FileNotFoundError:
            return 127, f"Command not found: {cmd[0]}"
        except Exception as exc:
            logger.exception("Unexpected error")
            return 1, str(exc)

    @abstractmethod
    def install(self, packages: List[str], **kwargs) -> Tuple[int, str]:
        ...

    @abstractmethod
    def update_all(self, **kwargs) -> Tuple[int, str]:
        ...

    @abstractmethod
    def update_package(self, packages: List[str], **kwargs) -> Tuple[int, str]:
        ...

    @abstractmethod
    def is_installed(self, package: str) -> bool:
        ...


# ---------------------------------------------------------------------------
# APT
# ---------------------------------------------------------------------------

class AptPackageManager(BasePackageManager):
    name = "apt"
    _LOCK_MSG = "Could not get lock"
    _RETRY_WAIT = 5
    _MAX_WAIT = 120

    def _run_apt(self, args, cancel_event=None, **kwargs):
        elapsed = 0

        while True:
            rc, out = self.run(args, cancel_event=cancel_event, **kwargs)

            if rc == 0 or self._LOCK_MSG not in out:
                return rc, out

            if cancel_event and cancel_event.is_set():
                return 1, "Cancelled during lock wait"

            if elapsed >= self._MAX_WAIT:
                return rc, out

            logger.warning("APT lock detected, retrying...")
            if kwargs.get("progress_cb"):
                kwargs["progress_cb"]("Waiting for apt lock...")

            for _ in range(self._RETRY_WAIT * 4):
                if cancel_event and cancel_event.is_set():
                    return 1, "Cancelled"
                time.sleep(0.25)

            elapsed += self._RETRY_WAIT

    def install(self, packages, **kwargs):
        self._run_apt(["apt-get", "update", "-y"], **kwargs)
        return self._run_apt(
            ["apt-get", "install", "-y"] + packages,
            env={"DEBIAN_FRONTEND": "noninteractive"},
            **kwargs,
        )

    def update_all(self, **kwargs):
        self._run_apt(["apt-get", "update", "-y"], **kwargs)
        return self._run_apt(["apt-get", "upgrade", "-y"], **kwargs)

    def update_package(self, packages, **kwargs):
        return self.install(packages, **kwargs)

    def is_installed(self, package: str) -> bool:
        rc, out = self.run(
            ["dpkg-query", "-W", "-f=${Status}", package],
            sudo=False
        )
        return "install ok installed" in out


# ---------------------------------------------------------------------------
# PACMAN
# ---------------------------------------------------------------------------

class PacmanPackageManager(BasePackageManager):
    name = "pacman"

    def install(self, packages, **kwargs):
        return self.run(["pacman", "-S", "--noconfirm"] + packages, **kwargs)

    def update_all(self, **kwargs):
        return self.run(["pacman", "-Syu", "--noconfirm"], **kwargs)

    def update_package(self, packages, **kwargs):
        return self.run(["pacman", "-S"] + packages, **kwargs)

    def is_installed(self, package: str) -> bool:
        rc, _ = self.run(["pacman", "-Q", package], sudo=False)
        return rc == 0


# ---------------------------------------------------------------------------
# SNAP
# ---------------------------------------------------------------------------

class SnapPackageManager(BasePackageManager):
    name = "snap"

    def install(self, packages, **kwargs):
        results = []
        for pkg in packages:
            rc, out = self.run(["snap", "install", pkg], **kwargs)
            results.append((rc, out))

        return max(r[0] for r in results), "\n".join(r[1] for r in results)

    def update_all(self, **kwargs):
        return self.run(["snap", "refresh"], **kwargs)

    def update_package(self, packages, **kwargs):
        return self.run(["snap", "refresh"] + packages, **kwargs)

    def is_installed(self, package: str) -> bool:
        rc, _ = self.run(["snap", "list", package], sudo=False)
        return rc == 0


# ---------------------------------------------------------------------------
# FLATPAK
# ---------------------------------------------------------------------------

class FlatpakPackageManager(BasePackageManager):
    name = "flatpak"

    def install(self, packages, **kwargs):
        return self.run(
            ["flatpak", "install", "-y"] + packages,
            sudo=False,
            **kwargs,
        )

    def update_all(self, **kwargs):
        return self.run(["flatpak", "update", "-y"], sudo=False, **kwargs)

    def update_package(self, packages, **kwargs):
        return self.run(["flatpak", "update", "-y"] + packages, sudo=False, **kwargs)

    def is_installed(self, package: str) -> bool:
        rc, _ = self.run(["flatpak", "info", package], sudo=False)
        return rc == 0


# ---------------------------------------------------------------------------
# APPIMAGE
# ---------------------------------------------------------------------------

class AppImagePackageManager(BasePackageManager):
    name = "appimage"

    def install(self, packages, **kwargs):
        return 0, "Handled externally"

    def update_all(self, **kwargs):
        return 0, "Manual update required"

    def update_package(self, packages, **kwargs):
        return 0, "Manual update required"

    def is_installed(self, package: str) -> bool:
        from pathlib import Path
        return (Path.home() / ".local/bin" / package).exists()


# ---------------------------------------------------------------------------
# FACTORY
# ---------------------------------------------------------------------------

_PM_MAP = {
    "apt": AptPackageManager,
    "pacman": PacmanPackageManager,
    "snap": SnapPackageManager,
    "flatpak": FlatpakPackageManager,
    "appimage": AppImagePackageManager,
}


def get_package_manager(name: str) -> BasePackageManager:
    cls = _PM_MAP.get(name.lower())
    if not cls:
        raise ValueError(f"Unsupported package manager: {name}")
    return cls()
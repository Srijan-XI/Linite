"""
Linite - Network Connectivity Check (Improved)
Reliable internet connectivity verification.
"""

import logging
import socket
import subprocess
import sys
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


# Default endpoints (diverse to avoid single-point failure)
DEFAULT_TARGETS: List[Tuple[str, int]] = [
    ("google.com", 80),
    ("cloudflare.com", 80),
    ("1.1.1.1", 53),
    ("8.8.8.8", 53),
]


def check_network(timeout_sec: int = 3, retries: int = 2) -> bool:
    """
    Check if the system has internet connectivity.

    Strategy:
    1. Try TCP connections to multiple hosts
    2. Fallback to ping if needed

    Returns:
        bool: True if internet is reachable, False otherwise
    """

    # Try TCP connectivity first (best signal)
    if _check_tcp_multiple(timeout_sec, retries):
        return True

    # Fallback: ping check
    if _check_ping(timeout_sec):
        return True

    return False


def _check_tcp_multiple(timeout_sec: int, retries: int) -> bool:
    """Try multiple hosts with retries."""
    for attempt in range(retries + 1):
        for host, port in DEFAULT_TARGETS:
            if _check_tcp(host, port, timeout_sec):
                logger.debug(f"Network check: TCP success {host}:{port}")
                return True

        logger.debug(f"Network check: TCP attempt {attempt + 1} failed")

    return False


def _check_tcp(host: str, port: int, timeout_sec: int) -> bool:
    """Attempt TCP connection to a host."""
    try:
        with socket.create_connection((host, port), timeout=timeout_sec):
            return True
    except (socket.timeout, socket.gaierror, OSError) as exc:
        logger.debug(f"TCP failed {host}:{port} → {exc}")
        return False


def _check_ping(timeout_sec: int) -> bool:
    """Fallback ICMP ping check (cross-platform)."""
    try:
        if sys.platform.startswith("win"):
            # Windows ping
            cmd = ["ping", "-n", "1", "-w", str(timeout_sec * 1000), "8.8.8.8"]
        else:
            # Linux / macOS
            cmd = ["ping", "-c", "1", "-W", str(timeout_sec), "8.8.8.8"]

        proc = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout_sec + 2,
        )

        success = proc.returncode == 0

        if success:
            logger.debug("Network check: ping succeeded")
        else:
            logger.debug(f"Network check: ping failed rc={proc.returncode}")

        return success

    except Exception as exc:
        logger.debug(f"Ping error: {type(exc).__name__}: {exc}")
        return False


def warn_if_offline() -> Optional[str]:
    """
    Return warning message if offline, otherwise None.
    """
    if not check_network():
        return (
            "⚠ Network connectivity check failed — your system appears offline. "
            "Installation may fail if packages cannot be downloaded."
        )
    return None


# Optional CLI usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    if check_network():
        print("✅ Internet is reachable")
    else:
        print("❌ No internet connectivity detected")
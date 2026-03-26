"""SSH primitives used by remote Linite operations."""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class RemoteTarget:
    """Parsed SSH target definition."""

    user: str
    host: str
    port: int = 22


def parse_remote_target(target: str) -> RemoteTarget:
    """Parse a target in the form user@host or user@host:port."""
    raw = target.strip()
    if "@" not in raw:
        raise ValueError("Remote target must be in the form user@host or user@host:port")

    user_part, host_part = raw.split("@", 1)
    user = user_part.strip()
    host_port = host_part.strip()

    if not user:
        raise ValueError("Remote target user is empty")
    if not host_port:
        raise ValueError("Remote target host is empty")

    if ":" in host_port:
        host, port_text = host_port.rsplit(":", 1)
        host = host.strip()
        if not host:
            raise ValueError("Remote target host is empty")
        try:
            port = int(port_text)
        except ValueError as exc:
            raise ValueError("Remote target port must be an integer") from exc
        if port < 1 or port > 65535:
            raise ValueError("Remote target port must be between 1 and 65535")
    else:
        host = host_port
        port = 22

    return RemoteTarget(user=user, host=host, port=port)


def run_remote_command(
    target: RemoteTarget,
    command: str,
    timeout_sec: int = 1800,
) -> tuple[int, str]:
    """Execute a shell command on the remote host over SSH."""
    ssh_cmd = [
        "ssh",
        "-p",
        str(target.port),
        f"{target.user}@{target.host}",
        command,
    ]
    proc = subprocess.run(
        ssh_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
    return proc.returncode, proc.stdout


def quote_remote_args(args: list[str]) -> str:
    """Build a safely quoted shell argument list for remote execution."""
    return " ".join(shlex.quote(a) for a in args)

"""Remote execution and SSH helpers for Linite.

This namespace isolates upcoming remote/SSH install logic from local operations.
"""

from core.remote.ssh import RemoteTarget, parse_remote_target, run_remote_command
from core.remote.install import build_remote_install_command

__all__ = [
    "RemoteTarget",
    "parse_remote_target",
    "run_remote_command",
    "build_remote_install_command",
]

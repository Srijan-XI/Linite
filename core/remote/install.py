"""Remote install command construction helpers."""

from __future__ import annotations

from core.remote.ssh import quote_remote_args


def build_remote_install_command(app_ids: list[str], skip_network_check: bool = False) -> str:
    """Build a remote Linite CLI install command for selected app IDs."""
    if not app_ids:
        raise ValueError("No app IDs provided for remote install command")

    base = ["linite", "--cli", "install", *app_ids]
    if skip_network_check:
        base.append("--skip-network-check")
    return quote_remote_args(base)

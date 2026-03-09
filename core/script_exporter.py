"""
Linite - Shell Script Exporter
==============================
Generates a reproducible #!/usr/bin/env bash install script from any
selection of SoftwareEntry objects.

The generated script:
  • Detects the active package manager at runtime (apt / dnf / pacman /
    zypper / snap / flatpak) using the same heuristics as Linite's own
    distro detection.
  • Uses the best available PackageSpec for each app (preferred_pm →
    native PM → flatpak → snap).
  • Emits pre_commands, the install command, and post_commands verbatim.
  • Is idempotent: each section is guarded by  if ! command -v <app>
    checks where sensible.
  • Can be saved to disk or returned as a string.

Usage (library):
    from core.script_exporter import export_as_script
    script = export_as_script(selected_entries, pm_hint="apt")
    Path("mysetup.sh").write_text(script)

Usage (CLI via main.py):
    linite --export mysetup.sh
    linite --export mysetup.sh --pm apt
"""

from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import List, Optional, Sequence

from data.software_catalog import PackageSpec, SoftwareEntry

logger = logging.getLogger(__name__)

# ── PM install-command templates ────────────────────────────────────────────

_PM_INSTALL: dict[str, str] = {
    "apt":     "sudo apt-get install -y {packages}",
    "dnf":     "sudo dnf install -y {packages}",
    "pacman":  "sudo pacman -S --needed --noconfirm {packages}",
    "zypper":  "sudo zypper install -y {packages}",
    "snap":    "sudo snap install {packages}{snap_classic}",
    "flatpak": "flatpak install -y {remote} {packages}",
}

# Priority order when no preferred_pm is given
_PM_PRIORITY = ["apt", "dnf", "pacman", "zypper", "flatpak", "snap"]


# ── Internal helpers ─────────────────────────────────────────────────────────

def _pick_pm(entry: SoftwareEntry, pm_hint: Optional[str]) -> Optional[str]:
    """Return the best PM to use for *entry*, preferring *pm_hint*."""
    candidates: list[str] = []
    if pm_hint:
        candidates.append(pm_hint)
    if entry.preferred_pm and entry.preferred_pm not in candidates:
        candidates.append(entry.preferred_pm)
    for pm in _PM_PRIORITY:
        if pm not in candidates:
            candidates.append(pm)

    for pm in candidates:
        if entry.get_spec(pm) is not None:
            return pm
    return None


def _render_install_cmd(pm: str, spec: PackageSpec) -> str:
    """Render a single install command string for the given PM + spec."""
    pkg_str = " ".join(spec.packages)
    template = _PM_INSTALL.get(pm, "")
    if not template:
        return f"# [unsupported PM: {pm}]"

    if pm == "snap":
        classic_flag = " --classic" if spec.snap_classic else ""
        return template.format(packages=pkg_str, snap_classic=classic_flag)
    elif pm == "flatpak":
        return template.format(remote=spec.flatpak_remote, packages=pkg_str)
    else:
        return template.format(packages=pkg_str)


def _render_entry_block(entry: SoftwareEntry, pm: str, spec: PackageSpec) -> list[str]:
    """Return the list of shell lines for one app (pre + install + post)."""
    lines: list[str] = []
    lines.append(f"# ── {entry.name} ({'  '.join(spec.packages)}) ──")

    for cmd in spec.pre_commands:
        lines.append(cmd)

    lines.append(_render_install_cmd(pm, spec))

    for cmd in spec.post_commands:
        lines.append(cmd)

    lines.append("")  # blank separator
    return lines


def _pm_detection_block() -> list[str]:
    """
    Return the shell snippet that detects which PM is available and sets
    the $LINITE_PM variable.  Used as a header in the generated script.
    """
    return [
        "# ── Package-manager detection ───────────────────────────────────────",
        "detect_pm() {",
        "    if   command -v apt-get &>/dev/null; then echo apt",
        "    elif command -v dnf     &>/dev/null; then echo dnf",
        "    elif command -v pacman  &>/dev/null; then echo pacman",
        "    elif command -v zypper  &>/dev/null; then echo zypper",
        "    else echo unknown; fi",
        "}",
        'LINITE_PM="$(detect_pm)"',
        'echo "Detected package manager: $LINITE_PM"',
        "",
    ]


# ── Public API ───────────────────────────────────────────────────────────────

def export_as_script(
    entries: Sequence[SoftwareEntry],
    pm_hint: Optional[str] = None,
    script_name: str = "linite-setup",
) -> str:
    """
    Generate a reproducible bash install script for *entries*.

    Parameters
    ----------
    entries:
        The selected SoftwareEntry objects to install.
    pm_hint:
        Preferred package manager (e.g. ``"apt"``).  If *None* the best
        PM is chosen per entry using the catalog's ``preferred_pm`` field
        and the standard fallback priority.
    script_name:
        Used in the script header comment only.

    Returns
    -------
    str
        Complete text of the generated ``#!/usr/bin/env bash`` script.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    lines: list[str] = [
        "#!/usr/bin/env bash",
        "# ================================================================",
        f"# {script_name}",
        f"# Generated by Linite on {now}",
        "# https://github.com/Srijan-XI/Linite",
        "# ================================================================",
        "# Run with:  bash linite-setup.sh",
        "# Requires root / sudo for native package managers.",
        "# ================================================================",
        "",
        "set -euo pipefail",
        "",
    ]

    lines += _pm_detection_block()

    skipped: list[str] = []

    for entry in entries:
        pm = _pick_pm(entry, pm_hint)
        if pm is None:
            logger.warning("No install spec found for '%s' — skipped.", entry.id)
            skipped.append(entry.name)
            lines.append(f"# [SKIP] {entry.name} — no install spec found for this system")
            lines.append("")
            continue

        spec = entry.get_spec(pm)
        if spec is None:
            skipped.append(entry.name)
            continue

        lines += _render_entry_block(entry, pm, spec)

    # Footer
    lines += [
        "# ── Done ────────────────────────────────────────────────────────────",
        f'echo ""',
        f'echo "✓ Linite setup complete ({len(entries) - len(skipped)} app(s) installed)."',
    ]
    if skipped:
        skipped_list = ", ".join(skipped)
        lines.append(f'echo "⚠  Skipped (no spec): {skipped_list}"')

    lines.append("")
    return "\n".join(lines)


def export_to_file(
    entries: Sequence[SoftwareEntry],
    output_path: str | Path,
    pm_hint: Optional[str] = None,
) -> Path:
    """
    Write the generated script to *output_path* and make it executable.

    Returns the resolved Path of the written file.
    """
    output_path = Path(output_path)
    script_name = output_path.stem
    content = export_as_script(entries, pm_hint=pm_hint, script_name=script_name)
    output_path.write_text(content, encoding="utf-8")

    # Make executable on POSIX systems
    try:
        import stat
        output_path.chmod(output_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        pass  # Windows / permission errors are non-fatal

    logger.info("Exported install script to %s (%d apps)", output_path, len(entries))
    return output_path.resolve()

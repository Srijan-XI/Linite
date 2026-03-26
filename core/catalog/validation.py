"""Catalog validation helpers used at startup and in CI checks."""

from __future__ import annotations

from typing import Optional


def catalog_lint(
    current_pm: Optional[str] = None,
    include_compatibility: bool = True,
) -> list[str]:
    """
    Validate loaded catalog entries and return human-readable warnings.

    Checks:
    - required metadata fields are present
    - install spec keys are known
    - non-script specs have at least one package
    - each app has a compatible install path for the current package manager
    """
    from data.software_catalog import CATALOG

    warnings: list[str] = []
    known_pm_keys = {
        "apt", "dnf", "yum", "pacman", "zypper", "snap", "flatpak",
        "appimage", "script", "universal", "nix", "aur",
    }

    for app in CATALOG:
        if not app.id.strip() or not app.name.strip() or not app.category.strip():
            warnings.append(
                f"[{app.id or '<missing-id>'}] Missing required metadata (id/name/category)."
            )

        if not app.install_specs:
            warnings.append(f"[{app.id}] No install_specs defined.")
            continue

        spec_keys = set(app.install_specs.keys())
        unknown_keys = sorted(k for k in spec_keys if k not in known_pm_keys)
        if unknown_keys:
            warnings.append(f"[{app.id}] Unknown install_specs key(s): {', '.join(unknown_keys)}")

        for pm_key, spec in app.install_specs.items():
            if pm_key in {"script"}:
                if not spec.script_url:
                    warnings.append(f"[{app.id}] script spec is missing script_url.")
                continue

            if pm_key in {"appimage"}:
                if not spec.packages and not spec.script_url:
                    warnings.append(f"[{app.id}] appimage spec has no URL/package hint.")
                continue

            if not spec.packages:
                warnings.append(f"[{app.id}] {pm_key} spec has no packages.")

        # Compatibility check for the host package manager.
        if include_compatibility and current_pm and current_pm != "unknown":
            compatible_keys = {current_pm, "universal", "flatpak", "snap", "appimage", "script"}
            # Treat yum and dnf as equivalent compatibility for linting.
            if current_pm == "yum":
                compatible_keys.add("dnf")
            if current_pm == "dnf":
                compatible_keys.add("yum")

            if spec_keys.isdisjoint(compatible_keys):
                warnings.append(
                    f"[{app.id}] No install path for host pm '{current_pm}' (or flatpak/snap/appimage/script fallback)."
                )

    return warnings

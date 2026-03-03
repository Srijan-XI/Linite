"""
Loads the software catalog from per-category TOML files under data/catalog/.

Exposes CATALOG, CATALOG_MAP, and CATEGORIES with the same types as the
original software_catalog.py so all existing import sites continue to work
without modification.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.software_catalog import PackageSpec, SoftwareEntry

CATALOG_DIR = Path(__file__).parent / "catalog"


def _load_spec(d: dict) -> "PackageSpec":
    from data.software_catalog import PackageSpec

    return PackageSpec(
        packages=d.get("packages", []),
        snap_classic=d.get("snap_classic", False),
        flatpak_remote=d.get("flatpak_remote", "flathub"),
        script_url=d.get("script_url", ""),
        sha256=d.get("sha256", ""),
        pre_commands=d.get("pre_commands", []),
        post_commands=d.get("post_commands", []),
    )


def _load_app(d: dict) -> "SoftwareEntry":
    from data.software_catalog import SoftwareEntry

    install_specs = {
        pm: _load_spec(spec) for pm, spec in d.get("install_specs", {}).items()
    }
    return SoftwareEntry(
        id=d["id"],
        name=d["name"],
        description=d["description"],
        category=d["category"],
        icon=d.get("icon", "📦"),
        website=d.get("website", ""),
        install_specs=install_specs,
        preferred_pm=d.get("preferred_pm"),
    )


def load_catalog() -> list:
    apps = []
    for toml_file in sorted(CATALOG_DIR.glob("*.toml")):
        with open(toml_file, "rb") as f:
            data = tomllib.load(f)
        apps.extend(_load_app(entry) for entry in data.get("apps", []))
    return apps


CATALOG = load_catalog()
CATALOG_MAP = {app.id: app for app in CATALOG}
CATEGORIES = sorted(set(app.category for app in CATALOG))

"""
Loads the software catalog from per-category TOML files under data/catalog/.

Exposes CATALOG, CATALOG_MAP, and CATEGORIES with the same types as the
original software_catalog.py so all existing import sites continue to work
without modification.

User-defined catalogs can be added to ~/.config/linite/catalog/*.toml
and will be automatically merged at startup. Apps with duplicate IDs
in user catalogs override built-in definitions.
"""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.software_catalog import PackageSpec, SoftwareEntry

logger = logging.getLogger(__name__)

CATALOG_DIR = Path(__file__).parent / "catalog"
USER_CATALOG_DIR = Path.home() / ".config" / "linite" / "catalog"


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
    """
    Load catalog entries from both built-in and user directories.
    
    Built-in catalogs are loaded from data/catalog/*.toml
    User catalogs are loaded from ~/.config/linite/catalog/*.toml
    
    If a user catalog contains an app with the same ID as a built-in app,
    the user version overrides the built-in version.
    
    Returns:
        List of SoftwareEntry objects, with user apps taking precedence.
    """
    # Load built-in apps first
    builtin_apps = {}
    for toml_file in sorted(CATALOG_DIR.glob("*.toml")):
        try:
            with open(toml_file, "rb") as f:
                data = tomllib.load(f)
            for entry in data.get("apps", []):
                app = _load_app(entry)
                builtin_apps[app.id] = app
        except Exception as exc:
            logger.error(f"Failed to load built-in catalog {toml_file.name}: {exc}")
    
    logger.info(f"Loaded {len(builtin_apps)} built-in apps from {CATALOG_DIR}")
    
    # Load user-defined apps (override built-ins with same ID)
    user_apps = {}
    if USER_CATALOG_DIR.exists():
        for toml_file in sorted(USER_CATALOG_DIR.glob("*.toml")):
            try:
                with open(toml_file, "rb") as f:
                    data = tomllib.load(f)
                for entry in data.get("apps", []):
                    app = _load_app(entry)
                    user_apps[app.id] = app
                    if app.id in builtin_apps:
                        logger.info(
                            f"User catalog {toml_file.name} overrides built-in app: {app.id}"
                        )
            except Exception as exc:
                logger.warning(
                    f"Failed to load user catalog {toml_file.name}: {exc}. "
                    f"Skipping this file."
                )
        
        if user_apps:
            logger.info(
                f"Loaded {len(user_apps)} user-defined apps from {USER_CATALOG_DIR}"
            )
    else:
        logger.debug(f"User catalog directory does not exist: {USER_CATALOG_DIR}")
    
    # Merge: user apps override built-ins
    merged = {**builtin_apps, **user_apps}
    return list(merged.values())


CATALOG = load_catalog()
CATALOG_MAP = {app.id: app for app in CATALOG}
CATEGORIES = sorted(set(app.category for app in CATALOG))

"""
Linite - TOML Package Mapping Layer
=====================================
Loads per-PM TOML files from  data/package_maps/<pm>.toml  and converts
them into PackageSpec objects.  Acts as a higher-priority source than the
Python software_catalog: if a mapping exists here it is used; otherwise the
catalog spec is returned as a fallback.

TOML file format (data/package_maps/apt.toml):
------------------------------------------------
[vlc]
packages = ["vlc"]

[vscode]
packages = ["code"]
pre_commands = ["wget -qO- … | gpg --dearmor > /tmp/ms.gpg"]

# spotify has no native APT build — omit entry; caller falls back to snap/flatpak.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import tomllib

from data.software_catalog import PackageSpec, SoftwareEntry, CATALOG_MAP

logger = logging.getLogger(__name__)

# Directory that holds per-PM TOML maps
_MAPS_DIR = Path(__file__).resolve().parent.parent / "data" / "package_maps"

# Supported PMs with a TOML map file
_PM_MAP_FILES: Dict[str, str] = {
    "apt":     "apt.toml",
    "dnf":     "dnf.toml",
    "pacman":  "pacman.toml",
    "zypper":  "zypper.toml",
    "snap":    "snap.toml",
    "flatpak": "flatpak.toml",
}


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def _load_pm_map(pm: str) -> Dict[str, dict]:
    """Load and cache the YAML map for *pm*.  Returns {} on any failure."""
    fname = _PM_MAP_FILES.get(pm)
    if not fname:
        return {}
    path = _MAPS_DIR / fname
    if not path.exists():
        logger.debug("Package map not found: %s", path)
        return {}
    try:
        with path.open("rb") as fh:
            raw = tomllib.load(fh) or {}
        logger.debug("Loaded %d entries from %s", len(raw), path.name)
        return raw
    except Exception as exc:
        logger.error("Failed to load %s: %s", path, exc)
        return {}


def _dict_to_spec(d: dict) -> PackageSpec:
    """Convert a YAML mapping dict to a PackageSpec."""
    pkgs = d.get("packages", [])
    if isinstance(pkgs, str):
        pkgs = [pkgs]
    return PackageSpec(
        packages=list(pkgs),
        snap_classic=bool(d.get("snap_classic", False)),
        flatpak_remote=str(d.get("flatpak_remote", "flathub")),
        script_url=str(d.get("script_url", "")),
        sha256=str(d.get("sha256", "")),
        pre_commands=list(d.get("pre_commands", [])),
        post_commands=list(d.get("post_commands", [])),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class PackageMapLoader:
    """
    Unified access to all per-PM YAML package maps with fallback to the
    Python software catalog.

    Usage::

        loader = PackageMapLoader()
        spec = loader.get_spec("vlc", "apt")      # PackageSpec or None
        pm   = loader.best_pm("vlc", available)   # "apt" | "flatpak" | None
    """

    def get_spec(self, app_id: str, pm: str) -> Optional[PackageSpec]:
        """
        Return a PackageSpec for *app_id* on *pm*.

        Priority:
          1. TOML map  (data/package_maps/<pm>.toml)
          2. Python catalog  (data/software_catalog.py)
          3. None  (app or PM not supported)
        """
        # 1. TOML map
        pm_map = _load_pm_map(pm)
        entry = pm_map.get(app_id)
        if entry is not None:
            return _dict_to_spec(entry)

        # 2. Python catalog fallback
        cat_entry: Optional[SoftwareEntry] = CATALOG_MAP.get(app_id)
        if cat_entry:
            return cat_entry.get_spec(pm)

        return None

    def best_pm(
        self,
        app_id: str,
        available_pms: List[str],
        preferred_pm: Optional[str] = None,
    ) -> Optional[str]:
        """
        Return the best available PM for *app_id* from *available_pms*.

        Order: preferred_pm (if in available_pms) → SUPPORTED_PMS order.
        """
        candidates = []
        if preferred_pm and preferred_pm in available_pms:
            candidates.append(preferred_pm)
        for pm in available_pms:
            if pm not in candidates:
                candidates.append(pm)

        for pm in candidates:
            if self.get_spec(app_id, pm) is not None:
                return pm
        return None

    def list_supported_pms(self, app_id: str) -> List[str]:
        """Return every PM for which this app has a spec (YAML + catalog)."""
        pms = []
        for pm in _PM_MAP_FILES:
            if self.get_spec(app_id, pm) is not None:
                pms.append(pm)
        return pms

    def reload(self) -> None:
        """Force a reload of all cached YAML maps."""
        _load_pm_map.cache_clear()


# Module-level singleton
package_map = PackageMapLoader()

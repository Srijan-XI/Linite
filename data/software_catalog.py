"""
Linite - Software Catalog
Defines all installable apps, their packages per distro family, and metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PackageSpec:
    """
    Describes how to install a single application via a specific package manager.

    apt / dnf / pacman / zypper  → list of package names
    snap                         → snap name  (+ classic flag)
    flatpak                      → Flatpak app-id  (+ remote, usually 'flathub')
    script                       → URL of a shell script to download & run
    """
    packages: List[str] = field(default_factory=list)
    snap_classic: bool = False          # used when pm == "snap"
    flatpak_remote: str = "flathub"     # used when pm == "flatpak"
    script_url: str = ""                # used when pm == "script"
    sha256: str = ""                    # expected SHA-256 of downloaded file (script / deb)
    pre_commands: List[str] = field(default_factory=list)   # run before install
    post_commands: List[str] = field(default_factory=list)  # run after install


@dataclass
class SoftwareEntry:
    id: str                         # unique slug
    name: str                       # display name
    description: str
    category: str
    icon: str = "📦"               # emoji fallback icon
    website: str = ""

    # Keyed by package-manager name.
    # Special key "universal" falls back when a specific PM has no entry.
    install_specs: Dict[str, PackageSpec] = field(default_factory=dict)

    # Optional: preferred install method  (apt | dnf | … | snap | flatpak | script)
    # If None, the distro's native PM is tried first, then flatpak, then snap.
    preferred_pm: Optional[str] = None

    def get_spec(self, pm_name: str) -> Optional[PackageSpec]:
        return self.install_specs.get(pm_name) or self.install_specs.get("universal")


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

def _s(packages, **kw) -> PackageSpec:
    """Shortcut to create a PackageSpec."""
    return PackageSpec(packages=packages if isinstance(packages, list) else [packages], **kw)


# ---------------------------------------------------------------------------
# Catalog data is loaded from per-category TOML files under data/catalog/.
# CATALOG, CATALOG_MAP and CATEGORIES are re-exported here so all existing
# import sites continue to work without modification.
# ---------------------------------------------------------------------------
from data.catalog_loader import CATALOG, CATALOG_MAP, CATEGORIES  # noqa: F401, E402

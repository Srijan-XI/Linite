"""
Linite - Profile Manager
Save and load app selections as JSON profiles so you can replay an install set.
"""

import json
from pathlib import Path
from typing import List, Set

PROFILES_DIR = Path.home() / ".config" / "linite" / "profiles"
PROFILE_VERSION = 1


def save_profile(app_ids: Set[str], path: str, name: str = ""):
    """Serialise a set of app IDs to a JSON profile file."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "version": PROFILE_VERSION,
        "name":    name or Path(path).stem,
        "apps":    sorted(app_ids),
    }
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_profile(path: str) -> List[str]:
    """Load app IDs from a JSON profile file. Returns a list of app id strings."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, list):          # bare list format
        return raw
    return raw.get("apps", [])


def list_saved_profiles() -> List[Path]:
    """Return all .json profiles in the default profiles directory."""
    if not PROFILES_DIR.exists():
        return []
    return sorted(PROFILES_DIR.glob("*.json"))

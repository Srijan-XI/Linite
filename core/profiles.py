"""
Linite - Profile Manager
Save and load app selections as JSON profiles so you can replay an install set.

File format (JSON object):
  {
    "version": 1,
    "name": "my-devbox",
    "apps": ["docker", "git", "vscode"]
  }

Legacy YAML profiles (*.yaml / *.yml) are still readable if PyYAML is
installed; newly saved profiles always use .json.
"""

import json
import logging
from pathlib import Path
from typing import List, Set

logger = logging.getLogger(__name__)

PROFILES_DIR    = Path.home() / ".config" / "linite" / "profiles"
PROFILE_VERSION = 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_profile(app_ids: Set[str], path: str, name: str = "") -> None:
    """Serialise a set of app IDs to a JSON profile file."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "version": PROFILE_VERSION,
        "name":    name or Path(path).stem,
        "apps":    sorted(app_ids),
    }
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False),
                          encoding="utf-8")


def load_profile(path: str) -> List[str]:
    """
    Load app IDs from a profile file.
    Accepts both JSON (.json) and legacy YAML (.yaml / .yml) files.
    Returns a list of app-id strings.
    """
    text   = Path(path).read_text(encoding="utf-8")
    suffix = Path(path).suffix.lower()

    if suffix in (".yaml", ".yml"):
        # Legacy YAML — try PyYAML if available
        try:
            import yaml as _yaml  # local — only for legacy file migration
            raw = _yaml.safe_load(text)
        except ImportError:
            logger.warning(
                "PyYAML not installed; cannot load legacy YAML profile %s", path
            )
            return []
    else:
        raw = json.loads(text)

    if isinstance(raw, list):          # bare list format (legacy)
        return raw
    return raw.get("apps", []) if isinstance(raw, dict) else []


def list_saved_profiles() -> List[Path]:
    """
    Return all saved profiles (JSON and legacy YAML) in the default
    profiles directory, sorted by name.
    """
    if not PROFILES_DIR.exists():
        return []
    json_files = sorted(PROFILES_DIR.glob("*.json"))
    yaml_files = sorted(PROFILES_DIR.glob("*.yaml"))
    yml_files  = sorted(PROFILES_DIR.glob("*.yml"))
    return json_files + yaml_files + yml_files  # JSON first (current format)

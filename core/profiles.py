"""
Linite - Profile Manager
Save and load app selections as YAML profiles so you can replay an install set.

File format (YAML mapping):
  version: 1
  name: my-devbox
  apps:
    - docker
    - git
    - vscode

Legacy JSON profiles (*.json) can still be imported and are transparently
read by load_profile(); newly saved profiles always use .yaml.
"""

import json
import logging
from pathlib import Path
from typing import List, Set

import yaml

logger = logging.getLogger(__name__)

PROFILES_DIR    = Path.home() / ".config" / "linite" / "profiles"
PROFILE_VERSION = 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_profile(app_ids: Set[str], path: str, name: str = "") -> None:
    """Serialise a set of app IDs to a YAML profile file."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "version": PROFILE_VERSION,
        "name":    name or Path(path).stem,
        "apps":    sorted(app_ids),
    }
    Path(path).write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def load_profile(path: str) -> List[str]:
    """
    Load app IDs from a profile file.
    Accepts both YAML (.yaml / .yml) and legacy JSON (.json) files.
    Returns a list of app-id strings.
    """
    text = Path(path).read_text(encoding="utf-8")

    # Detect format by extension; fall back to trying YAML then JSON
    suffix = Path(path).suffix.lower()
    if suffix in (".json",):
        raw = json.loads(text)
    else:
        raw = yaml.safe_load(text)

    if isinstance(raw, list):          # bare list format (legacy)
        return raw
    return raw.get("apps", []) if isinstance(raw, dict) else []


def list_saved_profiles() -> List[Path]:
    """
    Return all saved profiles (YAML and legacy JSON) in the default
    profiles directory, sorted by name.
    """
    if not PROFILES_DIR.exists():
        return []
    yaml_files = sorted(PROFILES_DIR.glob("*.yaml"))
    yml_files  = sorted(PROFILES_DIR.glob("*.yml"))
    json_files = sorted(PROFILES_DIR.glob("*.json"))
    return yaml_files + yml_files + json_files

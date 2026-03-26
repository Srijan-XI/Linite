"""
Linite - Install History
Records every install/uninstall attempt to ~/.config/linite/history.json

File format (JSON array of objects):
  [
    {"app_id": "vlc", "app_name": "VLC Media Player",
     "pm_used": "apt", "action": "install",
     "success": true, "timestamp": "2024-07-01T12:34:56.789012"}
  ]

Legacy YAML files (history.yaml) are transparently migrated on first read.
"""

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Set

logger = logging.getLogger(__name__)

_HISTORY_LOCK = threading.Lock()

_CONFIG_DIR   = Path.home() / ".config" / "linite"
HISTORY_FILE  = _CONFIG_DIR / "history.json"
_LEGACY_YAML  = _CONFIG_DIR / "history.yaml"   # auto-migrated on read


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load() -> List[dict]:
    """Load history from JSON, auto-migrating from legacy YAML if needed."""

    # Migrate legacy YAML → JSON once
    if _LEGACY_YAML.exists() and not HISTORY_FILE.exists():
        try:
            import yaml as _yaml  # local import — only used during migration
            raw = _yaml.safe_load(_LEGACY_YAML.read_text(encoding="utf-8"))
            data = raw if isinstance(raw, list) else []
            _save(data)
            _LEGACY_YAML.rename(_LEGACY_YAML.with_suffix(".yaml.bak"))
            logger.info("Migrated history from YAML to JSON (%d entries).", len(data))
        except Exception as exc:
            logger.warning("Could not migrate history.yaml: %s", exc)
            return []

    if HISTORY_FILE.exists():
        try:
            raw = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            return raw if isinstance(raw, list) else []
        except Exception as exc:
            logger.error("Failed to load history.json: %s", exc)
            return []
    return []


def _save(data: List[dict]) -> None:
    """Persist the history list to JSON."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def record(app_id: str, app_name: str, pm_used: str, success: bool,
           action: str = "install") -> None:
    """Append one install/uninstall event to history.json. Thread-safe."""
    with _HISTORY_LOCK:
        data = _load()
        data.append({
            "app_id":    app_id,
            "app_name":  app_name,
            "pm_used":   pm_used,
            "action":    action,        # "install" | "uninstall"
            "success":   success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        _save(data)


def get_installed_ids() -> Set[str]:
    """
    Return the set of app_ids that were successfully installed and not
    subsequently successfully uninstalled.
    """
    installed: Set[str] = set()
    for entry in _load():
        if not entry.get("success"):
            continue
        if entry.get("action") == "install":
            installed.add(entry["app_id"])
        elif entry.get("action") == "uninstall":
            installed.discard(entry["app_id"])
    return installed


def get_all() -> List[dict]:
    """Return the full history list, newest-first."""
    return list(reversed(_load()))


def clear() -> None:
    """Wipe all recorded history."""
    _save([])


def get_last_session_apps(session_window_minutes: int = 60) -> List[dict]:
    """
    Return all apps successfully installed in the most recent session.
    A session is defined as a contiguous block of recent installs (default: 60 minutes).
    
    Returns list of entries (dicts with app_id, app_name, pm_used, action, success, timestamp)
    ordered chronologically (oldest first).
    """
    from datetime import timedelta
    
    data = _load()
    
    # Filter to successful installs, sorted chronologically (oldest first)
    installs = [
        entry for entry in data
        if entry.get("action") == "install" and entry.get("success")
    ]
    
    if not installs:
        return []
    
    # Last install is the most recent
    last_install = installs[-1]
    last_timestamp = datetime.fromisoformat(last_install["timestamp"])
    cutoff = last_timestamp - timedelta(minutes=session_window_minutes)
    
    # Get all installs within the session window
    session_apps = [
        e for e in installs
        if datetime.fromisoformat(e["timestamp"]) >= cutoff
    ]
    
    return session_apps

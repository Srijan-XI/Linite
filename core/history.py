"""
Linite - Install History
Records every install/uninstall attempt to ~/.config/linite/history.json
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Set

HISTORY_FILE = Path.home() / ".config" / "linite" / "history.json"


def _load() -> List[dict]:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save(data: List[dict]):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record(app_id: str, app_name: str, pm_used: str, success: bool, action: str = "install"):
    """Record an install or uninstall event."""
    data = _load()
    data.append({
        "app_id":   app_id,
        "app_name": app_name,
        "pm_used":  pm_used,
        "action":   action,          # "install" | "uninstall"
        "success":  success,
        "timestamp": datetime.now().isoformat(),
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
    """Return the full history list, newest first."""
    return list(reversed(_load()))


def clear():
    _save([])

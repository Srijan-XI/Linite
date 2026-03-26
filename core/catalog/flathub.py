"""Flathub app metadata helpers with local cache support."""

from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from time import time
from typing import Any

_CACHE_TTL_SECONDS = 24 * 60 * 60
_FLATHUB_URL = "https://flathub.org/api/v2/appstream/{app_id}"


def _cache_dir() -> Path:
    return Path.home() / ".cache" / "linite" / "flathub"


def _cache_path(app_id: str) -> Path:
    safe = app_id.replace("/", "_")
    return _cache_dir() / f"{safe}.json"


def _strip_html(raw: str) -> str:
    text = raw.replace("</li>", "\n").replace("<li>", "- ")
    text = re.sub(r"<br\\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _parse_latest_release(payload: dict[str, Any]) -> dict[str, str]:
    releases = payload.get("releases") or []
    if not isinstance(releases, list):
        releases = []

    def _release_key(item: Any) -> int:
        if not isinstance(item, dict):
            return 0
        try:
            return int(item.get("timestamp") or 0)
        except (TypeError, ValueError):
            return 0

    ordered = sorted(
        [r for r in releases if isinstance(r, dict)],
        key=_release_key,
        reverse=True,
    )

    release = ordered[0] if ordered else {}
    version = str(release.get("version") or "Unknown")
    raw_notes = str(release.get("description") or "").strip()
    notes = _strip_html(raw_notes) if raw_notes else "No release notes available."
    url = str(release.get("url") or "").strip()

    return {
        "version": version,
        "notes": notes,
        "url": url,
    }


def load_flathub_metadata(app_id: str, timeout_sec: int = 8) -> dict[str, str]:
    """
    Load Flathub metadata for app_id with local cache fallback.

    Returns keys:
      - version
      - notes
      - url
      - source (network | cache | cache-stale)
    """
    cache_file = _cache_path(app_id)

    if cache_file.exists():
        age = time() - cache_file.stat().st_mtime
        if age <= _CACHE_TTL_SECONDS:
            payload = json.loads(cache_file.read_text(encoding="utf-8"))
            parsed = _parse_latest_release(payload)
            parsed["source"] = "cache"
            return parsed

    try:
        url = _FLATHUB_URL.format(app_id=app_id)
        with urllib.request.urlopen(url, timeout=timeout_sec) as response:
            payload = json.loads(response.read().decode("utf-8"))
        _cache_dir().mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(payload), encoding="utf-8")
        parsed = _parse_latest_release(payload)
        parsed["source"] = "network"
        return parsed
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        if cache_file.exists():
            payload = json.loads(cache_file.read_text(encoding="utf-8"))
            parsed = _parse_latest_release(payload)
            parsed["source"] = "cache-stale"
            return parsed
        raise

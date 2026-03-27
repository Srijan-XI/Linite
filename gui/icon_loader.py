"""
Linite - SVG Icon Loader
Loads SVG files from the assets directory and renders them as Tkinter-compatible
PhotoImage objects, with graceful fallback to emoji text if libraries are unavailable.

Usage:
    from gui.icon_loader import load_svg_icon, ICON_SIZE_CARD, ICON_SIZE_DETAIL

    photo = load_svg_icon("assets/firefox/firefox-dark.svg", size=ICON_SIZE_CARD)
    if photo:
        label = tk.Label(parent, image=photo)
        label.image = photo   # keep reference alive!
    else:
        label = tk.Label(parent, text="🦊", font=("", 18))
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Dict, Optional, Tuple
import tkinter as tk

logger = logging.getLogger(__name__)

# Icon sizes (pixels, square)
ICON_SIZE_CARD   = 32   # software list cards
ICON_SIZE_DETAIL = 48   # app detail popup header

# Internal LRU-style cache: (svg_path, size) → PhotoImage | None
_icon_cache: Dict[Tuple[str, int], Optional[object]] = {}
_cache_lock = threading.Lock()

# Resolve the root assets directory relative to this file  (gui/../assets)
_ASSETS_ROOT = Path(__file__).resolve().parents[1] / "assets"

# --------------------------------------------------------------------------- #
# Availability flags (tested once at import time)
# --------------------------------------------------------------------------- #
try:
    from PIL import Image, ImageTk          # type: ignore
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

try:
    import cairosvg                          # type: ignore
    _CAIRO_AVAILABLE = True
except ImportError:
    _CAIRO_AVAILABLE = False

try:
    import io
    _IO_AVAILABLE = True
except ImportError:
    _IO_AVAILABLE = False


def _render_svg_to_photoimage(svg_path: Path, size: int) -> Optional[object]:
    """
    Rasterise *svg_path* to a `size × size` Tkinter PhotoImage.

    Strategy:
      1. cairosvg  + Pillow  (best quality, anti-aliased)
      2. Pillow + RSVG via librsvg binding  (rarely available)
      3. Return None  (caller falls back to emoji)
    """
    if not svg_path.exists():
        return None

    if _CAIRO_AVAILABLE and _PIL_AVAILABLE:
        try:
            import io
            import cairosvg
            from PIL import Image, ImageTk
            png_bytes = cairosvg.svg2png(
                url=str(svg_path),
                output_width=size,
                output_height=size,
            )
            img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            return ImageTk.PhotoImage(img)
        except Exception as exc:
            logger.debug(f"cairosvg render failed for {svg_path}: {exc}")

    return None


def load_svg_icon(svg_relative_path: str, size: int = ICON_SIZE_CARD) -> Optional[object]:
    """
    Load an SVG icon from `assets/<svg_relative_path>` and return a
    Tkinter-compatible PhotoImage (or None on failure / missing libraries).

    Results are cached — the same svg+size returns the same object.
    The caller **must** keep a reference to prevent garbage collection.

    Args:
        svg_relative_path: Path relative to the project `assets/` directory,
                           e.g. ``"firefox/firefox-dark.svg"``.
        size:              Target side length in pixels (default: ICON_SIZE_CARD).
    """
    if not svg_relative_path:
        return None

    cache_key = (svg_relative_path, size)
    with _cache_lock:
        if cache_key in _icon_cache:
            return _icon_cache[cache_key]

    svg_path = _ASSETS_ROOT / svg_relative_path
    result = _render_svg_to_photoimage(svg_path, size)

    with _cache_lock:
        _icon_cache[cache_key] = result

    return result


def is_svg_rendering_available() -> bool:
    """Return True if both cairosvg and Pillow are importable."""
    return _CAIRO_AVAILABLE and _PIL_AVAILABLE


def get_svg_path_for_app(app_id: str, theme: str = "dark") -> str:
    """
    Auto-discover the best SVG for a given app ID and theme variant.

    Tries (in order):
      1. <app_id>/<app_id>-<theme>.svg
      2. <app_id>/<app_id>-auto.svg
      3. <app_id>/<app_id>.svg
      4. <app_id>.svg  (top-level file)

    Returns the relative path string, or "" if nothing is found.
    """
    # Some directories have non-standard names; map them here.
    _DIR_OVERRIDES: Dict[str, str] = {
        "wireshark":       "wireshare",
        "obsidian":        "obsidan",
        "libreoffice":     "office",
        "librewolf":       "office",
        "burpsuite":       "burp",
        "google-chrome":   "chromium",
        "microsoft-edge":  "edge",
        "protonvpn":       "protonvpn",
        "signal-desktop":  "signal",
        "tor-browser":     "tor",
        "openjdk":         "java",
        "openjdk-11":      "java",
        "openjdk-17":      "java",
        "openjdk-21":      "java",
        "openjdk-8":       "java",
        "vscodium":        "vscodium",
        "flameshot":       "flameshot",
        "qemu-kvm":        "qemu",
        "ffmpeg":          "ffmpeg",
        "github-desktop":  "github",
    }

    _FILE_OVERRIDES: Dict[str, str] = {
        "libreoffice":     "office/libreoffice",
        "librewolf":       "office/librewolf",
        "google-chrome":   "chromium/chrome",
        "microsoft-edge":  "edge/edge",
        "burpsuite":       "burp/burpsuite",
        "signal-desktop":  "signal",
        "tor-browser":     "tor/tor",
        "protonvpn":       "protonvpn/proton",
        "wireshark":       "wireshare/wireshark",
        "obsidian":        "obsidan/obsidian",
        "qemu-kvm":        "qemu/qemu",
        "github-desktop":  "github/githubdesktop",
        "openjdk":         "java/java",
        "openjdk-11":      "java/java",
        "openjdk-17":      "java/java",
        "openjdk-21":      "java/java",
        "openjdk-8":       "java/java",
    }

    # Build candidate paths
    base = _FILE_OVERRIDES.get(app_id)
    if not base:
        folder = _DIR_OVERRIDES.get(app_id, app_id)
        base = f"{folder}/{app_id}"

    for suffix in (f"-{theme}", "-auto", ""):
        candidate = f"{base}{suffix}.svg"
        if (_ASSETS_ROOT / candidate).exists():
            return candidate

    # Final fallback: top-level <app_id>.svg
    top_level = f"{app_id}.svg"
    if (_ASSETS_ROOT / top_level).exists():
        return top_level

    # Try signal / steam / telegram / docker / flameshot top-level
    for name in (app_id, app_id.replace("-", ""), app_id.split("-")[0]):
        top = f"{name}.svg"
        if (_ASSETS_ROOT / top).exists():
            return top

    return ""

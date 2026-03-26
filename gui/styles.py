"""
Linite - GUI Style Constants
Dark-mode and Light-mode color palettes for Tkinter.

Usage:
    from gui import styles as st

    # Apply a palette before building the UI:
    st.set_theme("light")   # or "dark" (default)

    # All widgets reference st.<NAME> — they update automatically when
    # set_theme() is called *before* window construction.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Palette definitions
# ---------------------------------------------------------------------------

_DARK = {
    "BG_DARK":        "#1e1e2e",   # main background
    "BG_MEDIUM":      "#2a2a3d",   # sidebar / card background
    "BG_LIGHT":       "#313145",   # hover / selected row
    "CARD_SELECTED":  "#2e2e50",   # card bg when checked
    "ACCENT":         "#7c6af7",   # purple accent (checkboxes, buttons)
    "ACCENT_HOVER":   "#9b8df9",
    "ACCENT_DIM":     "#4a3fa0",   # muted accent (badges, counts)
    "SUCCESS":        "#50fa7b",
    "SUCCESS_BG":     "#163a28",   # installed badge background
    "ERROR":          "#ff5555",
    "ERROR_BG":       "#3a1010",   # error badge background
    "WARNING":        "#f1fa8c",
    "TEXT_PRIMARY":   "#cdd6f4",
    "TEXT_SECONDARY": "#a6adc8",
    "TEXT_MUTED":     "#6c7086",
    "BORDER":         "#45475a",
    "DIVIDER":        "#55576a",   # stronger divider for button groups
    "TOOLTIP_BG":     "#3c3c58",
    "TOOLTIP_FG":     "#e0e0f8",
}

_LIGHT = {
    "BG_DARK":        "#f4f4f8",   # main background
    "BG_MEDIUM":      "#e8e8f0",   # sidebar / card background
    "BG_LIGHT":       "#d8d8ea",   # hover / selected row
    "CARD_SELECTED":  "#dcdcf0",   # card bg when checked
    "ACCENT":         "#5a44d8",   # purple accent
    "ACCENT_HOVER":   "#7060e8",
    "ACCENT_DIM":     "#b0a8f0",   # muted accent
    "SUCCESS":        "#1a8a45",
    "SUCCESS_BG":     "#d0f0dc",   # installed badge background
    "ERROR":          "#cc2222",
    "ERROR_BG":       "#ffe0e0",   # error badge background
    "WARNING":        "#b07800",
    "TEXT_PRIMARY":   "#1a1a2e",
    "TEXT_SECONDARY": "#3a3a5c",
    "TEXT_MUTED":     "#7070a0",
    "BORDER":         "#c0c0d8",
    "DIVIDER":        "#b0b0cc",
    "TOOLTIP_BG":     "#e0e0f0",
    "TOOLTIP_FG":     "#1a1a2e",
}

# ---------------------------------------------------------------------------
# Active palette (module-level mutable state — set before window is built)
# ---------------------------------------------------------------------------

_active_palette: dict[str, str] = dict(_DARK)
_current_theme: str = "dark"


def set_theme(theme: str) -> None:
    """Switch the active palette.  Call before constructing any widgets.

    Args:
        theme: ``"dark"`` (default) or ``"light"``.
    """
    global _active_palette, _current_theme
    _current_theme = theme.lower()
    _active_palette = dict(_DARK if _current_theme == "dark" else _LIGHT)


def current_theme() -> str:
    """Return the name of the current theme: ``"dark"`` or ``"light"``."""
    return _current_theme


# ---------------------------------------------------------------------------
# Colour accessors (delegating to the active palette)
# ---------------------------------------------------------------------------
# These are defined as module attributes so existing code that does
#   `from gui import styles as st` and then uses `st.BG_DARK` keeps working.
# They are updated by _refresh_module_attrs() after any set_theme() call.

def _refresh_module_attrs() -> None:
    import sys
    mod = sys.modules[__name__]
    for name, value in _active_palette.items():
        setattr(mod, name, value)


# Expose attributes with their dark-mode defaults initially
BG_DARK:        str = _DARK["BG_DARK"]
BG_MEDIUM:      str = _DARK["BG_MEDIUM"]
BG_LIGHT:       str = _DARK["BG_LIGHT"]
CARD_SELECTED:  str = _DARK["CARD_SELECTED"]
ACCENT:         str = _DARK["ACCENT"]
ACCENT_HOVER:   str = _DARK["ACCENT_HOVER"]
ACCENT_DIM:     str = _DARK["ACCENT_DIM"]
SUCCESS:        str = _DARK["SUCCESS"]
SUCCESS_BG:     str = _DARK["SUCCESS_BG"]
ERROR:          str = _DARK["ERROR"]
ERROR_BG:       str = _DARK["ERROR_BG"]
WARNING:        str = _DARK["WARNING"]
TEXT_PRIMARY:   str = _DARK["TEXT_PRIMARY"]
TEXT_SECONDARY: str = _DARK["TEXT_SECONDARY"]
TEXT_MUTED:     str = _DARK["TEXT_MUTED"]
BORDER:         str = _DARK["BORDER"]
DIVIDER:        str = _DARK["DIVIDER"]
TOOLTIP_BG:     str = _DARK["TOOLTIP_BG"]
TOOLTIP_FG:     str = _DARK["TOOLTIP_FG"]


# ── Fonts ─────────────────────────────────────────────────────────────────

FONT_FAMILY   = "Segoe UI"   # falls back to system default
FONT_SMALL    = (FONT_FAMILY, 9)
FONT_NORMAL   = (FONT_FAMILY, 10)
FONT_MEDIUM   = (FONT_FAMILY, 11)
FONT_LARGE    = (FONT_FAMILY, 13, "bold")
FONT_TITLE    = (FONT_FAMILY, 16, "bold")

# ── Dimensions ────────────────────────────────────────────────────────────

WINDOW_W      = 1080
WINDOW_H      = 700
SIDEBAR_W     = 192
PADDING       = 12
CARD_RADIUS   = 8      # cosmetic only (not native in Tkinter)
BTN_PADX      = 18
BTN_PADY      = 7


# ── Tooltip helper ────────────────────────────────────────────────────────

import tkinter as tk  # noqa: E402 (import at end of style module is fine)


class Tooltip:
    """
    Simple hover tooltip attached to any Tkinter widget.
    Usage: Tooltip(widget, "Your hint text")
    """

    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        self._widget = widget
        self._text   = text
        self._delay  = delay
        self._tw: tk.Toplevel | None = None
        self._after_id: str | None  = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self._widget.after(self._delay, self._show)

    def _cancel(self):
        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self):
        if self._tw:
            return
        x = self._widget.winfo_rootx() + 8
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tw = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            tw, text=self._text, background=TOOLTIP_BG, foreground=TOOLTIP_FG,
            font=FONT_SMALL, relief="flat", padx=8, pady=4,
        )
        lbl.pack()

    def _hide(self, _event=None):
        self._cancel()
        if self._tw:
            self._tw.destroy()
            self._tw = None

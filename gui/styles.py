"""
Linite - GUI Style Constants
Dark-mode color scheme and font definitions for Tkinter.
"""

# ── Palette ───────────────────────────────────────────────────────────────

BG_DARK        = "#1e1e2e"   # main background
BG_MEDIUM      = "#2a2a3d"   # sidebar / card background
BG_LIGHT       = "#313145"   # hover / selected row
CARD_SELECTED  = "#2e2e50"   # card bg when checked
ACCENT         = "#7c6af7"   # purple accent (checkboxes, buttons)
ACCENT_HOVER   = "#9b8df9"
ACCENT_DIM     = "#4a3fa0"   # muted accent (badges, counts)
SUCCESS        = "#50fa7b"
SUCCESS_BG     = "#163a28"   # installed badge background
ERROR          = "#ff5555"
ERROR_BG       = "#3a1010"   # error badge background
WARNING        = "#f1fa8c"
TEXT_PRIMARY   = "#cdd6f4"
TEXT_SECONDARY = "#a6adc8"
TEXT_MUTED     = "#6c7086"
BORDER         = "#45475a"
DIVIDER        = "#55576a"   # stronger divider for button groups
TOOLTIP_BG     = "#3c3c58"
TOOLTIP_FG     = "#e0e0f8"

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

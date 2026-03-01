"""
Linite - GUI Style Constants
Dark-mode color scheme and font definitions for Tkinter.
"""

# ── Palette ───────────────────────────────────────────────────────────────

BG_DARK       = "#1e1e2e"   # main background
BG_MEDIUM     = "#2a2a3d"   # sidebar / card background
BG_LIGHT      = "#313145"   # hover / selected row
ACCENT        = "#7c6af7"   # purple accent (checkboxes, buttons)
ACCENT_HOVER  = "#9b8df9"
SUCCESS       = "#50fa7b"
ERROR         = "#ff5555"
WARNING       = "#f1fa8c"
TEXT_PRIMARY  = "#cdd6f4"
TEXT_SECONDARY = "#a6adc8"
TEXT_MUTED    = "#6c7086"
BORDER        = "#45475a"

# ── Fonts ─────────────────────────────────────────────────────────────────

FONT_FAMILY   = "Segoe UI"   # falls back to system default
FONT_SMALL    = (FONT_FAMILY, 9)
FONT_NORMAL   = (FONT_FAMILY, 10)
FONT_MEDIUM   = (FONT_FAMILY, 11)
FONT_LARGE    = (FONT_FAMILY, 13, "bold")
FONT_TITLE    = (FONT_FAMILY, 16, "bold")

# ── Dimensions ────────────────────────────────────────────────────────────

WINDOW_W      = 1050
WINDOW_H      = 680
SIDEBAR_W     = 180
PADDING       = 12
CARD_RADIUS   = 8      # cosmetic only (not native in Tkinter)
BTN_PADX      = 20
BTN_PADY      = 8

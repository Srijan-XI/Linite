"""
Linite - Quick-Start Preset Picker
A modal dialog that lets the user choose a pre-defined app bundle (preset)
and apply it to the software panel with a single click.

Layout
------
┌─────────────────────────────────────────────┐
│  Quick-Start Profiles               [✕ Close]│
│  Choose a profile to pre-select a curated   │
│  set of applications for your use case.     │
├──────────┬──────────────────────────────────┤
│ [Card 1] │                                  │
│ [Card 2] │   Detail panel (right)           │
│ [Card 3] │   • icon + name + tagline        │
│ [Card 4] │   • description paragraph        │
│ [Card 5] │   • scrollable app list          │
│ [Card 6] │   • [Apply] button               │
└──────────┴──────────────────────────────────┘
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Set

from data.presets import Preset, PRESETS, PRESETS_MAP
from data.software_catalog import CATALOG_MAP
from gui import styles as st

# Accent colours per preset card when hovered / selected
_CARD_W = 190      # fixed width of the left card list


class PresetPickerDialog(tk.Toplevel):
    """
    Modal window for choosing a Quick-Start preset.

    :param parent:     Parent Tk widget (the main window).
    :param on_apply:   Callback(app_ids: Set[str]) invoked when the user
                       clicks 'Apply'.  The callback receives the set of
                       valid catalog IDs that the preset selected.
    """

    def __init__(self, parent: tk.Widget, on_apply: Callable[[Set[str]], None]):
        super().__init__(parent)
        self.title("Quick-Start Profiles")
        self.configure(bg=st.BG_DARK)
        self.resizable(True, True)
        self.minsize(760, 520)
        self.grab_set()     # modal

        self._on_apply  = on_apply
        self._selected: Optional[Preset] = None

        self._build()
        self._center(parent)

        # Pre-select first preset
        if PRESETS:
            self._select_preset(PRESETS[0])

    # ── Layout ────────────────────────────────────────────────────────────

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=st.BG_MEDIUM)
        hdr.pack(fill="x")

        tk.Label(
            hdr, text="⚡  Quick-Start Profiles",
            bg=st.BG_MEDIUM, fg=st.TEXT_PRIMARY, font=st.FONT_TITLE,
            padx=st.PADDING, pady=12,
        ).pack(side="left")

        tk.Label(
            hdr,
            text="Select a profile to pre-select a curated app bundle",
            bg=st.BG_MEDIUM, fg=st.TEXT_MUTED, font=st.FONT_SMALL,
        ).pack(side="left", pady=12)

        tk.Button(
            hdr, text="✕",
            bg=st.BG_MEDIUM, fg=st.TEXT_MUTED, font=st.FONT_MEDIUM,
            relief="flat", bd=0, padx=10, cursor="hand2",
            activebackground=st.BG_LIGHT, activeforeground=st.TEXT_PRIMARY,
            command=self.destroy,
        ).pack(side="right", padx=st.PADDING)

        tk.Frame(self, bg=st.BORDER, height=1).pack(fill="x")

        # ── Body: left cards + right detail ───────────────────────────────
        body = tk.Frame(self, bg=st.BG_DARK)
        body.pack(fill="both", expand=True)

        # Left card list
        left = tk.Frame(body, bg=st.BG_MEDIUM, width=_CARD_W)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(
            left, text="PROFILES",
            bg=st.BG_MEDIUM, fg=st.TEXT_MUTED,
            font=(st.FONT_FAMILY, 8, "bold"),
            anchor="w", padx=st.PADDING, pady=8,
        ).pack(fill="x")
        tk.Frame(left, bg=st.BORDER, height=1).pack(fill="x")

        self._card_frames: dict[str, tk.Frame]  = {}
        self._card_labels: dict[str, tk.Label]  = {}
        self._card_stripes: dict[str, tk.Frame] = {}

        for preset in PRESETS:
            self._make_card(left, preset)

        tk.Frame(body, bg=st.BORDER, width=1).pack(side="left", fill="y")

        # Right detail panel
        self._detail = tk.Frame(body, bg=st.BG_DARK)
        self._detail.pack(side="left", fill="both", expand=True,
                          padx=st.PADDING * 2, pady=st.PADDING)

    def _make_card(self, parent: tk.Widget, preset: Preset):
        """Create one row in the left sidebar for a preset."""
        row = tk.Frame(parent, bg=st.BG_MEDIUM, cursor="hand2")
        row.pack(fill="x")
        self._card_frames[preset.id] = row

        stripe = tk.Frame(row, bg=st.BG_MEDIUM, width=4)
        stripe.pack(side="left", fill="y")
        stripe.pack_propagate(False)
        self._card_stripes[preset.id] = stripe

        inner = tk.Frame(row, bg=st.BG_MEDIUM, padx=8, pady=10)
        inner.pack(side="left", fill="x", expand=True)

        icon_lbl = tk.Label(
            inner, text=preset.icon + "  " + preset.name,
            bg=st.BG_MEDIUM, fg=st.TEXT_PRIMARY,
            font=st.FONT_MEDIUM, anchor="w",
        )
        icon_lbl.pack(anchor="w")

        tag_lbl = tk.Label(
            inner, text=preset.tagline,
            bg=st.BG_MEDIUM, fg=st.TEXT_MUTED,
            font=st.FONT_SMALL, anchor="w",
        )
        tag_lbl.pack(anchor="w")
        self._card_labels[preset.id] = icon_lbl

        # Bind click + hover for all child widgets
        for w in (row, stripe, inner, icon_lbl, tag_lbl):
            w.bind("<Button-1>", lambda _e, p=preset: self._select_preset(p))
            w.bind("<Enter>",    lambda _e, p=preset: self._card_hover(p, True))
            w.bind("<Leave>",    lambda _e, p=preset: self._card_hover(p, False))

    # ── Selection logic ───────────────────────────────────────────────────

    def _select_preset(self, preset: Preset):
        # Deselect previous
        if self._selected:
            prev = self._selected
            self._set_card_active(prev, False)

        self._selected = preset
        self._set_card_active(preset, True)
        self._render_detail(preset)

    def _set_card_active(self, preset: Preset, active: bool):
        row    = self._card_frames[preset.id]
        stripe = self._card_stripes[preset.id]
        bg     = st.BG_LIGHT if active else st.BG_MEDIUM
        stripe_col = preset.color if active else st.BG_MEDIUM
        row.config(bg=bg)
        stripe.config(bg=stripe_col)
        for child in row.winfo_children():
            try:
                child.config(bg=bg)
                for grandchild in child.winfo_children():
                    grandchild.config(bg=bg)
            except tk.TclError:
                pass

    def _card_hover(self, preset: Preset, entering: bool):
        if self._selected and self._selected.id == preset.id:
            return
        bg = st.BG_LIGHT if entering else st.BG_MEDIUM
        row = self._card_frames[preset.id]
        row.config(bg=bg)
        for child in row.winfo_children():
            try:
                child.config(bg=bg)
                for grandchild in child.winfo_children():
                    grandchild.config(bg=bg)
            except tk.TclError:
                pass

    # ── Detail panel ─────────────────────────────────────────────────────

    def _render_detail(self, preset: Preset):
        """(Re)build the right-hand detail panel for the given preset."""
        for w in self._detail.winfo_children():
            w.destroy()

        # ── Preset header ─────────────────────────────────────────────────
        hdr = tk.Frame(self._detail, bg=st.BG_DARK)
        hdr.pack(fill="x", pady=(0, st.PADDING))

        # Coloured icon badge
        badge = tk.Frame(hdr, bg=preset.color, padx=6, pady=4)
        badge.pack(side="left", padx=(0, 12))
        badge.pack_propagate(False)
        badge.config(width=56, height=56)
        tk.Label(
            badge, text=preset.icon,
            bg=preset.color, font=(st.FONT_FAMILY, 26),
        ).pack(expand=True)

        title_col = tk.Frame(hdr, bg=st.BG_DARK)
        title_col.pack(side="left", fill="x", expand=True)

        tk.Label(
            title_col, text=preset.name,
            bg=st.BG_DARK, fg=st.TEXT_PRIMARY, font=st.FONT_LARGE, anchor="w",
        ).pack(anchor="w")
        tk.Label(
            title_col, text=preset.tagline,
            bg=st.BG_DARK, fg=preset.color, font=st.FONT_SMALL, anchor="w",
        ).pack(anchor="w")

        # App count badge
        valid_ids = [i for i in preset.app_ids if i in CATALOG_MAP]
        count_lbl = tk.Label(
            title_col,
            text=f"{len(valid_ids)} applications",
            bg=st.ACCENT_DIM, fg=st.TEXT_SECONDARY,
            font=st.FONT_SMALL, padx=8, pady=2,
        )
        count_lbl.pack(anchor="w", pady=(4, 0))

        tk.Frame(self._detail, bg=st.BORDER, height=1).pack(fill="x", pady=(0, st.PADDING))

        # ── Description ───────────────────────────────────────────────────
        tk.Label(
            self._detail, text=preset.description,
            bg=st.BG_DARK, fg=st.TEXT_SECONDARY, font=st.FONT_NORMAL,
            anchor="w", justify="left", wraplength=480,
        ).pack(anchor="w", pady=(0, st.PADDING))

        # ── Application list (scrollable) ─────────────────────────────────
        tk.Label(
            self._detail, text="INCLUDED APPLICATIONS",
            bg=st.BG_DARK, fg=st.TEXT_MUTED,
            font=(st.FONT_FAMILY, 8, "bold"), anchor="w",
        ).pack(anchor="w", pady=(0, 6))

        list_outer = tk.Frame(self._detail, bg=st.BG_MEDIUM,
                              highlightbackground=st.BORDER, highlightthickness=1)
        list_outer.pack(fill="both", expand=True, pady=(0, st.PADDING))

        canvas = tk.Canvas(list_outer, bg=st.BG_MEDIUM, highlightthickness=0, bd=0)
        vsb    = ttk.Scrollbar(list_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=st.BG_MEDIUM)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>",
                   lambda _e: canvas.config(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        for app_id in preset.app_ids:
            entry = CATALOG_MAP.get(app_id)
            if entry is None:
                continue   # skip IDs not in catalog
            row = tk.Frame(inner, bg=st.BG_MEDIUM)
            row.pack(fill="x", padx=8, pady=2)

            # Coloured left dot
            dot = tk.Frame(row, bg=preset.color, width=6, height=6)
            dot.pack(side="left", padx=(0, 8), pady=8)
            dot.pack_propagate(False)

            tk.Label(
                row, text=f"{entry.icon}  {entry.name}",
                bg=st.BG_MEDIUM, fg=st.TEXT_PRIMARY,
                font=st.FONT_NORMAL, anchor="w",
            ).pack(side="left")

            tk.Label(
                row, text=entry.description,
                bg=st.BG_MEDIUM, fg=st.TEXT_MUTED,
                font=st.FONT_SMALL, anchor="w",
            ).pack(side="left", padx=(8, 0))

        # ── Action buttons ────────────────────────────────────────────────
        btn_row = tk.Frame(self._detail, bg=st.BG_DARK)
        btn_row.pack(fill="x", pady=(0, 4))

        tk.Button(
            btn_row, text="Close",
            bg=st.BG_LIGHT, fg=st.TEXT_PRIMARY, font=st.FONT_NORMAL,
            relief="flat", bd=0, padx=16, pady=7, cursor="hand2",
            activebackground=st.BG_MEDIUM,
            command=self.destroy,
        ).pack(side="right", padx=(8, 0))

        apply_btn = tk.Button(
            btn_row,
            text=f'\u2b07  Apply "{preset.name}" ({len(valid_ids)} apps)',
            bg=preset.color, fg="#ffffff", font=st.FONT_MEDIUM,
            relief="flat", bd=0, padx=18, pady=7, cursor="hand2",
            activebackground=preset.color, activeforeground="#ffffff",
            command=lambda p=preset: self._apply(p),
        )
        apply_btn.pack(side="right")

        # Hover dimming on apply button
        def _dim(entering: bool, btn=apply_btn, col=preset.color):
            import colorsys, struct
            r, g, b = struct.unpack("BBB", bytes.fromhex(col.lstrip("#")))
            factor = 0.85 if entering else 1.0
            nr, ng, nb = int(r*factor), int(g*factor), int(b*factor)
            btn.config(bg=f"#{nr:02x}{ng:02x}{nb:02x}")
        apply_btn.bind("<Enter>", lambda _e: _dim(True))
        apply_btn.bind("<Leave>", lambda _e: _dim(False))

    # ── Apply ─────────────────────────────────────────────────────────────

    def _apply(self, preset: Preset):
        valid_ids: Set[str] = {i for i in preset.app_ids if i in CATALOG_MAP}
        self._on_apply(valid_ids)
        self.destroy()

    # ── Utility ───────────────────────────────────────────────────────────

    def _center(self, parent: tk.Widget):
        self.update_idletasks()
        pw = parent.winfo_x() + parent.winfo_width()  // 2
        ph = parent.winfo_y() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{pw - w//2}+{ph - h//2}")

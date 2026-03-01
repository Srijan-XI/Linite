"""
Linite - Software Selection Panel
Scrollable grid of app cards with:
  • Real-time search bar
  • Installed-state badge (detected from history)
  • Double-click / right-click to open detail popup
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional, Set

from data.software_catalog import SoftwareEntry
from gui import styles as st


class SoftwarePanel(tk.Frame):
    """Main content area showing software cards with checkboxes."""

    def __init__(
        self,
        parent,
        entries: List[SoftwareEntry],
        on_detail: Optional[Callable[[SoftwareEntry], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, bg=st.BG_DARK, **kwargs)
        self._all_entries       = entries
        self._visible_entries:  List[SoftwareEntry] = list(entries)
        self._checked:          Dict[str, tk.BooleanVar] = {}
        self._installed_ids:    Set[str] = set()
        self._on_detail         = on_detail
        self._current_category  = "All"
        self._search_text       = ""

        # ── Search bar ───────────────────────────────────────────────────
        search_bar = tk.Frame(self, bg=st.BG_DARK)
        search_bar.pack(fill="x", padx=st.PADDING, pady=(st.PADDING, 2))

        search_icon = tk.Label(
            search_bar, text="🔍", bg=st.BG_DARK,
            fg=st.TEXT_MUTED, font=st.FONT_NORMAL,
        )
        search_icon.pack(side="left", padx=(0, 6))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_change)

        search_entry = tk.Entry(
            search_bar,
            textvariable=self._search_var,
            bg=st.BG_MEDIUM,
            fg=st.TEXT_PRIMARY,
            insertbackground=st.TEXT_PRIMARY,
            font=st.FONT_NORMAL,
            relief="flat",
            bd=0,
        )
        search_entry.pack(side="left", fill="x", expand=True, ipady=5, ipadx=6)

        clear_btn = tk.Label(
            search_bar, text="✕", bg=st.BG_DARK,
            fg=st.TEXT_MUTED, font=st.FONT_SMALL, cursor="hand2",
        )
        clear_btn.pack(side="left", padx=(4, 0))
        clear_btn.bind("<Button-1>", lambda e: self._search_var.set(""))

        # ── Header bar ───────────────────────────────────────────────────
        header = tk.Frame(self, bg=st.BG_DARK)
        header.pack(fill="x", padx=st.PADDING, pady=(4, 4))

        self._count_label = tk.Label(
            header, text="", bg=st.BG_DARK,
            fg=st.TEXT_SECONDARY, font=st.FONT_SMALL,
        )
        self._count_label.pack(side="left")

        da_btn = tk.Label(
            header, text="Deselect All", bg=st.BG_DARK,
            fg=st.TEXT_MUTED, font=st.FONT_SMALL, cursor="hand2",
        )
        da_btn.pack(side="right", padx=(0, 8))
        da_btn.bind("<Button-1>", lambda e: self._select_all(False))

        sa_btn = tk.Label(
            header, text="Select All", bg=st.BG_DARK,
            fg=st.ACCENT, font=st.FONT_SMALL, cursor="hand2",
        )
        sa_btn.pack(side="right", padx=(0, 8))
        sa_btn.bind("<Button-1>", lambda e: self._select_all(True))

        # ── Scrollable canvas ────────────────────────────────────────────
        container = tk.Frame(self, bg=st.BG_DARK)
        container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(container, bg=st.BG_DARK, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg=st.BG_DARK)
        self._inner_id = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>",   self._on_mousewheel)
        self._canvas.bind_all("<Button-5>",   self._on_mousewheel)

        # Initialise BooleanVars and draw
        for entry in self._all_entries:
            self._checked[entry.id] = tk.BooleanVar(value=False)

        self._render()

    # ── Public API ────────────────────────────────────────────────────────

    def filter_by_category(self, category: str):
        self._current_category = category
        self._apply_filters()

    def set_installed_ids(self, ids: Set[str]):
        """Mark which app IDs are already installed (called from background thread via after())."""
        self._installed_ids = ids
        self._render()

    def get_selected(self) -> List[SoftwareEntry]:
        return [e for e in self._all_entries if self._checked[e.id].get()]

    def get_selected_ids(self) -> Set[str]:
        return {e.id for e in self._all_entries if self._checked[e.id].get()}

    def set_selected_ids(self, ids: Set[str]):
        """Check exactly the given ids (used for profile import)."""
        for entry in self._all_entries:
            self._checked[entry.id].set(entry.id in ids)
        self._on_check_change()

    # ── Filtering logic ───────────────────────────────────────────────────

    def _on_search_change(self, *_):
        self._search_text = self._search_var.get().lower().strip()
        self._apply_filters()

    def _apply_filters(self):
        entries = self._all_entries

        # Category filter
        if self._current_category != "All":
            entries = [e for e in entries if e.category == self._current_category]

        # Search filter
        if self._search_text:
            entries = [
                e for e in entries
                if self._search_text in e.name.lower()
                or self._search_text in e.description.lower()
                or self._search_text in e.category.lower()
                or self._search_text in e.id.lower()
            ]

        self._visible_entries = entries
        self._render()

    # ── Rendering ─────────────────────────────────────────────────────────

    def _render(self):
        for widget in self._inner.winfo_children():
            widget.destroy()

        count    = len(self._visible_entries)
        selected = sum(1 for e in self._visible_entries if self._checked[e.id].get())
        self._count_label.config(text=f"{count} apps  |  {selected} selected")

        for entry in self._visible_entries:
            self._make_card(entry)

        self._inner.update_idletasks()
        self._canvas.config(scrollregion=self._canvas.bbox("all"))

    def _make_card(self, entry: SoftwareEntry):
        var        = self._checked[entry.id]
        installed  = entry.id in self._installed_ids
        card_bg    = st.BG_MEDIUM

        card = tk.Frame(
            self._inner, bg=card_bg, pady=8, padx=10,
            relief="flat", bd=0, cursor="hand2",
        )
        card.pack(fill="x", padx=st.PADDING, pady=4)

        card.bind("<Button-1>",        lambda e, v=var: self._toggle(v))
        card.bind("<Double-Button-1>", lambda e, en=entry: self._open_detail(en))
        card.bind("<Button-3>",        lambda e, en=entry: self._open_detail(en))

        # ── Left section (icon + text) ────────────────────────────────────
        left = tk.Frame(card, bg=card_bg)
        left.pack(side="left", fill="both", expand=True)
        _bind_click(left, var, self._toggle, entry, self._open_detail)

        icon_label = tk.Label(left, text=entry.icon, bg=card_bg, font=(st.FONT_FAMILY, 18))
        icon_label.pack(side="left")
        _bind_click(icon_label, var, self._toggle, entry, self._open_detail)

        text_frame = tk.Frame(left, bg=card_bg)
        text_frame.pack(side="left", padx=(8, 0), fill="x", expand=True)
        _bind_click(text_frame, var, self._toggle, entry, self._open_detail)

        # App name (dim if installed)
        name_fg = st.TEXT_MUTED if installed else st.TEXT_PRIMARY
        name_lbl = tk.Label(
            text_frame, text=entry.name,
            bg=card_bg, fg=name_fg, font=st.FONT_MEDIUM, anchor="w",
        )
        name_lbl.pack(anchor="w")
        _bind_click(name_lbl, var, self._toggle, entry, self._open_detail)

        desc_lbl = tk.Label(
            text_frame, text=entry.description,
            bg=card_bg, fg=st.TEXT_SECONDARY, font=st.FONT_SMALL,
            anchor="w", wraplength=500,
        )
        desc_lbl.pack(anchor="w")
        _bind_click(desc_lbl, var, self._toggle, entry, self._open_detail)

        # ── Right section (installed badge + category + checkbox) ─────────
        right = tk.Frame(card, bg=card_bg)
        right.pack(side="right")

        if installed:
            tk.Label(
                right, text="✓ installed",
                bg="#1e3a2f", fg=st.SUCCESS, font=st.FONT_SMALL, padx=6, pady=2,
            ).pack(side="right", padx=(0, 6))

        tk.Label(
            right, text=entry.category,
            bg=st.BG_LIGHT, fg=st.TEXT_MUTED, font=st.FONT_SMALL, padx=6, pady=2,
        ).pack(side="right", padx=(0, 6))

        cb = tk.Checkbutton(
            right, variable=var,
            bg=card_bg, activebackground=card_bg,
            selectcolor=st.ACCENT, highlightthickness=0,
            command=self._on_check_change,
        )
        cb.pack(side="right")

        # Hover effect
        all_widgets = [card, left, text_frame, icon_label, name_lbl, desc_lbl, right]
        for w in all_widgets:
            w.bind("<Enter>", lambda e, c=card: self._card_hover(c, True))
            w.bind("<Leave>", lambda e, c=card: self._card_hover(c, False))

    def _card_hover(self, card: tk.Frame, enter: bool):
        bg = st.BG_LIGHT if enter else st.BG_MEDIUM
        card.config(bg=bg)
        for child in card.winfo_children():
            try:
                child.config(bg=bg)
            except tk.TclError:
                pass
            for gc in child.winfo_children():
                try:
                    gc.config(bg=bg)
                except tk.TclError:
                    pass

    def _open_detail(self, entry: SoftwareEntry):
        if self._on_detail:
            self._on_detail(entry)

    def _toggle(self, var: tk.BooleanVar):
        var.set(not var.get())
        self._on_check_change()

    def _on_check_change(self):
        selected = sum(1 for e in self._visible_entries if self._checked[e.id].get())
        count    = len(self._visible_entries)
        self._count_label.config(text=f"{count} apps  |  {selected} selected")

    def _select_all(self, value: bool):
        for entry in self._visible_entries:
            self._checked[entry.id].set(value)
        self._on_check_change()

    # ── Scroll helpers ────────────────────────────────────────────────────

    def _on_inner_configure(self, event):
        self._canvas.config(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._inner_id, width=event.width)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# ── Helper: bind left-click + double-click on a widget ───────────────────────

def _bind_click(widget, var, toggle_fn, entry, detail_fn):
    widget.bind("<Button-1>",        lambda e, v=var: toggle_fn(v))
    widget.bind("<Double-Button-1>", lambda e, en=entry: detail_fn(en))
    widget.bind("<Button-3>",        lambda e, en=entry: detail_fn(en))

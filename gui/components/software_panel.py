"""
Linite - Software Selection Panel
Scrollable grid of app cards with:
  • Real-time search bar (debounced 200 ms)
  • Installed-state badge (detected from history)
  • Double-click / right-click to open detail popup

Performance notes
-----------------
* All card widgets are built ONCE in _build_all_cards(); filtering only
  calls pack() / pack_forget() — no widget creation on every keystroke.
* Mousewheel is bound only while the pointer is inside the canvas, so it
  does not steal scroll events from other parts of the UI.
* Hover widget lists are cached at build time; _card_hover() is O(1).
* Search changes are debounced 200 ms to avoid re-renders on every key.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional, Set

from data.software_catalog import SoftwareEntry
from gui import styles as st

_SEARCH_DEBOUNCE_MS = 200


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
        self._search_after_id: Optional[str] = None   # debounce handle

        # Per-card caches built once by _build_all_cards()
        self._card_frames:        Dict[str, tk.Frame]        = {}
        self._card_hover_widgets: Dict[str, List[tk.Widget]] = {}
        self._card_name_labels:   Dict[str, tk.Label]        = {}
        self._card_inst_labels:   Dict[str, tk.Label]        = {}

        # ── Search bar ───────────────────────────────────────────────────
        search_outer = tk.Frame(self, bg=st.BG_DARK)
        search_outer.pack(fill="x", padx=st.PADDING, pady=(st.PADDING, 4))

        # Bordered container that holds the icon + entry
        search_bar = tk.Frame(
            search_outer,
            bg=st.BG_MEDIUM,
            highlightbackground=st.BORDER,
            highlightthickness=1,
        )
        search_bar.pack(fill="x")

        tk.Label(
            search_bar, text="🔍", bg=st.BG_MEDIUM,
            fg=st.TEXT_MUTED, font=st.FONT_NORMAL,
            padx=8,
        ).pack(side="left")

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_change)

        self._search_entry = tk.Entry(
            search_bar,
            textvariable=self._search_var,
            bg=st.BG_MEDIUM,
            fg=st.TEXT_PRIMARY,
            insertbackground=st.TEXT_PRIMARY,
            font=st.FONT_NORMAL,
            relief="flat",
            bd=0,
        )
        self._search_entry.pack(side="left", fill="x", expand=True, ipady=6)

        clear_btn = tk.Label(
            search_bar, text="✕", bg=st.BG_MEDIUM,
            fg=st.TEXT_MUTED, font=st.FONT_SMALL, cursor="hand2",
            padx=8,
        )
        clear_btn.pack(side="left")
        clear_btn.bind("<Button-1>", lambda e: self._search_var.set(""))
        clear_btn.bind("<Enter>", lambda e: clear_btn.config(fg=st.TEXT_PRIMARY))
        clear_btn.bind("<Leave>", lambda e: clear_btn.config(fg=st.TEXT_MUTED))

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
        da_btn.bind("<Enter>", lambda e: da_btn.config(fg=st.TEXT_PRIMARY))
        da_btn.bind("<Leave>", lambda e: da_btn.config(fg=st.TEXT_MUTED))

        sa_btn = tk.Label(
            header, text="Select All", bg=st.BG_DARK,
            fg=st.ACCENT, font=st.FONT_SMALL, cursor="hand2",
        )
        sa_btn.pack(side="right", padx=(0, 8))
        sa_btn.bind("<Button-1>", lambda e: self._select_all(True))
        sa_btn.bind("<Enter>", lambda e: sa_btn.config(fg=st.ACCENT_HOVER))
        sa_btn.bind("<Leave>", lambda e: sa_btn.config(fg=st.ACCENT))

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

        # bind_all catches wheel events on child widgets (cards) too.
        # _on_mousewheel guards against scrolling when the pointer is outside
        # the canvas bounds, so it won't steal scroll from the log panel.
        self.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows / macOS
        self.bind_all("<Button-4>",   self._on_mousewheel)  # Linux scroll up
        self.bind_all("<Button-5>",   self._on_mousewheel)  # Linux scroll down

        # Pre-build every BooleanVar and every card widget once.
        for entry in self._all_entries:
            self._checked[entry.id] = tk.BooleanVar(value=False)

        self._build_all_cards()
        self._apply_filters()

    # ── Public API ────────────────────────────────────────────────────────

    def filter_by_category(self, category: str):
        self._current_category = category
        self._apply_filters()

    def set_installed_ids(self, ids: Set[str]):
        """
        Mark which app IDs are already installed.
        Updates badge visibility and name dimming without recreating widgets.
        """
        prev = self._installed_ids
        self._installed_ids = ids

        changed = prev.symmetric_difference(ids)
        for app_id in changed:
            inst_lbl  = self._card_inst_labels.get(app_id)
            name_lbl  = self._card_name_labels.get(app_id)
            installed = app_id in ids
            if inst_lbl is not None:
                if installed:
                    inst_lbl.pack(side="right", padx=(0, 6))
                else:
                    inst_lbl.pack_forget()
            if name_lbl is not None:
                name_lbl.config(fg=st.TEXT_MUTED if installed else st.TEXT_PRIMARY)

    def get_selected(self) -> List[SoftwareEntry]:
        return [e for e in self._all_entries if self._checked[e.id].get()]

    def get_selected_ids(self) -> Set[str]:
        return {e.id for e in self._all_entries if self._checked[e.id].get()}

    def set_selected_ids(self, ids: Set[str]):
        """Check exactly the given ids (used for profile import)."""
        for entry in self._all_entries:
            self._checked[entry.id].set(entry.id in ids)
        self._on_check_change()

    # ── Card construction (runs once) ─────────────────────────────────────

    def _build_all_cards(self):
        """Create every card widget once; _apply_filters() shows/hides them."""
        for entry in self._all_entries:
            self._make_card(entry)

    def _make_card(self, entry: SoftwareEntry):
        var     = self._checked[entry.id]
        card_bg = st.BG_MEDIUM

        card = tk.Frame(
            self._inner, bg=card_bg, pady=6, padx=10,
            relief="flat", bd=0, cursor="hand2",
        )
        # Do NOT pack here — _apply_filters will pack/pack_forget.
        self._card_frames[entry.id] = card

        # Left selection stripe (3 px; visible when checked)
        sel_stripe = tk.Frame(card, bg=card_bg, width=3)
        sel_stripe.pack(side="left", fill="y")
        sel_stripe.pack_propagate(False)
        card._sel_stripe = sel_stripe  # type: ignore[attr-defined]
        _bind_click(sel_stripe, var, self._toggle, entry, self._open_detail)

        var.trace_add("write", lambda *_a, eid=entry.id: self._on_card_checked(eid))

        _bind_click(card, var, self._toggle, entry, self._open_detail)

        # ── Left section (icon + text) ────────────────────────────────────
        left = tk.Frame(card, bg=card_bg, padx=4)
        left.pack(side="left", fill="both", expand=True)
        _bind_click(left, var, self._toggle, entry, self._open_detail)

        icon_label = tk.Label(left, text=entry.icon, bg=card_bg, font=(st.FONT_FAMILY, 18))
        icon_label.pack(side="left")
        _bind_click(icon_label, var, self._toggle, entry, self._open_detail)

        text_frame = tk.Frame(left, bg=card_bg)
        text_frame.pack(side="left", padx=(8, 0), fill="x", expand=True)
        _bind_click(text_frame, var, self._toggle, entry, self._open_detail)

        name_lbl = tk.Label(
            text_frame, text=entry.name,
            bg=card_bg, fg=st.TEXT_PRIMARY, font=st.FONT_MEDIUM, anchor="w",
        )
        name_lbl.pack(anchor="w")
        _bind_click(name_lbl, var, self._toggle, entry, self._open_detail)
        self._card_name_labels[entry.id] = name_lbl

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

        # Installed badge — created hidden; set_installed_ids() shows/hides it.
        inst_lbl = tk.Label(
            right, text="✓ installed",
            bg=st.SUCCESS_BG, fg=st.SUCCESS, font=st.FONT_SMALL, padx=6, pady=2,
        )
        self._card_inst_labels[entry.id] = inst_lbl
        # (not packed yet — shown on demand)

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

        # Cache hover targets at build time for O(1) updates.
        hover_targets: List[tk.Widget] = [
            card, left, text_frame, icon_label, name_lbl, desc_lbl, right, cb,
        ]
        self._card_hover_widgets[entry.id] = hover_targets

        for w in hover_targets:
            w.bind("<Enter>", lambda e, eid=entry.id, c=card: self._card_hover(eid, c, True))
            w.bind("<Leave>", lambda e, eid=entry.id, c=card: self._card_hover(eid, c, False))

    # ── Filtering logic ───────────────────────────────────────────────────

    def _on_search_change(self, *_):
        """Debounce: wait 200 ms of idle before applying the search filter."""
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(_SEARCH_DEBOUNCE_MS, self._commit_search)

    def _commit_search(self):
        self._search_after_id = None
        self._search_text = self._search_var.get().lower().strip()
        self._apply_filters()

    def _apply_filters(self):
        """Show/hide pre-built card frames — no widget creation."""
        entries = self._all_entries

        if self._current_category != "All":
            entries = [e for e in entries if e.category == self._current_category]

        if self._search_text:
            q = self._search_text
            entries = [
                e for e in entries
                if q in e.name.lower()
                or q in e.description.lower()
                or q in e.category.lower()
                or q in e.id.lower()
            ]

        self._visible_entries = entries
        visible_ids = {e.id for e in entries}

        # Reset scroll before revealing new cards to avoid visual jump.
        self._canvas.yview_moveto(0)

        for entry in self._all_entries:
            card = self._card_frames[entry.id]
            if entry.id in visible_ids:
                card.pack(fill="x", padx=st.PADDING, pady=4)
            else:
                card.pack_forget()

        self._update_count_label()

    # ── Rendering helpers ─────────────────────────────────────────────────

    def _update_count_label(self):
        count    = len(self._visible_entries)
        selected = sum(1 for e in self._all_entries if self._checked[e.id].get())
        parts = [f"{count} app{'s' if count != 1 else ''}"]
        if selected:
            parts.append(f"{selected} selected")
        self._count_label.config(text="  ·  ".join(parts))

    def _on_card_checked(self, entry_id: str):
        """Update card background + stripe when its checkbox value changes."""
        checked = self._checked[entry_id].get()
        card    = self._card_frames.get(entry_id)
        if card is None:
            return
        bg = st.CARD_SELECTED if checked else st.BG_MEDIUM
        card.config(bg=bg)
        card._sel_stripe.config(bg=st.ACCENT if checked else bg)  # type: ignore[attr-defined]
        for w in self._card_hover_widgets.get(entry_id, []):
            try:
                w.config(bg=bg)
            except tk.TclError:
                pass
        self._update_count_label()

    def _card_hover(self, entry_id: str, card: tk.Frame, enter: bool):
        # Don't change background if the card is checked
        if self._checked[entry_id].get():
            return
        bg = st.BG_LIGHT if enter else st.BG_MEDIUM
        card.config(bg=bg)
        for w in self._card_hover_widgets[entry_id]:
            try:
                w.config(bg=bg)
            except tk.TclError:
                pass

    def _open_detail(self, entry: SoftwareEntry):
        if self._on_detail:
            self._on_detail(entry)

    def _toggle(self, var: tk.BooleanVar):
        var.set(not var.get())
        self._on_check_change()

    def _on_check_change(self):
        self._update_count_label()

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
        """Scroll only when the pointer is within the canvas bounds."""
        cx = self._canvas.winfo_rootx()
        cy = self._canvas.winfo_rooty()
        cw = self._canvas.winfo_width()
        ch = self._canvas.winfo_height()
        px, py = event.x_root, event.y_root
        if not (cx <= px < cx + cw and cy <= py < cy + ch):
            return
        if event.num == 4:
            self._canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(3, "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)) * 3, "units")


# ── Helper: bind left-click + double-click on a widget ───────────────────────

def _bind_click(widget, var, toggle_fn, entry, detail_fn):
    widget.bind("<Button-1>",        lambda e, v=var: toggle_fn(v))
    widget.bind("<Double-Button-1>", lambda e, en=entry: detail_fn(en))
    widget.bind("<Button-3>",        lambda e, en=entry: detail_fn(en))

"""
Linite - Software Selection Panel
Scrollable grid of app cards with checkboxes.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Set

from data.software_catalog import SoftwareEntry
from gui import styles as st


class SoftwarePanel(tk.Frame):
    """
    Main content area showing software cards with checkboxes.
    """

    def __init__(self, parent, entries: List[SoftwareEntry], **kwargs):
        super().__init__(parent, bg=st.BG_DARK, **kwargs)
        self._all_entries = entries
        self._visible_entries: List[SoftwareEntry] = list(entries)
        self._checked: Dict[str, tk.BooleanVar] = {}

        # ── Header bar ──────────────────────────────────────────────────
        header = tk.Frame(self, bg=st.BG_DARK)
        header.pack(fill="x", padx=st.PADDING, pady=(st.PADDING, 4))

        self._count_label = tk.Label(
            header,
            text="",
            bg=st.BG_DARK,
            fg=st.TEXT_SECONDARY,
            font=st.FONT_SMALL,
        )
        self._count_label.pack(side="left")

        # Select-all / deselect-all
        sa_btn = tk.Label(
            header,
            text="Select All",
            bg=st.BG_DARK,
            fg=st.ACCENT,
            font=st.FONT_SMALL,
            cursor="hand2",
        )
        sa_btn.pack(side="right", padx=(0, 8))
        sa_btn.bind("<Button-1>", lambda e: self._select_all(True))

        da_btn = tk.Label(
            header,
            text="Deselect All",
            bg=st.BG_DARK,
            fg=st.TEXT_MUTED,
            font=st.FONT_SMALL,
            cursor="hand2",
        )
        da_btn.pack(side="right", padx=(0, 8))
        da_btn.bind("<Button-1>", lambda e: self._select_all(False))

        # ── Scrollable canvas ────────────────────────────────────────────
        container = tk.Frame(self, bg=st.BG_DARK)
        container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(
            container, bg=st.BG_DARK, highlightthickness=0, bd=0
        )
        scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=self._canvas.yview
        )
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg=st.BG_DARK)
        self._inner_id = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw"
        )

        self._inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)

        # Build initial BooleanVars and render
        for entry in self._all_entries:
            self._checked[entry.id] = tk.BooleanVar(value=False)

        self._render()

    # ── Public API ────────────────────────────────────────────────────────

    def filter_by_category(self, category: str):
        if category == "All":
            self._visible_entries = list(self._all_entries)
        else:
            self._visible_entries = [
                e for e in self._all_entries if e.category == category
            ]
        self._render()

    def get_selected(self) -> List[SoftwareEntry]:
        return [e for e in self._all_entries if self._checked[e.id].get()]

    def get_selected_ids(self) -> Set[str]:
        return {e.id for e in self._all_entries if self._checked[e.id].get()}

    # ── Rendering ─────────────────────────────────────────────────────────

    def _render(self):
        # Clear old cards
        for widget in self._inner.winfo_children():
            widget.destroy()

        count = len(self._visible_entries)
        selected = sum(1 for e in self._visible_entries if self._checked[e.id].get())
        self._count_label.config(
            text=f"{count} apps  |  {selected} selected"
        )

        for entry in self._visible_entries:
            self._make_card(entry)

        self._inner.update_idletasks()
        self._canvas.config(scrollregion=self._canvas.bbox("all"))

    def _make_card(self, entry: SoftwareEntry):
        var = self._checked[entry.id]

        card = tk.Frame(
            self._inner,
            bg=st.BG_MEDIUM,
            pady=8,
            padx=10,
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        card.pack(fill="x", padx=st.PADDING, pady=4)

        # Toggle on card click
        card.bind("<Button-1>", lambda e, v=var: self._toggle(v))

        # Left: icon + texts
        left = tk.Frame(card, bg=st.BG_MEDIUM)
        left.pack(side="left", fill="both", expand=True)
        left.bind("<Button-1>", lambda e, v=var: self._toggle(v))

        icon_label = tk.Label(
            left, text=entry.icon, bg=st.BG_MEDIUM, font=(st.FONT_FAMILY, 18)
        )
        icon_label.pack(side="left")
        icon_label.bind("<Button-1>", lambda e, v=var: self._toggle(v))

        text_frame = tk.Frame(left, bg=st.BG_MEDIUM)
        text_frame.pack(side="left", padx=(8, 0), fill="x", expand=True)
        text_frame.bind("<Button-1>", lambda e, v=var: self._toggle(v))

        name_lbl = tk.Label(
            text_frame,
            text=entry.name,
            bg=st.BG_MEDIUM,
            fg=st.TEXT_PRIMARY,
            font=st.FONT_MEDIUM,
            anchor="w",
        )
        name_lbl.pack(anchor="w")
        name_lbl.bind("<Button-1>", lambda e, v=var: self._toggle(v))

        desc_lbl = tk.Label(
            text_frame,
            text=entry.description,
            bg=st.BG_MEDIUM,
            fg=st.TEXT_SECONDARY,
            font=st.FONT_SMALL,
            anchor="w",
            wraplength=540,
        )
        desc_lbl.pack(anchor="w")
        desc_lbl.bind("<Button-1>", lambda e, v=var: self._toggle(v))

        # Category badge
        badge = tk.Label(
            card,
            text=entry.category,
            bg=st.BG_LIGHT,
            fg=st.TEXT_MUTED,
            font=st.FONT_SMALL,
            padx=6,
            pady=2,
        )
        badge.pack(side="right", padx=(8, 8))
        badge.bind("<Button-1>", lambda e, v=var: self._toggle(v))

        # Checkbox (right side)
        cb = tk.Checkbutton(
            card,
            variable=var,
            bg=st.BG_MEDIUM,
            activebackground=st.BG_MEDIUM,
            selectcolor=st.ACCENT,
            highlightthickness=0,
            command=self._on_check_change,
        )
        cb.pack(side="right")

        # Hover effects
        all_widgets = [card, left, text_frame, icon_label, name_lbl, desc_lbl, badge]
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

    def _toggle(self, var: tk.BooleanVar):
        var.set(not var.get())
        self._on_check_change()

    def _on_check_change(self):
        selected = sum(1 for e in self._visible_entries if self._checked[e.id].get())
        count = len(self._visible_entries)
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

"""
Linite - Category Sidebar
Displays a list of software categories; clicking one filters the software panel.
"""

import tkinter as tk
from typing import Callable, List

from gui import styles as st


class CategoryPanel(tk.Frame):
    """Left sidebar listing software categories."""

    def __init__(
        self,
        parent,
        categories: List[str],
        on_select: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(parent, bg=st.BG_MEDIUM, **kwargs)
        self._on_select = on_select
        self._buttons: dict[str, tk.Label] = {}
        self._active: str = ""

        # Title
        tk.Label(
            self,
            text="Categories",
            bg=st.BG_MEDIUM,
            fg=st.TEXT_SECONDARY,
            font=st.FONT_SMALL,
            anchor="w",
            padx=st.PADDING,
            pady=8,
        ).pack(fill="x")

        # Separator
        tk.Frame(self, bg=st.BORDER, height=1).pack(fill="x", padx=8)

        # "All" entry
        all_cats = ["All"] + categories
        for cat in all_cats:
            self._make_button(cat)

        # Pre-select "All"
        self._select("All")

    def _make_button(self, label: str):
        btn = tk.Label(
            self,
            text=label,
            bg=st.BG_MEDIUM,
            fg=st.TEXT_PRIMARY,
            font=st.FONT_NORMAL,
            anchor="w",
            padx=st.PADDING,
            pady=7,
            cursor="hand2",
        )
        btn.pack(fill="x")
        btn.bind("<Button-1>", lambda e, l=label: self._select(l))
        btn.bind("<Enter>", lambda e, b=btn, l=label: self._hover(b, l))
        btn.bind("<Leave>", lambda e, b=btn, l=label: self._unhover(b, l))
        self._buttons[label] = btn

    def _select(self, label: str):
        # Deactivate previous
        if self._active and self._active in self._buttons:
            self._buttons[self._active].config(
                bg=st.BG_MEDIUM, fg=st.TEXT_PRIMARY
            )
        self._active = label
        self._buttons[label].config(bg=st.ACCENT, fg="#ffffff")
        self._on_select(label)

    def _hover(self, btn: tk.Label, label: str):
        if label != self._active:
            btn.config(bg=st.BG_LIGHT)

    def _unhover(self, btn: tk.Label, label: str):
        if label != self._active:
            btn.config(bg=st.BG_MEDIUM)

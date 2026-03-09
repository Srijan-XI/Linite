"""
Linite - Category Sidebar
Displays a list of software categories with app counts; clicking one filters
the software panel.  The active category shows a left-side accent stripe.
"""

import tkinter as tk
from typing import Callable, Dict, List, Optional

from gui import styles as st


class CategoryPanel(tk.Frame):
    """Left sidebar listing software categories."""

    def __init__(
        self,
        parent,
        categories: List[str],
        on_select: Callable[[str], None],
        counts: Optional[Dict[str, int]] = None,
        **kwargs,
    ):
        super().__init__(parent, bg=st.BG_MEDIUM, **kwargs)
        self._on_select = on_select
        self._counts    = counts or {}
        self._rows:   dict[str, tk.Frame] = {}   # outer row frame
        self._labels: dict[str, tk.Label] = {}   # inner text label
        self._active: str = ""

        # Title
        tk.Label(
            self,
            text="CATEGORIES",
            bg=st.BG_MEDIUM,
            fg=st.TEXT_MUTED,
            font=(st.FONT_FAMILY, 8, "bold"),
            anchor="w",
            padx=st.PADDING,
            pady=10,
        ).pack(fill="x")

        # Separator
        tk.Frame(self, bg=st.BORDER, height=1).pack(fill="x")

        all_cats = ["All"] + list(categories)
        for cat in all_cats:
            self._make_row(cat)

        # Pre-select "All"
        self._select("All")

    # ── Public API ────────────────────────────────────────────────────────

    def update_counts(self, counts: Dict[str, int]):
        """Refresh the count badges."""
        self._counts = counts

    # ── Construction helpers ─────────────────────────────────────────────

    def _make_row(self, label: str):
        """Create a row: [accent_stripe | inner_frame[text_label + count_badge]]."""
        row = tk.Frame(self, bg=st.BG_MEDIUM, cursor="hand2")
        row.pack(fill="x")
        self._rows[label] = row

        # Left colour stripe (3 px wide, hidden by default)
        stripe = tk.Frame(row, bg=st.BG_MEDIUM, width=3)
        stripe.pack(side="left", fill="y")
        stripe.pack_propagate(False)
        row._stripe = stripe  # type: ignore[attr-defined]

        inner = tk.Frame(row, bg=st.BG_MEDIUM)
        inner.pack(side="left", fill="x", expand=True)

        lbl = tk.Label(
            inner,
            text=label,
            bg=st.BG_MEDIUM,
            fg=st.TEXT_PRIMARY,
            font=st.FONT_NORMAL,
            anchor="w",
            padx=st.PADDING - 3,
            pady=7,
        )
        lbl.pack(side="left", fill="x", expand=True)
        self._labels[label] = lbl

        # Count badge
        count = self._counts.get(label, 0)
        if label == "All":
            count = sum(self._counts.values()) if self._counts else 0
        if count:
            tk.Label(
                inner,
                text=str(count),
                bg=st.ACCENT_DIM,
                fg=st.TEXT_SECONDARY,
                font=(st.FONT_FAMILY, 8),
                padx=5, pady=1,
            ).pack(side="right", padx=(0, st.PADDING - 3), pady=4)

        for widget in (row, inner, lbl):
            widget.bind("<Button-1>", lambda e, l=label: self._select(l))
            widget.bind("<Enter>",    lambda e, l=label: self._hover(l, True))
            widget.bind("<Leave>",    lambda e, l=label: self._hover(l, False))

    # ── Interaction ───────────────────────────────────────────────────────

    def _select(self, label: str):
        if self._active and self._active in self._rows:
            prev = self._rows[self._active]
            for w in [prev, prev.winfo_children()[1]]:
                w.config(bg=st.BG_MEDIUM)
            prev._stripe.config(bg=st.BG_MEDIUM)  # type: ignore[attr-defined]
            self._labels[self._active].config(
                bg=st.BG_MEDIUM, fg=st.TEXT_PRIMARY,
                font=st.FONT_NORMAL,
            )

        self._active = label
        row   = self._rows[label]
        inner = row.winfo_children()[1]
        for w in [row, inner]:
            w.config(bg=st.BG_LIGHT)
        row._stripe.config(bg=st.ACCENT)  # type: ignore[attr-defined]
        self._labels[label].config(
            bg=st.BG_LIGHT, fg=st.TEXT_PRIMARY,
            font=(st.FONT_FAMILY, 10, "bold"),
        )
        self._on_select(label)

    def _hover(self, label: str, entering: bool):
        if label == self._active:
            return
        bg = st.BG_LIGHT if entering else st.BG_MEDIUM
        row   = self._rows[label]
        inner = row.winfo_children()[1]
        for w in [row, inner]:
            w.config(bg=bg)
        self._labels[label].config(bg=bg)

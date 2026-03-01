"""
Linite - Progress / Log Panel
Shows real-time installation output, status badges, and overall progress bar.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List

from gui import styles as st


class ProgressPanel(tk.Frame):
    """
    Bottom panel with a progress bar and a scrollable log area.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=st.BG_MEDIUM, **kwargs)
        self._total = 0
        self._done = 0

        # ── Title bar ────────────────────────────────────────────────────
        title_bar = tk.Frame(self, bg=st.BG_MEDIUM)
        title_bar.pack(fill="x", padx=st.PADDING, pady=(8, 4))

        tk.Label(
            title_bar,
            text="Installation Log",
            bg=st.BG_MEDIUM,
            fg=st.TEXT_SECONDARY,
            font=st.FONT_SMALL,
        ).pack(side="left")

        self._status_label = tk.Label(
            title_bar,
            text="",
            bg=st.BG_MEDIUM,
            fg=st.TEXT_MUTED,
            font=st.FONT_SMALL,
        )
        self._status_label.pack(side="right")

        # ── Progress bar ─────────────────────────────────────────────────
        pb_frame = tk.Frame(self, bg=st.BG_MEDIUM)
        pb_frame.pack(fill="x", padx=st.PADDING, pady=(0, 6))

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Linite.Horizontal.TProgressbar",
            troughcolor=st.BG_DARK,
            background=st.ACCENT,
            thickness=6,
        )

        self._pb_var = tk.DoubleVar(value=0)
        self._pb = ttk.Progressbar(
            pb_frame,
            variable=self._pb_var,
            style="Linite.Horizontal.TProgressbar",
            maximum=100,
            mode="determinate",
        )
        self._pb.pack(fill="x")

        # ── Log text area ─────────────────────────────────────────────────
        log_frame = tk.Frame(self, bg=st.BG_MEDIUM)
        log_frame.pack(fill="both", expand=True, padx=st.PADDING, pady=(0, 8))

        self._log = tk.Text(
            log_frame,
            bg=st.BG_DARK,
            fg=st.TEXT_PRIMARY,
            font=(st.FONT_FAMILY, 9),
            state="disabled",
            wrap="word",
            relief="flat",
            bd=0,
            height=8,
        )
        v_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self._log.yview)
        self._log.configure(yscrollcommand=v_scroll.set)

        v_scroll.pack(side="right", fill="y")
        self._log.pack(side="left", fill="both", expand=True)

        # Text tags for coloring
        self._log.tag_config("info",    foreground=st.TEXT_PRIMARY)
        self._log.tag_config("success", foreground=st.SUCCESS)
        self._log.tag_config("error",   foreground=st.ERROR)
        self._log.tag_config("warn",    foreground=st.WARNING)
        self._log.tag_config("muted",   foreground=st.TEXT_MUTED)

    # ── Public API ────────────────────────────────────────────────────────

    def reset(self, total_apps: int = 0):
        """Clear log and reset progress for a new run."""
        self._total = total_apps
        self._done = 0
        self._pb_var.set(0)
        self._status_label.config(text="")
        self._clear_log()

    def log(self, message: str, tag: str = "info"):
        """Append one line to the log."""
        self._log.configure(state="normal")
        self._log.insert("end", message + "\n", tag)
        self._log.see("end")
        self._log.configure(state="disabled")

    def app_done(self, app_name: str, success: bool):
        """Call after each app finishes to advance the progress bar."""
        self._done += 1
        pct = (self._done / self._total * 100) if self._total else 100
        self._pb_var.set(pct)
        tag = "success" if success else "error"
        icon = "✓" if success else "✗"
        self.log(f"{icon} {app_name} — {'done' if success else 'failed'}", tag=tag)
        self._status_label.config(
            text=f"{self._done}/{self._total} complete"
        )

    def set_status(self, text: str):
        self._status_label.config(text=text)

    # ── Internal ─────────────────────────────────────────────────────────

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

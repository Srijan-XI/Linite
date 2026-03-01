"""
Linite - Progress / Log Panel
Shows real-time installation output, status badges, and overall progress bar.
Features: collapsible log area, clear-log button, indeterminate mode.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List

from gui import styles as st

_COLLAPSED_HEIGHT = 38   # px when log area is hidden
_EXPANDED_HEIGHT  = 180  # px when log area is visible


class ProgressPanel(tk.Frame):
    """
    Bottom panel with a progress bar and a collapsible scrollable log area.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=st.BG_MEDIUM, **kwargs)
        self._total = 0
        self._done  = 0
        self._expanded = True

        # ── Title / control bar ───────────────────────────────────────────
        title_bar = tk.Frame(self, bg=st.BG_MEDIUM)
        title_bar.pack(fill="x", padx=st.PADDING, pady=(6, 2))

        self._toggle_btn = tk.Label(
            title_bar, text="▾  Log",
            bg=st.BG_MEDIUM, fg=st.TEXT_SECONDARY,
            font=(st.FONT_FAMILY, 9, "bold"),
            cursor="hand2",
        )
        self._toggle_btn.pack(side="left")
        self._toggle_btn.bind("<Button-1>", lambda _e: self._toggle_log())

        self._status_label = tk.Label(
            title_bar, text="",
            bg=st.BG_MEDIUM, fg=st.TEXT_MUTED,
            font=st.FONT_SMALL,
        )
        self._status_label.pack(side="right")

        # Clear log button
        clear_btn = tk.Label(
            title_bar, text="Clear",
            bg=st.BG_MEDIUM, fg=st.TEXT_MUTED,
            font=st.FONT_SMALL, cursor="hand2",
        )
        clear_btn.pack(side="right", padx=(0, 10))
        clear_btn.bind("<Button-1>", lambda _e: self._clear_log())
        clear_btn.bind("<Enter>", lambda _e: clear_btn.config(fg=st.TEXT_PRIMARY))
        clear_btn.bind("<Leave>", lambda _e: clear_btn.config(fg=st.TEXT_MUTED))

        # ── Progress bar ─────────────────────────────────────────────────
        pb_frame = tk.Frame(self, bg=st.BG_MEDIUM)
        pb_frame.pack(fill="x", padx=st.PADDING, pady=(0, 4))

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Linite.Horizontal.TProgressbar",
            troughcolor=st.BG_DARK,
            background=st.ACCENT,
            thickness=5,
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
        self._log_frame = tk.Frame(self, bg=st.BG_MEDIUM)
        self._log_frame.pack(fill="both", expand=True, padx=st.PADDING, pady=(0, 6))

        self._log = tk.Text(
            self._log_frame,
            bg=st.BG_DARK,
            fg=st.TEXT_PRIMARY,
            font=(st.FONT_FAMILY, 9),
            state="disabled",
            wrap="word",
            relief="flat",
            bd=0,
            height=7,
        )
        v_scroll = ttk.Scrollbar(self._log_frame, orient="vertical", command=self._log.yview)
        self._log.configure(yscrollcommand=v_scroll.set)

        v_scroll.pack(side="right", fill="y")
        self._log.pack(side="left", fill="both", expand=True)

        # Text tags
        self._log.tag_config("info",    foreground=st.TEXT_PRIMARY)
        self._log.tag_config("success", foreground=st.SUCCESS)
        self._log.tag_config("error",   foreground=st.ERROR)
        self._log.tag_config("warn",    foreground=st.WARNING)
        self._log.tag_config("muted",   foreground=st.TEXT_MUTED)

    # ── Public API ────────────────────────────────────────────────────────

    def reset(self, total_apps: int = 0):
        """Clear log and reset progress for a new run."""
        self._total = total_apps
        self._done  = 0
        self._pb_var.set(0)
        self._pb.config(mode="determinate")
        self._status_label.config(text="")
        self._clear_log()
        if not self._expanded:
            self._toggle_log()   # auto-expand for a new run

    def set_indeterminate(self, running: bool):
        """Switch the progress bar to/from indeterminate (bouncing) mode."""
        if running:
            self._pb.config(mode="indeterminate")
            self._pb.start(15)
        else:
            self._pb.stop()
            self._pb.config(mode="determinate")
            self._pb_var.set(100)

    def log(self, message: str, tag: str = "info"):
        """Append one line to the log."""
        self._log.configure(state="normal")
        self._log.insert("end", message + "\n", tag)
        self._log.see("end")
        self._log.configure(state="disabled")

    def app_done(self, app_name: str, success: bool):
        """Advance progress bar after each app finishes."""
        self._done += 1
        pct = (self._done / self._total * 100) if self._total else 100
        self._pb_var.set(pct)
        tag  = "success" if success else "error"
        icon = "✓" if success else "✗"
        self.log(f"{icon} {app_name} — {'done' if success else 'failed'}", tag=tag)
        self._status_label.config(text=f"{self._done}/{self._total} complete")

    def set_status(self, text: str):
        self._status_label.config(text=text)

    # ── Internal ─────────────────────────────────────────────────────────

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _toggle_log(self):
        self._expanded = not self._expanded
        if self._expanded:
            self._log_frame.pack(fill="both", expand=True, padx=st.PADDING, pady=(0, 6))
            self._toggle_btn.config(text="▾  Log")
        else:
            self._log_frame.pack_forget()
            self._toggle_btn.config(text="▸  Log")

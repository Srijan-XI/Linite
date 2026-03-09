"""
Linite - Transaction Log Viewer
================================
A full-featured modal dialog that displays, filters, and exports the complete
transaction history from the log engine.

Layout
------
┌─────────────────────────────────────────────────────────────┐
│ 📋  Transaction Log                              [✕ Close]  │
│─────────────────────────────────────────────────────────────│
│  ┌──────── Stats bar ──────────────────────────────────┐   │
│  │ 42 ops · 38 OK · 4 failed · 95.2% · 3 sessions      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────── Filter bar ─────────────────────────────────┐   │
│  │ Action ▾  Status ▾  PM ▾  Search… [Clear filters]   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────── Treeview table ─────────────────────────────┐   │
│  │ Timestamp          Action     App          Status …  │   │
│  │ 2026-03-02 16:18   install    VLC          success   │   │
│  │ 2026-03-02 16:17   install    Docker       retried   │   │
│  │ …                                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────── Detail pane (expands on row click) ─────────┐   │
│  │ PM: apt · Took 12.3s · 2 attempts                    │   │
│  │ OUTPUT / ERROR …                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│  [📄 Export Text]  [📦 Export YAML]  [🗑 Clear Old Logs]   │
└─────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from core.log_engine import TransactionRecord, tx_log, LogStats
from gui import styles as st

# Column definitions: (heading, width, stretch, data_key)
_COLUMNS = [
    ("Timestamp",  150, False, "timestamp"),
    ("Action",      82, False, "action"),
    ("App",        180, True,  "app_name"),
    ("Status",      88, False, "status"),
    ("PM",          68, False, "pm_used"),
    ("Dur (s)",     62, False, "duration"),
    ("Attempts",    68, False, "attempts"),
]

_STATUS_COLOURS = {
    "success":   "#50fa7b",
    "retried":   "#f1fa8c",
    "fallback":  "#8be9fd",
    "failed":    "#ff5555",
    "skipped":   "#6c7086",
    "cancelled": "#6c7086",
}

_ACTION_ICONS = {
    "install":      "⬇",
    "uninstall":    "🗑",
    "update":       "🔄",
    "system_update":"🔄",
    "tweak":        "⚙",
    "profile_apply":"⚡",
}


class LogViewerDialog(tk.Toplevel):
    """
    Modal log viewer.  Loads records asynchronously to keep the UI responsive.
    """

    def __init__(self, parent: tk.Widget):
        super().__init__(parent)
        self.title("Transaction Log")
        self.configure(bg=st.BG_DARK)
        self.resizable(True, True)
        self.minsize(860, 540)
        self.grab_set()

        self._records:  List[TransactionRecord] = []
        self._filtered: List[TransactionRecord] = []
        self._detail_rec: Optional[TransactionRecord] = None

        self._build()
        self._center(parent)
        self._load_async()

    # ── Build ──────────────────────────────────────────────────────────────

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=st.BG_MEDIUM)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="📋  Transaction Log",
            bg=st.BG_MEDIUM, fg=st.TEXT_PRIMARY, font=st.FONT_TITLE,
            padx=st.PADDING, pady=12,
        ).pack(side="left")
        tk.Button(
            hdr, text="✕",
            bg=st.BG_MEDIUM, fg=st.TEXT_MUTED, font=st.FONT_MEDIUM,
            relief="flat", bd=0, padx=10, cursor="hand2",
            activebackground=st.BG_LIGHT, activeforeground=st.TEXT_PRIMARY,
            command=self.destroy,
        ).pack(side="right", padx=st.PADDING)
        tk.Frame(self, bg=st.BORDER, height=1).pack(fill="x")

        body = tk.Frame(self, bg=st.BG_DARK)
        body.pack(fill="both", expand=True, padx=st.PADDING, pady=st.PADDING)

        # ── Stats bar ─────────────────────────────────────────────────────
        stats_bar = tk.Frame(body, bg=st.BG_MEDIUM,
                             highlightbackground=st.BORDER, highlightthickness=1)
        stats_bar.pack(fill="x", pady=(0, st.PADDING))
        self._stats_labels: dict[str, tk.Label] = {}
        stat_defs = [
            ("total",    "─  ops",     st.TEXT_PRIMARY),
            ("success",  "✓  ok",      st.SUCCESS),
            ("fail",     "✗  failed",  st.ERROR),
            ("rate",     "%  rate",    st.ACCENT),
            ("sessions", "⟳  sessions",st.TEXT_SECONDARY),
            ("duration", "⏱  total",   st.TEXT_MUTED),
        ]
        for key, label, colour in stat_defs:
            col = tk.Frame(stats_bar, bg=st.BG_MEDIUM)
            col.pack(side="left", padx=16, pady=8)
            val = tk.Label(col, text="…", bg=st.BG_MEDIUM, fg=colour,
                           font=st.FONT_LARGE)
            val.pack()
            tk.Label(col, text=label, bg=st.BG_MEDIUM, fg=st.TEXT_MUTED,
                     font=(st.FONT_FAMILY, 8)).pack()
            self._stats_labels[key] = val

        # ── Filter bar ────────────────────────────────────────────────────
        filter_bar = tk.Frame(body, bg=st.BG_DARK)
        filter_bar.pack(fill="x", pady=(0, 6))

        self._action_var = tk.StringVar(value="All actions")
        self._status_var = tk.StringVar(value="All statuses")
        self._pm_var     = tk.StringVar(value="All PMs")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filters())

        action_opts = ["All actions", "install", "uninstall", "update",
                       "system_update", "tweak", "profile_apply"]
        status_opts = ["All statuses", "success", "retried", "fallback",
                       "failed", "skipped", "cancelled"]
        pm_opts     = ["All PMs", "apt", "dnf", "pacman", "zypper",
                       "flatpak", "snap"]

        for var, opts in (
            (self._action_var, action_opts),
            (self._status_var, status_opts),
            (self._pm_var,     pm_opts),
        ):
            om = tk.OptionMenu(filter_bar, var, *opts,
                               command=lambda *_: self._apply_filters())
            om.config(bg=st.BG_MEDIUM, fg=st.TEXT_PRIMARY, font=st.FONT_SMALL,
                      relief="flat", bd=0, activebackground=st.BG_LIGHT,
                      highlightthickness=0)
            om["menu"].config(bg=st.BG_MEDIUM, fg=st.TEXT_PRIMARY,
                              activebackground=st.BG_LIGHT, font=st.FONT_SMALL)
            om.pack(side="left", padx=(0, 6))

        # Search box
        search_frame = tk.Frame(filter_bar, bg=st.BG_MEDIUM,
                                highlightbackground=st.BORDER, highlightthickness=1)
        search_frame.pack(side="left", padx=(0, 6))
        tk.Label(search_frame, text="🔍", bg=st.BG_MEDIUM,
                 fg=st.TEXT_MUTED, font=st.FONT_SMALL, padx=4).pack(side="left")
        tk.Entry(
            search_frame, textvariable=self._search_var,
            bg=st.BG_MEDIUM, fg=st.TEXT_PRIMARY, font=st.FONT_SMALL,
            relief="flat", bd=0, insertbackground=st.TEXT_PRIMARY, width=20,
        ).pack(side="left", pady=4)

        tk.Button(
            filter_bar, text="Clear",
            bg=st.BG_LIGHT, fg=st.TEXT_MUTED, font=st.FONT_SMALL,
            relief="flat", bd=0, padx=8, pady=3, cursor="hand2",
            command=self._clear_filters,
        ).pack(side="left")

        self._count_lbl = tk.Label(
            filter_bar, text="",
            bg=st.BG_DARK, fg=st.TEXT_MUTED, font=st.FONT_SMALL,
        )
        self._count_lbl.pack(side="right")

        # ── Treeview ──────────────────────────────────────────────────────
        tree_frame = tk.Frame(body, bg=st.BG_DARK)
        tree_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Log.Treeview",
                        background=st.BG_DARK,
                        foreground=st.TEXT_PRIMARY,
                        fieldbackground=st.BG_DARK,
                        rowheight=26,
                        font=st.FONT_SMALL)
        style.configure("Log.Treeview.Heading",
                        background=st.BG_MEDIUM,
                        foreground=st.TEXT_SECONDARY,
                        font=(st.FONT_FAMILY, 9, "bold"),
                        relief="flat")
        style.map("Log.Treeview",
                  background=[("selected", st.BG_LIGHT)],
                  foreground=[("selected", st.TEXT_PRIMARY)])

        col_ids = [c[0] for c in _COLUMNS]
        self._tree = ttk.Treeview(
            tree_frame, columns=col_ids, show="headings",
            style="Log.Treeview", selectmode="browse",
        )
        for heading, width, stretch, _ in _COLUMNS:
            self._tree.heading(heading, text=heading,
                               command=lambda h=heading: self._sort_by(h))
            self._tree.column(heading, width=width, stretch=stretch,
                              anchor="w" if stretch else "center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)
        self._tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # Tag colours for status
        for status, colour in _STATUS_COLOURS.items():
            self._tree.tag_configure(status, foreground=colour)

        # ── Detail pane ───────────────────────────────────────────────────
        self._detail_frame = tk.Frame(body, bg=st.BG_MEDIUM,
                                      highlightbackground=st.BORDER,
                                      highlightthickness=1)
        self._detail_frame.pack(fill="x", pady=(6, 0))

        self._detail_header = tk.Label(
            self._detail_frame, text="Select a row to view details",
            bg=st.BG_MEDIUM, fg=st.TEXT_MUTED, font=st.FONT_SMALL,
            anchor="w", padx=8, pady=4,
        )
        self._detail_header.pack(fill="x")

        self._detail_text = tk.Text(
            self._detail_frame, height=4, wrap="word",
            bg=st.BG_MEDIUM, fg=st.TEXT_SECONDARY, font=st.FONT_SMALL,
            relief="flat", bd=0, state="disabled",
            padx=8, pady=4,
        )
        self._detail_text.pack(fill="x")

        # ── Action buttons ────────────────────────────────────────────────
        tk.Frame(self, bg=st.BORDER, height=1).pack(fill="x")
        btn_bar = tk.Frame(self, bg=st.BG_MEDIUM)
        btn_bar.pack(fill="x", pady=6, padx=st.PADDING)

        for label, cmd in (
            ("📄  Export Text",      self._export_text),
            ("📦  Export YAML",      self._export_yaml),
            ("🗑  Clear Old Logs",   self._clear_old),
        ):
            tk.Button(
                btn_bar, text=label,
                bg=st.BG_LIGHT, fg=st.TEXT_SECONDARY, font=st.FONT_SMALL,
                relief="flat", bd=0, padx=12, pady=5, cursor="hand2",
                activebackground=st.BG_DARK,
                command=cmd,
            ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_bar, text="Close",
            bg=st.BG_LIGHT, fg=st.TEXT_PRIMARY, font=st.FONT_NORMAL,
            relief="flat", bd=0, padx=16, pady=5, cursor="hand2",
            activebackground=st.BG_DARK, command=self.destroy,
        ).pack(side="right")

        self._sort_col   = "Timestamp"
        self._sort_asc   = False   # newest first by default

    # ── Data loading ──────────────────────────────────────────────────────

    def _load_async(self):
        """Load records in a background thread to keep the dialog snappy."""
        def _worker():
            recs  = tx_log.query(newest_first=True)
            stats = tx_log.get_stats()
            self.after(0, lambda: self._on_loaded(recs, stats))
        threading.Thread(target=_worker, daemon=True).start()

    def _on_loaded(self, recs: List[TransactionRecord], stats: LogStats):
        self._records = recs
        self._update_stats(stats)
        self._apply_filters()

    # ── Stats bar ─────────────────────────────────────────────────────────

    def _update_stats(self, stats: LogStats):
        self._stats_labels["total"].config(text=str(stats.total))
        self._stats_labels["success"].config(text=str(stats.successes))
        self._stats_labels["fail"].config(text=str(stats.failures))
        self._stats_labels["rate"].config(text=f"{stats.success_rate}%")
        self._stats_labels["sessions"].config(text=str(stats.sessions))
        mins = int(stats.total_duration // 60)
        secs = int(stats.total_duration % 60)
        self._stats_labels["duration"].config(
            text=f"{mins}m {secs}s" if mins else f"{secs}s"
        )

    # ── Filter / display ──────────────────────────────────────────────────

    def _apply_filters(self, *_):
        action = self._action_var.get()
        status = self._status_var.get()
        pm     = self._pm_var.get()
        q      = self._search_var.get().lower()

        filtered = self._records
        if action != "All actions":
            filtered = [r for r in filtered if r.action == action]
        if status != "All statuses":
            filtered = [r for r in filtered if r.status == status]
        if pm != "All PMs":
            filtered = [r for r in filtered if r.pm_used == pm]
        if q:
            filtered = [
                r for r in filtered
                if q in r.app_name.lower()
                or q in r.app_id.lower()
                or q in r.action.lower()
                or q in r.status.lower()
                or q in r.pm_used.lower()
            ]

        self._filtered = filtered
        self._count_lbl.config(
            text=f"{len(filtered)} of {len(self._records)} records"
        )
        self._refresh_tree()

    def _refresh_tree(self):
        self._tree.delete(*self._tree.get_children())
        for rec in self._filtered:
            icon = _ACTION_ICONS.get(rec.action, "")
            ts   = rec.timestamp[:19].replace("T", " ")
            dur  = f"{rec.duration:.1f}" if rec.duration else "—"
            self._tree.insert(
                "", "end",
                iid=rec.transaction_id,
                values=(
                    ts,
                    f"{icon} {rec.action}",
                    rec.app_name or "(system)",
                    rec.status,
                    rec.pm_used or "—",
                    dur,
                    rec.attempts,
                ),
                tags=(rec.status,),
            )

    def _sort_by(self, heading: str):
        if self._sort_col == heading:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = heading
            self._sort_asc = False

        col_map = {c[0]: c[3] for c in _COLUMNS}
        key = col_map.get(heading, "timestamp")
        self._filtered.sort(
            key=lambda r: getattr(r, key, ""),
            reverse=not self._sort_asc,
        )
        self._refresh_tree()

    def _clear_filters(self):
        self._action_var.set("All actions")
        self._status_var.set("All statuses")
        self._pm_var.set("All PMs")
        self._search_var.set("")
        self._apply_filters()

    # ── Row detail ────────────────────────────────────────────────────────

    def _on_row_select(self, _event=None):
        sel = self._tree.selection()
        if not sel:
            return
        tid = sel[0]
        rec = next((r for r in self._records
                    if r.transaction_id == tid), None)
        if rec is None:
            return

        colour = _STATUS_COLOURS.get(rec.status, st.TEXT_PRIMARY)
        self._detail_header.config(
            text=(
                f"  {_ACTION_ICONS.get(rec.action, '')} {rec.action.upper()}  "
                f"{rec.app_name or '(system)'}  ·  "
                f"PM: {rec.pm_used or '—'}  ·  "
                f"{rec.duration:.1f}s  ·  "
                f"{rec.attempts} attempt(s)  ·  "
                f"Session: {rec.session_id}"
            ),
            fg=colour,
        )
        body = ""
        if rec.error:
            body += f"ERROR: {rec.error}\n"
        if rec.output:
            body += rec.output[-800:]   # last 800 chars
        if not body:
            body = "No additional output recorded."

        self._detail_text.config(state="normal")
        self._detail_text.delete("1.0", "end")
        self._detail_text.insert("1.0", body)
        self._detail_text.config(state="disabled")

    # ── Export / maintenance ──────────────────────────────────────────────

    def _export_text(self):
        path = filedialog.asksaveasfilename(
            title="Export log as text",
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            n = tx_log.export_text(path)
            messagebox.showinfo("Exported",
                                f"Wrote {n} records to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))

    def _export_yaml(self):
        path = filedialog.asksaveasfilename(
            title="Export log as YAML",
            defaultextension=".yaml",
            filetypes=[("YAML file", "*.yaml"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            n = tx_log.export_yaml(path)
            messagebox.showinfo("Exported",
                                f"Wrote {n} records to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))

    def _clear_old(self):
        if not messagebox.askyesno(
            "Clear old logs",
            "Delete log files older than 30 days?\nThis cannot be undone.",
        ):
            return
        try:
            n = tx_log.clear_old_logs(keep_days=30)
            messagebox.showinfo("Done",
                                f"Removed {n} old log file(s).")
            self._load_async()
        except Exception as exc:
            messagebox.showerror("Failed", str(exc))

    # ── Utility ───────────────────────────────────────────────────────────

    def _center(self, parent: tk.Widget):
        self.update_idletasks()
        pw = parent.winfo_x() + parent.winfo_width()  // 2
        ph = parent.winfo_y() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{pw - w//2}+{ph - h//2}")

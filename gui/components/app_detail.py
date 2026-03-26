"""
Linite - App Detail Popup
Shows full information about a selected app in a modal window.
"""

import tkinter as tk
from tkinter import ttk
import threading
import webbrowser
from typing import Optional

from core.catalog.flathub import load_flathub_metadata
from core.distro import DistroInfo
from core.installer import _pick_pm
from data.software_catalog import SoftwareEntry
from gui import styles as st


class AppDetailWindow(tk.Toplevel):
    """Modal window showing full details for a single app."""

    def __init__(self, parent, entry: SoftwareEntry, distro: Optional[DistroInfo] = None):
        super().__init__(parent)
        self.title(f"{entry.name} — Details")
        self.configure(bg=st.BG_DARK)
        self.resizable(True, True)
        self.minsize(520, 380)
        self.grab_set()           # modal

        self._entry = entry
        self._distro = distro
        self._latest_version_value: Optional[tk.Label] = None
        self._latest_notes_value: Optional[tk.Label] = None
        self._latest_link: Optional[tk.Label] = None

        self._build(entry, distro)
        self._center(parent)

    def _build(self, entry: SoftwareEntry, distro: Optional[DistroInfo]):
        pad = st.PADDING

        # ── Header ────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=st.BG_MEDIUM, padx=pad * 2, pady=pad)
        header.pack(fill="x")

        tk.Label(
            header, text=entry.icon, bg=st.BG_MEDIUM, font=(st.FONT_FAMILY, 32)
        ).pack(side="left", padx=(0, 12))

        title_col = tk.Frame(header, bg=st.BG_MEDIUM)
        title_col.pack(side="left", fill="x", expand=True)

        tk.Label(
            title_col, text=entry.name,
            bg=st.BG_MEDIUM, fg=st.TEXT_PRIMARY, font=st.FONT_TITLE, anchor="w"
        ).pack(anchor="w")

        cat_badge = tk.Label(
            title_col, text=entry.category,
            bg=st.BG_LIGHT, fg=st.TEXT_MUTED, font=st.FONT_SMALL, padx=6, pady=2
        )
        cat_badge.pack(anchor="w")

        # ── Body ──────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=st.BG_DARK, padx=pad * 2, pady=pad)
        body.pack(fill="both", expand=True)

        # Description
        self._row(body, "Description", entry.description, wrap=True)

        # Website
        if entry.website:
            self._link_row(body, "Website", entry.website)

        # Package manager that will be used
        if distro:
            pm = _pick_pm(entry, distro) or "none"
            spec = entry.get_spec(pm) if pm != "none" else None
            pm_text = pm.upper()
            if spec and spec.packages:
                pm_text += f"  →  {', '.join(spec.packages)}"
            elif spec and spec.flatpak_remote:
                pm_text += f"  →  Flatpak ({spec.flatpak_remote})"
            self._row(body, "Install via", pm_text)

        # All available package managers
        pms = list(entry.install_specs.keys())
        self._row(body, "Supported PMs", "  •  ".join(pms) or "—")

        # Flatpak metadata (version/changelog) via Flathub API, cached locally.
        self._build_flatpak_metadata_section(body, entry)

        # Pre/post commands note
        if distro:
            pm = _pick_pm(entry, distro)
            spec = entry.get_spec(pm) if pm else None
            if spec and spec.pre_commands:
                self._row(body, "Pre-install steps", f"{len(spec.pre_commands)} command(s)")
            if spec and spec.post_commands:
                self._row(body, "Post-install steps", f"{len(spec.post_commands)} command(s)")
            if spec and spec.sha256:
                self._row(body, "SHA-256", spec.sha256[:24] + "…")

        # ── Footer buttons ─────────────────────────────────────────────────
        footer = tk.Frame(self, bg=st.BG_MEDIUM, padx=pad, pady=8)
        footer.pack(fill="x")

        tk.Button(
            footer, text="Close",
            bg=st.BG_LIGHT, fg=st.TEXT_PRIMARY, font=st.FONT_NORMAL,
            relief="flat", bd=0, padx=16, pady=6, cursor="hand2",
            command=self.destroy,
        ).pack(side="right", padx=(0, pad))

        if entry.website:
            tk.Button(
                footer, text="🌐  Open Website",
                bg=st.ACCENT, fg="#ffffff", font=st.FONT_NORMAL,
                relief="flat", bd=0, padx=16, pady=6, cursor="hand2",
                command=lambda: webbrowser.open(entry.website),
            ).pack(side="right", padx=(0, 8))

    # ── Helpers ────────────────────────────────────────────────────────────

    def _row(self, parent, label: str, value: str, wrap: bool = False):
        row = tk.Frame(parent, bg=st.BG_DARK)
        row.pack(fill="x", pady=4)

        tk.Label(
            row, text=label + ":",
            bg=st.BG_DARK, fg=st.TEXT_MUTED, font=st.FONT_SMALL,
            anchor="w", width=18,
        ).pack(side="left", anchor="n")

        kw = dict(wraplength=340, justify="left") if wrap else {}
        tk.Label(
            row, text=value,
            bg=st.BG_DARK, fg=st.TEXT_PRIMARY, font=st.FONT_SMALL,
            anchor="w", **kw,
        ).pack(side="left", fill="x", expand=True)

    def _dynamic_row(self, parent, label: str, initial: str, wrap: bool = False) -> tk.Label:
        row = tk.Frame(parent, bg=st.BG_DARK)
        row.pack(fill="x", pady=4)

        tk.Label(
            row,
            text=label + ":",
            bg=st.BG_DARK,
            fg=st.TEXT_MUTED,
            font=st.FONT_SMALL,
            anchor="w",
            width=18,
        ).pack(side="left", anchor="n")

        kw = dict(wraplength=340, justify="left") if wrap else {}
        value = tk.Label(
            row,
            text=initial,
            bg=st.BG_DARK,
            fg=st.TEXT_PRIMARY,
            font=st.FONT_SMALL,
            anchor="w",
            **kw,
        )
        value.pack(side="left", fill="x", expand=True)
        return value

    def _dynamic_link_row(self, parent, label: str, initial: str = "—") -> tk.Label:
        row = tk.Frame(parent, bg=st.BG_DARK)
        row.pack(fill="x", pady=4)

        tk.Label(
            row,
            text=label + ":",
            bg=st.BG_DARK,
            fg=st.TEXT_MUTED,
            font=st.FONT_SMALL,
            anchor="w",
            width=18,
        ).pack(side="left")

        link = tk.Label(
            row,
            text=initial,
            bg=st.BG_DARK,
            fg=st.TEXT_MUTED,
            font=st.FONT_SMALL,
            anchor="w",
            cursor="arrow",
        )
        link.pack(side="left")
        return link

    def _build_flatpak_metadata_section(self, body, entry: SoftwareEntry):
        flatpak_spec = entry.install_specs.get("flatpak")
        if not flatpak_spec or not flatpak_spec.packages:
            return

        app_id = flatpak_spec.packages[0]
        self._row(body, "Flatpak ID", app_id)
        self._latest_version_value = self._dynamic_row(body, "Latest version", "Loading…")
        self._latest_notes_value = self._dynamic_row(
            body,
            "Changelog",
            "Loading release notes…",
            wrap=True,
        )
        self._latest_link = self._dynamic_link_row(body, "Release URL")

        threading.Thread(
            target=self._load_flatpak_metadata,
            args=(app_id,),
            daemon=True,
        ).start()

    def _load_flatpak_metadata(self, app_id: str):
        try:
            info = load_flathub_metadata(app_id)
            self.after(0, lambda: self._apply_flatpak_metadata(info, None))
        except Exception as exc:
            self.after(0, lambda: self._apply_flatpak_metadata(None, str(exc)))

    def _apply_flatpak_metadata(self, info: Optional[dict[str, str]], error: Optional[str]):
        if not self.winfo_exists():
            return

        if error:
            if self._latest_version_value is not None:
                self._latest_version_value.config(text="Unavailable")
            if self._latest_notes_value is not None:
                self._latest_notes_value.config(text="Could not load release metadata.")
            if self._latest_link is not None:
                self._latest_link.config(text="—", fg=st.TEXT_MUTED, cursor="arrow")
            return

        assert info is not None
        version = info.get("version", "Unknown")
        notes = info.get("notes", "No release notes available.")
        source = info.get("source", "")
        url = info.get("url", "")

        if self._latest_version_value is not None:
            suffix = ""
            if source == "cache":
                suffix = " (cached)"
            elif source == "cache-stale":
                suffix = " (cached, stale)"
            self._latest_version_value.config(text=f"{version}{suffix}")

        if self._latest_notes_value is not None:
            truncated = notes[:1200] + "…" if len(notes) > 1200 else notes
            self._latest_notes_value.config(text=truncated)

        if self._latest_link is not None:
            if url:
                self._latest_link.config(text=url, fg=st.ACCENT, cursor="hand2")
                self._latest_link.bind("<Button-1>", lambda _e: webbrowser.open(url))
                self._latest_link.bind("<Enter>", lambda _e: self._latest_link.config(fg=st.ACCENT_HOVER))
                self._latest_link.bind("<Leave>", lambda _e: self._latest_link.config(fg=st.ACCENT))
            else:
                self._latest_link.config(text="—", fg=st.TEXT_MUTED, cursor="arrow")

    def _link_row(self, parent, label: str, url: str):
        row = tk.Frame(parent, bg=st.BG_DARK)
        row.pack(fill="x", pady=4)

        tk.Label(
            row, text=label + ":",
            bg=st.BG_DARK, fg=st.TEXT_MUTED, font=st.FONT_SMALL,
            anchor="w", width=18,
        ).pack(side="left")

        link = tk.Label(
            row, text=url,
            bg=st.BG_DARK, fg=st.ACCENT, font=st.FONT_SMALL,
            anchor="w", cursor="hand2",
        )
        link.pack(side="left")
        link.bind("<Button-1>", lambda e: webbrowser.open(url))
        link.bind("<Enter>", lambda e: link.config(fg=st.ACCENT_HOVER))
        link.bind("<Leave>", lambda e: link.config(fg=st.ACCENT))

    def _center(self, parent):
        self.update_idletasks()
        pw = parent.winfo_x() + parent.winfo_width() // 2
        ph = parent.winfo_y() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{pw - w // 2}+{ph - h // 2}")

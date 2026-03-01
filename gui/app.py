"""
Linite - Main Application Window
Assembles all panels into the final Tkinter app.
"""

import threading
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional

from core import distro as distro_mod
from core.distro import DistroInfo
from core.installer import install_apps, Status as InstallStatus
from core.updater import update_system
from data.software_catalog import CATALOG, CATEGORIES, SoftwareEntry
from gui import styles as st
from gui.components.category_panel import CategoryPanel
from gui.components.software_panel import SoftwarePanel
from gui.components.progress_panel import ProgressPanel


class LiniteApp(tk.Tk):
    """Root window for the Linite application."""

    def __init__(self):
        super().__init__()
        self.title("Linite — Linux Software Installer")
        self.configure(bg=st.BG_DARK)
        self.geometry(f"{st.WINDOW_W}x{st.WINDOW_H}")
        self.minsize(800, 550)

        # Detect distro
        self._distro: DistroInfo = distro_mod.detect()
        self._busy = False

        self._build_ui()
        self._update_distro_label()

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        # ── Top title bar ─────────────────────────────────────────────────
        title_bar = tk.Frame(self, bg=st.BG_MEDIUM, height=52)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        tk.Label(
            title_bar,
            text="🐧  Linite",
            bg=st.BG_MEDIUM,
            fg=st.TEXT_PRIMARY,
            font=st.FONT_TITLE,
            padx=st.PADDING,
        ).pack(side="left", pady=10)

        tk.Label(
            title_bar,
            text="Install multiple Linux apps in one click",
            bg=st.BG_MEDIUM,
            fg=st.TEXT_MUTED,
            font=st.FONT_SMALL,
        ).pack(side="left", pady=10)

        self._distro_label = tk.Label(
            title_bar,
            text="",
            bg=st.BG_MEDIUM,
            fg=st.TEXT_SECONDARY,
            font=st.FONT_SMALL,
            padx=st.PADDING,
        )
        self._distro_label.pack(side="right")

        # ── Main body (sidebar + content) ──────────────────────────────────
        body = tk.Frame(self, bg=st.BG_DARK)
        body.pack(fill="both", expand=True)

        # Content area (software list + progress) — created first so the
        # CategoryPanel callback can reference _sw_panel during its __init__.
        content = tk.Frame(body, bg=st.BG_DARK)

        self._sw_panel = SoftwarePanel(content, entries=CATALOG)
        self._sw_panel.pack(fill="both", expand=True)

        # Sidebar — its __init__ fires on_select("All") which needs _sw_panel.
        self._cat_panel = CategoryPanel(
            body,
            categories=CATEGORIES,
            on_select=self._on_category_select,
            width=st.SIDEBAR_W,
        )

        # Pack in correct visual order: sidebar | divider | content
        self._cat_panel.pack(side="left", fill="y")
        tk.Frame(body, bg=st.BORDER, width=1).pack(side="left", fill="y")
        content.pack(side="left", fill="both", expand=True)

        tk.Frame(content, bg=st.BORDER, height=1).pack(fill="x")

        self._prog_panel = ProgressPanel(content)
        self._prog_panel.pack(fill="x")

        # ── Bottom action bar ──────────────────────────────────────────────
        action_bar = tk.Frame(self, bg=st.BG_MEDIUM, height=52)
        action_bar.pack(fill="x", side="bottom")
        action_bar.pack_propagate(False)

        # Install button
        self._install_btn = tk.Button(
            action_bar,
            text="⬇  Install Selected",
            bg=st.ACCENT,
            fg="#ffffff",
            font=st.FONT_MEDIUM,
            relief="flat",
            bd=0,
            padx=st.BTN_PADX,
            pady=st.BTN_PADY,
            cursor="hand2",
            activebackground=st.ACCENT_HOVER,
            activeforeground="#ffffff",
            command=self._on_install,
        )
        self._install_btn.pack(side="right", padx=st.PADDING, pady=10)

        # Update system button
        self._update_btn = tk.Button(
            action_bar,
            text="🔄  Update System",
            bg=st.BG_LIGHT,
            fg=st.TEXT_PRIMARY,
            font=st.FONT_MEDIUM,
            relief="flat",
            bd=0,
            padx=st.BTN_PADX,
            pady=st.BTN_PADY,
            cursor="hand2",
            activebackground=st.BG_LIGHT,
            command=self._on_update_system,
        )
        self._update_btn.pack(side="right", padx=(0, 8), pady=10)

        # Selection info
        self._sel_label = tk.Label(
            action_bar,
            text="No apps selected",
            bg=st.BG_MEDIUM,
            fg=st.TEXT_MUTED,
            font=st.FONT_NORMAL,
            padx=st.PADDING,
        )
        self._sel_label.pack(side="left", pady=10)

        # Poll selection count
        self._poll_selection()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _update_distro_label(self):
        d = self._distro
        text = f"🖥  {d.display_name}  |  PM: {d.package_manager}"
        self._distro_label.config(text=text)

    def _on_category_select(self, category: str):
        self._sw_panel.filter_by_category(category)

    def _poll_selection(self):
        selected = self._sw_panel.get_selected()
        n = len(selected)
        self._sel_label.config(
            text=f"{n} app{'s' if n != 1 else ''} selected" if n else "No apps selected"
        )
        self.after(300, self._poll_selection)

    def _set_busy(self, busy: bool):
        self._busy = busy
        state = "disabled" if busy else "normal"
        self._install_btn.config(state=state)
        self._update_btn.config(state=state)

    # ── Actions ────────────────────────────────────────────────────────────

    def _on_install(self):
        if self._busy:
            return
        selected = self._sw_panel.get_selected()
        if not selected:
            messagebox.showinfo("No selection", "Please select at least one app to install.")
            return

        names = "\n".join(f"  • {e.name}" for e in selected)
        if not messagebox.askyesno(
            "Confirm installation",
            f"Install {len(selected)} app(s)?\n\n{names}\n\nThis requires sudo / root access.",
        ):
            return

        self._prog_panel.reset(total_apps=len(selected))
        self._set_busy(True)

        def worker():
            def progress(app_id: str, line: str):
                self.after(0, lambda: self._prog_panel.log(line, tag="muted"))

            results = install_apps(selected, self._distro, progress_cb=progress)

            for result in results:
                success = result.status == InstallStatus.SUCCESS
                self.after(0, lambda r=result, s=success: self._prog_panel.app_done(r.app_name, s))

            self.after(0, lambda: self._set_busy(False))
            all_ok = all(r.status == InstallStatus.SUCCESS for r in results)
            msg = "All apps installed successfully!" if all_ok else "Some apps failed to install. Check the log."
            self.after(0, lambda: messagebox.showinfo("Installation complete", msg))

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_system(self):
        if self._busy:
            return
        if not messagebox.askyesno(
            "Update system",
            "This will update all installed packages on your system.\n"
            "It may take several minutes. Continue?",
        ):
            return

        self._prog_panel.reset()
        self._prog_panel.set_status("Updating …")
        self._set_busy(True)

        def worker():
            def progress(app_id: str, line: str):
                self.after(0, lambda: self._prog_panel.log(line, tag="muted"))

            results = update_system(self._distro, progress_cb=progress)
            all_ok = all(rc == 0 for rc, _ in results.values())
            self.after(0, lambda: self._set_busy(False))
            self.after(0, lambda: self._prog_panel.set_status("Update complete ✓" if all_ok else "Update finished with errors"))

            msg = "System updated successfully!" if all_ok else "Update finished with some errors. Check the log."
            self.after(0, lambda: messagebox.showinfo("Update complete", msg))

        threading.Thread(target=worker, daemon=True).start()


def run():
    app = LiniteApp()
    app.mainloop()

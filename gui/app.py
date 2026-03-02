"""
Linite - Main Application Window
Assembles all panels into the final Tkinter app.
Features: parallel installs, search, installed-state, detail popup,
          uninstall, export/import profiles, quick-start presets,
          transaction log.
"""

import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional

from core import distro as distro_mod
from core.distro import DistroInfo
from core.history import get_installed_ids
from core.log_engine import tx_log
from core.installer import install_apps, Status as InstallStatus
from core.package_manager import clear_cancel, request_cancel
from core.profiles import load_profile, save_profile
from core.uninstaller import uninstall_apps
from core.updater import update_system
from data.software_catalog import CATALOG, CATALOG_MAP, CATEGORIES, SoftwareEntry
from gui import styles as st
from gui.components.app_detail import AppDetailWindow
from gui.components.category_panel import CategoryPanel
from gui.components.log_viewer import LogViewerDialog
from gui.components.preset_panel import PresetPickerDialog
from gui.components.progress_panel import ProgressPanel
from gui.components.software_panel import SoftwarePanel

logger = logging.getLogger(__name__)

# Build per-category counts from catalog
_CAT_COUNTS: dict[str, int] = {}
for _e in CATALOG:
    _CAT_COUNTS[_e.category] = _CAT_COUNTS.get(_e.category, 0) + 1


class LiniteApp(tk.Tk):
    """Root window for the Linite application."""

    def __init__(self):
        super().__init__()
        self.title("Linite — Linux Software Installer")
        self.configure(bg=st.BG_DARK)
        self.geometry(f"{st.WINDOW_W}x{st.WINDOW_H}")
        self.minsize(880, 600)

        # Detect distro
        self._distro: DistroInfo = distro_mod.detect()
        tx_log.set_distro(self._distro.display_name)   # stamp log records
        self._busy = False
        self._busy_dot = None   # created inside _build_ui; guard before it exists

        self._build_ui()
        self._update_distro_label()
        # Load installed state from history in background
        self._refresh_installed_state()
        self._bind_shortcuts()
        # Offer to install yay on Arch-based systems that lack an AUR helper
        self.after(500, self._check_aur_helper)

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        # ── Top title bar ─────────────────────────────────────────────────
        title_bar = tk.Frame(self, bg=st.BG_MEDIUM, height=52)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        tk.Label(
            title_bar, text="🐧  Linite",
            bg=st.BG_MEDIUM, fg=st.TEXT_PRIMARY, font=st.FONT_TITLE, padx=st.PADDING,
        ).pack(side="left", pady=10)

        tk.Label(
            title_bar, text="Install multiple Linux apps in one click",
            bg=st.BG_MEDIUM, fg=st.TEXT_MUTED, font=st.FONT_SMALL,
        ).pack(side="left", pady=10)

        self._distro_label = tk.Label(
            title_bar, text="",
            bg=st.BG_MEDIUM, fg=st.TEXT_SECONDARY, font=st.FONT_SMALL, padx=st.PADDING,
        )
        self._distro_label.pack(side="right")

        # Quick-Start preset button
        qs_btn = tk.Button(
            title_bar, text="\u26a1  Quick Start",
            bg=st.ACCENT_DIM, fg="#c8bfff", font=st.FONT_SMALL,
            relief="flat", bd=0, padx=14, pady=6,
            cursor="hand2",
            activebackground=st.ACCENT, activeforeground="#ffffff",
            command=self._on_quick_start,
        )
        qs_btn.pack(side="right", padx=(0, 4), pady=10)
        qs_btn.bind("<Enter>", lambda _e: qs_btn.config(bg=st.ACCENT))
        qs_btn.bind("<Leave>", lambda _e: qs_btn.config(bg=st.ACCENT_DIM))

        # View Log button
        log_btn = tk.Button(
            title_bar, text="\U0001f4cb  Log",
            bg=st.BG_LIGHT, fg=st.TEXT_SECONDARY, font=st.FONT_SMALL,
            relief="flat", bd=0, padx=12, pady=6,
            cursor="hand2",
            activebackground=st.BG_MEDIUM, activeforeground=st.TEXT_PRIMARY,
            command=self._on_view_log,
        )
        log_btn.pack(side="right", padx=(0, 4), pady=10)
        log_btn.bind("<Enter>", lambda _e: log_btn.config(bg=st.BG_MEDIUM))
        log_btn.bind("<Leave>", lambda _e: log_btn.config(bg=st.BG_LIGHT))

        # ── Main body ──────────────────────────────────────────────────────
        body = tk.Frame(self, bg=st.BG_DARK)
        body.pack(fill="both", expand=True)

        # Content area created first so CategoryPanel can call filter on init
        content = tk.Frame(body, bg=st.BG_DARK)

        self._sw_panel = SoftwarePanel(
            content,
            entries=CATALOG,
            on_detail=self._open_detail,
        )
        self._sw_panel.pack(fill="both", expand=True)

        self._cat_panel = CategoryPanel(
            body,
            categories=CATEGORIES,
            on_select=self._on_category_select,
            counts=_CAT_COUNTS,
            width=st.SIDEBAR_W,
        )
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

        # Cancel (shown only while busy)
        self._cancel_btn = tk.Button(
            action_bar, text="⏹  Cancel",
            bg="#5a1a1a", fg="#ff8888", font=st.FONT_MEDIUM,
            relief="flat", bd=0, padx=st.BTN_PADX, pady=st.BTN_PADY,
            cursor="hand2", activebackground="#6e2020",
            command=self._on_cancel,
        )
        # Packed into the bar dynamically by _set_busy()

        # Install
        self._install_btn = tk.Button(
            action_bar, text="⬇  Install Selected",
            bg=st.ACCENT, fg="#ffffff", font=st.FONT_MEDIUM,
            relief="flat", bd=0, padx=st.BTN_PADX, pady=st.BTN_PADY,
            cursor="hand2", activebackground=st.ACCENT_HOVER, activeforeground="#ffffff",
            command=self._on_install,
        )
        self._install_btn.pack(side="right", padx=st.PADDING, pady=10)

        # Uninstall
        self._uninstall_btn = tk.Button(
            action_bar, text="🗑  Uninstall",
            bg="#5a1a1a", fg="#ff8888", font=st.FONT_MEDIUM,
            relief="flat", bd=0, padx=st.BTN_PADX, pady=st.BTN_PADY,
            cursor="hand2", activebackground="#6e2020",
            command=self._on_uninstall,
        )
        self._uninstall_btn.pack(side="right", padx=(0, 8), pady=10)

        # Update system
        self._update_btn = tk.Button(
            action_bar, text="🔄  Update System",
            bg=st.BG_LIGHT, fg=st.TEXT_PRIMARY, font=st.FONT_MEDIUM,
            relief="flat", bd=0, padx=st.BTN_PADX, pady=st.BTN_PADY,
            cursor="hand2", activebackground=st.BG_LIGHT,
            command=self._on_update_system,
        )
        self._update_btn.pack(side="right", padx=(0, 8), pady=10)

        # Profile: Export
        self._export_btn = tk.Button(
            action_bar, text="💾  Export Profile",
            bg=st.BG_LIGHT, fg=st.TEXT_SECONDARY, font=st.FONT_SMALL,
            relief="flat", bd=0, padx=12, pady=st.BTN_PADY,
            cursor="hand2", activebackground=st.BG_LIGHT,
            command=self._on_export_profile,
        )
        self._export_btn.pack(side="right", padx=(0, 4), pady=10)

        # Profile: Import
        self._import_btn = tk.Button(
            action_bar, text="📂  Import Profile",
            bg=st.BG_LIGHT, fg=st.TEXT_SECONDARY, font=st.FONT_SMALL,
            relief="flat", bd=0, padx=12, pady=st.BTN_PADY,
            cursor="hand2", activebackground=st.BG_LIGHT,
            command=self._on_import_profile,
        )
        self._import_btn.pack(side="right", padx=(0, 4), pady=10)

        # Selection info (left side)
        self._sel_label = tk.Label(
            action_bar, text="No apps selected",
            bg=st.BG_MEDIUM, fg=st.TEXT_MUTED, font=st.FONT_NORMAL, padx=st.PADDING,
        )
        self._sel_label.pack(side="left", pady=10)

        self._poll_selection()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _update_distro_label(self):
        d = self._distro
        self._distro_label.config(
            text=f"🖥  {d.display_name}  ·  {d.package_manager.upper()}"
        )

    def _on_category_select(self, category: str):
        self._sw_panel.filter_by_category(category)

    def _open_detail(self, entry: SoftwareEntry):
        AppDetailWindow(self, entry, self._distro)

    def _poll_selection(self):
        n = len(self._sw_panel.get_selected())
        self._sel_label.config(
            text=f"{n} app{'s' if n != 1 else ''} selected" if n else "No apps selected"
        )
        self.after(300, self._poll_selection)

    def _bind_shortcuts(self):
        """Register keyboard shortcuts for common actions."""
        self.bind("<Return>",    lambda _e: self._on_install())
        self.bind("<Control-a>", lambda _e: self._sw_panel._select_all(True))
        self.bind("<Escape>",    lambda _e: (self._on_cancel() if self._busy else None))
        self.bind("<Control-q>", lambda _e: self._on_quick_start())
        self.bind("<Control-l>", lambda _e: self._on_view_log())
        self.bind("<Control-f>", lambda _e: self._sw_panel.focus_search())

    def _set_busy(self, busy: bool):
        self._busy = busy
        state = "disabled" if busy else "normal"
        for btn in (self._install_btn, self._uninstall_btn,
                    self._update_btn, self._export_btn, self._import_btn):
            btn.config(state=state)
        # Busy dot in title bar: green when active
        if self._busy_dot is not None:
            dot_color = st.SUCCESS if busy else st.BG_MEDIUM
            self._busy_dot.config(fg=dot_color)
        if busy:
            self._cancel_btn.pack(side="right", padx=(0, 4), pady=10)
        else:
            self._cancel_btn.pack_forget()

    def _on_cancel(self):
        request_cancel()
        self._prog_panel.log("⏹ Cancelling — waiting for current command to finish …", tag="warn")
        self._cancel_btn.config(state="disabled")

    def _refresh_installed_state(self):
        """Load history-based installed IDs and push them to the panel."""
        def _load():
            ids = get_installed_ids()
            self.after(0, lambda: self._sw_panel.set_installed_ids(ids))
        threading.Thread(target=_load, daemon=True).start()

    # ── Log viewer ─────────────────────────────────────────────────────────

    def _on_view_log(self):
        """Open the Transaction Log viewer dialog."""
        LogViewerDialog(self)
    # ── AUR helper detection / bootstrap (Arch-based distros) ────────────

    def _check_aur_helper(self):
        """Prompt to install yay when the distro is Arch-based but no AUR helper is found."""
        if not self._distro.is_arch_based:
            return
        from core.detection import detect_aur_helper
        if detect_aur_helper():
            return
        if messagebox.askyesno(
            "AUR Helper Not Found",
            "You\'re on an Arch-based distro but neither yay nor paru is installed.\n\n"
            "Without an AUR helper, AUR-only packages cannot be installed.\n\n"
            "Would you like Linite to install yay automatically?",
            icon="warning",
        ):
            self._install_yay()

    def _install_yay(self):
        """Bootstrap yay from the AUR in a background thread, logging to the progress panel."""
        def _run():
            import subprocess, tempfile, os
            log = self._prog_panel.log
            log("[AUR] Installing yay from source — this may take a minute …")
            with tempfile.TemporaryDirectory(prefix="linite_yay_") as tmpdir:
                steps = [
                    # Make sure base-devel and git are present
                    ["sudo", "pacman", "-S", "--needed", "--noconfirm", "base-devel", "git"],
                    # Clone yay-bin (pre-compiled, faster than building from source)
                    ["git", "clone", "https://aur.archlinux.org/yay-bin.git",
                     os.path.join(tmpdir, "yay-bin")],
                ]
                for cmd in steps:
                    log(f"[AUR] $ {' '.join(cmd)}")
                    proc = subprocess.run(
                        cmd, capture_output=True, text=True, cwd=tmpdir
                    )
                    for line in (proc.stdout + proc.stderr).splitlines():
                        log(f"[AUR] {line}")
                    if proc.returncode != 0:
                        log("[AUR] ✗ Failed — check the log for details.", tag="error")
                        return

                # makepkg must NOT be run as root; run as current user
                srcdir = os.path.join(tmpdir, "yay-bin")
                log("[AUR] $ makepkg -si --noconfirm")
                proc = subprocess.run(
                    ["makepkg", "-si", "--noconfirm"],
                    capture_output=True, text=True, cwd=srcdir,
                )
                for line in (proc.stdout + proc.stderr).splitlines():
                    log(f"[AUR] {line}")
                if proc.returncode == 0:
                    log("[AUR] ✓ yay installed successfully!", tag="success")
                else:
                    log("[AUR] ✗ makepkg failed — check the log for details.", tag="error")

        threading.Thread(target=_run, daemon=True, name="linite-yay-bootstrap").start()
    # ── Quick-Start presets ────────────────────────────────────────────────

    def _on_quick_start(self):
        """Open the Quick-Start preset picker dialog."""
        PresetPickerDialog(self, on_apply=self._apply_preset)

    def _apply_preset(self, app_ids: set):
        """
        Called when the user clicks 'Apply' in the preset dialog.
        Merges the preset app IDs with whatever is already checked,
        then logs a summary to the progress panel.
        """
        current = self._sw_panel.get_selected_ids()
        merged  = current | app_ids
        self._sw_panel.set_selected_ids(merged)
        n_new = len(app_ids - current)
        self._prog_panel.log(
            f"\u26a1 Quick Start applied: {len(app_ids)} apps selected "
            f"({n_new} newly added).",
            tag="info",
        )

    # ── Install ────────────────────────────────────────────────────────────

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
        clear_cancel()

        def worker():
            _LOCK_PREFIX = "dpkg lock"

            def progress(app_id: str, line: str):
                tag = "warn" if _LOCK_PREFIX in line else "muted"
                self.after(0, lambda l=line, t=tag: self._prog_panel.log(l, tag=t))

            try:
                results = install_apps(selected, self._distro, progress_cb=progress)
                for result in results:
                    success = result.status == InstallStatus.SUCCESS
                    self.after(0, lambda r=result, s=success:
                               self._prog_panel.app_done(r.app_name, s))
                    # ── Transaction log ───────────────────────────────────
                    tx_log.log(
                        action   = "install",
                        status   = "success" if success else "failed",
                        app_id   = result.app_id,
                        app_name = result.app_name,
                        pm_used  = result.pm_used,
                        output   = result.output,
                        error    = result.error,
                    )
                all_ok = all(r.status == InstallStatus.SUCCESS for r in results)
                msg = "All apps installed successfully!" if all_ok \
                      else "Some apps failed to install. Check the log."
            except Exception as exc:
                logger.exception("Unexpected error during install")
                msg = f"Installation failed unexpectedly:\n{exc}"
            finally:
                self.after(0, lambda: self._set_busy(False))
                self.after(0, self._refresh_installed_state)

            self.after(0, lambda m=msg: messagebox.showinfo("Installation complete", m))

        threading.Thread(target=worker, daemon=True).start()

    def _on_uninstall(self):
        if self._busy:
            return
        selected = self._sw_panel.get_selected()
        if not selected:
            messagebox.showinfo("No selection", "Select apps to uninstall first.")
            return

        names = "\n".join(f"  • {e.name}" for e in selected)
        if not messagebox.askyesno(
            "Confirm uninstall",
            f"Remove {len(selected)} app(s)?\n\n{names}\n\nThis requires sudo / root access.",
        ):
            return

        self._prog_panel.reset(total_apps=len(selected))
        self._set_busy(True)
        clear_cancel()

        def worker():
            def progress(app_id: str, line: str):
                self.after(0, lambda l=line: self._prog_panel.log(l, tag="muted"))

            try:
                results = uninstall_apps(selected, self._distro, progress_cb=progress)
                for app_id, (rc, out) in results.items():
                    entry = CATALOG_MAP.get(app_id)
                    name  = entry.name if entry else app_id
                    success = (rc == 0)
                    self.after(0, lambda n=name, s=success:
                               self._prog_panel.app_done(n, s))
                    # ── Transaction log ───────────────────────────────────
                    tx_log.log(
                        action   = "uninstall",
                        status   = "success" if success else "failed",
                        app_id   = app_id,
                        app_name = name,
                        output   = out,
                        error    = "" if success else out,
                    )
                all_ok = all(rc == 0 for rc, _ in results.values())
                msg = "Apps removed successfully!" if all_ok \
                      else "Some apps failed to uninstall. Check the log."
            except Exception as exc:
                logger.exception("Unexpected error during uninstall")
                msg = f"Uninstall failed unexpectedly:\n{exc}"
            finally:
                self.after(0, lambda: self._set_busy(False))
                self.after(0, self._refresh_installed_state)

            self.after(0, lambda m=msg: messagebox.showinfo("Uninstall complete", m))

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
        self._prog_panel.set_indeterminate(True)
        self._set_busy(True)
        clear_cancel()

        def worker():
            _LOCK_PREFIX = "dpkg lock"

            def progress(app_id: str, line: str):
                tag = "warn" if _LOCK_PREFIX in line else "muted"
                self.after(0, lambda l=line, t=tag: self._prog_panel.log(l, tag=t))

            try:
                results = update_system(self._distro, progress_cb=progress)
                all_ok = all(rc == 0 for rc, _ in results.values())
                status_text = "Update complete \u2713" if all_ok else "Update finished with errors"
                msg = "System updated successfully!" if all_ok \
                      else "Update finished with some errors. Check the log."
                # ── Transaction log (one record per PM updated) ────────────
                for pm_name, (rc, out) in results.items():
                    tx_log.log(
                        action   = "system_update",
                        status   = "success" if rc == 0 else "failed",
                        pm_used  = pm_name,
                        app_name = f"System update ({pm_name})",
                        output   = out,
                        error    = "" if rc == 0 else out,
                    )
            except Exception as exc:
                logger.exception("Unexpected error during system update")
                all_ok = False
                status_text = "Update failed"
                msg = f"Update failed unexpectedly:\n{exc}"
            finally:
                self.after(0, lambda: self._prog_panel.set_indeterminate(False))
                self.after(0, lambda: self._set_busy(False))

            self.after(0, lambda s=status_text: self._prog_panel.set_status(s))
            self.after(0, lambda m=msg: messagebox.showinfo("Update complete", m))

        threading.Thread(target=worker, daemon=True).start()

    def _on_export_profile(self):
        selected_ids = self._sw_panel.get_selected_ids()
        if not selected_ids:
            messagebox.showinfo("Nothing to export", "Select at least one app first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save profile",
            defaultextension=".yaml",
            filetypes=[("Linite profile", "*.yaml *.yml"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            save_profile(selected_ids, path)
            messagebox.showinfo("Exported", f"Profile saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))

    def _on_import_profile(self):
        path = filedialog.askopenfilename(
            title="Open profile",
            filetypes=[
                ("Linite profile", "*.yaml *.yml *.json"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            ids = load_profile(path)
            # Only keep IDs that exist in the current catalog
            valid = {i for i in ids if i in CATALOG_MAP}
            unknown = set(ids) - valid
            self._sw_panel.set_selected_ids(valid)
            msg = f"Loaded {len(valid)} app(s) from profile."
            if unknown:
                msg += f"\n\nSkipped {len(unknown)} unknown id(s):\n" + ", ".join(sorted(unknown))
            messagebox.showinfo("Profile imported", msg)
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))


def run():
    app = LiniteApp()
    app.mainloop()

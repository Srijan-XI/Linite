#!/usr/bin/env python3
"""
Linite — Universal Linux Software Installer
Entry point: launches the GUI or runs CLI install/update commands.

Usage:
  python main.py                          # Launch GUI
  python main.py --cli install vlc git    # CLI install
  python main.py --cli update             # CLI update all
  python main.py --list                   # Print software catalog
  python main.py --export mysetup.sh      # Export a shell install script
  python main.py --export mysetup.sh --pm apt --cli install vlc git  # filtered export
  python main.py --verbose                # Enable debug logging
"""

import argparse
import sys

from utils.helpers import warn_if_not_linux, setup_logging, warn_if_not_root


def parse_args():
    parser = argparse.ArgumentParser(
        prog="linite",
        description="Linite — Install multiple Linux apps in one click",
    )
    parser.add_argument(
        "--cli",
        nargs="+",
        metavar="COMMAND",
        help="Run in CLI mode. COMMAND: 'install <ids...>'  or  'update'",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available software and exit.",
    )
    parser.add_argument(
        "--export",
        metavar="FILE",
        help="Export a reproducible bash install script and exit.  "
             "If --cli install <ids> is also given, only those apps are included; "
             "otherwise the full catalog is exported.",
    )
    parser.add_argument(
        "--pm",
        metavar="PM",
        choices=["apt", "dnf", "pacman", "zypper", "snap", "flatpak"],
        help="Preferred package manager to use when exporting a script (optional).",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Undo (uninstall) all apps from the most recent installation session.",
    )
    parser.add_argument(
        "--dry",
        action="store_true",
        help="With --rollback: preview what would be removed without making changes.",
    )
    parser.add_argument(
        "--skip-network-check",
        action="store_true",
        help="Skip network connectivity check before installation (not recommended).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug output.",
    )
    return parser.parse_args()


def cmd_export(output_file: str, ids: list, pm_hint: str | None):
    """Generate and save a reproducible bash install script."""
    from data.software_catalog import CATALOG, CATALOG_MAP
    from core.script_exporter import export_to_file

    if ids:
        entries = []
        for app_id in ids:
            entry = CATALOG_MAP.get(app_id)
            if entry is None:
                print(f"  [!] Unknown app id: '{app_id}' — skipped")
            else:
                entries.append(entry)
    else:
        entries = list(CATALOG)

    if not entries:
        print("No valid apps to export.")
        sys.exit(1)

    path = export_to_file(entries, output_file, pm_hint=pm_hint)
    print(f"✓ Script exported to: {path}  ({len(entries)} app(s))")


def cmd_rollback(dry_run: bool = False):
    """Rollback (uninstall) all apps from the most recent session."""
    from core.ops.uninstall import rollback_last_session
    from core.system import distro as distro_mod

    distro = distro_mod.detect()
    print(f"Detected: {distro.display_name}  |  Package manager: {distro.package_manager}")

    def progress(app_id, line):
        if line.strip():
            print(f"  [{app_id}] {line}" if app_id else f"  {line}")

    mode = "preview" if dry_run else "removing"
    print(f"\n── Rollback {mode} ──────────────────────────────────────")
    
    results = rollback_last_session(distro, progress_cb=progress, dry_run=dry_run)

    if not results:
        print("  (no apps to rollback)")
        return

    print(f"\n── Results ──────────────────────────────────────")
    success_count = sum(1 for rc, _ in results.values() if rc == 0)
    total_count = len(results)
    
    for app_id, (rc, output) in results.items():
        icon = "✓" if rc == 0 else "✗"
        status = "ok" if rc == 0 else "failed"
        print(f"  {icon} {app_id}: {status}")

    print(f"\n  {success_count}/{total_count} app(s) {'removed' if not dry_run else 'would be removed'}")


def cmd_list():
    """Print software catalog to stdout."""
    from data.software_catalog import CATALOG, CATEGORIES

    print(f"\n{'Category':<20} {'ID':<20} {'Name'}")
    print("─" * 65)
    for cat in CATEGORIES:
        apps = [a for a in CATALOG if a.category == cat]
        for app in apps:
            print(f"{cat:<20} {app.id:<20} {app.name}")
    print(f"\n{len(CATALOG)} apps in {len(CATEGORIES)} categories.\n")


def cmd_cli(args_list: list, verbose: bool, skip_network_check: bool = False):
    """Headless install / update."""
    from core.ops.install import install_apps
    from core.ops.update import update_system
    from core.system import distro as distro_mod
    from data.software_catalog import CATALOG_MAP

    distro = distro_mod.detect()
    print(f"Detected: {distro.display_name}  |  Package manager: {distro.package_manager}")
    warn_if_not_root()

    command = args_list[0].lower() if args_list else ""

    if command == "install":
        ids = args_list[1:]
        if not ids:
            print("Error: specify app IDs to install, e.g.: --cli install vlc git")
            sys.exit(1)

        entries = []
        for app_id in ids:
            entry = CATALOG_MAP.get(app_id)
            if entry is None:
                print(f"  [!] Unknown app id: '{app_id}' — skipped")
            else:
                entries.append(entry)

        if not entries:
            print("No valid apps found.")
            sys.exit(1)

        # Check network connectivity unless skipped
        if not skip_network_check:
            from core.system.network import warn_if_offline
            warning = warn_if_offline()
            if warning:
                print(f"\n⚠ {warning}\n")

        def progress(app_id, line):
            if line.strip():
                print(f"  [{app_id}] {line}")

        results = install_apps(entries, distro, progress_cb=progress)

        print("\n── Results ──────────────────────────────────────")
        for r in results:
            icon = "✓" if r.status.name == "SUCCESS" else "✗"
            print(f"  {icon} {r.app_name}  ({r.pm_used})  → {r.status.name}")
        print()

    elif command == "update":
        def progress(app_id, line):
            if line.strip():
                print(f"  {line}")

        results = update_system(distro, progress_cb=progress)
        for pm, (rc, _) in results.items():
            icon = "✓" if rc == 0 else "✗"
            print(f"  {icon} {pm} update finished (exit {rc})")

    else:
        print(f"Unknown CLI command: '{command}'. Use 'install' or 'update'.")
        sys.exit(1)


def cmd_gui():
    """Launch the Tkinter GUI."""
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print(
            "Error: tkinter is not installed.\n"
            "Install it with:  sudo apt install python3-tk   (Debian/Ubuntu)\n"
            "                  sudo dnf install python3-tkinter  (Fedora)\n"
            "                  sudo pacman -S tk  (Arch)\n",
            file=sys.stderr,
        )
        sys.exit(1)

    from gui.app import run
    run()


def main():
    args = parse_args()
    setup_logging(verbose=args.verbose)
    warn_if_not_linux()

    # Non-fatal startup catalog validation.
    try:
        from core.catalog.validation import catalog_lint
        from core.system import distro as distro_mod

        detected_pm = distro_mod.detect().package_manager
        lint_warnings = catalog_lint(current_pm=detected_pm)
        if lint_warnings:
            print(
                f"[WARNING] Catalog lint found {len(lint_warnings)} issue(s) for host pm '{detected_pm}'.",
                file=sys.stderr,
            )
            max_preview = 12
            for msg in lint_warnings[:max_preview]:
                print(f"  - {msg}", file=sys.stderr)
            if len(lint_warnings) > max_preview:
                hidden = len(lint_warnings) - max_preview
                print(f"  ... and {hidden} more", file=sys.stderr)
    except Exception as exc:
        print(f"[WARNING] Catalog lint failed: {exc}", file=sys.stderr)

    if args.list:
        cmd_list()
        return

    if args.export:
        # If --cli install <ids> is also provided, use those IDs; else full catalog
        ids = args.cli[1:] if (args.cli and args.cli[0].lower() == "install") else []
        cmd_export(args.export, ids, pm_hint=getattr(args, "pm", None))
        return

    if args.rollback:
        warn_if_not_root()
        cmd_rollback(dry_run=args.dry)
        return

    if args.cli:
        cmd_cli(args.cli, verbose=args.verbose, skip_network_check=args.skip_network_check)
        return

    # Default: launch GUI
    cmd_gui()


if __name__ == "__main__":
    main()

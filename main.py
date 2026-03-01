#!/usr/bin/env python3
"""
Linite — Universal Linux Software Installer
Entry point: launches the GUI or runs CLI install/update commands.

Usage:
  python main.py                          # Launch GUI
  python main.py --cli install vlc git    # CLI install
  python main.py --cli update             # CLI update all
  python main.py --list                   # Print software catalog
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
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug output.",
    )
    return parser.parse_args()


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


def cmd_cli(args_list: list, verbose: bool):
    """Headless install / update."""
    from core import distro as distro_mod
    from core.installer import install_apps
    from core.updater import update_system
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

    if args.list:
        cmd_list()
        return

    if args.cli:
        cmd_cli(args.cli, verbose=args.verbose)
        return

    # Default: launch GUI
    cmd_gui()


if __name__ == "__main__":
    main()

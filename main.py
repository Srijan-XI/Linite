#!/usr/bin/env python3
"""
Linite — Universal Linux Software Installer
Entry point: launches the GUI or runs CLI install/update commands.

Usage:
  python main.py                          # Launch GUI
  python main.py --light                  # Launch GUI in light mode
  python main.py --cli install vlc git    # CLI install
  python main.py --cli update             # CLI update all
    python main.py --remote user@host --install vlc git   # Remote install over SSH
    python main.py --remote user@host --update            # Remote update over SSH
  python main.py --list                   # Print software catalog
  python main.py --export mysetup.sh      # Export a shell install script
  python main.py --export mysetup.sh --pm apt --cli install vlc git  # filtered export
  python main.py --export-profile dev.json --cli install vlc git  # save profile
  python main.py --import-profile dev.json  # restore profile (prints IDs)
  python main.py --cache                  # pre-download all packages
  python main.py --cache --pm apt         # pre-download only apt packages
  python main.py --verbose                # Enable debug logging
"""

import argparse
import re
import shutil
import subprocess
import sys
import time

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
        "--daemon",
        action="store_true",
        help="Run scheduled daily update checks with desktop notifications.",
    )
    parser.add_argument(
        "--daemon-interval-hours",
        type=int,
        default=24,
        help="Interval in hours for --daemon update cycles (default: 24).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug output.",
    )
    parser.add_argument(
        "--light",
        action="store_true",
        help="Launch the GUI in light mode instead of the default dark mode.",
    )
    parser.add_argument(
        "--export-profile",
        metavar="FILE",
        help="Save the app selection (from --cli install <ids>) as a JSON profile file.",
    )
    parser.add_argument(
        "--import-profile",
        metavar="FILE",
        help="Load a profile file and print the contained app IDs (stdout).",
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Pre-download packages to ~/.cache/linite/ before installing. "
             "Supports apt, dnf, pacman, zypper. "
             "Combine with --pm to restrict to one package manager.",
    )
    parser.add_argument(
        "--cache-info",
        action="store_true",
        help="Show what is currently cached and its disk usage, then exit.",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Delete all pre-downloaded packages from ~/.cache/linite/ and exit.",
    )
    parser.add_argument(
        "--remote",
        metavar="TARGET",
        help="Run command on a remote host over SSH (user@host or user@host:port).",
    )
    parser.add_argument(
        "--install",
        nargs="+",
        metavar="APP_ID",
        help="Install app IDs (primarily used with --remote).",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Run system update (primarily used with --remote).",
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


def cmd_gui(light_mode: bool = False):
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

    if light_mode:
        from gui import styles
        styles.set_theme("light")
        styles._refresh_module_attrs()  # propagate to all colour constants

    from gui.app import run
    run()


def _notify(title: str, body: str):
    """Best-effort desktop notification; falls back to stdout."""
    if sys.platform.startswith("linux") and shutil.which("notify-send"):
        subprocess.run(["notify-send", title, body], capture_output=True, text=True)
    else:
        print(f"[notify] {title}: {body}")


def _estimate_updated_packages(output: str) -> int:
    """Best-effort package-count extraction from PM output."""
    patterns = [
        r"(\d+)\s+upgraded",
        r"Upgraded:\s*(\d+)",
        r"(\d+)\s+packages?\s+to\s+upgrade",
        r"Updated:\s*(\d+)",
    ]
    for pat in patterns:
        m = re.search(pat, output, flags=re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                return 0
    return 0


def cmd_daemon(interval_hours: int = 24):
    """Run periodic update checks/updates and issue desktop notifications."""
    from core.ops.update import update_system
    from core.system import distro as distro_mod

    interval_hours = max(1, interval_hours)
    distro = distro_mod.detect()
    _notify("Linite Daemon", f"Started (interval: {interval_hours}h, pm: {distro.package_manager})")
    print(f"Linite daemon running every {interval_hours}h (Ctrl+C to stop)")

    while True:
        started = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{started}] Running scheduled update cycle...")

        try:
            results = update_system(distro)
            failed = [pm for pm, (rc, _) in results.items() if rc != 0]
            updated_count = sum(_estimate_updated_packages(out) for _, (_, out) in results.items())

            if failed:
                _notify(
                    "Linite Update Warning",
                    f"Some managers failed: {', '.join(failed)}",
                )
            else:
                _notify(
                    "Linite Update Complete",
                    f"Cycle complete. Approx updated packages: {updated_count}",
                )
        except Exception as exc:
            _notify("Linite Daemon Error", str(exc))

        time.sleep(interval_hours * 3600)


def cmd_export_profile(output_file: str, ids: list[str]) -> None:
    """Serialize a set of app IDs to a JSON profile file."""
    from core.profiles import save_profile

    if not ids:
        print("Error: specify app IDs to save, e.g.: --cli install vlc git --export-profile mysetup.json")
        sys.exit(1)

    save_profile(set(ids), output_file, name="")
    print(f"✓ Profile saved to: {output_file}  ({len(ids)} app(s))")


def cmd_import_profile(profile_file: str) -> None:
    """Load a profile file and print the app IDs it contains."""
    from core.profiles import load_profile
    from data.software_catalog import CATALOG_MAP

    ids = load_profile(profile_file)
    valid = [i for i in ids if i in CATALOG_MAP]
    unknown = [i for i in ids if i not in CATALOG_MAP]

    print(f"Profile: {profile_file}  ({len(ids)} app(s) stored)")
    print()
    for app_id in valid:
        entry = CATALOG_MAP[app_id]
        print(f"  ✓  {app_id:<28} {entry.name}")
    if unknown:
        print()
        for app_id in unknown:
            print(f"  ?  {app_id:<28} (not in catalog)")

    print()
    print("# CLI usage:")
    print(f"  linite --cli install {' '.join(valid)}")


def cmd_cache(ids: list[str], pm_filter: str | None) -> None:
    """Pre-download packages to ~/.cache/linite/."""
    from core.cache import cache_packages
    from data.software_catalog import CATALOG, CATALOG_MAP

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
        print("No valid apps to cache.")
        sys.exit(1)

    print(f"Pre-downloading {len(entries)} app(s) …")
    results = cache_packages(entries, pm_filter=pm_filter, progress_cb=print)

    if results:
        ok = sum(1 for v in results.values() if v)
        print(f"\n✓ {ok}/{len(results)} package-manager block(s) cached successfully.")
    else:
        print("Nothing was cached (selected apps may use only unsupported PMs).")


def cmd_cache_info() -> None:
    """Print information about the local package cache."""
    from core.cache import cache_info, CACHE_DIR

    info = cache_info()
    if not info:
        print(f"Cache is empty (or does not exist: {CACHE_DIR})")
        return

    print(f"Cache directory: {CACHE_DIR}")
    print()
    total_mb = 0.0
    for pm, data in sorted(info.items()):
        print(f"  {pm:<12} {data['file_count']:>5} file(s)   {data['total_mb']:>7.1f} MB")
        total_mb += data["total_mb"]
    print()
    print(f"  {'TOTAL':<12} {'':>5}          {total_mb:>7.1f} MB")


def cmd_clear_cache(pm_filter: str | None = None) -> None:
    """Delete the local package cache."""
    from core.cache import clear_cache, CACHE_DIR

    clear_cache(pm=pm_filter)
    scope = pm_filter if pm_filter else "all"
    print(f"✓ Cache cleared ({scope}). Path: {CACHE_DIR}")


def cmd_remote(
    target_text: str,
    cli_args: list[str] | None,
    install_ids: list[str] | None,
    do_update: bool,
    skip_network_check: bool,
) -> int:
    """Execute a Linite command on a remote host over SSH."""
    from core.remote.install import build_remote_install_command
    from core.remote.ssh import parse_remote_target, quote_remote_args, run_remote_command

    if not shutil.which("ssh"):
        print("Error: ssh command not found in PATH.")
        return 2

    target = parse_remote_target(target_text)

    requested_modes = int(bool(install_ids)) + int(bool(do_update)) + int(bool(cli_args))
    if requested_modes == 0:
        print("Error: remote mode requires one of: --install ..., --update, or --cli ...")
        return 2
    if cli_args and (install_ids or do_update):
        print("Error: when using --remote --cli ..., do not also pass --install/--update.")
        return 2
    if install_ids and do_update:
        print("Error: choose only one remote operation (--install or --update).")
        return 2

    if cli_args:
        remote_command = quote_remote_args(["linite", *cli_args])
    elif install_ids:
        remote_command = build_remote_install_command(
            install_ids,
            skip_network_check=skip_network_check,
        )
    else:
        remote_command = quote_remote_args(["linite", "--cli", "update"])

    print(f"Remote target: {target.user}@{target.host}:{target.port}")
    print(f"Remote command: {remote_command}")
    print("\n── Remote Output ──────────────────────────────────────")
    rc, output = run_remote_command(target, remote_command)
    if output.strip():
        print(output.rstrip())
    print("\n── Remote Status ──────────────────────────────────────")
    icon = "✓" if rc == 0 else "✗"
    print(f"{icon} Exit code: {rc}")
    return rc


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

    if args.daemon:
        warn_if_not_root()
        try:
            cmd_daemon(interval_hours=args.daemon_interval_hours)
        except KeyboardInterrupt:
            print("\nLinite daemon stopped.")
        return

    if args.remote:
        try:
            rc = cmd_remote(
                target_text=args.remote,
                cli_args=args.cli,
                install_ids=args.install,
                do_update=args.update,
                skip_network_check=args.skip_network_check,
            )
        except ValueError as exc:
            print(f"Error: {exc}")
            sys.exit(2)
        sys.exit(rc)

    if args.install or args.update:
        print("Error: --install/--update shorthand is only valid with --remote.")
        print("Use local mode as: --cli install <ids...>  or  --cli update")
        sys.exit(2)

    # ── Profile import / export ──────────────────────────────────────────
    if args.import_profile:
        cmd_import_profile(args.import_profile)
        return

    if args.export_profile:
        ids = args.cli[1:] if (args.cli and args.cli[0].lower() == "install") else []
        cmd_export_profile(args.export_profile, ids)
        return

    # ── Cache management ─────────────────────────────────────────────────
    if args.cache_info:
        cmd_cache_info()
        return

    if args.clear_cache:
        cmd_clear_cache(pm_filter=getattr(args, "pm", None))
        return

    if args.cache:
        ids = args.cli[1:] if (args.cli and args.cli[0].lower() == "install") else []
        cmd_cache(ids, pm_filter=getattr(args, "pm", None))
        return

    if args.cli:
        cmd_cli(args.cli, verbose=args.verbose, skip_network_check=args.skip_network_check)
        return

    # Default: launch GUI
    cmd_gui(light_mode=getattr(args, "light", False))


if __name__ == "__main__":
    main()

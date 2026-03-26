#!/usr/bin/env python3
"""
Catalog validator for Linite.

Default mode checks structural integrity only.
Use --compat to also check host package-manager compatibility.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import tomllib

from core import distro as distro_mod
from core.catalog.validation import catalog_lint


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="check_catalog.py",
        description="Validate Linite catalog integrity.",
    )
    parser.add_argument(
        "--compat",
        action="store_true",
        help="Include host package-manager compatibility checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    warnings: list[str] = []

    # Raw-file duplicate ID detection (before loader merge/override behavior).
    catalog_dir = pathlib.Path("data/catalog")
    seen: dict[str, str] = {}
    for toml_file in sorted(catalog_dir.glob("*.toml")):
        data = tomllib.loads(toml_file.read_text(encoding="utf-8"))
        for app in data.get("apps", []):
            app_id = app.get("id", "").strip()
            if not app_id:
                continue
            if app_id in seen:
                warnings.append(
                    f"Duplicate app id '{app_id}' in {toml_file.name} (already defined in {seen[app_id]})"
                )
            else:
                seen[app_id] = toml_file.name

    current_pm = distro_mod.detect().package_manager if args.compat else None
    warnings.extend(catalog_lint(
        current_pm=current_pm,
        include_compatibility=args.compat,
    ))

    mode = "structural+compatibility" if args.compat else "structural"
    if not warnings:
        print(f"OK: catalog {mode} checks passed")
        return 0

    print(f"WARN: catalog {mode} checks found {len(warnings)} issue(s)")
    for msg in warnings:
        print(f" - {msg}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
